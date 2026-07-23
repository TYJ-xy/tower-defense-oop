# -*- coding: utf-8 -*-
"""Tower 继承体系.

策略模式核心:
  Tower 抽象基类定义攻击接口, 子类通过覆写实现不同攻击策略.
  防御塔自动选择射程内进度最大的敌人进行攻击.

继承链:
  GameObject (ABC)
    └── Tower (ABC)
          ├── ArrowTower   (快速, 单体, 低伤害)
          ├── CannonTower  (慢速, 溅射, 高伤害)
          └── IceTower     (中速, 减速效果)

设计模式:
  - 策略模式: 不同塔 = 不同攻击策略, 统一接口 update()
  - 与 Day6 Grader 同构: Grader.grade() ↔ Tower.update()
  - 工厂注册在 wave.py 的 TowerRegistry 中

对标 Day6:
  - 继承: class ArrowTower(Tower) ↔ class PassFailGrader(Grader)
  - @property: cost/range/cooldown 只读属性
  - 多态: for tower in self._towers: tower.update(...)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
import matplotlib.pyplot as plt

from .game_object import GameObject
from .projectile import Arrow, Cannonball, IceShard


class Tower(GameObject, ABC):
    """防御塔抽象基类.

    每帧自动选择射程内进度最大的敌人进行攻击.
    攻击冷却结束后创建 Projectile 实例.

    Attributes:
        _col, _row: 网格坐标
        _cooldown_remaining: 剩余冷却时间
        _target: 当前锁定的目标 Enemy
        _projectiles: 对本塔创建的子弹的引用 (由 Game 管理)
        _total_damage_dealt: 累计造成伤害 (统计分析用)
        _total_kills: 累计击杀数 (统计分析用)
    """

    def __init__(self, col: int, row: int):
        # 塔位于单元格中心
        super().__init__(col + 0.5, row + 0.5, size=0.45)
        self._col = col
        self._row = row
        # 根据放置位置错开初始冷却, 避免多塔同时开火
        # 导致伤害集中在同一帧爆发 ("血条一下掉很多")
        offset = ((col * 7 + row * 13) % 100) / 100.0
        self._cooldown_remaining = offset * self.attack_cooldown
        self._target: Optional[Enemy] = None
        self._total_damage_dealt = 0.0
        self._total_kills = 0

    # ── 子类定义 ────────────────────────────────────────────

    @property
    @abstractmethod
    def cost(self) -> int: ...
    @property
    @abstractmethod
    def attack_range(self) -> float: ...
    @property
    @abstractmethod
    def attack_cooldown(self) -> float: ...
    @property
    @abstractmethod
    def attack_damage(self) -> float: ...
    @property
    @abstractmethod
    def color(self) -> str: ...
    @property
    @abstractmethod
    def marker(self) -> str: ...
    @property
    @abstractmethod
    def type_name(self) -> str: ...

    # ── 公共属性 ────────────────────────────────────────────

    @property
    def grid_col(self) -> int:
        return self._col

    @property
    def grid_row(self) -> int:
        return self._row

    @property
    def total_damage(self) -> float:
        return self._total_damage_dealt

    @property
    def total_kills(self) -> int:
        return self._total_kills

    def record_kill(self) -> None:
        self._total_kills += 1

    # ── 创建子弹 (工厂方法) ─────────────────────────────────

    @abstractmethod
    def _create_projectile(self, target: 'Enemy') -> GameObject:
        """创建对应的子弹实例 (工厂方法)."""
        ...

    # ── 目标选择 (策略: 选择进度最大的敌人) ──────────────────

    def _find_target(self, enemies: List['Enemy']) -> Optional['Enemy']:
        """在射程内选择沿路径进度最大的敌人.

        策略: 优先攻击最接近基地的敌人 (path_progress 最大).
        """
        best = None
        best_progress = -1.0
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = np.sqrt(dx * dx + dy * dy)
            if dist <= self.attack_range and enemy.path_progress > best_progress:
                best = enemy
                best_progress = enemy.path_progress
        return best

    # ── 核心逻辑 ────────────────────────────────────────────

    def _do_update(self, dt: float, **kwargs) -> None:
        """更新塔状态: 冷却计时 → 选择目标 → 攻击.

        需要 kwargs 中包含:
            enemies: List[Enemy] — 场上所有敌人
            projectiles: List[Projectile] — 子弹列表 (用于追加)
        """
        enemies = kwargs.get('enemies', [])
        projectiles = kwargs.get('projectiles', None)

        # 冷却倒计时
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= dt

        # 选择目标
        self._target = self._find_target(enemies)

        # 攻击
        if self._target is not None and self._target.alive and self._cooldown_remaining <= 0:
            proj = self._create_projectile(self._target)
            if projectiles is not None:
                projectiles.append(proj)
            self._cooldown_remaining = self.attack_cooldown
            self._total_damage_dealt += self.attack_damage

    # ── 渲染 ─────────────────────────────────────────────────

    def draw(self, ax) -> None:
        """绘制塔 (带射程圈半透明指示)."""
        # 射程范围 (半透明圆)
        range_circle = plt.Circle(
            (self.x, self.y), self.attack_range,
            color=self.color, alpha=0.08, zorder=2)
        ax.add_patch(range_circle)

        # 塔本体
        size = self._size * 900
        ax.scatter(self.x, self.y, s=size, c=self.color,
                   marker=self.marker, edgecolors='black',
                   linewidths=0.8, zorder=10)

        # 冷却指示 (冷却中则显示灰色覆盖)
        if self._cooldown_remaining > 0:
            ratio = self._cooldown_remaining / self.attack_cooldown
            ax.scatter(self.x, self.y, s=size * ratio, c='gray',
                       marker=self.marker, alpha=0.5, zorder=11)


# ═══════════════════════════════════════════════════════════════
# 具体塔类
# ═══════════════════════════════════════════════════════════════

class ArrowTower(Tower):
    """箭塔 — 快速攻击, 单体伤害, 造价低."""

    @property
    def cost(self) -> int: return 50
    @property
    def attack_range(self) -> float: return 3.0
    @property
    def attack_cooldown(self) -> float: return 0.5
    @property
    def attack_damage(self) -> float: return 18
    @property
    def color(self) -> str: return '#2196F3'
    @property
    def marker(self) -> str: return '^'
    @property
    def type_name(self) -> str: return '箭塔'

    def _create_projectile(self, target):
        return Arrow(self.x, self.y, target)


class CannonTower(Tower):
    """炮塔 — 慢速攻击, 范围溅射, 高伤害."""

    @property
    def cost(self) -> int: return 100
    @property
    def attack_range(self) -> float: return 2.5
    @property
    def attack_cooldown(self) -> float: return 1.5
    @property
    def attack_damage(self) -> float: return 55
    @property
    def color(self) -> str: return '#F44336'
    @property
    def marker(self) -> str: return 's'
    @property
    def type_name(self) -> str: return '炮塔'

    @property
    def splash_radius(self) -> float:
        """溅射半径 (网格单位)."""
        return 1.0

    def _create_projectile(self, target):
        return Cannonball(self.x, self.y, target, self.splash_radius)


class IceTower(Tower):
    """冰塔 — 减速效果, 中等伤害."""

    @property
    def cost(self) -> int: return 75
    @property
    def attack_range(self) -> float: return 2.8
    @property
    def attack_cooldown(self) -> float: return 1.0
    @property
    def attack_damage(self) -> float: return 12
    @property
    def color(self) -> str: return '#00BCD4'
    @property
    def marker(self) -> str: return 'D'
    @property
    def type_name(self) -> str: return '冰塔'

    @property
    def slow_factor(self) -> float:
        return 0.4

    @property
    def slow_duration(self) -> float:
        return 2.0

    def _create_projectile(self, target):
        return IceShard(self.x, self.y, target,
                        self.slow_factor, self.slow_duration)


# ── 塔类型注册表 (简单工厂) ─────────────────────────────────

class TowerRegistry:
    """塔类型注册表 — 简单工厂模式.

    类比 Day6 SolverFactory: 字符串名 → 类映射.
    """

    _registry = {
        'arrow': ArrowTower,
        'cannon': CannonTower,
        'ice': IceTower,
    }

    @classmethod
    def get(cls, name: str):
        """根据名称获取塔类."""
        if name not in cls._registry:
            raise ValueError(f"未知塔类型 '{name}'. 可选: {list(cls._registry.keys())}")
        return cls._registry[name]

    @classmethod
    def create(cls, name: str, col: int, row: int) -> Tower:
        """创建塔实例.

        Args:
            name: 'arrow' | 'cannon' | 'ice'
            col, row: 网格坐标

        Returns:
            Tower 子类实例
        """
        return cls.get(name)(col, row)

    @classmethod
    def list_types(cls):
        """返回所有可用塔类型的 (name, cost, type_name) 列表."""
        result = []
        for name, tower_cls in cls._registry.items():
            # 创建临时实例获取属性
            temp = tower_cls(0, 0)
            result.append((name, temp.cost, temp.type_name))
            temp.kill()
        return result

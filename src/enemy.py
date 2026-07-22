"""Enemy 继承体系.

策略模式 + 继承:
  Enemy 抽象基类定义移动接口, 子类通过覆写属性实现差异化.
  不同敌人类型仅在数值参数上不同, 行为逻辑共享基类实现.

继承链:
  GameObject (ABC)
    └── Enemy (ABC)
          ├── Goblin   (快速, 低血量, 低奖励)
          ├── Orc      (中速, 中血量, 中奖励)
          └── Boss     (慢速, 高血量, 高奖励)

对标 Day6:
  - 继承: class Goblin(Enemy) 与 class PassFailGrader(Grader) 同构
  - 多态: 所有敌人共享 update() 接口, 每帧遍历列表统一调用
  - @property: hp/speed/reward 等属性封装
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt

from .game_object import GameObject


class Enemy(GameObject, ABC):
    """敌人抽象基类.

    沿路径移动, 到达终点后对基地造成伤害.
    子类只需定义属性 (hp, speed, reward, damage), 移动逻辑共享.

    Attributes:
        _waypoints: 路径拐点列表
        _wp_index: 当前目标拐点索引
        _path_progress: 沿路径行进的总距离 (用于塔选择最优目标)
        _hp: 当前血量
        _max_hp: 最大血量
        _speed: 移动速度 (网格单位/秒)
        _reward: 击杀奖励金币
        _damage_to_base: 到达基地造成的伤害
        _slow_factor: 减速系数 (1.0 = 正常, 0.5 = 减速 50%)
        _slow_timer: 减速剩余时间
    """

    def __init__(self, waypoints: List[Tuple[int, int]]):
        x0, y0 = waypoints[0]
        super().__init__(x0 + 0.5, y0 + 0.5, size=0.35)
        self._waypoints = waypoints
        self._wp_index = 1  # 第一个目标拐点
        self._path_progress = 0.0
        self._slow_factor = 1.0
        self._slow_timer = 0.0

    # ── 子类必须定义的属性 ──────────────────────────────────

    @property
    @abstractmethod
    def max_hp(self) -> float: ...
    @property
    @abstractmethod
    def speed(self) -> float: ...
    @property
    @abstractmethod
    def reward(self) -> int: ...
    @property
    @abstractmethod
    def damage_to_base(self) -> int: ...
    @property
    @abstractmethod
    def color(self) -> str: ...
    @property
    @abstractmethod
    def type_name(self) -> str: ...

    # ── 公共属性 ────────────────────────────────────────────

    @property
    def hp(self) -> float:
        return self._hp

    @property
    def hp_ratio(self) -> float:
        """血量百分比 (0.0 ~ 1.0)."""
        return max(0.0, self._hp / self.max_hp)

    @property
    def path_progress(self) -> float:
        """沿路径行进的总距离 (塔用此选择最靠前的目标)."""
        return self._path_progress

    @property
    def slow_factor(self) -> float:
        return self._slow_factor

    def take_damage(self, damage: float) -> bool:
        """受到伤害. 返回 True 表示死亡."""
        self._hp -= damage
        if self._hp <= 0:
            self._hp = 0
            self.kill()
            return True
        return False

    def apply_slow(self, factor: float, duration: float) -> None:
        """施加减速效果.

        Args:
            factor: 减速系数 (0.5 = 减速50%)
            duration: 持续时间 (秒)
        """
        if factor < self._slow_factor:  # 只取最大的减速效果
            self._slow_factor = factor
            self._slow_timer = duration

    # ── 核心逻辑 (模板方法的钩子) ────────────────────────────

    def _do_update(self, dt: float, **kwargs) -> None:
        """更新敌人位置 (沿路径移动)."""
        # 更新减速计时器
        if self._slow_timer > 0:
            self._slow_timer -= dt
            if self._slow_timer <= 0:
                self._slow_factor = 1.0

        # 计算有效速度
        effective_speed = self.speed * self._slow_factor

        # 向当前目标拐点移动
        while effective_speed > 0 and self._wp_index < len(self._waypoints):
            tx, ty = self._waypoints[self._wp_index]
            target = (tx + 0.5, ty + 0.5)  # 单元格中心
            dx = target[0] - self.x
            dy = target[1] - self.y
            dist = np.sqrt(dx * dx + dy * dy)

            if dist <= effective_speed * dt:
                # 到达当前拐点
                self.x, self.y = target
                self._path_progress += dist
                effective_speed -= dist / dt  # 剩余速度
                self._wp_index += 1
            else:
                # 向拐点移动
                self.x += (dx / dist) * effective_speed * dt
                self.y += (dy / dist) * effective_speed * dt
                self._path_progress += effective_speed * dt
                effective_speed = 0

    def has_reached_base(self) -> bool:
        """是否已到达基地 (最后一个拐点)."""
        return self._wp_index >= len(self._waypoints)

    # ── 渲染 ─────────────────────────────────────────────────

    def draw(self, ax) -> None:
        """绘制敌人 (圆形 + 血条)."""
        # 主体
        circle = ax.scatter(self.x, self.y, s=self._size * 800,
                           c=self.color, edgecolors='black',
                           linewidths=0.5, zorder=10, marker='o')
        # 血条 (敌人上方)
        if self.hp_ratio < 1.0:
            bar_w = 0.6
            bar_h = 0.06
            bar_y = self.y + 0.35
            # 背景条
            ax.add_patch(plt.Rectangle(
                (self.x - bar_w/2, bar_y), bar_w, bar_h,
                color='darkred', zorder=9))
            # 血量条
            ax.add_patch(plt.Rectangle(
                (self.x - bar_w/2, bar_y), bar_w * self.hp_ratio, bar_h,
                color='limegreen', zorder=10))
        return circle


# ═══════════════════════════════════════════════════════════════
# 具体敌人类 (策略具体实现)
# ═══════════════════════════════════════════════════════════════

class Goblin(Enemy):
    """哥布林 — 快速但脆弱的近战敌人."""

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self._hp = self.max_hp  # 在 super().__init__ 之后设置

    @property
    def max_hp(self) -> float: return 60
    @property
    def speed(self) -> float: return 2.5
    @property
    def reward(self) -> int: return 10
    @property
    def damage_to_base(self) -> int: return 1
    @property
    def color(self) -> str: return '#4CAF50'
    @property
    def type_name(self) -> str: return '哥布林'


class Orc(Enemy):
    """兽人 — 中等速度, 中等血量."""

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self._hp = self.max_hp

    @property
    def max_hp(self) -> float: return 180
    @property
    def speed(self) -> float: return 1.5
    @property
    def reward(self) -> int: return 25
    @property
    def damage_to_base(self) -> int: return 2
    @property
    def color(self) -> str: return '#FF9800'
    @property
    def type_name(self) -> str: return '兽人'


class Boss(Enemy):
    """Boss — 缓慢但血量极高, 高奖励."""

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self._hp = self.max_hp

    @property
    def max_hp(self) -> float: return 600
    @property
    def speed(self) -> float: return 0.9
    @property
    def reward(self) -> int: return 100
    @property
    def damage_to_base(self) -> int: return 5
    @property
    def color(self) -> str: return '#F44336'
    @property
    def type_name(self) -> str: return 'Boss'

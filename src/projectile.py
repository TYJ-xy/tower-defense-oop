"""Projectile 继承体系.

子弹沿直线飞向目标敌人, 命中后造成伤害和附加效果.
飞行过程中如果目标已死亡, 子弹自毁.

继承链:
  GameObject (ABC)
    └── Projectile (ABC)
          ├── Arrow       (快速, 单体直伤)
          ├── Cannonball  (中速, 溅射伤害)
          └── IceShard    (中速, 减速效果)

多态体现: 所有子弹共享 update() / draw() 接口,
         命中时各自调用不同的 _apply_effect().

对标 Day6:
  - 继承: class Arrow(Projectile) ↔ class LetterGrader(Grader)
  - 多态: for proj in self._projectiles: proj.update(...)
  - 与 Tower 的组合: Tower "creates" Projectile (依赖关系)
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt

from .game_object import GameObject


class Projectile(GameObject, ABC):
    """子弹抽象基类.

    从塔飞向目标敌人, 命中时造成伤害并触发附加效果.

    Attributes:
        _target: 目标敌人 (弱引用)
        _speed: 飞行速度 (网格单位/秒)
        _damage: 命中伤害
        _target_dead: 目标是否在子弹飞行期间死亡
    """

    def __init__(self, x: float, y: float, target, speed: float,
                 damage: float, size: float = 0.12):
        super().__init__(x, y, size=size)
        self._target = target
        self._speed = speed
        self._damage = damage
        self._hit = False

    # ── 子类可覆写 ──────────────────────────────────────────

    @abstractmethod
    def _apply_effect(self, enemies: list) -> None:
        """命中时对目标 (及附近敌人) 施加效果. 子类覆写."""
        ...

    # ── 核心逻辑 ────────────────────────────────────────────

    def _do_update(self, dt: float, **kwargs) -> None:
        """向目标飞行, 到达后造成伤害."""
        enemies = kwargs.get('enemies', [])

        if self._hit:
            return

        # 目标已死亡 → 自毁
        if not self._target.alive:
            self._hit = True
            self.kill()
            return

        # 向目标移动
        tx, ty = self._target.x, self._target.y
        dx, dy = tx - self.x, ty - self.y
        dist = np.sqrt(dx * dx + dy * dy)

        if dist <= self._speed * dt:
            # 到达目标: 造成伤害 + 附加效果
            self._target.take_damage(self._damage)
            self._apply_effect(enemies)
            self._hit = True
            self.kill()
        else:
            # 继续飞行
            self.x += (dx / dist) * self._speed * dt
            self.y += (dy / dist) * self._speed * dt

    # ── 渲染 ─────────────────────────────────────────────────

    def draw(self, ax) -> None:
        """绘制子弹 (小圆点)."""
        if self._hit:
            return
        ax.scatter(self.x, self.y, s=self._size * 300,
                   c=self.color, edgecolors='none',
                   alpha=0.9, zorder=9)


# ═══════════════════════════════════════════════════════════════
# 具体子弹类
# ═══════════════════════════════════════════════════════════════

class Arrow(Projectile):
    """箭矢 — 快速单体伤害."""

    def __init__(self, x: float, y: float, target):
        super().__init__(x, y, target, speed=12.0, damage=0, size=0.10)
        # 实际伤害由 Tower.attack_damage 决定, 这里设为0, 伤害在 tower.py 中记录
        self._damage = 18

    @property
    def color(self) -> str:
        return '#2196F3'

    def _apply_effect(self, enemies: list) -> None:
        pass  # 无额外效果


class Cannonball(Projectile):
    """炮弹 — 溅射伤害."""

    def __init__(self, x: float, y: float, target, splash_radius: float = 1.0):
        super().__init__(x, y, target, speed=8.0, damage=55, size=0.16)
        self._splash_radius = splash_radius

    @property
    def color(self) -> str:
        return '#FF5722'

    def _apply_effect(self, enemies: list) -> None:
        """溅射: 对目标周围敌人也造成伤害."""
        tx, ty = self._target.x, self._target.y
        splash_damage = self._damage * 0.5  # 溅射伤害为直伤的 50%
        for enemy in enemies:
            if not enemy.alive or enemy is self._target:
                continue
            dx = enemy.x - tx
            dy = enemy.y - ty
            if np.sqrt(dx * dx + dy * dy) <= self._splash_radius:
                enemy.take_damage(splash_damage)


class IceShard(Projectile):
    """冰晶 — 减速效果."""

    def __init__(self, x: float, y: float, target,
                 slow_factor: float = 0.4, slow_duration: float = 2.0):
        super().__init__(x, y, target, speed=9.0, damage=12, size=0.11)
        self._slow_factor = slow_factor
        self._slow_duration = slow_duration

    @property
    def color(self) -> str:
        return '#80DEEA'

    def _apply_effect(self, enemies: list) -> None:
        """对目标施加减速."""
        self._target.apply_slow(self._slow_factor, self._slow_duration)

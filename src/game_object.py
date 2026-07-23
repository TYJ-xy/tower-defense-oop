# -*- coding: utf-8 -*-
"""GameObject 抽象基类.

Template Method 模式:
  update() 定义更新流水线, 子类覆写 _do_update().
  所有游戏对象共享统一的存活/死亡状态管理.

对标 Day6 知识:
  - 抽象基类: ABC + @abstractmethod (与 Grader 相同)
  - @property: 封装内部状态 (与 BankAccount 相同)
  - 模板方法: update() 定义流程, _do_update() 是钩子
"""

from abc import ABC, abstractmethod
from typing import Tuple


class GameObject(ABC):
    """所有游戏对象的抽象基类.

    统一 alive 状态管理和 update/draw 接口.
    使用模板方法模式: update() 检查存活状态后调用 _do_update().

    Attributes:
        _position: [x, y] 连续坐标 (list, 便于就地修改)
        _size: 显示尺寸
        _alive: 是否存活
    """

    def __init__(self, x: float, y: float, size: float = 0.4):
        self._position = [float(x), float(y)]
        self._size = size
        self._alive = True

    # ── 属性 (对标 Day6 @property) ──────────────────────────

    @property
    def position(self) -> Tuple[float, float]:
        """当前位置 (x, y)."""
        return (self._position[0], self._position[1])

    @property
    def x(self) -> float:
        return self._position[0]

    @x.setter
    def x(self, val: float) -> None:
        self._position[0] = float(val)

    @property
    def y(self) -> float:
        return self._position[1]

    @y.setter
    def y(self, val: float) -> None:
        self._position[1] = float(val)

    @property
    def alive(self) -> bool:
        return self._alive

    def kill(self) -> None:
        """标记为死亡 (子类可覆写以添加死亡特效)."""
        self._alive = False

    # ── 模板方法 ────────────────────────────────────────────

    def update(self, dt: float, **kwargs) -> None:
        """模板方法: 检查存活后执行子类更新逻辑."""
        if not self._alive:
            return
        self._do_update(dt, **kwargs)

    @abstractmethod
    def _do_update(self, dt: float, **kwargs) -> None:
        """子类覆写: 具体更新逻辑 (钩子方法)."""
        ...

    # ── 抽象方法 ────────────────────────────────────────────

    @abstractmethod
    def draw(self, ax) -> None:
        """在 matplotlib axes 上绘制自身."""
        ...

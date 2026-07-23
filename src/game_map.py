# -*- coding: utf-8 -*-
"""GameMap — 塔防地图管理.

Composition: Game 拥有一个 GameMap 实例 (has-a, 而非 is-a).
对标 Day6: "Car has an Engine" → 组合优于继承.

功能:
  - 网格坐标系统 (cols × rows)
  - 敌人路径定义 (waypoints → 路径单元格)
  - 塔放置合法性检测
  - 坐标转换 (网格 ↔ 显示坐标)
"""

from typing import List, Tuple, Set


class GameMap:
    """塔防游戏地图.

    Attributes:
        cols, rows: 网格列数、行数
        waypoints: 路径拐点列表 [(col, row), ...]
        path_cells: 路径覆盖的所有单元格集合 (不可放置塔)
        start: 敌人生成位置
        base: 基地位置 (敌人到达后扣血)
    """

    # ── 默认路径配置 ────────────────────────────────────────
    DEFAULT_WAYPOINTS: List[Tuple[int, int]] = [
        (0, 1),    # 起点: 左侧进入
        (5, 1),    # 向右到 col 5
        (5, 5),    # 向下到 row 5
        (9, 5),    # 向右到 col 9
        (9, 2),    # 向上到 row 2
        (14, 2),   # 向右到 col 14
        (14, 7),   # 向下到 row 7 (基地)
    ]

    def __init__(self, cols: int = 15, rows: int = 9,
                 waypoints: List[Tuple[int, int]] = None):
        """
        Args:
            cols: 网格列数
            rows: 网格行数
            waypoints: 路径拐点. 默认使用 DEFAULT_WAYPOINTS.
        """
        self.cols = cols
        self.rows = rows
        self.waypoints = waypoints if waypoints is not None else self.DEFAULT_WAYPOINTS
        self._path_cells = self._compute_path_cells()
        self.start = self.waypoints[0]
        self.base = self.waypoints[-1]

    # ── 路径计算 ────────────────────────────────────────────

    def _compute_path_cells(self) -> Set[Tuple[int, int]]:
        """根据 waypoints 计算路径覆盖的所有网格单元格.

        相邻 waypoint 之间填充直线上的所有单元格 (仅水平/垂直).
        """
        cells = set()
        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]
            if x1 == x2:  # 垂直移动
                step = 1 if y2 > y1 else -1
                for y in range(y1, y2 + step, step):
                    cells.add((x1, y))
            elif y1 == y2:  # 水平移动
                step = 1 if x2 > x1 else -1
                for x in range(x1, x2 + step, step):
                    cells.add((x, y1))
        # 加入终点
        cells.add(self.waypoints[-1])
        return cells

    @property
    def path_cells(self) -> Set[Tuple[int, int]]:
        """路径覆盖的所有单元格 (不可放置塔)."""
        return self._path_cells

    # ── 坐标合法性检测 ──────────────────────────────────────

    def is_valid_cell(self, col: int, row: int) -> bool:
        """检查网格坐标是否在地图范围内."""
        return 0 <= col < self.cols and 0 <= row < self.rows

    def can_place_tower(self, col: int, row: int) -> bool:
        """检查 (col, row) 是否可以放置塔.

        Returns:
            True 如果: 在范围内 + 不在路径上.
        """
        return self.is_valid_cell(col, row) and (col, row) not in self._path_cells

    def is_on_path(self, col: int, row: int) -> bool:
        """检查 (col, row) 是否在路径上."""
        return (col, row) in self._path_cells

    # ── 坐标转换 ────────────────────────────────────────────

    def cell_center(self, col: int, row: int) -> Tuple[float, float]:
        """返回网格单元格的中心坐标 (用于渲染)."""
        return (col + 0.5, row + 0.5)

    def grid_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        """显示坐标 → 网格坐标 (用于点击检测)."""
        return (int(round(x)), int(round(y)))

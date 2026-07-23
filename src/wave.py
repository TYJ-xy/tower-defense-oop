# -*- coding: utf-8 -*-
"""波次系统 — 工厂模式.

WaveFactory 使用注册表模式管理波次配置.
每波包含多个 spawn 事件: (延迟时间, 敌人类型, 数量).

设计模式:
  - 工厂模式: WaveFactory 按模板生产敌人列表
  - 注册表模式: 波次配置集中管理, 易于扩展

对标 Day6:
  - 工厂: WaveFactory.create_wave() ↔ SolverFactory.create()
  - 注册表: _registry dict ↔ Grader 体系中的类映射
"""

from typing import List, Dict, Tuple
from .enemy import Enemy, Goblin, Orc, Boss


# ── 敌人类型 → 类映射 (注册表) ──────────────────────────────

ENEMY_REGISTRY = {
    'goblin': Goblin,
    'orc': Orc,
    'boss': Boss,
}


# ── 波次配置 ────────────────────────────────────────────────

# 格式: 每波是 [(spawn_delay_seconds, enemy_type, count), ...]
# spawn_delay: 该组敌人开始出现的时间偏移
# enemy_type: 'goblin' | 'orc' | 'boss'
# count: 该组敌人数量

WAVE_CONFIGS: List[List[Tuple[float, str, int]]] = [
    # 第 1 波: 简单 — 5 只哥布林
    [(0.0, 'goblin', 5)],

    # 第 2 波: 8 只哥布林, 分批
    [(0.0, 'goblin', 4),
     (2.0, 'goblin', 4)],

    # 第 3 波: 哥布林 + 兽人
    [(0.0, 'goblin', 5),
     (1.5, 'orc', 2)],

    # 第 4 波: 更多兽人
    [(0.0, 'goblin', 3),
     (1.0, 'orc', 3),
     (3.0, 'goblin', 5)],

    # 第 5 波: 第一个 Boss
    [(0.0, 'goblin', 5),
     (2.0, 'orc', 3),
     (5.0, 'boss', 1)],

    # 第 6 波: 兽人为主
    [(0.0, 'orc', 4),
     (2.0, 'orc', 3),
     (4.0, 'goblin', 6)],

    # 第 7 波: 混合大军
    [(0.0, 'goblin', 6),
     (1.5, 'orc', 3),
     (3.0, 'goblin', 4),
     (5.0, 'orc', 3)],

    # 第 8 波: 双 Boss
    [(0.0, 'goblin', 5),
     (2.0, 'orc', 3),
     (4.0, 'boss', 1),
     (4.5, 'orc', 2)],

    # 第 9 波: 高强度混合
    [(0.0, 'orc', 3),
     (1.5, 'goblin', 8),
     (3.0, 'orc', 4),
     (5.0, 'boss', 1)],

    # 第 10 波: 最终波 — 大量敌人
    [(0.0, 'goblin', 10),
     (2.0, 'orc', 5),
     (4.0, 'boss', 1),
     (5.0, 'boss', 1),
     (6.0, 'orc', 3)],
]


class Wave:
    """单波敌人进攻.

    Attributes:
        wave_number: 波次编号 (从1开始)
        spawn_events: 生成事件列表 [(delay, enemy_type_str, count), ...]
        total_enemies: 本波敌人总数
        enemies_killed: 已击杀数
        all_spawned: 是否已完成所有生成
        completed: 波次是否完成 (所有敌人已生成且已死亡)
    """

    def __init__(self, wave_number: int, spawn_events: List[Tuple[float, str, int]]):
        self.wave_number = wave_number
        self.spawn_events = spawn_events
        self.total_enemies = sum(count for _, _, count in spawn_events)
        self.enemies_killed = 0
        self._elapsed = 0.0
        self._spawn_index = 0
        self._counters: Dict[tuple, int] = {}  # (spawn_index, etype) → 已生成计数

    @property
    def all_spawned(self) -> bool:
        """是否已完成所有敌人生成."""
        return self._spawn_index >= len(self.spawn_events)

    @property
    def completed(self) -> bool:
        """波次是否已完成."""
        return self.all_spawned and self.enemies_killed >= self.total_enemies

    def get_spawns(self, dt: float, waypoints) -> List[Enemy]:
        """获取本时间步应生成的敌人.

        Args:
            dt: 经过的时间 (秒)
            waypoints: 路径拐点列表

        Returns:
            新生成的敌人列表
        """
        self._elapsed += dt
        spawned = []

        while self._spawn_index < len(self.spawn_events):
            delay, etype, count = self.spawn_events[self._spawn_index]
            if self._elapsed >= delay:
                enemy_cls = ENEMY_REGISTRY.get(etype)
                if enemy_cls is None:
                    raise ValueError(f"未知敌人类型: {etype}")

                # 生成该组敌人 (逐个, 间隔 0.3 秒)
                # 使用 (spawn_index, etype) 作为 key，避免同类型不同批次
                # 之间的计数器互相干扰 (如第2波两批哥布林)
                key = (self._spawn_index, etype)
                already = self._counters.get(key, 0)
                to_spawn = min(count - already,
                               max(1, int(dt / 0.3)) if already < count else 0)

                for _ in range(to_spawn):
                    enemy = enemy_cls(waypoints)
                    spawned.append(enemy)

                self._counters[key] = already + to_spawn
                if self._counters[key] >= count:
                    self._spawn_index += 1
            else:
                break

        return spawned


class WaveFactory:
    """波次工厂 — 根据编号生成 Wave 实例.

    使用注册表模式: WAVE_CONFIGS 列表定义每波的生成计划.
    """

    _configs = WAVE_CONFIGS

    @classmethod
    def total_waves(cls) -> int:
        """总波次数."""
        return len(cls._configs)

    @classmethod
    def create_wave(cls, wave_number: int) -> Wave:
        """创建指定编号的波次.

        Args:
            wave_number: 1-based 波次编号

        Returns:
            Wave 实例

        Raises:
            ValueError: 波次编号超出范围
        """
        if wave_number < 1 or wave_number > len(cls._configs):
            raise ValueError(
                f"波次编号 {wave_number} 超出范围 (1-{len(cls._configs)})"
            )
        return Wave(wave_number, cls._configs[wave_number - 1])

    @classmethod
    def get_wave_info(cls, wave_number: int) -> Dict:
        """获取波次信息 (用于 UI 显示)."""
        config = cls._configs[wave_number - 1]
        enemies = {}
        for _, etype, count in config:
            enemies[etype] = enemies.get(etype, 0) + count
        return {
            'wave': wave_number,
            'total': sum(enemies.values()),
            'enemies': enemies,
        }

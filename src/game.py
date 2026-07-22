"""Game — 塔防游戏主循环.

使用 matplotlib FuncAnimation 驱动游戏循环 + 键盘/鼠标交互.
这是整个项目的编排层 (Composition root), 组合 Map/Tower/Enemy/Wave/Stats.

依赖关系:
  Game ◆→ GameMap (组合)
  Game ◇→ Tower[] (聚合)
  Game ◇→ Enemy[] (聚合)
  Game ◇→ Projectile[] (聚合)
  Game → WaveFactory (依赖)
  Game → GameStats (依赖)

对标 Day6 CourseTaskSystem: Game 是课程任务系统的游戏版本,
  同样组合了多个对象并协调它们之间的交互.
"""

from typing import List, Optional, Tuple
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle, FancyBboxPatch

from .game_map import GameMap
from .enemy import Enemy
from .tower import Tower, TowerRegistry
from .projectile import Projectile
from .wave import Wave, WaveFactory
from .stats import GameStats


class Game:
    """塔防游戏主类 — 组合所有游戏组件并驱动主循环.

    Attributes:
        _map: 游戏地图
        _gold: 当前金币
        _base_hp: 基地血量
        _score: 总得分
        _wave_number: 当前波次 (0 = 未开始)
        _game_state: 'idle' | 'playing' | 'victory' | 'defeat'
        _towers: 已放置的塔列表
        _enemies: 场上敌人列表
        _projectiles: 飞行中的子弹列表
        _selected_tower: 当前选中的塔类型 ('arrow'|'cannon'|'ice')
        _stats: 统计分析器
    """

    def __init__(self, map_config=None):
        """初始化游戏.

        Args:
            map_config: 可选的地图配置 dict, 包含 cols/rows/waypoints.
        """
        # ── 地图 ──
        if map_config:
            self._map = GameMap(**map_config)
        else:
            self._map = GameMap()

        # ── 游戏状态 ──
        self._gold = 200
        self._base_hp = 10
        self._score = 0
        self._wave_number = 0
        self._game_state = 'idle'  # idle → playing → wave_done → idle ...

        # ── 实体容器 ──
        self._towers: List[Tower] = []
        self._enemies: List[Enemy] = []
        self._projectiles: List[Projectile] = []

        # ── 波次系统 ──
        self._current_wave: Optional[Wave] = None
        self._wave_bonus_gold = 0

        # ── 塔选择 ──
        self._selected_tower = 'arrow'

        # ── 统计分析 ──
        self._stats = GameStats()

        # ── Matplotlib 初始化 ──
        self._setup_plot()

    # ═══════════════════════════════════════════════════════════
    # 图形界面设置
    # ═══════════════════════════════════════════════════════════

    def _setup_plot(self) -> None:
        """设置 matplotlib 双面板布局: 游戏区 + 侧边栏."""
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei',
                                                    'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

        self._fig = plt.figure(figsize=(16, 8), facecolor='#1a1a2e')
        gs = self._fig.add_gridspec(1, 2, width_ratios=[4, 1],
                                     wspace=0.02)

        # 游戏面板
        self._ax_game = self._fig.add_subplot(gs[0])
        self._ax_game.set_facecolor('#16213e')

        # 侧边栏
        self._ax_side = self._fig.add_subplot(gs[1])
        self._ax_side.set_facecolor('#0f3460')
        self._ax_side.set_xlim(0, 100)
        self._ax_side.set_ylim(0, 100)
        self._ax_side.axis('off')

        # ── 事件绑定 ──
        self._fig.canvas.mpl_connect('button_press_event', self._on_click)
        self._fig.canvas.mpl_connect('key_press_event', self._on_key)

        # ── 动画 ──
        self._ani = FuncAnimation(self._fig, self._update, interval=80,
                                  cache_frame_data=False, save_count=0)

    # ═══════════════════════════════════════════════════════════
    # 输入处理
    # ═══════════════════════════════════════════════════════════

    def _on_key(self, event) -> None:
        """键盘事件处理.

        1/2/3: 选择塔类型
        SPACE: 开始下一波
        Q: 退出
        """
        if event.key == '1':
            self._selected_tower = 'arrow'
        elif event.key == '2':
            self._selected_tower = 'cannon'
        elif event.key == '3':
            self._selected_tower = 'ice'
        elif event.key == ' ':
            if self._game_state == 'idle':
                self._start_next_wave()
        elif event.key == 'q':
            plt.close(self._fig)

    def _on_click(self, event) -> None:
        """鼠标点击处理 — 在游戏区放置塔.

        仅在 idle 状态可放置 (防止战斗中临时布置).
        点击网格空白区域放置当前选中的塔.
        """
        if self._game_state not in ('idle',):
            return
        if event.inaxes != self._ax_game:
            return
        if event.xdata is None or event.ydata is None:
            return

        col = int(round(event.xdata - 0.5))
        row = int(round(event.ydata - 0.5))

        self._place_tower(col, row)

    def _place_tower(self, col: int, row: int) -> bool:
        """放置塔的通用方法 (可供 AI 或测试调用).

        Returns:
            True 如果成功放置.
        """
        # 合法性检查
        if not self._map.can_place_tower(col, row):
            return False

        # 检查是否已有塔
        for tower in self._towers:
            if tower.grid_col == col and tower.grid_row == row:
                return False

        # 金币检查
        tower_cls = TowerRegistry.get(self._selected_tower)
        temp = tower_cls(col, row)
        cost = temp.cost
        temp.kill()

        if self._gold < cost:
            return False

        # 创建并放置
        tower = TowerRegistry.create(self._selected_tower, col, row)
        self._towers.append(tower)
        self._gold -= cost
        self._score += 5  # 放置塔获得少量分数
        return True

    # ═══════════════════════════════════════════════════════════
    # 波次管理
    # ═══════════════════════════════════════════════════════════

    def _start_next_wave(self) -> None:
        """启动下一波敌人."""
        next_wave = self._wave_number + 1
        try:
            self._current_wave = WaveFactory.create_wave(next_wave)
        except ValueError:
            # 所有波次已完成
            self._game_state = 'victory'
            return

        self._wave_number = next_wave
        self._game_state = 'playing'
        self._wave_bonus_gold = 0
        self._stats.record_wave_start(next_wave)
        self._stats.record_gold(next_wave, self._gold)

    # ═══════════════════════════════════════════════════════════
    # 游戏主循环
    # ═══════════════════════════════════════════════════════════

    def _update(self, frame: int) -> Tuple:
        """每帧更新 (FuncAnimation 回调).

        固定时间步长 dt = 0.08s (约 12.5 FPS).
        对塔防游戏足够, 且视觉效果流畅.
        """
        dt = 0.08

        if self._game_state == 'playing':
            self._update_spawning(dt)
            self._update_enemies(dt)
            self._update_towers(dt)
            self._update_projectiles(dt)
            self._check_wave_complete()
            self._check_defeat()

        self._render()
        return ()

    def _update_spawning(self, dt: float) -> None:
        """波次敌人生成."""
        if self._current_wave is None:
            return
        new_enemies = self._current_wave.get_spawns(dt, self._map.waypoints)
        self._enemies.extend(new_enemies)

    def _update_enemies(self, dt: float) -> None:
        """更新所有敌人并检查到达基地."""
        for enemy in self._enemies:
            if enemy.alive and not enemy.has_reached_base():
                enemy.update(dt)
            elif enemy.alive and enemy.has_reached_base():
                # 敌人到达基地
                self._base_hp -= enemy.damage_to_base
                enemy.kill()

    def _update_towers(self, dt: float) -> None:
        """更新所有塔 (攻击逻辑)."""
        for tower in self._towers:
            tower.update(dt, enemies=self._enemies,
                        projectiles=self._projectiles)

    def _update_projectiles(self, dt: float) -> None:
        """更新所有子弹并检测击杀."""
        for proj in self._projectiles:
            if proj.alive:
                proj.update(dt, enemies=self._enemies)

        # 检查击杀并记录
        for enemy in self._enemies:
            if not enemy.alive and enemy.hp <= 0:
                if not getattr(enemy, '_kill_recorded', False):
                    enemy._kill_recorded = True
                    self._gold += enemy.reward
                    self._score += enemy.reward
                    self._wave_bonus_gold += enemy.reward
                    self._stats.record_kill(self._wave_number, enemy.type_name)
                    if self._current_wave:
                        self._current_wave.enemies_killed += 1

        # 清理死亡实体
        self._enemies = [e for e in self._enemies if e.alive]
        self._projectiles = [p for p in self._projectiles if p.alive]

    def _check_wave_complete(self) -> None:
        """检查当前波次是否完成."""
        if self._current_wave and self._current_wave.completed:
            # 波次完成奖励
            bonus = 50 + self._wave_number * 10  # 基础奖励 + 波次加成
            self._gold += bonus
            self._score += bonus
            self._stats.record_wave_end(
                self._wave_number,
                self._current_wave.total_enemies,
                self._wave_bonus_gold + bonus,
                self._base_hp,
            )
            self._stats.record_gold(self._wave_number, self._gold)

            # 检查是否所有波次完成
            if self._wave_number >= WaveFactory.total_waves():
                self._game_state = 'victory'
            else:
                self._game_state = 'idle'

    def _check_defeat(self) -> None:
        """检查失败条件."""
        if self._base_hp <= 0:
            self._base_hp = 0
            self._game_state = 'defeat'

    # ═══════════════════════════════════════════════════════════
    # 渲染
    # ═══════════════════════════════════════════════════════════

    def _render(self) -> None:
        """渲染完整画面: 游戏区 + 侧边栏."""
        self._render_game()
        self._render_sidebar()

    def _render_game(self) -> None:
        """渲染游戏面板."""
        ax = self._ax_game
        ax.clear()
        ax.set_facecolor('#16213e')
        ax.set_xlim(-1, self._map.cols + 1)
        ax.set_ylim(-1, self._map.rows + 1)
        ax.set_aspect('equal')
        ax.axis('off')

        # ── 网格线 ──
        for x in range(self._map.cols + 1):
            ax.axvline(x, color='#2a3a5c', linewidth=0.5, alpha=0.5, zorder=0)
        for y in range(self._map.rows + 1):
            ax.axhline(y, color='#2a3a5c', linewidth=0.5, alpha=0.5, zorder=0)

        # ── 路径 ──
        path_cells = list(self._map.path_cells)
        for col, row in path_cells:
            rect = Rectangle((col, row), 1, 1, color='#3d2b1f',
                            alpha=0.6, zorder=1)
            ax.add_patch(rect)

        # 路径方向箭头
        waypoints = self._map.waypoints
        for i in range(len(waypoints) - 1):
            x1, y1 = waypoints[i]
            x2, y2 = waypoints[i + 1]
            mx, my = (x1 + x2) / 2 + 0.5, (y1 + y2) / 2 + 0.5
            ax.annotate('', xy=((x2 + 0.5 + (x1 + 0.5)) / 2,
                                 (y2 + 0.5 + (y1 + 0.5)) / 2),
                        xytext=(x1 + 0.5, y1 + 0.5),
                        arrowprops=dict(arrowstyle='->', color='#8B7355',
                                       lw=1.5, alpha=0.5),
                        zorder=2)

        # ── 基地标记 ──
        bx, by = self._map.base
        ax.scatter(bx + 0.5, by + 0.5, s=500, c='#FFD700', marker='*',
                   edgecolors='#FF8C00', linewidths=1.5, zorder=15)
        ax.text(bx + 0.5, by - 0.3, f'❤️{self._base_hp}',
                ha='center', fontsize=9, color='white', fontweight='bold',
                zorder=20)

        # ── 起点标记 ──
        sx, sy = self._map.start
        ax.scatter(sx + 0.5, sy + 0.5, s=300, c='#00FF00', marker='s',
                   edgecolors='white', linewidths=1, alpha=0.7, zorder=15)

        # ── 塔放置预览 (idle 状态) ──
        if self._game_state == 'idle':
            for col in range(self._map.cols):
                for row in range(self._map.rows):
                    if self._map.can_place_tower(col, row):
                        has_tower = any(t.grid_col == col and t.grid_row == row
                                      for t in self._towers)
                        if not has_tower:
                            rect = Rectangle((col + 0.05, row + 0.05), 0.9, 0.9,
                                           color='#4CAF50', alpha=0.08,
                                           zorder=0)
                            ax.add_patch(rect)

        # ── 已放置的塔 ──
        for tower in self._towers:
            tower.draw(ax)
            # 塔等级/类型标签
            ax.text(tower.x, tower.y - 0.35, tower.type_name[0],
                    ha='center', fontsize=7, color='white', fontweight='bold',
                    zorder=15)

        # ── 敌人 ──
        for enemy in self._enemies:
            if enemy.alive:
                enemy.draw(ax)

        # ── 子弹 ──
        for proj in self._projectiles:
            if proj.alive:
                proj.draw(ax)

        # ── 状态信息 (游戏区内) ──
        status_text = self._get_status_text()
        ax.text(0.02, 0.98, status_text, transform=ax.transAxes,
                fontsize=11, color='white', fontfamily='monospace',
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='#0f3460', alpha=0.8))

        # ── 游戏结束覆盖 ──
        if self._game_state in ('victory', 'defeat'):
            text = '🎉 胜利!' if self._game_state == 'victory' else '💀 失败!'
            color = '#FFD700' if self._game_state == 'victory' else '#F44336'
            ax.text(0.5, 0.5, text, transform=ax.transAxes,
                    fontsize=48, color=color, fontweight='bold',
                    ha='center', va='center', alpha=0.9,
                    bbox=dict(boxstyle='round', facecolor='#1a1a2e',
                             alpha=0.85, pad=0.5))

    def _render_sidebar(self) -> None:
        """渲染侧边栏 (游戏信息 + 操作提示)."""
        ax = self._ax_side
        ax.clear()
        ax.set_facecolor('#0f3460')
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')

        y = 95
        gap = 6

        # ── 标题 ──
        ax.text(50, y, '🏰 塔防指挥中心', ha='center', fontsize=14,
                color='#FFD700', fontweight='bold')
        y -= gap * 2

        # ── 游戏数据 ──
        info_lines = [
            f'💰 金币: {self._gold}',
            f'❤️ 基地血量: {self._base_hp} / 10',
            f'🌊 波次: {self._wave_number} / {WaveFactory.total_waves()}',
            f'⭐ 得分: {self._score}',
            f'🗼 塔数: {len(self._towers)}',
        ]

        if self._current_wave and self._game_state == 'playing':
            info_lines.append(
                f'👾 剩余敌人: {self._current_wave.total_enemies - self._current_wave.enemies_killed}'
            )

        for line in info_lines:
            ax.text(5, y, line, fontsize=11, color='white',
                    fontfamily='monospace')
            y -= gap

        y -= gap

        # ── 状态标签 ──
        state_map = {
            'idle': ('按空格键开始下一波', '#4CAF50'),
            'playing': ('战斗中...', '#FF9800'),
            'victory': ('✨ 全部波次清除!', '#FFD700'),
            'defeat': ('💀 基地已陷落', '#F44336'),
        }
        state_text, state_color = state_map.get(
            self._game_state, ('', 'white'))
        ax.text(5, y, state_text, fontsize=11, color=state_color,
                fontweight='bold')
        y -= gap * 2

        # ── 塔选择 ──
        ax.text(5, y, '── 塔类型 ──', fontsize=11, color='#FFD700',
                fontweight='bold')
        y -= gap

        tower_types = TowerRegistry.list_types()
        tower_colors = {'arrow': '#2196F3', 'cannon': '#F44336', 'ice': '#00BCD4'}
        tower_keys = {'arrow': '[1]', 'cannon': '[2]', 'ice': '[3]'}

        for name, cost, type_name in tower_types:
            sel_marker = '▶ ' if name == self._selected_tower else '  '
            color = tower_colors.get(name, 'white')
            ax.text(8, y,
                    f'{sel_marker}{tower_keys[name]} {type_name}',
                    fontsize=10, color=color, fontfamily='monospace')
            ax.text(72, y, f'{cost}g', fontsize=10, color='#FFD700',
                    fontfamily='monospace')
            y -= gap

        y -= gap

        # ── 操作说明 ──
        ax.text(5, y, '── 操作 ──', fontsize=11, color='#FFD700',
                fontweight='bold')
        y -= gap
        controls = [
            '1/2/3  选择塔类型',
            '鼠标点击  放置塔',
            '空格键  开始波次',
            'Q  退出游戏',
        ]
        for ctrl in controls:
            ax.text(8, y, ctrl, fontsize=9, color='#AAAAAA',
                    fontfamily='monospace')
            y -= gap

        y -= gap

        # ── 放置预览区域 ──
        if self._game_state == 'idle':
            ax.text(5, y, '── 当前选择 ──', fontsize=10, color='#FFD700',
                    fontweight='bold')
            y -= gap
            tower_info = TowerRegistry.list_types()
            for name, cost, type_name in tower_info:
                if name == self._selected_tower:
                    ax.text(8, y, f'{type_name} ({cost}g)',
                            fontsize=11, color=tower_colors.get(name, 'white'),
                            fontweight='bold')

    def _get_status_text(self) -> str:
        """生成游戏区左上角状态文本."""
        if self._game_state == 'playing':
            return (f'波次 {self._wave_number} | '
                    f'💰{self._gold} | ❤️{self._base_hp}')
        elif self._game_state == 'idle':
            return f'准备阶段 | 💰{self._gold} | 按空格开始第{self._wave_number + 1}波'
        else:
            return f'💰{self._gold} | ❤️{self._base_hp}'

    # ═══════════════════════════════════════════════════════════
    # 公共接口
    # ═══════════════════════════════════════════════════════════

    def run(self) -> None:
        """启动游戏主循环."""
        plt.tight_layout()
        plt.show()

        # 游戏结束后显示统计报告
        if self._game_state in ('victory', 'defeat'):
            self._stats.show_report()
            plt.show()

    def get_state(self) -> dict:
        """返回当前游戏状态快照 (用于测试/AI分析)."""
        return {
            'gold': self._gold,
            'base_hp': self._base_hp,
            'wave': self._wave_number,
            'score': self._score,
            'state': self._game_state,
            'towers': len(self._towers),
            'enemies_alive': sum(1 for e in self._enemies if e.alive),
            'projectiles': len(self._projectiles),
        }

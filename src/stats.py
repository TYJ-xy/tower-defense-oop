# -*- coding: utf-8 -*-
"""GameStats — 游戏数据分析模块.

使用 pandas 记录游戏全程数据, matplotlib 生成统计图表.
对接 Day4 (Pandas) + Day3 (Matplotlib), 展示课程体系完整性.

记录内容:
  - 每波敌人击杀明细
  - 金币收支时间线
  - 各塔的累计伤害和击杀
"""

from typing import List, Optional
import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei',
                                            'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt


class GameStats:
    """游戏统计分析.

    记录完整游戏过程中的事件, 游戏结束后生成多维度分析图表.

    Attributes:
        wave_records: 每波的统计数据列表
        kill_events: 击杀事件 [(wave, enemy_type, time), ...]
        gold_history: 金币变化 [(wave, gold), ...]
    """

    def __init__(self):
        self.wave_records = []
        self.kill_events = []  # (wave, enemy_type, timestamp)
        self.gold_history = []  # (wave, gold_amount)
        self.tower_stats = {}   # tower_id -> {damage, kills, type}

    def record_wave_start(self, wave: int) -> None:
        """记录波次开始."""
        pass

    def record_kill(self, wave: int, enemy_type: str) -> None:
        """记录击杀事件."""
        self.kill_events.append((wave, enemy_type))

    def record_gold(self, wave: int, gold: int) -> None:
        """记录金币数量."""
        self.gold_history.append((wave, gold))

    def record_wave_end(self, wave: int, enemies_killed: int,
                        gold_earned: int, base_hp: int) -> None:
        """记录波次结束."""
        self.wave_records.append({
            '波次': wave,
            '击杀数': enemies_killed,
            '获得金币': gold_earned,
            '剩余基地血量': base_hp,
        })

    # ── 数据分析与可视化 ─────────────────────────────────────

    def show_report(self) -> None:
        """生成游戏结束后的分析报告 (2×2 子图布局)."""
        if not self.wave_records:
            print("无统计数据.")
            return

        df_waves = pd.DataFrame(self.wave_records)
        df_kills = pd.DataFrame(self.kill_events,
                                columns=['波次', '敌人类型'])

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('塔防游戏 — 战斗数据报告', fontsize=16, fontweight='bold')

        # 1. 每波击杀数柱状图
        ax1 = axes[0, 0]
        ax1.bar(df_waves['波次'], df_waves['击杀数'],
                color='#2196F3', edgecolor='white')
        ax1.set_title('每波击杀数')
        ax1.set_xlabel('波次')
        ax1.set_ylabel('击杀数')
        ax1.set_xticks(df_waves['波次'])

        # 2. 敌人类型分布饼图
        ax2 = axes[0, 1]
        if len(df_kills) > 0:
            type_counts = df_kills['敌人类型'].value_counts()
            colors = {'goblin': '#4CAF50', 'orc': '#FF9800', 'boss': '#F44336'}
            pie_colors = [colors.get(t, '#999') for t in type_counts.index]
            ax2.pie(type_counts.values, labels=type_counts.index,
                    autopct='%1.1f%%', colors=pie_colors, startangle=90)
            ax2.set_title('击杀敌人类型分布')

        # 3. 基地血量变化折线图
        ax3 = axes[1, 0]
        ax3.plot(df_waves['波次'], df_waves['剩余基地血量'],
                 'o-', color='#E91E63', linewidth=2, markersize=8)
        ax3.fill_between(df_waves['波次'], df_waves['剩余基地血量'],
                          alpha=0.2, color='#E91E63')
        ax3.set_title('基地血量变化')
        ax3.set_xlabel('波次')
        ax3.set_ylabel('剩余血量')
        ax3.set_ylim(0, max(df_waves['剩余基地血量']) + 2)
        ax3.set_xticks(df_waves['波次'])
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)

        # 4. 汇总数据表
        ax4 = axes[1, 1]
        ax4.axis('off')
        total_kills = df_waves['击杀数'].sum()
        total_gold = df_waves['获得金币'].sum()
        survived = len(df_waves)
        summary_text = (
            f"══════ 战斗总结 ══════\n\n"
            f"  完成波次:  {survived} 波\n"
            f"  总击杀数:  {total_kills}\n"
            f"  总获得金币: {total_gold}\n"
            f"  最终血量:  {df_waves['剩余基地血量'].iloc[-1]}\n"
            f"  每波均杀:  {total_kills / survived:.1f}\n"
        )
        ax4.text(0.1, 0.5, summary_text, transform=ax4.transAxes,
                 fontsize=14, fontfamily='monospace',
                 verticalalignment='center',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        # 保存图片到 doc/
        import os
        save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'doc')
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, 'battle_report.png'), dpi=150,
                    bbox_inches='tight')
        print(f"统计报告已保存到 doc/battle_report.png")

# -*- coding: utf-8 -*-
"""生成 UML 类图 (使用 matplotlib).

产生 doc/uml_diagram.png 用于嵌入项目报告.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# 必须在创建 figure 之前设置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def draw_class_box(ax, x, y, w, h, name, attrs, methods, color='#E3F2FD',
                   header_color='#1565C0', abstract=False):
    """绘制 UML 风格的类框 (三段式: 类名|属性|方法)."""
    # 类名区域
    title_h = 0.4
    rect_top = mpatches.FancyBboxPatch(
        (x, y + h - title_h), w, title_h,
        boxstyle="round,pad=0.02", facecolor=header_color,
        edgecolor='#0D47A1', linewidth=1.5, zorder=10)
    ax.add_patch(rect_top)
    style = 'italic' if abstract else 'normal'
    display_name = '<<abstract>>\n' + name if abstract else name
    ax.text(x + w/2, y + h - title_h/2, display_name, ha='center', va='center',
            fontsize=7, fontweight='bold', color='white', style=style, zorder=11)

    # 计算区域高度
    n_attrs = len(attrs)
    n_methods = len(methods)
    attr_h = max(0.3, n_attrs * 0.22)
    method_h = max(0.3, n_methods * 0.22)
    total_inner = title_h + attr_h + method_h

    # 属性区域
    if n_attrs > 0:
        attr_y = y + h - title_h - attr_h
        rect_attr = mpatches.FancyBboxPatch(
            (x, attr_y), w, attr_h, boxstyle="round,pad=0.02",
            facecolor=color, edgecolor='#90CAF9', linewidth=1, zorder=10)
        ax.add_patch(rect_attr)
        for i, attr in enumerate(attrs):
            ax.text(x + 0.08, attr_y + attr_h - 0.12 - i * 0.22, attr,
                    fontsize=5.5, fontfamily='monospace', color='#333', zorder=11)

    # 方法区域
    if n_methods > 0:
        method_y = y
        rect_method = mpatches.FancyBboxPatch(
            (x, method_y), w, method_h, boxstyle="round,pad=0.02",
            facecolor='#FAFAFA', edgecolor='#BDBDBD', linewidth=1, zorder=10)
        ax.add_patch(rect_method)
        for i, method in enumerate(methods):
            ax.text(x + 0.08, method_y + method_h - 0.12 - i * 0.22, method,
                    fontsize=5.5, fontfamily='monospace', color='#333', zorder=11)


def draw_inheritance_arrow(ax, from_xy, to_xy):
    """绘制继承箭头 (空心三角, 实线)."""
    ax.annotate('', xy=to_xy, xytext=from_xy,
                arrowprops=dict(arrowstyle='-|>', facecolor='white',
                               edgecolor='#333', linewidth=1.5),
                zorder=5)


def draw_dependency_arrow(ax, from_xy, to_xy, label=''):
    """绘制依赖箭头 (虚线, 开放箭头)."""
    ax.annotate(label, xy=to_xy, xytext=from_xy,
                arrowprops=dict(arrowstyle='->', linestyle='dashed',
                               color='#666', linewidth=1),
                fontsize=6, color='#666', zorder=5)


def main():
    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    ax.set_xlim(-1, 25)
    ax.set_ylim(-1, 17)
    ax.axis('off')
    ax.set_facecolor('#FAFAFA')

    # ═══════════════════════════════════════════════════════════
    # GameObject (顶部中央) - 抽象基类
    # ═══════════════════════════════════════════════════════════
    draw_class_box(ax, 10, 13, 3.2, 1.8, 'GameObject', [
        '- _position: [float, float]',
        '- _size: float',
        '- _alive: bool',
    ], [
        '+ position: tuple (property)',
        '+ update(dt): None',
        '# _do_update(dt): None (abstract)',
        '+ draw(ax): None (abstract)',
    ], color='#E3F2FD', header_color='#1565C0', abstract=True)

    # ═══════════════════════════════════════════════════════════
    # Enemy 继承链 (左侧)
    # ═══════════════════════════════════════════════════════════
    draw_class_box(ax, 1.5, 9, 2.8, 2.0, 'Enemy', [
        '- _waypoints: list',
        '- _wp_index: int',
        '- _hp: float',
        '- _slow_factor: float',
        '- _path_progress: float',
    ], [
        '+ hp: float (property)',
        '+ speed: float (abstract)',
        '+ reward: int (abstract)',
        '+ take_damage(d): bool',
        '+ apply_slow(f, t): None',
        '# _do_update(dt): None',
    ], color='#E8F5E9', header_color='#2E7D32', abstract=True)

    # Enemy 子类
    for i, (name, hp, spd, reward, x_pos) in enumerate([
        ('Goblin', 60, 2.5, 10, 0.3),
        ('Orc', 180, 1.5, 25, 3.1),
        ('Boss', 600, 0.9, 100, 5.9),
    ]):
        draw_class_box(ax, x_pos, 5.5, 2.4, 1.2, name, [
            f'- _hp: float = {hp}',
        ], [
            f'+ max_hp: {hp}',
            f'+ speed: {spd}',
            f'+ reward: {reward}',
        ], color='#C8E6C9', header_color='#388E3C')
        draw_inheritance_arrow(ax, (x_pos + 1.2, 5.5 + 1.2), (2.9, 9.0))

    # ═══════════════════════════════════════════════════════════
    # Tower 继承链 (中间)
    # ═══════════════════════════════════════════════════════════
    draw_class_box(ax, 12, 9, 2.8, 2.0, 'Tower', [
        '- _col, _row: int',
        '- _cooldown_remaining: float',
        '- _target: Enemy',
        '- _total_kills: int',
    ], [
        '+ cost: int (abstract)',
        '+ attack_range: float (abstract)',
        '+ attack_cooldown: float (abstract)',
        '+ attack_damage: float (abstract)',
        '# _create_projectile(t): Proj',
        '# _do_update(dt): None',
    ], color='#E3F2FD', header_color='#1565C0', abstract=True)

    # Tower 子类
    tower_specs = [
        ('ArrowTower', 10.5, 'cost=50\nrange=3.0\ncd=0.5s\ndmg=18'),
        ('CannonTower', 13.3, 'cost=100\nrange=2.5\ncd=1.5s\ndmg=55\nsplash=1.0'),
        ('IceTower', 16.1, 'cost=75\nrange=2.8\ncd=1.0s\ndmg=12\nslow=40%'),
    ]
    for name, x_pos, spec in tower_specs:
        lines = spec.split('\n')
        attrs = [f'- {lines[0]}'] if lines else []
        methods = [f'+ {l}' for l in lines[1:]] if len(lines) > 1 else lines
        draw_class_box(ax, x_pos, 5.5, 2.4, 1.2, name, attrs, methods,
                      color='#BBDEFB', header_color='#1976D2')
        draw_inheritance_arrow(ax, (x_pos + 1.2, 5.5 + 1.2), (13.4, 9.0))

    # ═══════════════════════════════════════════════════════════
    # Projectile 继承链 (右侧)
    # ═══════════════════════════════════════════════════════════
    draw_class_box(ax, 21, 9, 2.4, 1.6, 'Projectile', [
        '- _target: Enemy',
        '- _speed: float',
        '- _damage: float',
        '- _hit: bool',
    ], [
        '# _apply_effect(e): None',
        '# _do_update(dt): None',
        '+ draw(ax): None',
    ], color='#FFF3E0', header_color='#E65100', abstract=True)

    # Projectile 子类
    for i, (name, spec, y_pos) in enumerate([
        ('Arrow', 'dmg=18, single', 7.0),
        ('Cannonball', 'dmg=55, splash', 5.5),
        ('IceShard', 'dmg=12, slow', 4.0),
    ]):
        draw_class_box(ax, 20.5, y_pos, 2.4, 1.0, name, [],
                      [f'+ damage: {spec.split(",")[0]}', f'+ effect: {spec.split(",")[1] if "," in spec else ""}'],
                      color='#FFE0B2', header_color='#EF6C00')
        draw_inheritance_arrow(ax, (21.7, y_pos + 1.0), (22.2, 9.0))

    # ═══════════════════════════════════════════════════════════
    # 辅助类 (底部)
    # ═══════════════════════════════════════════════════════════
    draw_class_box(ax, 0.5, 1.5, 2.6, 1.2, 'GameMap', [
        '+ cols, rows: int', '+ waypoints: list',
    ], [
        '+ can_place_tower(c,r): bool',
        '+ is_on_path(c,r): bool',
    ], color='#F3E5F5', header_color='#7B1FA2')

    draw_class_box(ax, 3.6, 1.5, 2.6, 1.2, 'Wave', [
        '+ wave_number: int', '+ total_enemies: int',
    ], [
        '+ get_spawns(dt,wp): list',
        '+ completed: bool',
    ], color='#F3E5F5', header_color='#7B1FA2')

    draw_class_box(ax, 6.7, 1.5, 2.6, 1.2, 'WaveFactory', [
        '- _configs: list (class)',
    ], [
        '+ create_wave(n): Wave',
        '+ total_waves(): int',
    ], color='#F3E5F5', header_color='#7B1FA2')

    draw_class_box(ax, 9.8, 1.5, 2.6, 1.2, 'TowerRegistry', [
        '- _registry: dict (class)',
    ], [
        '+ create(name,c,r): Tower',
        '+ list_types(): list',
    ], color='#E0F2F1', header_color='#00695C')

    draw_class_box(ax, 12.9, 1.2, 3.4, 2.0, 'Game', [
        '- _map: GameMap',
        '- _gold: int',
        '- _base_hp: int',
        '- _towers: list[Tower]',
        '- _enemies: list[Enemy]',
        '- _projectiles: list[Proj]',
    ], [
        '+ run(): None',
        '+ get_state(): dict',
        '- _update(frame): None',
        '- _place_tower(c,r): bool',
    ], color='#E0F2F1', header_color='#00695C')

    draw_class_box(ax, 18, 1.5, 2.6, 1.2, 'GameStats', [
        '+ wave_records: list',
        '+ kill_events: list',
    ], [
        '+ show_report(): None',
        '+ record_kill(w,t): None',
    ], color='#E0F2F1', header_color='#00695C')

    # ═══════════════════════════════════════════════════════════
    # 继承箭头 (到 GameObject)
    # ═══════════════════════════════════════════════════════════
    draw_inheritance_arrow(ax, (3.5, 9.0 + 2.0), (11.3, 13.0))      # Enemy → GO
    draw_inheritance_arrow(ax, (13.4, 9.0 + 2.0), (11.6, 13.0))     # Tower → GO
    draw_inheritance_arrow(ax, (22.2, 9.0 + 1.6), (11.9, 13.0))     # Projectile → GO

    # ═══════════════════════════════════════════════════════════
    # 关系箭头
    # ═══════════════════════════════════════════════════════════
    # Tower → Projectile (creates)
    draw_dependency_arrow(ax, (16.5, 7.5), (19.5, 7.5), '<<creates>>')

    # Game ◆→ GameMap (组合)
    ax.annotate('', xy=(2.0, 2.7), xytext=(12.9, 3.2),
                arrowprops=dict(arrowstyle='->', color='#333', linewidth=1.5),
                zorder=5)
    ax.plot(12.9, 3.2, 'D', color='#333', markersize=8, zorder=6)

    # WaveFactory → Wave
    draw_dependency_arrow(ax, (6.7, 2.7), (4.9, 2.7), '<<creates>>')

    # Game → WaveFactory / GameStats / TowerRegistry
    draw_dependency_arrow(ax, (12.0, 2.5), (8.0, 2.5), 'uses')
    draw_dependency_arrow(ax, (14.0, 2.5), (18.0, 2.5), 'uses')
    draw_dependency_arrow(ax, (12.0, 2.0), (11.1, 2.0), 'uses')

    # ═══════════════════════════════════════════════════════════
    # 标题和图例
    # ═══════════════════════════════════════════════════════════
    ax.text(12, 16.2, 'Tower Defense — UML Class Diagram', ha='center',
            fontsize=18, fontweight='bold', color='#333')
    ax.text(12, 15.6, '2026 Summer Semester Final Project | 11 Classes, 3 Inheritance Trees',
            ha='center', fontsize=10, color='#666')

    # 图例
    ly = 0.6
    ax.plot([1, 2], [ly, ly], 'k-', linewidth=1.5)
    ax.text(2.1, ly, 'Inheritance (is-a)', fontsize=7, va='center')
    ax.plot([5.5, 6.5], [ly, ly], 'k--', linewidth=1)
    ax.text(6.6, ly, 'Dependency (uses/creates)', fontsize=7, va='center')
    ax.plot([10.5, 11.5], [ly, ly], 'k-', linewidth=1.5)
    ax.scatter(11.0, ly, marker='D', s=40, color='#333', zorder=10)
    ax.text(11.7, ly, 'Composition (has-a)', fontsize=7, va='center')

    fig.savefig('doc/uml_diagram.png', dpi=150, bbox_inches='tight',
                facecolor='white', pad_inches=0.3)
    plt.close(fig)
    print("UML diagram saved to doc/uml_diagram.png")


if __name__ == '__main__':
    main()

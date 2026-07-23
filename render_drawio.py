# -*- coding: utf-8 -*-
"""将 draw.io UML 文件渲染为 PNG.

解析 .drawio (mxGraphModel XML) 文件，
用 matplotlib 渲染所有类框、文本和关系箭头。
"""

import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import Dict, List, Tuple, Optional

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def parse_color(style_str: str, key: str, default: str) -> str:
    """从 style 字符串中提取颜色."""
    for part in style_str.split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            if k.strip() == key:
                val = v.strip()
                if val.lower() == 'none':
                    return default
                return '#' + val if not val.startswith('#') else val
    return default


def parse_drawio(filepath: str) -> Tuple[List[Dict], List[Dict]]:
    """解析 drawio 文件，返回 (vertices, edges) 列表."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    # 找到 mxGraphModel → root → mxCell 元素
    cells = {}
    vertices = []
    edges = []

    for cell in root.iter('mxCell'):
        cell_id = cell.get('id', '')
        parent = cell.get('parent', '1')
        is_vertex = cell.get('vertex') == '1'
        is_edge = cell.get('edge') == '1'
        value = (cell.get('value') or '').replace('&#xa;', '\n').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&amp;', '&')
        style = cell.get('style', '')

        geom = cell.find('mxGeometry')
        if geom is not None:
            x = float(geom.get('x', '0'))
            y = float(geom.get('y', '0'))
            w = float(geom.get('width', '0'))
            h = float(geom.get('height', '0'))
        else:
            x = y = w = h = 0

        cells[cell_id] = {
            'id': cell_id, 'parent': parent, 'vertex': is_vertex, 'edge': is_edge,
            'value': value, 'style': style, 'x': x, 'y': y, 'w': w, 'h': h,
            'source': cell.get('source', ''), 'target': cell.get('target', ''),
        }

        if is_vertex and parent == '1':  # 顶层顶点
            vertices.append(cells[cell_id])
        elif is_edge:
            edges.append(cells[cell_id])

    return cells, vertices, edges


def render_drawio(input_path: str, output_path: str, dpi: int = 150):
    """将 drawio 文件渲染为 PNG."""
    cells, vertices, edges = parse_drawio(input_path)

    # ── 计算画布范围 (包含所有单元格) ──
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    for c in cells.values():
        if not c['vertex']:
            continue
        min_x = min(min_x, c['x'])
        min_y = min(min_y, c['y'])
        max_x = max(max_x, c['x'] + c['w'])
        max_y = max(max_y, c['y'] + c['h'])

    # 添加边距
    pad = 50
    min_x -= pad; min_y -= pad
    max_x += pad; max_y += pad

    fig_w = (max_x - min_x) / 72  # 72 points per inch
    fig_h = (max_y - min_y) / 72

    fig, ax = plt.subplots(1, 1, figsize=(max(12, fig_w), max(8, fig_h)))
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(max_y, min_y)  # drawio y 轴向下
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor('#FAFAFA')

    # ── 按 z-order 排序 (parent 先, children 后) ──
    def sort_key(cell):
        pid = cell['id']
        return (0 if cell['parent'] == '1' else 1, cell['y'], cell['x'])

    all_cells = sorted(cells.values(), key=sort_key)

    # ── 渲染顶点 ──
    drawn = set()
    for cell in all_cells:
        if not cell['vertex'] or cell['id'] in drawn:
            continue
        drawn.add(cell['id'])

        style = cell['style']
        x, y, w, h = cell['x'], cell['y'], cell['w'], cell['h']
        value = cell['value']
        is_swimlane = 'swimlane' in style

        if is_swimlane:
            # 找出子单元格
            children = [c for cid, c in cells.items()
                       if c['parent'] == cell['id'] and c['vertex']]
            children.sort(key=lambda c: c['y'])

            # 标题栏高度 (从 style 的 startSize 获取，默认 26-30)
            title_h = 26
            for part in style.split(';'):
                if part.startswith('startSize='):
                    title_h = float(part.split('=')[1])
            if not children:
                title_h = h

            # 绘制标题栏
            fill = parse_color(style, 'fillColor', '#E3F2FD')
            stroke = parse_color(style, 'strokeColor', '#1565C0')
            font_color = parse_color(style, 'fontColor', '#FFFFFF')
            is_abstract = 'fontStyle=2' in style  # bold+italic

            rect = mpatches.FancyBboxPatch(
                (x, y), w, title_h,
                boxstyle="round,pad=2", facecolor=stroke,
                edgecolor=stroke, linewidth=1.5, zorder=10)
            ax.add_patch(rect)

            display_text = value.replace('\n', '\n')
            ax.text(x + w/2, y + title_h/2, display_text,
                   ha='center', va='center', fontsize=8, fontweight='bold',
                   color='white', style='italic' if is_abstract else 'normal',
                   zorder=15)

            # 绘制子单元格
            for child in children:
                cx, cy, cw, ch = child['x'], child['y'], child['w'], child['h']
                child_style = child['style']
                child_fill = parse_color(child_style, 'fillColor', '#FAFAFA')

                rect = mpatches.FancyBboxPatch(
                    (cx, cy), cw, ch,
                    boxstyle="round,pad=2", facecolor=child_fill,
                    edgecolor='#BDBDBD', linewidth=0.8, zorder=10)
                ax.add_patch(rect)

                child_text = child['value'].replace('\n', '\n')
                lines = child_text.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        ax.text(cx + 6, cy + ch - 6 - i * 14, line.strip(),
                               fontsize=6.5, fontfamily='monospace',
                               color='#333', va='top', zorder=15)
                drawn.add(child['id'])

            # 绘制内容区域背景（标题下方）
            if children:
                content_top = y + title_h
                if len(children) >= 1:
                    content_bottom = children[-1]['y'] + children[-1]['h']
                else:
                    content_bottom = y + h

                # 覆盖类框的主体背景
                rect = mpatches.FancyBboxPatch(
                    (x, y), w, h,
                    boxstyle="round,pad=2", facecolor='none',
                    edgecolor=stroke, linewidth=1.5, zorder=5)
                ax.add_patch(rect)

        elif 'text' in style and cell['parent'] == '1':
            # 独立的文本元素 (如标题)
            ax.text(x + w/2, y + h/2, value, ha='center', va='center',
                   fontsize=11, color='#333', zorder=15)

    # ── 渲染边 ──
    for edge in edges:
        style = edge['style']
        source_id = edge['source']
        target_id = edge['target']

        if source_id not in cells or target_id not in cells:
            continue

        src = cells[source_id]
        tgt = cells[target_id]

        # 计算连接点
        sx = src['x'] + src['w'] / 2
        sy = src['y']
        tx = tgt['x'] + tgt['w'] / 2
        ty = tgt['y'] + tgt['h']

        is_dashed = 'dashed=1' in style
        is_inheritance = 'endArrow=block' in style and 'endFill=0' in style
        is_composition = 'startArrow=diamondThin' in style

        if is_inheritance:
            # 空心三角
            ax.annotate('', xy=(tx, ty), xytext=(sx, sy),
                       arrowprops=dict(arrowstyle='-|>', facecolor='white',
                                      edgecolor='#333', linewidth=1.5),
                       zorder=3)
        elif is_composition:
            # 实心菱形
            ax.plot(sx, sy, 'D', color='#333', markersize=8, zorder=3)
            ax.annotate('', xy=(tx, ty), xytext=(sx, sy),
                       arrowprops=dict(arrowstyle='->', color='#333', linewidth=1.5),
                       zorder=3)
        elif is_dashed:
            # 虚线箭头
            ax.annotate(edge['value'], xy=(tx, ty), xytext=(sx, sy),
                       arrowprops=dict(arrowstyle='->', linestyle='dashed',
                                      color='#666', linewidth=1),
                       fontsize=7, color='#666', zorder=3)

    fig.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor='white', pad_inches=0.3)
    plt.close(fig)
    print(f"Rendered: {output_path}")


if __name__ == '__main__':
    render_drawio('doc/uml_diagram.drawio', 'doc/uml_diagram.png')

# 🏰 塔防游戏 (Tower Defense)

基于 Python + Matplotlib 的塔防游戏，2026 年夏季小学期面向对象架构设计大作业。

## 技术栈

- **Python 3.x** — 编程语言
- **NumPy** — 数值计算
- **Matplotlib** — 实时渲染与交互 (FuncAnimation)
- **Pandas** — 游戏数据分析

## 运行方式

```bash
cd tower_defense
python main.py
```

## 操作说明

| 按键 | 功能 |
|------|------|
| `1` / `2` / `3` | 选择塔类型 (箭塔 / 炮塔 / 冰塔) |
| 鼠标点击网格 | 放置选中的塔 |
| 空格键 | 开始下一波敌人 |
| `Q` | 退出游戏 |

## 项目结构

```
tower_defense/
├── main.py              # 入口程序
├── README.md            # 本文件
├── src/                 # 源代码
│   ├── __init__.py
│   ├── game_object.py   # 抽象基类 (模板方法模式)
│   ├── game_map.py      # 地图管理
│   ├── enemy.py         # 敌人继承体系
│   ├── tower.py         # 塔继承体系 + 注册表 (策略模式)
│   ├── projectile.py    # 子弹继承体系
│   ├── wave.py          # 波次 + 工厂 (工厂模式)
│   ├── stats.py         # 数据分析 (Pandas + Matplotlib)
│   └── game.py          # 游戏主循环
└── doc/                 # 文档
    ├── project_report.pdf   # 说明文档
    ├── uml_diagram.png      # UML 类图
    └── ai_assistance.pdf    # AI 辅助记录
```

## 设计模式

- **策略模式** — Tower 继承体系 (不同塔 = 不同攻击策略)
- **模板方法模式** — GameObject.update() 定义流程框架
- **工厂模式** — WaveFactory 管理波次配置
- **组合优于继承** — Game 组合 GameMap、实体列表等

## 类继承关系

```
GameObject (ABC)
├── Enemy (ABC) → Goblin / Orc / Boss
├── Tower (ABC) → ArrowTower / CannonTower / IceTower
└── Projectile (ABC) → Arrow / Cannonball / IceShard
```

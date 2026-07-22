"""main.py — 塔防游戏入口.

启动即进入游戏.
所有类实现位于 src/ 文件夹下.

运行方式:
    python main.py

操作说明:
    1/2/3 — 选择塔类型 (箭塔/炮塔/冰塔)
    鼠标点击网格 — 放置选中的塔
    空格键 — 开始下一波敌人
    Q — 退出游戏

游戏规则:
    - 初始金币 200, 基地血量 10
    - 敌人沿路径移动, 到达基地造成伤害
    - 塔自动攻击范围内的敌人
    - 击杀敌人获得金币奖励
    - 清除全部 10 波敌人即胜利
    - 基地血量归零则失败
"""

from src.game import Game


def main():
    """启动游戏."""
    print("=" * 50)
    print("  🏰 塔防游戏 — Tower Defense")
    print("=" * 50)
    print()
    print("  操作提示:")
    print("    1/2/3 — 选择塔类型")
    print("    点击网格 — 放置塔")
    print("    空格键 — 开始下一波")
    print("    Q — 退出")
    print()
    print("  提示: 先在路径旁放置几个箭塔,")
    print("        再按空格开始第一波!")
    print()

    game = Game()
    game.run()

    # 游戏结束后的状态
    final_state = game.get_state()
    print()
    print("=" * 50)
    print(f"  最终状态: {final_state['state']}")
    print(f"  得分: {final_state['score']}")
    print(f"  剩余金币: {final_state['gold']}")
    print(f"  基地血量: {final_state['base_hp']}")
    print(f"  存活塔数: {final_state['towers']}")
    print("=" * 50)


if __name__ == '__main__':
    main()

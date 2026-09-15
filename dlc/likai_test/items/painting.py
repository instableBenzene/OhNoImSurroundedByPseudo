"""测试 DLC 物品：印象派名画（红色 · 工具 / 工艺品 · 屋主物品栏持续生效）。"""

from weiren_game.data.types import I

CATEGORY = "artworks"

ITEMS = {
    "impressionist_painting": I(
        "impressionist_painting",
        "印象派名画",
        CATEGORY,
        5,
        "一副临摹很好看的印象派名画；放在屋主物品栏时，每回合开始为所有房客回复2理智。",
        ("tool", "craft"),
    ),
}


def _painting_turn_start(engine: object) -> None:
    """每回合开始为所有屋内房客回复 2 理智。"""
    for tenant in engine.home_tenants():
        engine._restore_sanity(tenant, 2, "印象派名画")


ITEM_HOOKS = {
    "impressionist_painting": {
        "turn_start.house": {"每回合全员回复2理智": _painting_turn_start},
    },
}

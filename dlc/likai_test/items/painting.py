"""测试 DLC 物品：印象派名画（红色 · 工具 / 工艺品 · 屋主物品栏持续生效）。"""

from weiren_game.data.types import I
from weiren_game.data.lang import pack_text_from_file
TEXT = pack_text_from_file(__file__)

CATEGORY = "artworks"

ITEMS = {
    "impressionist_painting": I(
        "impressionist_painting",
        TEXT["item.impressionist_painting.name"],
        CATEGORY,
        5,
        TEXT["item.impressionist_painting.description"],
        ("tool", "craft"),
    ),
}


def _painting_turn_start(engine: object) -> None:
    """每回合开始为所有屋内房客回复 2 理智。"""
    for tenant in engine.home_tenants():
        engine._restore_sanity(tenant, 2, TEXT["dlc.likai_test.items.painting._painting_turn_start.1"])


ITEM_HOOKS = {
    "impressionist_painting": {
        "turn_start.house": {"每回合全员回复2理智": _painting_turn_start},
    },
}

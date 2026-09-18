"""物资：STAR 的个人佩枪「流星信标」。

它同时承担两次「射击」：
- **掩护射击**：为在外搜索的队友提供抵御（机制在角色模块的 modifier provider 里，
  因为抵御判定作用于**搜索者**，而枪在枪主身上——物品 hook 只看持有者自己的背包）。
- **开火**：放空全部电量，对门口事件判定一次（机制在角色模块的 `ACTIVE_DISPATCH`）。
"""

from weiren_game.data.types import I

CATEGORY = "character"

# 风味文本：面向屋主的描写 / 台词，与机制无关。
FLAVOR = (
    "STAR专用手枪型能量武器，通过自身供能无需弹药同时共享传感器数据；如同身体的延伸。"
    "\n「流星信标，校准完毕。交给本人吧。」"
)

ITEMS = {
    "star_sidearm": I(
        "star_sidearm",
        "流星信标",
        CATEGORY,
        4,
        # **只讲物品自己**，不复述技能机制。
        "STAR 的个人佩枪，满足特定能力的发动条件。",
        ("tool", "sidearm"),   # 不打 fragile（否则 keen 的减易损会白给收益）
        searchable=False,      # 只此一把
        flavor=FLAVOR,         # 让定义自描述（当前显示层不读它，见下方说明）
    ),
}


# ---------------------------------------------------------------- 风味登记
from weiren_game.data.items.flavor import ITEM_FLAVOR as _ITEM_FLAVOR  # noqa: E402

_ITEM_FLAVOR["star_sidearm"] = FLAVOR

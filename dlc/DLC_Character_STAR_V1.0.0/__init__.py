"""DLC_Character_STAR 的自定义注册入口。

`dlc/` 装载器自动处理的目录（以 `weiren_game/dlc.py` 为准）：
    characters/  items/  tags/(json+py)  statuses/  personalities/
    locations/  information/  pseudos/  codex/
    avatars/  item/{item,tag}/  icon/<section>/     ← 外观资产

本包用到 `characters/` `items/` `pseudos/`，外加：
- `item/item/star_sidearm.svg`：佩枪自己的图标。**这是首选做法** —— 内容层放同名文件即生效，
  loader 与界面都不用改；图标里 `#d7ddd2`（或 `currentColor`）是**底色**、其余颜色会被换成
  该物品的**品质色**，所以同一张图不会在别的品质上串色。
- 这里登记 loader 覆盖不到的**展示层标签**：tag 的中文名与内置图标。

统一走 `ctx`（`ContentManager`）的方法而不是直接 import 内部模块——
`ctx` 是稳定的内容注册边界，且这些登记会被热切换快照一起回滚。

⚠️ 内置图标有**优先级**：`_item_icon()` 是按 `ITEM_TAG_ICON_PRIORITY` 顺序取
"第一个命中且有图标"的 tag，而 `register_item_tag_icon` 不带 `priority` 时是把 tag
**追加到列表末尾**。本物品的 tags 是 `("tool", "sidearm")`，`tool` 在第 16 位且已映射
`i-tool` —— 所以不指定优先级的 `sidearm/i-target` 永远不会被查到，会一直显示那把扳手。
（有了 `item/item/star_sidearm.svg` 之后这条路只是**兜底**：给别处"只带 sidearm 标签、
又没有专属图"的物品用。）
"""


def register(ctx: object) -> None:
    """登记本包自定义 tag 的中文名与内置图标；任一不可用都不阻断装载。"""
    for call in (
        lambda: ctx.register_item_tag_label("sidearm", "佩枪"),
        # priority=5 → 插在 flintlock(第 4 位) 之后、armor 之前，稳赢 tool(第 16 位)。
        lambda: ctx.register_item_tag_icon("sidearm", "i-target", priority=5),
    ):
        try:
            call()
        except (AttributeError, TypeError):
            # 老版本 ContentManager 没有该入口（或不吃 priority 参数）：
            # 展示层退化为默认值（会显示成 i-tool），不影响机制。
            continue

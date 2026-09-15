"""tag: food（食物通用行为：食用食物后的扳机，DLC 新增食物可复用）。"""


def after_food(engine: object, tenant: object, item: object) -> None:
    """食 tag 物品被食用后的扳机：扫描屋内有 seasoning tag 的物品并触发其钩子。

    使用处：item_system._use_general_item 经 tag 分发调用。
    """
    from weiren_game.data import ITEM_HOOKS, ITEMS

    if "seasoning" in ITEMS[item.item_id].tags:
        return
    for held in engine.state.house.inventory:
        definition = ITEMS.get(held.item_id)
        if definition is None or "seasoning" not in definition.tags:
            continue
        for hook in ITEM_HOOKS.get(held.item_id, {}).get("after_food", {}).values():
            hook(engine, tenant, held)


__all__ = ["after_food"]

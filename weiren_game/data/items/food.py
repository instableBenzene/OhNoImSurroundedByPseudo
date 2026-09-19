"""大类：食物／零食／饮品（含具名食品）。"""

from ..types import I
from weiren_game.data.lang import TEXT

ITEMS = {
    "simple_food": I("simple_food", TEXT["item.simple_food.name"], "food", 0, TEXT["item.simple_food.description"], ("food", "consumable", "placeholder"), consumable=True, stack_size=16, on_use="simple_food"),
    "common_food": I("common_food", TEXT["item.common_food.name"], "food", 1, TEXT["item.common_food.description"], ("food", "consumable", "placeholder"), consumable=True, stack_size=16, on_use="common_food"),
    "tasty_food": I("tasty_food", TEXT["item.tasty_food.name"], "food", 2, TEXT["item.tasty_food.description"], ("food", "consumable", "placeholder"), consumable=True, stack_size=16, on_use="tasty_food"),
    "delicate_food": I("delicate_food", TEXT["item.delicate_food.name"], "food", 3, TEXT["item.delicate_food.description"], ("food", "consumable", "placeholder"), consumable=True, stack_size=16, on_use="delicate_food"),
    "quality_food": I("quality_food", TEXT["item.quality_food.name"], "food", 4, TEXT["item.quality_food.description"], ("food", "consumable", "placeholder"), consumable=True, stack_size=16, on_use="quality_food"),
    "mcdangdang": I("mcdangdang", TEXT["item.mcdangdang.name"], "food", 4, TEXT["item.mcdangdang.description"], ("food", "durability_consumable"), max_durability=5, use_cost=1, on_use="mcdangdang"),
    "garlic": I("garlic", TEXT["item.garlic.name"], "food", 2, TEXT["item.garlic.description"], ("food", "seasoning", "consumable", "fragile"), consumable=True, fragile_chance=.10, stack_size=32, on_use="garlic"),
    "pancake": I("pancake", TEXT["item.pancake.name"], "food", 2, TEXT["item.pancake.description"], ("food", "durability_consumable"), max_durability=3, use_cost=1, on_use="pancake"),
    "cola": I("cola", TEXT["item.cola.name"], "food", 1, TEXT["item.cola.description"], ("food", "drink", "consumable"), consumable=True, stack_size=8, on_use="cola"),
    "water": I("water", TEXT["item.water.name"], "food", 1, TEXT["item.water.description"], ("food", "drink", "consumable"), consumable=True, stack_size=8, on_use="water"),
    "luncheon_meat": I("luncheon_meat", TEXT["item.luncheon_meat.name"], "food", 3, TEXT["item.luncheon_meat.description"], ("food", "can", "durability_consumable"), max_durability=5, use_cost=1, on_use="luncheon_meat"),
    "chocolate_bar": I("chocolate_bar", TEXT["item.chocolate_bar.name"], "food", 2, TEXT["item.chocolate_bar.description"], ("food", "snack", "consumable"), consumable=True, stack_size=16, on_use="chocolate_bar"),
    "gum": I("gum", TEXT["item.gum.name"], "food", 1, TEXT["item.gum.description"], ("food", "snack", "consumable"), consumable=True, stack_size=16, on_use="gum"),
    "double_mint": I("double_mint", TEXT["item.double_mint.name"], "food", 1, TEXT["item.double_mint.description"], ("food", "snack", "consumable"), consumable=True, stack_size=32, on_use="double_mint"),
    "weird_beans": I("weird_beans", TEXT["item.weird_beans.name"], "food", 2, TEXT["item.weird_beans.description"], ("food", "snack", "consumable"), consumable=True, stack_size=32, on_use="weird_beans"),
    "chips": I("chips", TEXT["item.chips.name"], "food", 3, TEXT["item.chips.description"], ("food", "snack", "durability_consumable"), max_durability=3, use_cost=1, on_use="chips"),
    "cookies": I("cookies", TEXT["item.cookies.name"], "food", 3, TEXT["item.cookies.description"], ("food", "snack", "consumable"), consumable=True, stack_size=32, on_use="cookies"),
    "spicy_beef": I("spicy_beef", TEXT["item.spicy_beef.name"], "food", 3, TEXT["item.spicy_beef.description"], ("food", "snack", "consumable"), consumable=True, stack_size=16, on_use="spicy_beef"),
    "fiji_chocolate": I("fiji_chocolate", TEXT["item.fiji_chocolate.name"], "food", 4, TEXT["item.fiji_chocolate.description"], ("food", "snack", "consumable"), consumable=True, stack_size=8, on_use="fiji_chocolate"),
}


def mcdangdang_aftertaste(engine: object, tenant: object) -> None:
    """麦当当余味：condition 存在期间回合初 +3 理智。"""
    condition = tenant.condition("mcdangdang_aftertaste")
    if condition.active:
        engine._restore_sanity(tenant, 3, "mcdangdang_aftertaste")


from weiren_game.condition import StatusDefinition, register_status_definition

register_status_definition(
    StatusDefinition(
        "mcdangdang_aftertaste",
        TEXT["status.mcdangdang_aftertaste.label"],
        "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="item:mcdangdang",
        nodes=frozenset({"turn_start.status_effects"}),
        hook=mcdangdang_aftertaste,
     description=TEXT["status.mcdangdang_aftertaste.description"])
)


def _garlic_seasoning(engine: object, tenant: object, seasoning: object) -> None:
    """蒜瓣（调味品）：食物被食用后强化 +1/+1，并按易损概率消耗蒜瓣。"""
    from weiren_game.data import EVENT_IDS, ITEMS

    engine._restore_health(tenant, 1, "garlic_pairing")
    engine._restore_sanity(tenant, 1, "garlic_pairing")
    fragile = ITEMS[seasoning.item_id].fragile_chance
    if (
        engine._rng(EVENT_IDS["garlic.passive"], tenant.id).random()
        < engine._fragile_chance(fragile, tenant)
    ):
        engine._take_item(seasoning.item_id)


# 物品对象的生命周期声明（与对象紧贴）：item_id → node → {condition/effect}
ITEM_HOOKS = {
    "mcdangdang": {
        "turn_start.status_effects": {
            "mcdangdang_aftertaste": mcdangdang_aftertaste,
        },
    },
    "garlic": {
        "after_food": {
            "蒜瓣调味": _garlic_seasoning,
        },
    },
}


# ---------------------------------------------------------------- on_use 效果
# 指名食物效果与其对象紧贴；引擎经 ItemDefinition.on_use 查 ITEM_EFFECTS。

def _effect_simple_food(engine: object, tenant: object, item: object) -> None:
    """简陋的食物：回复 5 生命。"""
    engine._restore_health(tenant, 5, item.name)


def _effect_common_food(engine: object, tenant: object, item: object) -> None:
    """常见的食物：回复 8 生命。"""
    engine._restore_health(tenant, 8, item.name)


def _effect_tasty_food(engine: object, tenant: object, item: object) -> None:
    """美味的食物：回复 12 生命、3 理智。"""
    engine._restore_health(tenant, 12, item.name)
    engine._restore_sanity(tenant, 3, item.name)


def _effect_delicate_food(engine: object, tenant: object, item: object) -> None:
    """精致的食物：回复 20 生命、5 理智。"""
    engine._restore_health(tenant, 20, item.name)
    engine._restore_sanity(tenant, 5, item.name)


def _effect_quality_food(engine: object, tenant: object, item: object) -> None:
    """优质的食物：回复 30 生命、10 理智。"""
    engine._restore_health(tenant, 30, item.name)
    engine._restore_sanity(tenant, 10, item.name)


def _effect_mcdangdang(engine: object, tenant: object, item: object) -> None:
    """麦当当：回复 20 生命、5 理智，之后 3 回合开始额外回复 3 理智。"""
    engine._restore_health(tenant, 20, item.name)
    engine._restore_sanity(tenant, 5, item.name)
    tenant.set_status(
        "mcdangdang_aftertaste",
        intensity=1,
        layers=3,
    )


def _effect_garlic(engine: object, tenant: object, item: object) -> None:
    """蒜瓣：回复 3 生命、5 理智（调味加成在通用尾部处理）。"""
    engine._restore_health(tenant, 3, item.name)
    engine._restore_sanity(tenant, 5, item.name)


def _effect_pancake(engine: object, tenant: object, item: object) -> None:
    """松饼：回复 5 生命、3 理智。"""
    engine._restore_health(tenant, 5, item.name)
    engine._restore_sanity(tenant, 3, item.name)


def _effect_cola(engine: object, tenant: object, item: object) -> None:
    """无糖可乐：回复 1 生命、3 理智，下一次搜索成功率+5%。"""
    engine._restore_health(tenant, 1, item.name)
    engine._restore_sanity(tenant, 3, item.name)
    tenant.search_bonus += .05


def _effect_water(engine: object, tenant: object, item: object) -> None:
    """矿泉水：回复 1 生命；50% 概率令紊乱层数-1。"""
    from weiren_game.data import EVENT_IDS

    engine._restore_health(tenant, 1, item.name)
    if engine._rng(EVENT_IDS["water"], tenant.id).random() < .50:
        engine._recover_condition(tenant.disorder, 1, 0)


def _effect_luncheon_meat(engine: object, tenant: object, item: object) -> None:
    """午餐肉罐头：回复 8 生命。"""
    engine._restore_health(tenant, 8, item.name)


def _effect_chocolate_bar(engine: object, tenant: object, item: object) -> None:
    """巧克力棒：回复 2 生命并使≤3级侵蚀情绪-1/-1。"""
    engine._restore_health(tenant, 2, item.name)
    engine._reduce_emotion_set(tenant, "erosion", 1, 1, 3)


def _effect_gum(engine: object, tenant: object, item: object) -> None:
    """口香糖：使≤3级侵蚀情绪-1/-1。"""
    engine._reduce_emotion_set(tenant, "erosion", 1, 1, 3)


def _effect_double_mint(engine: object, tenant: object, item: object) -> None:
    """Double劲爆薄荷糖：回复 1 理智，觉醒情绪层数+1。"""
    engine._restore_sanity(tenant, 1, item.name)
    engine._adjust_emotion_set(tenant, "awakening", 0, 1, item.name)


def _effect_weird_beans(engine: object, tenant: object, item: object) -> None:
    """奇趣怪味豆：70% 正面恢复，30% 增加侵蚀情绪层数。"""
    from weiren_game.data import EVENT_IDS

    if engine._rng(EVENT_IDS["beans"], tenant.id).random() < .70:
        engine._restore_health(tenant, 1, item.name)
        engine._restore_sanity(tenant, 2, item.name)
        engine._reduce_emotion_set(tenant, "erosion", 1, 1, 6)
    else:
        engine._adjust_emotion_set(tenant, "erosion", 0, 1, item.name)


def _effect_chips(engine: object, tenant: object, item: object) -> None:
    """咔嚓薯片：回复 3 生命、5 理智，使≤6级侵蚀情绪-1/-2。"""
    engine._restore_health(tenant, 3, item.name)
    engine._restore_sanity(tenant, 5, item.name)
    engine._reduce_emotion_set(tenant, "erosion", 1, 2, 6)


def _effect_cookies(engine: object, tenant: object, item: object) -> None:
    """曲多多曲奇：回复 3 生命、5 理智；非负消沉减少 5%（至少 20）。"""
    engine._restore_health(tenant, 3, item.name)
    engine._restore_sanity(tenant, 5, item.name)
    if tenant.depression >= 0:
        tenant.depression -= max(20, tenant.depression * .05)


def _effect_spicy_beef(engine: object, tenant: object, item: object) -> None:
    """香辣牛肉干：回复 5 生命、5 理智，侵蚀-2/-2、强化昂扬。"""
    engine._restore_health(tenant, 5, item.name)
    engine._restore_sanity(tenant, 5, item.name)
    engine._reduce_emotion_set(tenant, "erosion", 2, 2, 6)
    engine._strengthen_emotion_set(tenant, "awakening", 2, 2, item.name)


def _effect_fiji_chocolate(engine: object, tenant: object, item: object) -> None:
    """斐济巧克力：回复 5 生命、10 理智，侵蚀-3/-3，3 回合消沉获取-20%。"""
    engine._restore_health(tenant, 5, item.name)
    engine._restore_sanity(tenant, 10, item.name)
    engine._reduce_emotion_set(tenant, "erosion", 3, 3)
    tenant.set_status("fiji_afterglow", intensity=1, layers=3)


ITEM_EFFECTS: dict[str, object] = {
    "simple_food": _effect_simple_food,
    "common_food": _effect_common_food,
    "tasty_food": _effect_tasty_food,
    "delicate_food": _effect_delicate_food,
    "quality_food": _effect_quality_food,
    "mcdangdang": _effect_mcdangdang,
    "garlic": _effect_garlic,
    "pancake": _effect_pancake,
    "cola": _effect_cola,
    "water": _effect_water,
    "luncheon_meat": _effect_luncheon_meat,
    "chocolate_bar": _effect_chocolate_bar,
    "gum": _effect_gum,
    "double_mint": _effect_double_mint,
    "weird_beans": _effect_weird_beans,
    "chips": _effect_chips,
    "cookies": _effect_cookies,
    "spicy_beef": _effect_spicy_beef,
    "fiji_chocolate": _effect_fiji_chocolate,
}


def _fiji_depression_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    change = context.get("change")
    if not change or change <= 0:
        return
    afterglow = tenant.condition("fiji_afterglow")
    if afterglow.active:
        yield spec("depressionChange").path("depression").mul(0.8).source("item", "food", "fiji_chocolate")


from weiren_game.modifier_rules import register_modifier_provider as _regfd
_regfd("depressionChange", _fiji_depression_modifier)

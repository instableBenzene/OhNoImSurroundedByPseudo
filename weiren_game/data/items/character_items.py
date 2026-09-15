"""大类：角色专属物资。"""

from weiren_game.probability import resolve

from ..types import I

ITEMS = {
    "star_doll": I("star_doll", "可爱的玩偶", "character", 3, "仅比格小星可用，回复25理智。", ("tool", "craft", "consumable", "star_doll"), consumable=True, on_use="star_doll"),
    "walmart_bag": I("walmart_bag", "沃尔玛购物袋", "character", 4, "携带容量+5；返回时25%损坏，ED Tear仅15%。", ("tool", "fragile", "walmart_bag"), fragile_chance=.25, searchable=False),
    "flintlock": I("flintlock", "燧发枪", "character", 4, "搜索中25%抵御伪人技能；消耗1枚弹药时提升至100%。抵御后25%消耗自身，若消耗了弹药则改为5%。", ("tool", "fragile", "flintlock"), fragile_chance=.25, searchable=False),
    "flintlock_ammo": I("flintlock_ammo", "弹药-燧发枪", "character", 3, "供燧发枪消耗。", ("tool", "consumable", "ammo"), consumable=True, stack_size=16, searchable=False),
    "stimulant": I("stimulant", "强心剂", "medical", 2, "急躁羁绊激活时获得；使用后主性格改为急躁并回复20生命。", ("medical_supply", "consumable"), consumable=True, stack_size=8, searchable=False, on_use="stimulant"),
}


def _effect_star_doll(engine: object, tenant: object, item: object) -> None:
    """可爱的玩偶：仅比格小星可用的角色专属回复物。"""
    from weiren_game.data.characters import bigstar as bigstar_module

    bigstar_module.use_star_doll(engine, tenant, item)


def _effect_stimulant(engine: object, tenant: object, item: object) -> None:
    """强心剂：主性格改为急躁并回复 20 生命。"""
    keys = list(tenant.personalities)
    if keys:
        keys[0] = "impatient"
        tenant.personalities = {key: 1.0 for key in keys}
    else:
        tenant.personalities = {"impatient": 1.0}
    engine._restore_health(tenant, 20, item.name)


ITEM_EFFECTS: dict[str, object] = {
    "star_doll": _effect_star_doll,
    "stimulant": _effect_stimulant,
}


def _resist_flintlock(
    engine: object,
    mission: object,
    tenant: object,
    event: str,
    penalty: float,
    occurrence: int,
) -> bool:
    """燧发枪：消耗弹药时 100% 抵御，否则 25%；抵御成功后按弹药决定损坏率。"""
    from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers

    suffix = "" if occurrence == 0 else f".{occurrence}"
    ammo = tenant.inventory.earliest(
        lambda value: value.item_id == "flintlock_ammo"
    )
    used_ammo = ammo is not None
    if used_ammo:
        tenant.inventory.remove(ammo.item_instance_id)
        engine._recalculate_search(mission)
    context = {"engine": engine, "tenant": tenant, "used_ammo": used_ammo}
    resist_source = ("抵御", "伪人使用主动能力", "伪人技能", "搜索")
    resist_chance = calculate_modified_amount(
        0.0, collect_modifiers("chance", resist_source, context)
    ) - penalty
    resisted = (
        engine._rng(f"{event}.flintlock{suffix}").random() < resolve(resist_chance)
    )
    engine._skill_outcome(tenant, "tool.flintlock", resisted)
    # 触发后无论是否抵御成功，都判定是否被消耗（base 25%，用弹药 -100% → 5%）。
    break_source = ("易损", "燧发枪", "搜索", "触发后")
    break_chance = calculate_modified_amount(
        0.25, collect_modifiers("chance", break_source, context)
    )
    if engine._rng(f"{event}.flintlock.break{suffix}").random() < engine._fragile_chance(
        resolve(break_chance), tenant
    ):
        engine._break_search_tool(mission, tenant, "flintlock")
    return resisted


def _flintlock_modifier(context: object):
    """燧发枪：抵御 base 25%、用弹药 +150%（收敛 95%）；消耗 base 25%、用弹药 -100%（5%）。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if not any(value.item_id == "flintlock" for value in tenant.inventory.items):
        return
    yield (
        spec("chance").flat(0.25).match("all")
        .path("抵御", "伪人使用主动能力").source("物品", "工具", "燧发枪")
    )
    if context.get("used_ammo"):
        yield (
            spec("chance").flat(1.50).match("all")
            .path("抵御", "伪人使用主动能力").source("物品", "工具", "弹药-燧发枪")
        )
        yield (
            spec("chance").flat(-1.00).match("all")
            .path("易损", "燧发枪").source("物品", "工具", "弹药-燧发枪")
        )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _flintlock_modifier)


ITEM_HOOKS = {
    "flintlock": {"search_resist": {"伪人搜索抵御": _resist_flintlock}},
}

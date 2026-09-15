"""大类：工具／装甲／消遣物／工艺品。"""

from weiren_game.probability import resolve

from ..types import I
from weiren_game.types import EngineProtocol

ITEMS = {
    "flashlight": I("flashlight", "手电筒", "tool", 2, "搜索成功率+10%；返回后25%消耗。", ("tool", "fragile"), fragile_chance=.25),
    "compass": I("compass", "指南针", "tool", 2, "搜索回合数-1；返回后25%消耗。", ("tool", "fragile"), fragile_chance=.25),
    "crowbar": I("crowbar", "撬棍", "tool", 3, "蓝色及以上掉率+25%；15%损坏；可25%抵御伪人技能。", ("tool", "fragile"), fragile_chance=.15),
    "sports_shoes": I("sports_shoes", "运动鞋-雪晨2.5", "tool", 2, "搜索回合数-1；15%损坏；可20%抵御伪人技能。", ("tool", "shoes", "fragile"), fragile_chance=.15),
    "chain_vest": I("chain_vest", "锁链防刺服", "tool", 2, "装备后生命伤害-3，触发消耗2耐久。", ("tool", "armor", "durability_consumable"), max_durability=50, use_cost=2),
    "motocross_helmet": I("motocross_helmet", "越野摩托头盔", "tool", 3, "装备后受到≥5伤害时伤害-5，触发消耗5耐久。", ("tool", "armor", "durability_consumable"), max_durability=25, use_cost=5),
    "polar_jacket": I("polar_jacket", "极地冲锋衣", "tool", 4, "装备后伤害-5；25%概率避免创伤/紊乱。", ("tool", "armor", "durability_consumable"), max_durability=125, use_cost=2),
    "ghillie_suit": I("ghillie_suit", "吉利服", "tool", 4, "搜索遭遇率-75%，返程生命消耗-5，并避免返程状态恶化。", ("tool", "armor", "durability_consumable"), max_durability=100, use_cost=10),
    "walkman": I("walkman", "随身听", "tool", 3, "装备者回合开始回复5理智并减轻侵蚀；回合末15%损坏。", ("tool", "entertainment", "fragile"), fragile_chance=.15),
    "gramophone": I("gramophone", "典藏留声机", "tool", 5, "在屋主物品栏时，每回合开始全员回复1理智。", ("tool", "craft")),
}


def _walkman_start_of_turn(
    engine: EngineProtocol, tenant: object, held: object
) -> None:
    """随身听：回合初持有人回复 5 理智并减轻侵蚀。

    使用处：round_effects 回合初背包实例节点（按 ITEM_HOOKS 扫描）。
    """
    engine._restore_sanity(tenant, 5, "随身听")
    engine._reduce_emotion_set(tenant, "erosion", 0, 1)


def _walkman_end_of_turn(
    engine: EngineProtocol, tenant: object, held: object
) -> None:
    """随身听：回合末以 15% 概率损坏并从背包移除。

    使用处：round_effects 回合末装备节点（按 ITEM_HOOKS 扫描）。
    """
    from weiren_game.data import EVENT_IDS

    chance = engine._fragile_chance(.15, tenant)
    if engine._rng(EVENT_IDS["walkman.break"], tenant.id).random() < chance:
        tenant.inventory.items.remove(held)
        engine._log(f"{engine.character(tenant).name}的随身听损坏。")


ITEM_HOOKS = {
    "walkman": {
        "turn_start.backpack": {"随身听回合初效果": _walkman_start_of_turn},
        "turn_end.held": {"随身听回合末损坏": _walkman_end_of_turn},
    },
}


def apply_armour(engine: EngineProtocol, tenant: object, amount: float) -> float:
    """按最先装备的护甲减免本次生命伤害并消耗对应耐久。

    使用处：value_system._damage_health 的护甲段。
    """
    from weiren_game.data import ITEMS as ALL_ITEMS

    result = amount
    held = next(
        (
            value
            for value in tenant.inventory.items
            if "armor" in ALL_ITEMS[value.item_id].tags
        ),
        None,
    )
    if held is None:
        return result
    if held.item_id == "chain_vest":
        result = max(0.0, result - 3)
        engine._consume_held_durability(tenant, held, 2)
    elif held.item_id == "motocross_helmet" and result >= 5:
        result = max(0.0, result - 5)
        engine._consume_held_durability(tenant, held, 5)
    elif held.item_id == "polar_jacket":
        result = max(0.0, result - 5)
        engine._consume_held_durability(tenant, held, 2)
    return result


def armour_allows_status(engine: EngineProtocol, tenant: object, source: str) -> bool:
    """极地冲锋衣：以 25% 概率判定 4 次，命中则避免本次创伤/紊乱施加。

    使用处：condition_system._status_avoidance 的极地冲锋衣段。
    """
    from weiren_game.data import ITEMS as ALL_ITEMS

    first_armour = next(
        (
            value
            for value in tenant.inventory.items
            if "armor" in ALL_ITEMS[value.item_id].tags
        ),
        None,
    )
    if first_armour is None or first_armour.item_id != "polar_jacket":
        return False
    from weiren_game.data import EVENT_IDS

    avoided = any(
        engine._rng(EVENT_IDS["polar.avoid"], tenant.id, attempt).random() < .25
        for attempt in range(4)
    )
    engine._consume_held_durability(tenant, first_armour, 5)
    if avoided:
        engine._log(f"极地冲锋衣帮助{engine.character(tenant).name}避免了{source}的状态。")
    return avoided


def _ghillie_search_return(
    engine: EngineProtocol, tenant: object, held: object, mission: object
) -> None:
    """吉利服：搜索返程按是否触发规避消耗耐久。"""
    base_cost = 10 + (5 if mission.loot_context.get("ghillie_avoidance") else 0)
    engine._consume_held_durability(tenant, held, base_cost)


def _walmart_bag_search_return(
    engine: EngineProtocol, tenant: object, held: object, mission: object
) -> None:
    """沃尔玛购物袋：base 25% 破损；ED Tear 携带时由修饰器 -10%。"""
    from weiren_game.data import EVENT_IDS
    from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers
    from weiren_game.probability import resolve

    source = ("物品", "工具", "沃尔玛购物袋", "易损", "返程", tenant.character_id)
    context = {"engine": engine, "tenant": tenant, "item": held}
    base = calculate_modified_amount(
        0.25, collect_modifiers("chance", source, context)
    )
    if engine._rng(EVENT_IDS["held.search.break"], held.item_id, tenant.id).random() < engine._fragile_chance(resolve(base), tenant):
        tenant.inventory.items.remove(held)
        engine._log(f"{engine.character(tenant).name}的沃尔玛购物袋在返程时破损。")


def _walmart_bag_modifier(context: object):
    """沃尔玛购物袋自身能力：携带者为 ED Tear 时破损概率 -10%。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "tear" or not engine._passive_available(tenant, "tear.held_bag_return"):
        return
    yield (
        spec("chance").flat(-0.10).match("all")
        .path("易损", "沃尔玛购物袋")
        .source("物品", "工具", "沃尔玛购物袋")
    )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _walmart_bag_modifier)


def _fragile_search_return(
    engine: EngineProtocol, tenant: object, held: object, mission: object
) -> None:
    """易损工具：按物品 fragile_chance 判定返程损坏。"""
    from weiren_game.data import EVENT_IDS, ITEMS as ALL_ITEMS

    item = ALL_ITEMS[held.item_id]
    chance = engine._fragile_chance(item.fragile_chance, tenant)
    if engine._rng(EVENT_IDS["tool.return"], held.item_id, tenant.id).random() < chance:
        tenant.inventory.items.remove(held)
        engine._log(f"携带的{item.name}在搜索中损坏。")


_return_fragile_tools = ("flashlight", "compass", "crowbar", "sports_shoes")
ITEM_HOOKS.update(
    {
        "ghillie_suit": {"search.return": {"返程耐久消耗": _ghillie_search_return}},
        "walmart_bag": {"search.return": {"返程破损判定": _walmart_bag_search_return}},
    }
)
for _tool_id in _return_fragile_tools:
    ITEM_HOOKS[_tool_id] = {"search.return": {"返程易损判定": _fragile_search_return}}


def _gramophone_turn_start(engine: EngineProtocol) -> None:
    """典藏留声机：屋主物品栏持有期间，回合初全员回复 1 理智。"""
    for tenant in engine.home_tenants():
        engine._restore_sanity(tenant, 1, "典藏留声机")
    engine._log("典藏留声机的沙沙声让所有房客回复1理智。")


def _smartphone_turn_start(engine: EngineProtocol) -> None:
    """智能手机：屋主持有期间，回合初有 10% 概率生成一条待验证信息。"""
    from weiren_game.data import EVENT_IDS

    if engine._rng(EVENT_IDS["smartphone.info"]).random() < .10:
        engine._create_random_information(False, "智能手机")


ITEM_HOOKS.update(
    {
        "gramophone": {"turn_start.house": {"全员回复": _gramophone_turn_start}},
        "smartphone": {"turn_start.house": {"随机信息": _smartphone_turn_start}},
    }
)


def _crowbar_loot_quality(
    engine: EngineProtocol,
    tenant: object,
    mission: object,
    quality_weights: list[float],
) -> list[float]:
    """撬棍：携带时搜索掉落蓝色及以上品质权重 ×1.25。

    使用处：search_system._loot_for_mission 经 ITEM_HOOKS["loot.quality"] 扫描。
    """
    return [
        weight * (1.25 if quality >= 2 else 1.0)
        for quality, weight in enumerate(quality_weights)
    ]


ITEM_HOOKS["crowbar"] = {
    **ITEM_HOOKS.get("crowbar", {}),
    "loot.quality": {"蓝色以上掉落加权": _crowbar_loot_quality},
}


def _resist_crowbar(
    engine: EngineProtocol,
    mission: object,
    tenant: object,
    event: str,
    penalty: float,
    occurrence: int,
) -> bool:
    """撬棍：25% 抵御搜索伪人技能；成功时推迟伪人到访并 95% 概率损坏。"""
    from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers

    suffix = "" if occurrence == 0 else f".{occurrence}"
    source = ("抵御", "伪人使用主动能力", "伪人技能", "搜索")
    ctx = {"engine": engine, "tenant": tenant, "item_id": "crowbar"}
    chance = calculate_modified_amount(
        0.0, collect_modifiers("chance", source, ctx)
    ) - penalty
    if engine._rng(f"{event}.crowbar{suffix}").random() >= resolve(chance):
        engine._skill_outcome(tenant, "tool.crowbar", False)
        return False
    engine._skill_outcome(tenant, "tool.crowbar", True)
    engine.state.world.visitors.next_pseudo_turn += 1
    if (
        engine._rng(f"{event}.crowbar.break{suffix}").random()
        < engine._fragile_chance(.95, tenant)
    ):
        engine._break_search_tool(mission, tenant, "crowbar")
    return True


def _resist_sports_shoes(
    engine: EngineProtocol,
    mission: object,
    tenant: object,
    event: str,
    penalty: float,
    occurrence: int,
) -> bool:
    """运动鞋：20% 抵御搜索伪人技能；成功抵御后 45% 概率损坏。"""
    from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers

    suffix = "" if occurrence == 0 else f".{occurrence}"
    source = ("抵御", "伪人使用主动能力", "伪人技能", "搜索")
    ctx = {"engine": engine, "tenant": tenant, "item_id": "sports_shoes"}
    chance = calculate_modified_amount(
        0.0, collect_modifiers("chance", source, ctx)
    ) - penalty
    if engine._rng(f"{event}.shoes{suffix}").random() >= resolve(chance):
        engine._skill_outcome(tenant, "tool.sports_shoes", False)
        return False
    engine._skill_outcome(tenant, "tool.sports_shoes", True)
    if (
        engine._rng(f"{event}.shoes.break{suffix}").random()
        < engine._fragile_chance(.45, tenant)
    ):
        engine._break_search_tool(mission, tenant, "sports_shoes")
    return True


for _tool_id, _resist in (
    ("crowbar", _resist_crowbar),
    ("sports_shoes", _resist_sports_shoes),
):
    ITEM_HOOKS.setdefault(_tool_id, {})
    ITEM_HOOKS[_tool_id]["search_resist"] = {"伪人搜索抵御": _resist}


def _walmart_carry_mod(
    engine: EngineProtocol, tenant: object, held: object
) -> int:
    """沃尔玛购物袋：携带时搜索容量 +5。"""
    return 5


def _compass_start_mod(
    engine: EngineProtocol, tenant: object, held: object
) -> tuple[int, float]:
    """罗盘：携带时搜索回合 -1。"""
    return -1, 0.0


def _sports_shoes_start_mod(
    engine: EngineProtocol, tenant: object, held: object
) -> tuple[int, float]:
    """运动鞋：携带时搜索回合 -1。"""
    return -1, 0.0


def _flashlight_start_mod(
    engine: EngineProtocol, tenant: object, held: object
) -> tuple[int, float]:
    """手电筒：每携带一把成功率 +10%。"""
    return 0, .10


def _ghillie_return_mod(
    engine: EngineProtocol, tenant: object, held: object, damage: float
) -> tuple[float, bool]:
    """吉利服：返程伤害 10→5，并豁免返程状态恶化。"""
    return 5.0, True


_SEARCH_START_MODS = {
    "compass": _compass_start_mod,
    "sports_shoes": _sports_shoes_start_mod,
    "flashlight": _flashlight_start_mod,
}
ITEM_HOOKS.setdefault("walmart_bag", {})
ITEM_HOOKS["walmart_bag"]["search.carry_mod"] = {"容量+5": _walmart_carry_mod}
for _tool_id, _mod in _SEARCH_START_MODS.items():
    ITEM_HOOKS.setdefault(_tool_id, {})
    ITEM_HOOKS[_tool_id]["search.start_mod"] = {"出发修正": _mod}
ITEM_HOOKS.setdefault("ghillie_suit", {})
ITEM_HOOKS["ghillie_suit"]["search.return_mod"] = {"返程减伤与豁免": _ghillie_return_mod}


HOOKS = {
    "armour.allows_status": armour_allows_status,
    "armour.apply": apply_armour,
}

def _ghillie_encounter_modifier(context: object):
    """吉利服：搜索遭遇 -75%。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if not any(v.item_id == "ghillie_suit" for v in tenant.inventory.items):
        return
    yield (
        spec("chance").path("遭遇").percent(-0.75)
        .source("物品", "防具", "吉利服")
    )


from weiren_game.modifier_rules import register_modifier_provider as _reg
_reg("chance", _ghillie_encounter_modifier)


def _crowbar_resist_modifier(context: object):
    """撬棍：抵御 +25%。"""
    from weiren_game.modifier_rules import spec

    if context.get("item_id") != "crowbar":
        return
    yield (
        spec("chance").flat(0.25).match("all")
        .path("抵御", "伪人使用主动能力").source("物品", "工具", "撬棍")
    )


def _shoes_resist_modifier(context: object):
    """运动鞋：抵御 +20%。"""
    from weiren_game.modifier_rules import spec

    if context.get("item_id") != "sports_shoes":
        return
    yield (
        spec("chance").flat(0.20).match("all")
        .path("抵御", "伪人使用主动能力").source("物品", "工具", "运动鞋")
    )


from weiren_game.modifier_rules import register_modifier_provider as _reg2
_reg2("chance", _crowbar_resist_modifier)
_reg2("chance", _shoes_resist_modifier)


def _compass_start_modifier(context: object):
    from weiren_game.modifier_rules import spec
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    if any(v.item_id == "compass" for v in tenant.inventory.items):
        yield spec("search").path("回合").flat(-1).source("物品", "工具", "指南针")


def _shoes_start_modifier(context: object):
    from weiren_game.modifier_rules import spec
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    if any(v.item_id == "sports_shoes" for v in tenant.inventory.items):
        yield spec("search").path("回合").flat(-1).source("物品", "工具", "运动鞋")


def _flashlight_start_modifier(context: object):
    from weiren_game.modifier_rules import spec
    tenant = context["tenant"]  # type: ignore[index]
    if any(v.item_id == "flashlight" for v in tenant.inventory.items):
        yield spec("chance").path("搜索").flat(0.10).source("物品", "工具", "手电筒")


def _walmart_carry_modifier(context: object):
    from weiren_game.modifier_rules import spec
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    if any(v.item_id == "walmart_bag" for v in tenant.inventory.items):
        yield spec("search").path("携带").flat(5).source("物品", "工具", "沃尔玛购物袋")


from weiren_game.modifier_rules import register_modifier_provider as _reg3
_reg3("search", _compass_start_modifier)
_reg3("search", _shoes_start_modifier)
_reg3("search", _walmart_carry_modifier)
_reg3("chance", _flashlight_start_modifier)

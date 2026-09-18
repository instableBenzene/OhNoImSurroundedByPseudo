"""大类：书籍／报刊／录影带／手机（信息载体）。"""

from ..types import I
from weiren_game.types import EngineProtocol

ITEMS = {
    "bls_book": I("bls_book", "《基础生命支持》", "information", 3, "持有5回合习得BLS：医疗物资成功率+10%。", ("information_carrier", "book", "durability_consumable"), max_durability=25, use_cost=1),
    "plants_book": I("plants_book", "《野外常见可食用植被图鉴》", "information", 3, "持有5回合习得植被辨识：搜索必得食物。", ("information_carrier", "book", "durability_consumable"), max_durability=25, use_cost=1),
    "disaster_book": I("disaster_book", "《自然灾害避险手册》", "information", 3, "持有5回合习得防备：搜索遭遇率-10%。", ("information_carrier", "book", "durability_consumable"), max_durability=25, use_cost=1),
    "nebula_legend": I("nebula_legend", "《星云传说》", "information", 5, "回合末理智消耗-10并减轻侵蚀；持有7回合习得古老传说。", ("information_carrier", "book")),
    "newspaper": I("newspaper", "《乡野日报》", "information", 2, "获得时兑换1条待验证物资或来访信息。", ("information_carrier", "consultation_carrier", "consumable"), consumable=True),
    "medical_newspaper": I("medical_newspaper", "《炎黄医学报》", "information", 3, "获得时兑换1条待验证物资信息及1条已证实物资信息。", ("information_carrier", "consultation_carrier", "consumable"), consumable=True),
    "video_tape": I("video_tape", "监控录影带", "information", 4, "获得时兑换3条已证实信息。", ("information_carrier", "consultation_carrier", "consumable"), consumable=True),
    "smartphone": I("smartphone", "智能手机", "information", 5, "获得时取得10条待验证信息；使用回复15理智并减轻消沉，50%损坏。", ("information_carrier", "consultation_carrier", "entertainment", "fragile"), fragile_chance=.50, on_use="smartphone"),
}


def _effect_smartphone(engine: object, tenant: object, item: object) -> None:
    """智能手机：回复 15 理智并减轻消沉。"""
    engine._restore_sanity(tenant, 15, item.name)
    tenant.depression -= abs(tenant.depression) * .5


ITEM_EFFECTS: dict[str, object] = {
    "smartphone": _effect_smartphone,
}


def ancient_legend_start_of_turn(engine: EngineProtocol, tenant: object) -> None:
    """古老而崭新的传说：回合初使觉醒情绪 +2/+2。

    使用处：round_effects 回合初房客实例效果。
    """
    if (
        tenant.has_ability("ancient_legend")
        and engine._passive_available(tenant, "book.ancient_legend")
    ):
        engine._adjust_emotion_set(tenant, "awakening", 2, 2, "古老的崭新的传说")


def ancient_legend_blocks_erosion(engine: EngineProtocol, tenant: object) -> bool:
    """古老而崭新的传说：习得后每回合首次侵蚀情绪施加失效（1 回合冷却）。

    使用处：condition_system._emotion_application_blocked 的侵蚀拦截段。
    """
    if not tenant.has_ability("ancient_legend"):
        return False
    state = tenant.ability_state("ancient_legend")
    if state is None or state.cooldown_until > engine.state.flow.turn:
        return False
    state.cooldown_until = engine.state.flow.turn + 1
    return True


# 书本研读数据：物品 ID → (习得能力, 需要持有回合数)。
BOOK_STUDIES = {
    "bls_book": ("bls", 5),
    "plants_book": ("plant_identification", 5),
    "disaster_book": ("prepared", 5),
    "nebula_legend": ("ancient_legend", 7),
}


def _book_held_end_of_turn(
    engine: EngineProtocol, tenant: object, held: object
) -> None:
    """书籍回合末：星云传说减轻侵蚀；满持有回合时习得对应被动。"""
    item_id = held.item_id
    if item_id == "nebula_legend":
        engine._reduce_emotion_set(tenant, "erosion", 2, 2)
    learned, threshold = BOOK_STUDIES[item_id]
    if held.held_turns >= threshold and not tenant.has_ability(learned):
        engine._grant_learned_passive(tenant, learned)
        engine._log(
            f"{engine.character(tenant).name}研读{ITEMS[item_id].name}，习得被动能力。"
        )


def _book_base_consume_cost(
    engine: EngineProtocol, tenant: object, held: object, cost: float
) -> float:
    """书籍对回合末理智消耗的修正（星云 -10、防灾/急救 +2/+2、植被辨识 +1）。"""
    item_id = held.item_id
    if item_id == "nebula_legend":
        return max(0.0, cost - 10)
    if item_id in {"bls_book", "disaster_book"}:
        return cost + 2
    if item_id == "plants_book":
        return cost + 1
    return cost


ITEM_HOOKS = {
    item_id: {
        "turn_end.held": {"研读结算": _book_held_end_of_turn},
        "turn_end.base_consume": {"理智消耗修正": _book_base_consume_cost},
    }
    for item_id in BOOK_STUDIES
}


def legend_erosion_block(engine: object, tenant: object, key: str) -> bool:
    """古老传说：持有时提供侵蚀免疫（供通用节点调用）。"""
    return ancient_legend_blocks_erosion(engine, tenant)


def _legend_erosion_block_gate(context: object) -> object:
    """古老传说：持有时侵蚀免疫（闸门 provider）。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine"); tenant = context.get("tenant"); key = context.get("key")
    if engine is None or tenant is None:
        return
    from weiren_game.condition import EROSION_EMOTIONS

    if key not in EROSION_EMOTIONS or not ancient_legend_blocks_erosion(engine, tenant):
        return
    yield (
        gate("emotion.apply.block").path("施加", key).match("all")
        .source("物品", "古老传说", "侵蚀免疫").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.apply.block", _legend_erosion_block_gate)


def _plants_search_reward(engine: object, tenant: object, guaranteed: list) -> None:
    """植被辨识：搜索必得一件食物。"""
    from weiren_game.data import EVENT_IDS

    if tenant.has_ability("plant_identification") and engine._passive_available(tenant, "book.plants"):
        guaranteed.append(
            engine._random_item(
                required_tags=("food",), event_id=EVENT_IDS["book.plants"],
                event_suffix=(tenant.id,),
            )
        )


HOOKS = {
    "legend.turn_start": ancient_legend_start_of_turn,
    "search.reward": _plants_search_reward,
}


# BLS 被动：在「医疗成功率」调用点提供 +10 固定加算（供 _medical 收集）。
from weiren_game.modifier_rules import register_modifier_provider, spec


def _bls_medical_modifier(context: object):
    """BLS 被动提供的医疗成功率修饰器（条件满足时产出）。"""
    engine = context["engine"]  # type: ignore[index]
    tenant = context["tenant"]  # type: ignore[index]
    if tenant.has_ability("bls") and engine._passive_available(tenant, "book.bls"):
        yield (
            spec("chance")
            .flat(0.10)
            .path("手术包", "药箱")
            .source("物品", "书", "基础生命支持", "角色技能", "被动", "BLS")
        )


register_modifier_provider("chance", _bls_medical_modifier)


def _prepared_encounter_modifier(context: object):
    """防备（灾害书被动）：搜索遭遇 -10%。"""
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.has_ability("prepared") and engine._passive_available(tenant, "book.prepared"):
        yield (
            spec("chance").path("遭遇").flat(-0.10)
            .source("物品", "书", "自然灾害避险", "角色技能", "被动", "防备")
        )


register_modifier_provider("chance", _prepared_encounter_modifier)


def _book_sanity_modifier(context: object):
    """书籍对回合末理智消耗的修正。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    held = {value.item_id for value in tenant.inventory.items}
    if "bls_book" in held:
        yield spec("sanityConsume").path("回合末消耗").flat(2).source("物品", "信息载体", "书", "基础生命支持")
    if "disaster_book" in held:
        yield spec("sanityConsume").path("回合末消耗").flat(2).source("物品", "信息载体", "书", "自然灾害避险")
    if "plants_book" in held:
        yield spec("sanityConsume").path("回合末消耗").flat(1).source("物品", "信息载体", "书", "植物图鉴")
    if "nebula_legend" in held:
        yield spec("sanityConsume").path("回合末消耗").final().flat(-10).source("物品", "信息载体", "书", "星云传说")


register_modifier_provider("sanityConsume", _book_sanity_modifier)

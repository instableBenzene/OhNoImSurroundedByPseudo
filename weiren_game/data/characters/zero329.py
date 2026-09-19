"""房客档案：澪叁贰玖（11 号，警觉印记机制）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, B, CharacterDefinition, CostEffectLink, MarkDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "zero329", 11, TEXT["character.zero329.name"], TEXT["character.zero329.description"],
    "suspicious", "keen", 3, (TEXT["character.zero329.tag.0"], TEXT["character.zero329.tag.1"], TEXT["character.zero329.tag.2"], TEXT["character.zero329.tag.3"]),
    # 正文排版样板（规则见 docs/STYLE.md §12）：· 分行、数值加粗、限制交给 chips。
    (A("sharp_instinct", TEXT["ability.sharp_instinct.name"],
       TEXT["ability.sharp_instinct.description"]),),
    # 冷却只写在 chips 里（原来正文还重复了一句"*该能力有3回合冷却时间。*"）——见 STYLE §12 规则 3。
    (A("information_collect", TEXT["ability.information_collect.name"],
       TEXT["ability.information_collect.description"],
       "information", chips=(TEXT["ability.information_collect.chip.0"],)),
     A(
         "intent_awareness",
         TEXT["ability.intent_awareness.name"],
         TEXT["ability.intent_awareness.description"],
         "amount",
         prompt=TEXT["ability.intent_awareness.prompt"],
         amount_label=TEXT["ability.intent_awareness.amount_label"],
         amount_mark="alert",
         options=(("discern",TEXT["ability.intent_awareness.option.0"],"i-search",TEXT["data.characters.zero329.module.1"]),),
         branches=(
             B(
                 max_on_force=True,
                 terms=(
                     T("mark", None, key="alert", maximum=True, tag="alert_use"),
                     T("sanity", 30, optional=True, tag="discern_fee"),
                 ),
                 links=(
                     CostEffectLink(
                         costs=("alert_use",),
                         effects=("spawn_information",),
                     ),
                     CostEffectLink(
                         costs=("alert_use", "discern_fee"),
                         effects=("resolve_information",),
                     ),
                 ),
                 forced_terms=(
                     T("health", 10, payer="target"),
                     T("sanity", 10, payer="target"),
                 ),
             ),
         ),
     )),
)

# ---------------------------------------------------------------- modifier
def blocks_erosion(engine: EngineProtocol, tenant: object, key: str) -> bool:
    """警觉印记使侵蚀情绪施加失效（每个情绪各判定一次）。

    使用处：condition_system._emotion_application_blocked。
    """
    return (
        engine._mark_count(tenant, "alert") > 0
        and engine._passive_available(tenant, f"zero329.sharp_instinct.{key}")
    )


def _erosion_block_gate(context: object) -> object:
    """侵蚀免疫（闸门 provider）：持有警觉印记时，侵蚀情绪的施加失效。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine"); tenant = context.get("tenant"); key = context.get("key")
    if engine is None or tenant is None:
        return
    from weiren_game.condition import EROSION_EMOTIONS

    if key not in EROSION_EMOTIONS or not blocks_erosion(engine, tenant, key):
        return
    yield (
        gate("emotion.apply.block").path("apply", key).match("all")
        .source("character", "zero329", "sharp_instinct").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.apply.block", _erosion_block_gate)


def sanity_cost_multiplier(engine: EngineProtocol, tenant: object) -> float:
    """回合末理智消耗倍率：持有警觉印记时为 1.5 倍。

    使用处：round_effects 的回合末理智消耗计算。
    """
    if (
        engine._mark_count(tenant, "alert")
        and engine._passive_available(tenant, "zero329.alert_cost")
    ):
        return 1.50
    return 1.0


# ---------------------------------------------------------------- function
def use_information_collect(
    engine: EngineProtocol, actor: object, ability_id: str, *, option: object, amount: object
) -> None:
    """情报收集：消耗 1 警觉印记识破物资/地点信息并强化本回合搜索。

    使用处：ability_system.use_ability 的澪叁贰玖分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    infos = [
        value for value in engine.state.house.information
        if value.status == "pending"
        and value.kind in {"material_reward", "location_modifier"}
    ]
    if not infos:
        raise RuleViolation(TEXT["data.characters.zero329.use_information_collect.1"])
    chosen = next((value for value in infos if value.info_instance_id == option), infos[0])
    engine._verify_information_object(chosen)
    actor.set_status(
        "information_gathering_zero329",
        intensity=1,
        layers=1,
    )
    engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 3)


def costs_information_collect(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """情报收集：消耗 1 层警觉印记。"""
    return [T("mark", 1, key="alert")]


def use_intent_awareness(
    engine: EngineProtocol,
    actor: object,
    *,
    option: object,
    amount: object,
    force_max: bool = False,
    forced: bool = False,
) -> None:
    """意图觉察／决策：消耗任意警觉印记获得等量伪人信息。

    使用处：ability_system.use_ability 的澪叁贰玖分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    if force_max:
        spend = int(engine._mark_count(actor, "alert"))
    else:
        spend = min(int(amount or 1), int(engine._mark_count(actor, "alert")))
    if spend <= 0:
        raise RuleViolation(TEXT["data.characters.zero329.use_intent_awareness.1"])
    created = [
        engine._create_random_information(False, TEXT["data.characters.zero329.use_intent_awareness.2"], {"visit", "pseudo_skill"})
        for _ in range(spend)
    ]
    discern = forced or option == "discern"
    costs = [T("mark", spend, key="alert")]
    if discern and not forced:
        if actor.sanity < 30:
            raise RuleViolation(TEXT["data.characters.zero329.use_intent_awareness.3"])
        costs.append(T("sanity", 30))
    if not forced:
        engine._pay_ability_costs(actor, costs)
    if discern:
        for info in created:
            engine._verify_information_object(info)


def start_of_turn(engine: EngineProtocol, tenant: object) -> None:
    """敏锐直觉：回合开始依伪人潜伏情况生成信息或补一层警觉印记。

    使用处：round_effects 回合初实例节点经 TURN_START_HOOKS 查表调用。
    """
    if (
        engine._mark_count(tenant, "alert") > 0
        and engine._passive_available(tenant, "zero329.start_information")
    ):
        chance = .65 if engine.pseudo_in_house() else .25
        success = engine._rng(_event_id("zero329.info"), tenant.id).random() < chance
        engine._skill_outcome(tenant, "zero329.sharp_instinct.info", success)
        if success:
            engine._create_random_information(
                False, TEXT["data.characters.zero329.start_of_turn.1"],
                {"material_reward", "visit", "pseudo_skill", "pseudo_inhome"},
            )
    if (
        tenant.condition("vigilant_pseudo_zero329").active
        and engine._passive_available(tenant, "zero329.seen_pseudo_mark")
    ):
        engine._gain_mark(tenant, "alert", 1)


def on_pseudo_visit(engine: EngineProtocol, tenant: object) -> None:
    """伪人来访时获得警觉印记并记下「已见过伪人」。

    使用处：pseudo_system._resolve_pseudo_visit 的房客遍历。
    """
    if engine._passive_available(tenant, "zero329.pseudo_visit"):
        engine._gain_mark(tenant, "alert", 1)
        tenant.set_status("vigilant_pseudo_zero329", intensity=1, layers=1)


def on_tenant_replaced(
    engine: EngineProtocol, *, tenant: object = None, **_: object
) -> None:
    """有房客被伪人替身顶替时，澪叁贰玖有机会识破并获得警觉印记。

    使用处：通用节点 ``pseudo.tenant_replaced``（任何伪人顶替屋内房客时广播）。
    本角色据此响应，伪人侧无需知道澪叁贰玖的存在。
    """
    if tenant is None or not getattr(tenant, "is_pseudo", False):
        return
    ling = next(
        (value for value in engine.home_tenants() if value.character_id == "zero329"),
        None,
    )
    if ling and engine._passive_available(ling, "zero329.detect"):
        success = (
            engine._rng(_event_id("zero329.detect.pseudo")).random() < .15
        )
        engine._skill_outcome(ling, "zero329.detect", success)
        if success:
            engine._gain_mark(ling, "alert", 1)
            handler = engine._pseudo_handler("create_accusation")
            if handler is not None:
                handler(engine, True)


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "information_collect": (
        lambda engine, actor, *, option=None, amount=None, ability_id=None, **kwargs:
        use_information_collect(
            engine, actor, ability_id or "information_collect",
            option=option, amount=amount,
        )
    ),
    "intent_awareness": (
        lambda engine, actor, *, option=None, amount=None,
        force_max_amount=False, forced=False, **kwargs:
        use_intent_awareness(
            engine, actor, option=option, amount=amount,
            force_max=force_max_amount, forced=forced,
        )
    ),
}

def turn_start(engine, tenant):
    """回合初实例钩子：委托给「敏锐直觉」。"""
    start_of_turn(engine, tenant)

TURN_START = turn_start


def end_of_turn_sanity_cost(
    engine: EngineProtocol, tenant: object, cost: float
) -> float:
    """澪叁贰玖的回合末理智消耗倍率：持有警觉印记时 ×1.5。

    使用处：round_effects 回合末 base_consume 经 CHARACTER_VALUE_HOOKS 查表调用。
    """
    return cost * sanity_cost_multiplier(engine, tenant)


VALUE_HOOKS = {"end_sanity_cost": end_of_turn_sanity_cost}


# ---------------------------------------------------------------- runtime


MARKS = (
    MarkDefinition(
        id="alert",
        label=TEXT["mark.alert.label"],
        acquisition=TEXT["mark.alert.acquisition"],
        minimum=0,
        maximum=3,
        # 1 = 够付一次能力代价；3 = 满档。
        bar_tiers=((1, TEXT["data.characters.zero329.module.2"], "danger"), (3, TEXT["data.characters.zero329.module.3"], "warn")),
        triggers=("pseudo.visit", "turn_start.instances"),
        hooks=(on_pseudo_visit,),
     description=TEXT["mark.alert.description"]),
)


def search_start_bonus(engine: EngineProtocol, tenant: object) -> tuple[int, int]:
    """信息收集：满足条件时搜索回合 -1、携带 +1。"""
    gathering = tenant.condition("information_gathering_zero329")
    if gathering.active:
        return (-1, 1)
    return (0, 0)


HOOKS = {
    "pseudo.tenant_replaced": on_tenant_replaced,
}


def _gathering_search_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]  # type: ignore[index]
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    gathering = tenant.condition("information_gathering_zero329")
    if gathering.active:
        yield spec("search").path("turn").flat(-1).source("ability", "zero329", "information_collect")
        yield spec("search").path("carry").flat(1).source("ability", "zero329", "information_collect")


from weiren_game.modifier_rules import register_modifier_provider as _regz
_regz("search", _gathering_search_modifier)


def _zero329_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "zero329":
        return
    mult = sanity_cost_multiplier(engine, tenant)
    if mult != 1.0:
        yield spec("sanityConsume").path("turn_end_consume").mul(mult).source("ability", "zero329", "alert")


from weiren_game.modifier_rules import register_modifier_provider as _regz
_regz("sanityConsume", _zero329_sanity_modifier)

NODE_HOOKS = {"pseudo_visit": on_pseudo_visit}

# 界面头像图标（内容自声明）。
AVATAR = "i-av12"


# ---------------------------------------------------------------- ui bridge
def information_candidates(engine: object, actor: object) -> list:
    """情报收集的候选：当前待识破的物资/地点信息（供界面选择）。"""
    return [
        {"value": info.info_instance_id, "label": info.title, "desc": info.text}
        for info in engine.state.house.information
        if info.status == "pending" and info.kind in {"material_reward", "location_modifier"}
    ]


TARGET_OPTIONS = {"information_collect": information_candidates}

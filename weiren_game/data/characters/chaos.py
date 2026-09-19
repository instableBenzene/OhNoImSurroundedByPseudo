"""房客档案：混（15 号，混沌性格与理智／癫狂机制）。

本文件按「定义 / 修饰器 / 技能函数」三节组织，混的专属逻辑（性格/携带量
随机切换、癫狂转化、混沌的思想、混沌的氛围、权限转让、回合末理智修正、
锁定自我）全部集中在此；系统只保留调用点。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.data.lang import TEXT

register_status_definition(StatusDefinition(
    "pure_self", TEXT["status.pure_self.label"], "other", shown=frozenset({"icon", "description"}),
    source_id="passive:chaos.self_lock",
    permanent=True,
 description=TEXT["status.pure_self.description"]))
register_status_definition(StatusDefinition(
    "chaos_carry", TEXT["status.chaos_carry.label"], "other", shown=frozenset(),
    source_id="passive:chaos.self_lock",
    permanent=True,
 description=TEXT["status.chaos_carry.description"]))
register_status_definition(StatusDefinition(
    "permission_shift", TEXT["status.permission_shift.label"], "other", shown=frozenset({"icon", "description"}),
    source_id="ability:permission_transfer@chaos",
    permanent=True,
    description=TEXT["status.permission_shift.description"]))

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "chaos", 15, TEXT["character.chaos.name"], TEXT["character.chaos.description"],
    "dynamic", "dynamic", 1, (TEXT["character.chaos.tag.0"], TEXT["character.chaos.tag.1"], TEXT["character.chaos.tag.2"]),
    # 注意：判据读的是**情绪「理智」的层数**（`tenant.reason.layers`）——它是**情绪**，不是理智**值**；
    # "理智值很高" 和 "攒够 10 层清醒情绪" 是两件事（玩家真这么误解过：以为有理智就能解锁）。
    (A("chaotic_personality", TEXT["ability.chaotic_personality.name"],
       TEXT["ability.chaotic_personality.description"]),
     A("reason_madness", TEXT["ability.reason_madness.name"],
       TEXT["ability.reason_madness.description"]),
     A("chaotic_thought", TEXT["ability.chaotic_thought.name"], TEXT["ability.chaotic_thought.description"]),
     A("chaotic_atmosphere", TEXT["ability.chaotic_atmosphere.name"], TEXT["ability.chaotic_atmosphere.description"])),
    (A("permission_transfer", TEXT["ability.permission_transfer.name"], TEXT["ability.permission_transfer.description"], "tenant", chips=(TEXT["ability.permission_transfer.chip.0"],), options=(("imitate",TEXT["ability.permission_transfer.option.0"],"i-hand",TEXT["data.characters.chaos.module.1"]),("trauma",TEXT["ability.permission_transfer.option.1"],"i-trauma",TEXT["data.characters.chaos.module.2"]),("disorder",TEXT["ability.permission_transfer.option.2"],"i-disorder",TEXT["data.characters.chaos.module.3"])), nested_option="imitate", per_turn=True),),
)

# ---------------------------------------------------------------- modifier
def reason_madness_available(engine: EngineProtocol, *, at_turn_end: bool = False) -> bool:
    """判断「情绪显现-清醒／癫狂」是否正在生效（任一屋内混通过被动判定）。

    回合开始与回合末使用不同的被动事件 ID。
    使用处：round_effects 的回合开始/回合末总调度。
    """
    event_id = "chaos.reason_madness.end" if at_turn_end else "chaos.reason_madness.start"
    return any(
        tenant.character_id == "chaos"
        and engine._passive_available(tenant, event_id)
        for tenant in engine.home_tenants()
    )


def locked_personality_weights(engine: EngineProtocol, tenant: object) -> tuple[float, float] | None:
    """混锁定自我后的主/副性格权重（2.0/1.0）；未锁定时返回 None。

    使用处：personality_system._personality_weights 的性格加权汇总。
    """
    if tenant.character_id == "chaos" and tenant.condition("pure_self").active:
        return 2.0, 1.0
    return None


# ---------------------------------------------------------------- function
def roll_personality_and_carry(engine: EngineProtocol, tenant: object) -> None:
    """混沌的性格：回合开始时**随机**切换主/副性格与可携带量（未锁定时）。

    使用处：round_effects 回合初实例节点经 TURN_START_HOOKS 查表调用。
    """
    if tenant.condition("pure_self").active:
        return
    available = engine._passive_available(tenant, "chaos.chaotic_personality")
    engine._skill_outcome(tenant, "chaos.chaotic_personality", available)
    if not available:
        return
    from weiren_game.data import PERSONALITIES, PERSONALITY_LABELS

    # 随机切换（不是玩家自选）：直接由种子随机取两个不同性格。
    rng = engine._rng(_event_id("chaos.personality"), tenant.id)
    primary, secondary = rng.sample(list(PERSONALITIES), 2)
    tenant.personalities = {primary: 1.0, secondary: 1.0}
    tenant.set_status("chaos_carry", intensity=4, layers=99)
    engine._log(
        TEXT["data.characters.chaos.roll_personality_and_carry.1"].format(p1=PERSONALITY_LABELS[primary], p2=PERSONALITY_LABELS[secondary])
    )


def persona_label(engine: EngineProtocol, tenant: object) -> str | None:
    """混未固定自我时，对外的性格显示为「混沌」；固定后交给运行时性格显示。

    使用处：web_ui 的房客卡（模块级 ``PERSONA_LABEL`` 钩子）。
    """
    from weiren_game.data import PERSONALITY_LABELS

    if tenant.condition("pure_self").active:
        return None
    return PERSONALITY_LABELS["dynamic"]


PERSONA_LABEL = persona_label


def chaotic_thought(engine: EngineProtocol, tenant: object) -> None:
    """混沌的思想：按屋内困境房客数量为混累计理智层数。

    使用处：round_effects 回合初实例节点经 TURN_START_HOOKS 查表调用。
    """
    available = engine._passive_available(tenant, "chaos.chaotic_thought")
    engine._skill_outcome(tenant, "chaos.chaotic_thought", available)
    if not available:
        return
    struggling = sum(
        1 for other in engine.home_tenants()
        if other.health <= 60 or other.sanity <= 60 or other.depression >= 25
    )
    if struggling:
        tenant.reason.intensity = 1
        tenant.reason.layers = min(99, tenant.reason.layers + struggling)


def convert_excess_madness(engine: EngineProtocol, tenant: object, *, emotions_active: bool) -> None:
    """回合开始把房客超过 1 层的癫狂转化为等量创伤与紊乱。

    「情绪显现-清醒／癫狂」生效（emotions_active）且层数达到 10 时才触发；
    转化保留基础 1 层癫狂，强度固定为 1。
    使用处：round_effects._start_of_turn_effects 的房客遍历。
    """
    if not emotions_active or tenant.madness.layers < 10:
        return
    excess = tenant.madness.layers - 1
    tenant.madness.intensity = tenant.madness.layers = 1
    for condition, label in ((tenant.trauma, TEXT["data.characters.chaos.convert_excess_madness.1"]), (tenant.disorder, TEXT["data.characters.chaos.convert_excess_madness.2"])):
        condition.intensity = max(1, condition.intensity)
        condition.layers = min(99, condition.layers + excess)
        condition.clamp(intensity_max=10)
        engine._log(TEXT["data.characters.chaos.convert_excess_madness.3"].format(p1=engine.character(tenant).name, p2=label, p3=excess))


def end_turn_sanity_modifier(
    engine: EngineProtocol, tenant: object, cost: float, *, emotions_active: bool
) -> float:
    """回合末理智修正：清醒情绪-5、癫狂情绪+10（情绪显现生效时）。

    使用处：round_effects._settle_base_end_effects 的理智消耗计算。
    """
    if not emotions_active:
        return cost
    if tenant.reason.active:
        cost = max(0, cost - 5)
    if tenant.madness.active:
        cost += 10
    return cost


def rescue_sanity(engine: EngineProtocol, tenant: object) -> None:
    """混沌的氛围：房客理智归零时拉回 50 并附加 5 层癫狂。

    使用处：value_system._reduce_sanity 的理智削减末尾。
    """
    if tenant.sanity > 0:
        return
    helpers = [value for value in engine.home_tenants() if value.character_id == "chaos"]
    fired = False
    for value in helpers:
        ok = engine._passive_available(value, "chaos.chaotic_atmosphere")
        engine._skill_outcome(value, "chaos.chaotic_atmosphere", ok)
        if ok:
            fired = True
            break
    if not fired:
        return
    tenant.sanity = 50
    tenant.madness.intensity = 1
    tenant.madness.layers = min(99, max(1, tenant.madness.layers + 5))
    engine._log(TEXT["data.characters.chaos.rescue_sanity.1"].format(p1=engine.character(tenant).name))


def pure_ego_personality(engine: EngineProtocol, tenant: object) -> None:
    """纯真的自我：清醒情绪达 10 层时**自动**固定性格与携带量（混的私有机制）。

    使用处：`round_effects._settle_tenant_instance_start` 的回合初实例节点
    （经 `TURN_START_HOOKS` 查表，见本模块 `TURN_START`）。核心不认识这条机制。
    """
    if tenant.character_id != "chaos":
        return
    if tenant.condition("pure_self").active or tenant.reason.layers < 10:
        return
    tenant.set_status("pure_self", intensity=1, layers=99)
    tenant.set_status("chaos_carry", intensity=4, layers=99)
    engine._log(TEXT["data.characters.chaos.pure_ego_personality.1"])


def use_permission_transfer(
    engine: EngineProtocol,
    actor: object,
    target_id: str | None,
    *,
    option: object,
    copied_ability_id: str | None,
    secondary_target_id: str | None,
    secondary_option: str | None,
    secondary_amount: int | None,
) -> object:
    """权限转让：模仿目标的主动能力，或治疗目标的创伤/紊乱。

    - **首次**发动：混消耗 1 层理智并获得 1 层癫狂（启动；存入 `permission_shift`）；
      启动之后两种效果都不再消耗，只受每回合 1 次的频次约束。
    - （外）模仿：目标以「10 生命 + 10 理智」的替代代价被强制发动技能，冷却保持目标原状；
    - （内）治疗：目标创伤或紊乱强度/层数各-1。
    使用处：ability_system.use_ability 的混分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    target = engine._require_home_tenant(target_id)
    # 前置的「消耗理智获得癫狂」只在第一次发动时支付一次（外置启动代价）。
    if not actor.condition("permission_shift").active:
        if actor.reason.layers < 1:
            raise RuleViolation(TEXT["data.characters.chaos.use_permission_transfer.1"])
        actor.reason.layers -= 1
        actor.reason.clamp()
        actor.madness.intensity = 1
        actor.madness.layers = max(1, actor.madness.layers + 1)
        actor.set_status("permission_shift", intensity=1, layers=99)
        engine._log(TEXT["data.characters.chaos.use_permission_transfer.2"])
    if option == "imitate":
        target_abilities = engine.character(target).actives
        copied = next((value for value in target_abilities if value.id == copied_ability_id), None)
        if copied is None and target_abilities:
            copied = target_abilities[0]
        if not copied or target.character_id == "chaos":
            raise RuleViolation(TEXT["data.characters.chaos.use_permission_transfer.3"])
        if target.health < 10 or target.sanity < 10:
            raise RuleViolation(TEXT["data.characters.chaos.use_permission_transfer.4"])
        # 前置替代代价由公共能力成本层统一结算（_DEFAULT_FORCED_COST_TERMS），
        # 只对尚未接入公共成本层的技能保留旧的手工扣除路径。
        copied_module = engine._local_skill_module(target.character_id)
        if not callable(getattr(copied_module, f"costs_{copied.id}", None)):
            engine._consume_health(target, 10, "permission_transfer")
            engine._consume_sanity(target, 10, "permission_transfer")
        saved_cooldowns = {
            state.ability_id: state.cooldown_until for state in target.abilities
        }
        try:
            result = engine.use_ability(
                target.id,
                secondary_target_id,
                copied.id,
                secondary_option,
                secondary_amount,
                force_max_amount=True,
                forced=True,
                _bypass_limits=True,
            )
        finally:
            for state in target.abilities:
                state.cooldown_until = saved_cooldowns.get(
                    state.ability_id, state.cooldown_until
                )
        engine._log(TEXT["data.characters.chaos.use_permission_transfer.7"].format(p1=engine.character(target).name, p2=copied.name))
        return result
    else:
        chosen = target.trauma if option != "disorder" else target.disorder
        engine._recover_condition(chosen, 1, 1)
    return None


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "permission_transfer": (
        lambda engine, actor, *, target_id=None, option=None,
        copied_ability_id=None, secondary_target_id=None,
        secondary_option=None, secondary_amount=None, **kwargs:
        use_permission_transfer(
            engine, actor, target_id, option=option,
            copied_ability_id=copied_ability_id,
            secondary_target_id=secondary_target_id,
            secondary_option=secondary_option,
            secondary_amount=secondary_amount,
        )
    ),
}


def turn_start(engine: EngineProtocol, tenant: object) -> None:
    """回合初实例钩子：先看是否该固定自我，再切换性格与累计思想。"""
    pure_ego_personality(engine, tenant)
    roll_personality_and_carry(engine, tenant)
    chaotic_thought(engine, tenant)


TURN_START = turn_start


def _chaos_emotion_visible(context: object) -> object:
    """情绪显现-清醒／癫狂（闸门 provider）：屋内有混时，理智/癫狂对屋主可见。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine")
    key = context.get("key")
    if engine is None or key not in {"reason", "madness"}:
        return
    if not any(value.character_id == "chaos" for value in engine.home_tenants()):
        return
    yield (
        gate("emotion.visible").path("emotion_visible", key).match("all")
        .source("character", "chaos", "emotion_reveal").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.visible", _chaos_emotion_visible)


def carry_override(engine: EngineProtocol, tenant: object):
    """混的性格锁定后的携带量覆盖（未锁定时返回 None）。"""
    condition = tenant.condition("chaos_carry")
    return int(condition.intensity) if condition.active else None


HOOKS = {
    "sanity.after_decrease": rescue_sanity,
    "personality.weights": locked_personality_weights,
    "madness.available": reason_madness_available,
    "madness.convert_excess": convert_excess_madness,
    "end_turn.sanity_modifier": end_turn_sanity_modifier,
    "search.carry_override": carry_override,
}


def _chaos_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    from weiren_game.data import NODE_HOOKS
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    active = any(hook(engine, at_turn_end=True) for hook in NODE_HOOKS.get("madness.available", ()))
    if not active:
        return
    if tenant.reason.active:
        yield spec("sanityConsume").path("turn_end_consume").flat(-5).source("ability", "dynamic", "sanity")
    if tenant.madness.active:
        yield spec("sanityConsume").path("turn_end_consume").flat(10).source("ability", "dynamic", "madness")


from weiren_game.modifier_rules import register_modifier_provider as _regch
_regch("sanityConsume", _chaos_sanity_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av3"




def detail_slot(engine: EngineProtocol, tenant: object) -> list[dict]:
    """详情页小面板：一张太极图。

    未固定自我时方向与速度都不定（每次刷新随机）；
    变成「纯真的自我」后稳定顺时针转。
    """
    pure = tenant.condition("pure_self").active
    return [{
        "kind": "glyph",
        # 角色自带图形（不借资源包贴图）：太极。
        "svg": ('<circle cx="12" cy="12" r="9"/><path d="M12 3a4.5 4.5 0 0 1 0 9 '
                '4.5 4.5 0 0 0 0 9"/><circle cx="12" cy="7.5" r="1.1"/>'
                '<circle cx="12" cy="16.5" r="1.1"/>'),
        "label": TEXT["data.characters.chaos.detail_slot.1"] if pure else TEXT["data.characters.chaos.detail_slot.2"],
        # 未解锁时把**进度**写出来：混乱值 ≠ 理智值，写清是"清醒情绪层数"才不会再误解。
        "hint": (TEXT["data.characters.chaos.detail_slot.3"] if pure
                 else TEXT["data.characters.chaos.detail_slot.4"] % tenant.reason.layers),
        "spin": "cw" if pure else "random",
    }]


DETAIL_SLOT = detail_slot

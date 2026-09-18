"""房客档案：混（15 号，混沌性格与理智／癫狂机制）。

本文件按「定义 / 修饰器 / 技能函数」三节组织，混的专属逻辑（性格/携带量
随机切换、癫狂转化、混沌的思想、混沌的氛围、权限转让、回合末理智修正、
锁定自我）全部集中在此；系统只保留调用点。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition

register_status_definition(StatusDefinition(
    "pure_self", "纯真的自我", "other", shown=frozenset({"icon", "description"}),
    source_id="passive:chaos.self_lock",
    permanent=True,
 description="守住「我还是我」这一点执念，不被情绪推着走。"))
register_status_definition(StatusDefinition(
    "chaos_carry", "混沌携带量", "other", shown=frozenset(),
    source_id="passive:chaos.self_lock",
    permanent=True,
 description="身上多出的那点分量，提醒着它借来的模样。"))
register_status_definition(StatusDefinition(
    "permission_shift", "权限转让·启动", "other", shown=frozenset({"icon", "description"}),
    source_id="ability:permission_transfer@chaos",
    permanent=True,
    description="权限已在流转——不再需要支付理智。"))

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "chaos", 15, "混", "思维跳脱，精神状态时常在正反之间横跳。",
    "dynamic", "dynamic", 1, ("无业游民", "25-30岁", "精神疾病"),
    (A("chaotic_personality", "混沌的性格／纯真的自我", "· 回合开始时，主性格与副性格分别在**八个性格**中随机切换；可携带物资数在 **1~4** 之间随机。\n· 理智层数 **≥10** 时，可以**固定**自己的主副性格（主性格权重变为 **2.0**），可携带物资数固定为 **4**。"),
     A("reason_madness", "情绪显现-理智／癫狂", "混在屋内时，屋主可以看到所有房客的理智与癫狂强度、层数（强度固定为 **1**）：\n· 理智：回合末消耗理智 **−5**。\n· 癫狂：回合末消耗理智 **+10**；层数 **≥10** 时，回合开始消耗所有额外癫狂，转化为同层数的创伤与紊乱。"),
     A("chaotic_thought", "混沌的思想", "每回合开始时，每有1名屋内的房客满足以下任一条件时，混理智层数+1：生命值≤60；理智值≤60；消沉值≥25。"),
     A("chaotic_atmosphere", "混沌的氛围", "混在屋内时，若有房客理智值≤0，将立刻将理智值恢复至50并使其癫狂层数+5。")),
    (A("permission_transfer", "权限转让", "**首次**发动时，混消耗 **1 层理智**、换来 **1 层癫狂**；此后不再消耗。发动时二选一：\n· **代你出手**：一名房客付出 **10 生命**与 **10 理智**，使用其主动能力（可无视回合、对局限制）。\n· **收走**一名房客身上的一道伤、或一团乱（层数 **−1**、强度 **−1**）。", "tenant", chips=("每回合 1 次",), options=(("imitate","代我出手","i-hand","让对方用它的主动能力出手"),("trauma","收走那道伤","i-trauma","创伤层数-1、强度-1"),("disorder","收走那点乱","i-disorder","紊乱层数-1、强度-1")), nested_option="imitate", per_turn=True),),
)

# ---------------------------------------------------------------- modifier
def reason_madness_available(engine: EngineProtocol, *, at_turn_end: bool = False) -> bool:
    """判断「情绪显现-理智／癫狂」是否正在生效（任一屋内混通过被动判定）。

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
        f"混本回合变为{PERSONALITY_LABELS[primary]}-"
        f"{PERSONALITY_LABELS[secondary]}，携带量4。"
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

    「情绪显现-理智／癫狂」生效（emotions_active）且层数达到 10 时才触发；
    转化保留基础 1 层癫狂，强度固定为 1。
    使用处：round_effects._start_of_turn_effects 的房客遍历。
    """
    if not emotions_active or tenant.madness.layers < 10:
        return
    excess = tenant.madness.layers - 1
    tenant.madness.intensity = tenant.madness.layers = 1
    for condition, label in ((tenant.trauma, "创伤"), (tenant.disorder, "紊乱")):
        condition.intensity = max(1, condition.intensity)
        condition.layers = min(99, condition.layers + excess)
        condition.clamp(intensity_max=10)
        engine._log(f"癫狂转化：{engine.character(tenant).name}的{label}层数+{excess}。")


def end_turn_sanity_modifier(
    engine: EngineProtocol, tenant: object, cost: float, *, emotions_active: bool
) -> float:
    """回合末理智修正：理智情绪-5、癫狂情绪+10（情绪显现生效时）。

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
    engine._log(f"混沌的氛围将{engine.character(tenant).name}的理智拉回50。")


def lock_personality(engine: EngineProtocol, actor: object) -> None:
    """混消耗 10 层理智情绪，固定当前性格与携带量（纯真的自我）。

    使用处：personality_system.lock_personality。
    """
    from weiren_game.exceptions import RuleViolation

    if actor.character_id != "chaos" or actor.reason.layers < 10:
        raise RuleViolation("混需要至少10层理智情绪才能固定自我。")
    actor.set_status("pure_self", intensity=1, layers=99)
    actor.set_status("chaos_carry", intensity=4, layers=99)
    engine._log("混固定了本回合的性格：主性格权重变为2.0，携带量固定为4。")


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
            raise RuleViolation("首次发动权限转让需要1层理智情绪。")
        actor.reason.layers -= 1
        actor.reason.clamp()
        actor.madness.intensity = 1
        actor.madness.layers = max(1, actor.madness.layers + 1)
        actor.set_status("permission_shift", intensity=1, layers=99)
        engine._log("权限转让启动：混消耗1层理智并获得1层癫狂；此后无需再消耗。")
    if option == "imitate":
        target_abilities = engine.character(target).actives
        copied = next((value for value in target_abilities if value.id == copied_ability_id), None)
        if copied is None and target_abilities:
            copied = target_abilities[0]
        if not copied or target.character_id == "chaos":
            raise RuleViolation("目标没有可安全模仿的主动能力。")
        if target.health < 10 or target.sanity < 10:
            raise RuleViolation("被转让权限的房客需要至少10生命和10理智。")
        # 前置替代代价由公共能力成本层统一结算（_DEFAULT_FORCED_COST_TERMS），
        # 只对尚未接入公共成本层的技能保留旧的手工扣除路径。
        if not (
            engine._ability_has_local_cost(target.character_id, copied.id)
        ):
            engine._consume_health(target, 10, "权限转让")
            engine._consume_sanity(target, 10, "权限转让")
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
        engine._log(f"混通过「权限转让」调用了{engine.character(target).name}的「{copied.name}」。")
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
    """回合初实例钩子：混沌的性格切换与混沌的思想。"""
    roll_personality_and_carry(engine, tenant)
    chaotic_thought(engine, tenant)


TURN_START = turn_start


def _chaos_emotion_visible(context: object) -> object:
    """情绪显现-理智／癫狂（闸门 provider）：屋内有混时，理智/癫狂对屋主可见。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine")
    key = context.get("key")
    if engine is None or key not in {"reason", "madness"}:
        return
    if not any(value.character_id == "chaos" for value in engine.home_tenants()):
        return
    yield (
        gate("emotion.visible").path("显示情绪", key).match("all")
        .source("角色", "混", "情绪显现").any()
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
    "personality.lock": lock_personality,
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
        yield spec("sanityConsume").path("回合末消耗").flat(-5).source("角色技能", "混沌", "理智")
    if tenant.madness.active:
        yield spec("sanityConsume").path("回合末消耗").flat(10).source("角色技能", "混沌", "癫狂")


from weiren_game.modifier_rules import register_modifier_provider as _regch
_regch("sanityConsume", _chaos_sanity_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av3"


def can_lock_personality(engine: object, tenant: object) -> bool:
    """是否可在理智达 10 层时固定性格与携带量（供系统通用询问）。"""
    return (
        tenant.character_id == "chaos"
        and not tenant.condition("pure_self").active
        and tenant.reason.layers >= 10
    )


CAN_LOCK_PERSONALITY = can_lock_personality


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
        "label": "纯真的自我" if pure else "混沌",
        "hint": "纯真的自我：方向已定。" if pure else "混沌：方向与速度都不由人。",
        "spin": "cw" if pure else "random",
    }]


DETAIL_SLOT = detail_slot

"""房客档案：葱头（5 号，共情与情绪剥离；也是伪人洋葱的人类形态）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition, MarkDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "onion", 5, TEXT["character.onion.name"], TEXT["character.onion.description"],
    "gentle", "steady", 3, (TEXT["character.onion.tag.0"], TEXT["character.onion.tag.1"], TEXT["character.onion.tag.2"], TEXT["character.onion.tag.3"], TEXT["character.onion.tag.4"]),
    (A("irritation_reveal", TEXT["ability.irritation_reveal.name"], TEXT["ability.irritation_reveal.description"]),
     A("calm", TEXT["ability.calm.name"], TEXT["ability.calm.description"])),
    (A("emotion_strip", TEXT["ability.emotion_strip.name"], TEXT["ability.emotion_strip.description"], "tenant", chips=(TEXT["ability.emotion_strip.chip.0"],)),
     A("group_counselling", TEXT["ability.group_counselling.name"], TEXT["ability.group_counselling.description"], chips=(TEXT["ability.group_counselling.chip.0"],))),
)

# ---------------------------------------------------------------- modifier
def blocks_irritation(engine: EngineProtocol, tenant: object) -> bool:
    """情绪显现-烦躁：葱头自身免疫烦躁。

    使用处：condition_system._emotion_application_blocked。
    """
    if tenant.character_id != "onion":
        return False
    return engine._passive_available(tenant, "onion.irritation_immunity")


def calm_irritation(engine: EngineProtocol, target: object) -> bool:
    """平静：葱头以 30% 概率阻止他人烦躁并获得共情印记。

    使用处：condition_system._emotion_application_blocked。
    """
    for onion in engine.home_tenants():
        if (
            onion.character_id == "onion"
            and engine._passive_available(onion, "onion.calm")
        ):
            success = engine._rng(_event_id("onion.calm"), target.id).random() < .30
            engine._skill_outcome(onion, "onion.calm", success)
            if success:
                engine._gain_mark(onion, "empathy", 1)
                engine._log(TEXT["data.characters.onion.calm_irritation.1"].format(p1=engine.character(target).name))
                return True
    return False


def _irritation_block_gate(context: object) -> object:
    """情绪显现-烦躁（闸门 provider）：葱头自身免疫烦躁。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine"); tenant = context.get("tenant"); key = context.get("key")
    if engine is None or tenant is None or key != "irritation":
        return
    if not blocks_irritation(engine, tenant):
        return
    yield (
        gate("emotion.apply.block").path("apply", "irritation").match("all")
        .source("character", "onion", "irritation_reveal").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.apply.block", _irritation_block_gate)


# ---------------------------------------------------------------- function
def use_emotion_strip(
    engine: EngineProtocol, actor: object, target_id: str | None, ability_id: str
) -> None:
    """情绪剥离：消耗共情印记或理智移除目标烦躁。

    使用处：ability_system.use_ability 的葱头分发分支。
    """
    target = engine._require_home_tenant(target_id)
    used_empathy = engine._mark_count(actor, "empathy") >= 1
    if used_empathy:
        costs = [T("mark", 1, key="empathy")]
    else:
        if actor.sanity < 15:
            from weiren_game.exceptions import RuleViolation

            raise RuleViolation(TEXT["data.characters.onion.use_emotion_strip.1"])
        costs = [T("sanity", 15)]
    engine._pay_ability_costs(actor, costs)
    if used_empathy:
        engine._restore_sanity(actor, 5, "emotion_strip")
        engine._restore_sanity(target, 5, "emotion_strip")
    target.irritation.clear()
    target.set_status(
        "calm_onion", intensity=1, layers=1
    )
    engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 2)


def use_group_counselling(engine: EngineProtocol, actor: object) -> None:
    """群体心理疏导：清除全员侵蚀情绪并减少消沉。

    使用处：ability_system.use_ability 的葱头分发分支。
    """
    from weiren_game.exceptions import RuleViolation
    from weiren_game.data import EROSION_EMOTIONS

    for tenant in engine.home_tenants():
        for key in EROSION_EMOTIONS:
            tenant.condition(key).clear()
        tenant.depression *= .25


def costs_group_counselling(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """群体心理疏导：3 层共情印记 + 每局一次。"""
    return [
        T("mark", 3, key="empathy"),
        T("game", 1, key="group_counselling_once"),
    ]


from weiren_game.condition import StatusDefinition, register_status_definition

register_status_definition(
    StatusDefinition(
        "calm_onion", TEXT["status.calm_onion.label"], "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="ability:emotion_strip@onion",
        nodes=frozenset({"status_applied.allow"}),
        blocked_emotions=("irritation",),
        hook=(lambda engine, tenant: tenant.condition("calm_onion").active),
     description=TEXT["status.calm_onion.description"])
)


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "emotion_strip": (
        lambda engine, actor, *, target_id=None, ability_id=None, **kwargs:
        use_emotion_strip(engine, actor, target_id, ability_id or "emotion_strip")
    ),
    "group_counselling": (
        lambda engine, actor, **kwargs: use_group_counselling(engine, actor)
    ),
}


def _onion_emotion_visible(context: object) -> object:
    """情绪显现-烦躁（闸门 provider）：屋内有葱头时，烦躁对屋主可见。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine")
    key = context.get("key")
    if engine is None or key != "irritation":
        return
    if not any(value.character_id == "onion" for value in engine.home_tenants()):
        return
    yield (
        gate("emotion.visible").path("emotion_visible", "irritation").match("all")
        .source("character", "onion", "irritation_reveal").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.visible", _onion_emotion_visible)


# 印记资源声明：mark 资源 key -> (GameState 容器字段, 读取方法, 写入方法)。
# ---------------------------------------------------------------- runtime


MARKS = (
    MarkDefinition(
        id="empathy",
        label=TEXT["mark.empathy.label"],
        acquisition=TEXT["mark.empathy.acquisition"],
        minimum=0,
        maximum=3,
        # 1 = 够付一次「平静」；3 = 大招代价。
        bar_tiers=((1, TEXT["data.characters.onion.module.1"], "danger"), (3, TEXT["data.characters.onion.module.2"], "warn")),
        triggers=("status_applied.allow",),
        hooks=(calm_irritation,),
     description=TEXT["mark.empathy.description"]),
)


HOOKS = {"condition.irritation.settle": calm_irritation}

# 界面头像图标（内容自声明）。
AVATAR = "i-av2"

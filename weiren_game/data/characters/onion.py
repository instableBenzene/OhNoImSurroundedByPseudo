"""房客档案：葱头（5 号，共情与情绪剥离；也是伪人洋葱的人类形态）。

按“定义 / 修饰器 / 技能函数”组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition, MarkDefinition, T
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "onion", 5, "葱头", "带着从容与神秘笑容的绿发少女，爱好心理学研究。",
    "gentle", "steady", 3, ("心理学专业", "研究生", "大学生", "18-24岁", "女性"),
    (A("irritation_reveal", "情绪显现-烦躁", "洋葱在屋内时，屋主可以看到所有房客的烦躁强度、层数。洋葱免疫烦躁效果。"),
     A("calm", "平静", "洋葱在屋内时，房客在获得烦躁时，有30%的可能免疫该效果。若触发该效果，洋葱获得1个【共情印记-洋葱】（至多3个）。")),
    (A("emotion_strip", "情绪剥离", "消耗 **1 个**【共情印记-洋葱】或 **15 理智**，移除 1 名房客的烦躁，并使其本回合不会获得烦躁。\n*若消耗的是印记，则令洋葱和该房客额外回复 **5 理智**。*", "tenant", chips=("冷却 2 回合",)),
     A("group_counselling", "群体心理疏导", "消耗3个【共情印记-洋葱】，移除所有房客的所有情绪负面效果，并使其消沉值减少75%。*每次对局仅能使用1次。", chips=("每次对局 1 次",))),
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
                engine._log(f"洋葱以“平静”帮助{engine.character(target).name}免疫了烦躁。")
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
        gate("emotion.apply.block").path("施加", "irritation").match("all")
        .source("角色", "葱头", "情绪显现-烦躁").any()
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

            raise RuleViolation("需要1层共情印记或15理智。")
        costs = [T("sanity", 15)]
    engine._pay_ability_costs(actor, costs)
    if used_empathy:
        engine._restore_sanity(actor, 5, "情绪剥离")
        engine._restore_sanity(target, 5, "情绪剥离")
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
        "calm_onion", "平静-洋葱", "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="ability:emotion_strip@onion",
        nodes=frozenset({"status_applied.allow"}),
        blocked_emotions=("irritation",),
        hook=(lambda engine, tenant: tenant.condition("calm_onion").active),
     description="把翻涌的烦躁按回水底，海面暂时平静。")
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
        gate("emotion.visible").path("显示情绪", "irritation").match("all")
        .source("角色", "葱头", "情绪显现-烦躁").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.visible", _onion_emotion_visible)


# 印记资源声明：mark 资源 key -> (GameState 容器字段, 读取方法, 写入方法)。
# ---------------------------------------------------------------- runtime


MARKS = (
    MarkDefinition(
        id="empathy",
        label="共情印记-洋葱",
        acquisition="洋葱触发“平静”免疫烦躁时获得 1 层。",
        minimum=0,
        maximum=3,
        # 1 = 够付一次「平静」；3 = 大招代价。
        bar_tiers=((1, "可平静", "danger"), (3, "大招", "warn")),
        triggers=("status_applied.allow",),
        hooks=(calm_irritation,),
     description="对他人情绪的共鸣，攒够了便能反过来安抚自己。"),
)


HOOKS = {"condition.irritation.settle": calm_irritation}

# 界面头像图标（内容自声明）。
AVATAR = "i-av2"

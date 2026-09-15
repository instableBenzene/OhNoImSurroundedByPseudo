"""房客档案：罗兹（13 号，恶魔印记机制）。

按“定义 / 修饰器 / 技能函数”组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition, MarkDefinition, T
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "rose", 13, "罗兹", "流淌着恶魔血液的魔人，为寻找友人踏入未知领域。",
    "suspicious", "stubborn", 3, ("学生", "16-18岁", "男性", "神秘学研究者"),
    (A("blood_drive", "驭血", "当罗兹的生命值以任何方式减少时，获得1层【恶魔印记-罗兹】（最多6层，后称为印记）。当印记≤3时，罗兹消沉值变化量-25%。当印记＞3时，罗兹消沉值变化量+10%。当印记≥6层时，罗兹将消耗所有印记及当前50%理智值，获得1层【魔化印记-罗兹】（最多1层），将生命值恢复至100；且下回合无法行动或使用能力。"),),
    (A("rose_recover", "风花雪月／该我上场了？", "消耗1层印记。为自身回复5生命或5理智；若拥有【魔化印记-罗兹】，则额外消耗1层【魔化印记-罗兹】，对所有房客造成5点生命伤害，并使自身回复等额的理智。*每个回合仅能使用1次。", "resource", prompt="回复哪种资源？", options=(("health","生命"),("sanity","理智")), chips=("每回合 1 次",), per_turn=True),
     A("rose_expel", "千裁缠天／本小姐可没什么负罪感", "消耗4层印记，驱逐1名房客。若目标为人类，罗兹流失25理智，回复25生命；若目标为伪人，罗兹将回复40理智值；若拥有【魔化印记-罗兹】，则额外消耗1层【魔化印记-罗兹】，为自己回复等同于被驱逐房客的生命和理智。", "other_tenant", prompt="选择要驱逐的房客")),
)

# ---------------------------------------------------------------- modifier
def emotion_value_multiplier(engine: EngineProtocol, tenant: object) -> float:
    """情绪结算的恶魔印记修饰：印记 ≤3 时减轻，否则加重。

    使用处：round_effects 的消沉值结算。
    """
    if (
        engine._passive_available(tenant, "rose.blood.emotion_value")
    ):
        return .75 if engine._mark_count(tenant, "demon") <= 3 else 1.10
    return 1.0


def costs_rose_recover(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """风花雪月：消耗 1 层恶魔印记。"""
    return [T("mark", 1, key="demon")]


def costs_rose_expel(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """千裁缠天：消耗 4 层恶魔印记。"""
    return [T("mark", 4, key="demon")]


# ---------------------------------------------------------------- function
def use_rose_recover(engine: EngineProtocol, actor: object, *, option: object) -> None:
    """风花雪月：消耗 1 恶魔印记回复自身 5 生命或 5 理智。

    使用处：ability_system.use_ability 的罗兹分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    if option == "sanity":
        engine._restore_sanity(actor, 5, "风花雪月")
    else:
        engine._restore_health(actor, 5, "风花雪月")
    if engine._mark_count(actor, "magic") > 0:
        engine._consume_mark(actor, "magic", 1)
        total = 0.0
        for tenant in engine.home_tenants():
            before = tenant.health
            engine._damage_health(tenant, 5, "罗兹魔化")
            total += max(0, before - tenant.health)
        engine._restore_sanity(actor, total, "罗兹魔化")


def use_rose_expel(engine: EngineProtocol, actor: object, target_id: str | None) -> None:
    """千裁缠天：消耗 4 恶魔印记驱逐一名房客。

    使用处：ability_system.use_ability 的罗兹分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    target = engine._require_home_tenant(target_id)
    if target.id == actor.id:
        raise RuleViolation("罗兹不能驱逐自己。")
    was_pseudo = target.is_pseudo
    target_health, target_sanity = target.health, target.sanity
    engine._expel_tenant(target, "罗兹")
    if was_pseudo:
        engine._restore_sanity(actor, 40, "驱逐伪人")
    else:
        engine._loss_sanity(actor, 25, "驱逐人类")
        engine._restore_health(actor, 25, "驱逐人类")
    if engine._mark_count(actor, "magic") > 0:
        engine._consume_mark(actor, "magic", 1)
        engine._restore_health(actor, max(0, target_health), "魔化吸收")
        engine._restore_sanity(actor, max(0, target_sanity), "魔化吸收")


def on_health_decrease(engine: EngineProtocol, tenant: object) -> None:
    """驭血：生命下降时积累恶魔印记（满 6 层由 mark.reached 触发魔化）。

    使用处：value_system._after_health_decrease。
    """
    if tenant.character_id != "rose":
        return
    available = engine._passive_available(tenant, "rose.blood")
    engine._skill_outcome(tenant, "rose.blood", available)
    if not available:
        return
    engine._gain_mark(tenant, "demon", 1)


def on_mark_reached(
    engine: EngineProtocol, tenant: object, mark_id: str, amount: float
) -> None:
    """恶魔印记达到上限：消耗 6 层、50% 理智，获得魔化并恢复全部生命。

    使用处：mark.reached 节点（在印记获得时派发）。
    """
    if mark_id != "demon" or tenant.character_id != "rose":
        return
    engine._consume_mark(tenant, "demon", 6)
    engine._consume_sanity(tenant, max(0.0, tenant.sanity * .50), "驭血魔化")
    engine._gain_mark(tenant, "magic", 1)
    tenant.health = tenant.max_health
    tenant.skip_until_turn = engine.state.flow.turn + 1
    engine._log("罗兹集齐6层恶魔印记：魔化、恢复全部生命，并将在下一回合无法行动。")


ON_MARK_REACHED = on_mark_reached

ACTIVE_DISPATCH = {
    "rose_recover": (
        lambda engine, actor, *, option=None, **kwargs:
        use_rose_recover(engine, actor, option=option)
    ),
    "rose_expel": (
        lambda engine, actor, *, target_id=None, **kwargs:
        use_rose_expel(engine, actor, target_id)
    ),
}


VALUE_HOOKS = {
    "after_health_decrease": on_health_decrease,
    "emotion_value_multiplier": emotion_value_multiplier,
}


# ---------------------------------------------------------------- runtime


MARKS = (
    MarkDefinition(
        id="demon",
        label="恶魔印记-罗兹",
        acquisition="罗兹生命值以任何方式减少时获得 1 层。",
        minimum=0,
        maximum=6,
        # 3 = 代码里的分档点（≤3 / >3 的伤害倍率）；4 = 千裁缠天；6 = 满档转化。
        bar_tiers=((3, "临界"), (4, "可驱逐", "danger"), (6, "转化", "warn")),
        triggers=("health.changed.after",),
        hooks=(on_health_decrease,),
     description="每一次流血都在饲育体内的东西，越痛它越清醒。"),
    MarkDefinition(
        id="magic",
        label="魔化印记-罗兹",
        acquisition="恶魔印记达到 6 层时，消耗全部印记与当前 50% 理智获得 1 层。",
        minimum=0,
        maximum=1,
        triggers=("mark.demon.full",),
        hooks=(on_health_decrease,),
     description="与体内之物达成的交易，代价是清醒的一半。"),
)


def _rose_depression_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "rose":
        return
    if not engine._passive_available(tenant, "rose.blood.emotion_value"):
        return
    mult = .75 if engine._mark_count(tenant, "demon") <= 3 else 1.10
    yield spec("depressionChange").path("消沉").mul(mult).source("角色技能", "罗兹", "驭血")


from weiren_game.modifier_rules import register_modifier_provider as _regr
_regr("depressionChange", _rose_depression_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av4"

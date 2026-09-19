"""房客档案：罗兹（13 号，恶魔印记机制）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition, MarkDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "rose", 13, TEXT["character.rose.name"], TEXT["character.rose.description"],
    "suspicious", "stubborn", 3, (TEXT["character.rose.tag.0"], TEXT["character.rose.tag.1"], TEXT["character.rose.tag.2"], TEXT["character.rose.tag.3"]),
    (A("blood_drive", TEXT["ability.blood_drive.name"], TEXT["ability.blood_drive.description"]),),
    (A("rose_recover", TEXT["ability.rose_recover.name"], TEXT["ability.rose_recover.description"], "resource", prompt=TEXT["ability.rose_recover.prompt"], options=(("health",TEXT["ability.rose_recover.option.0"],"i-cross",TEXT["data.characters.rose.module.1"]),("sanity",TEXT["ability.rose_recover.option.1"],"i-emotion",TEXT["data.characters.rose.module.2"])), chips=(TEXT["ability.rose_recover.chip.0"],), per_turn=True),
     A("rose_expel", TEXT["ability.rose_expel.name"], TEXT["ability.rose_expel.description"], "other_tenant", prompt=TEXT["ability.rose_expel.prompt"])),
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
        engine._restore_sanity(actor, 5, "rose_blizzard")
    else:
        engine._restore_health(actor, 5, "rose_blizzard")
    if engine._mark_count(actor, "magic") > 0:
        engine._consume_mark(actor, "magic", 1)
        total = 0.0
        for tenant in engine.home_tenants():
            before = tenant.health
            engine._damage_health(tenant, 5, "rose_demonize")
            total += max(0, before - tenant.health)
        engine._restore_sanity(actor, total, "rose_demonize")


def use_rose_expel(engine: EngineProtocol, actor: object, target_id: str | None) -> None:
    """千裁缠天：消耗 4 恶魔印记驱逐一名房客。

    使用处：ability_system.use_ability 的罗兹分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    target = engine._require_home_tenant(target_id)
    if target.id == actor.id:
        raise RuleViolation(TEXT["data.characters.rose.use_rose_expel.1"])
    was_pseudo = target.is_pseudo
    target_health, target_sanity = target.health, target.sanity
    engine._expel_tenant(target, TEXT["data.characters.rose.use_rose_expel.2"])
    if was_pseudo:
        engine._restore_sanity(actor, 40, "expel_pseudo")
    else:
        engine._loss_sanity(actor, 25, "expel_human")
        engine._restore_health(actor, 25, "expel_human")
    if engine._mark_count(actor, "magic") > 0:
        engine._consume_mark(actor, "magic", 1)
        engine._restore_health(actor, max(0, target_health), "demonize_absorb")
        engine._restore_sanity(actor, max(0, target_sanity), "demonize_absorb")


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
    engine._consume_sanity(tenant, max(0.0, tenant.sanity * .50), "blood_drive_demonize")
    engine._gain_mark(tenant, "magic", 1)
    tenant.health = tenant.max_health
    tenant.skip_until_turn = engine.state.flow.turn + 1
    # 真警告（少用）：魔化是强力但有代价的状态，下一回合不能行动要提前让人看到。
    engine._log(TEXT["data.characters.rose.on_mark_reached.2"], kind="warn")


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
        label=TEXT["mark.demon.label"],
        acquisition=TEXT["mark.demon.acquisition"],
        minimum=0,
        maximum=6,
        # 3 = 代码里的分档点（≤3 / >3 的伤害倍率）；4 = 千裁缠天；6 = 满档转化。
        bar_tiers=((3, TEXT["data.characters.rose.module.3"]), (4, TEXT["data.characters.rose.module.4"], "danger"), (6, TEXT["data.characters.rose.module.5"], "warn")),
        triggers=("health.changed.after",),
        hooks=(on_health_decrease,),
     description=TEXT["mark.demon.description"]),
    MarkDefinition(
        id="magic",
        label=TEXT["mark.magic.label"],
        acquisition=TEXT["mark.magic.acquisition"],
        minimum=0,
        maximum=1,
        triggers=("mark.demon.full",),
        hooks=(on_health_decrease,),
     description=TEXT["mark.magic.description"]),
)


def _rose_depression_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "rose":
        return
    if not engine._passive_available(tenant, "rose.blood.emotion_value"):
        return
    mult = .75 if engine._mark_count(tenant, "demon") <= 3 else 1.10
    yield spec("depressionChange").path("depression").mul(mult).source("ability", "rose", "blood_drive")


from weiren_game.modifier_rules import register_modifier_provider as _regr
_regr("depressionChange", _rose_depression_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av4"

"""房客档案：苯环（4 号，孤独喧闹／重症监护，也是伪人苯环的人类形态）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "benzene", 4, TEXT["character.benzene.name"], TEXT["character.benzene.description"],
    "loner", "steady", 4, (TEXT["character.benzene.tag.0"], TEXT["character.benzene.tag.1"], TEXT["character.benzene.tag.2"], TEXT["character.benzene.tag.3"], TEXT["character.benzene.tag.4"]),
    (A("quiet_noise", TEXT["ability.quiet_noise.name"], TEXT["ability.quiet_noise.description"]),
     A("icu", TEXT["ability.icu.name"], TEXT["ability.icu.description"])),
    (A("emergency_treatment", TEXT["ability.emergency_treatment.name"], TEXT["ability.emergency_treatment.description"], "tenant_condition", prompt=TEXT["ability.emergency_treatment.prompt"], options=(("trauma",TEXT["ability.emergency_treatment.option.0"],"i-trauma",TEXT["data.characters.benzene.module.1"]),("disorder",TEXT["ability.emergency_treatment.option.1"],"i-disorder",TEXT["data.characters.benzene.module.2"]))),),
)

# ---------------------------------------------------------------- function
def use_emergency_treatment(engine: EngineProtocol, target_id: str | None, option: object) -> None:
    """紧急处置：移除目标创伤或紊乱，目标按强度×层数消耗理智。

    「强度×层数」的理智消耗属于技能 effect，不是前置 cost，因此本技能不声明
    cost 分支；该扣除由效果函数直接结算。
    使用处：ability_system.use_ability 的苯环分发分支。
    """
    from weiren_game.exceptions import RuleViolation

    target = engine._require_home_tenant(target_id)
    selected = option
    if selected not in {"trauma", "disorder"}:
        selected = "trauma" if target.trauma.active else "disorder"
    condition_obj = target.trauma if selected == "trauma" else target.disorder
    if not condition_obj.active:
        raise RuleViolation(TEXT["data.characters.benzene.use_emergency_treatment.1"])
    cost = condition_obj.intensity * condition_obj.layers
    condition_obj.clear()
    engine._consume_sanity(target, cost, "emergency_treatment")


def end_turn_cost(engine: EngineProtocol, tenant: object, cost: float) -> float:
    """孤独／喧闹与重症监护：回合末理智消耗修正。

    使用处：round_effects 的回合末理智消耗计算。
    """
    if engine._passive_available(tenant, "benzene.solitude_noise"):
        if 3 <= len(engine.home_tenants()) <= 6:
            cost = max(0, cost - 3)
        else:
            cost += 3
    return cost


def icu_maintain(engine: EngineProtocol) -> None:
    """重症监护（icu）：苯环在屋且理智>20 时，把生命<20 者抬到 20 并扣 10 理智。

    注册到 health-changed 节点；每次生命数值变动后即时判定。
    """
    doctor = next(
        (
            tenant
            for tenant in engine.home_tenants()
            if tenant.character_id == "benzene" and tenant.sanity > 20
        ),
        None,
    )
    if doctor is None:
        return
    patients = [tenant for tenant in engine.home_tenants() if tenant.health < 20]
    if not patients:
        return
    for tenant in patients:
        tenant.health = 20.0
    engine._consume_sanity(doctor, 10, "icu")


HEALTH_CHANGED = icu_maintain


def end_of_turn_loss_reduction(
    engine: EngineProtocol, tenant: object, amount: float
) -> float:
    """孤独／喧闹：屋内 3~6 人时回合末生命流失 -3。

    使用处：value_system._loss_health 经 CHARACTER_VALUE_HOOKS 查表调用。
    """
    if (
        engine.state.flow.phase == "turn_end"
        and 3 <= len(engine.home_tenants()) <= 6
    ):
        amount = max(0.0, amount - 3)
    return amount


VALUE_HOOKS = {
    "health_loss": end_of_turn_loss_reduction,
    "end_sanity_cost": end_turn_cost,
}


def _dispatch_emergency_treatment(engine, actor, *, target_id=None, option=None, **kwargs):
    return use_emergency_treatment(engine, target_id, option)

ACTIVE_DISPATCH = {
    "emergency_treatment": _dispatch_emergency_treatment,
}


# ---------------------------------------------------------------- runtime


def _benzene_loss_modifier(context: object):
    """孤独/喧闹：苯环在 3~6 人的屋内时，回合末自身生命流失 -3。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "benzene":
        return
    if engine.state.flow.phase == "turn_end" and 3 <= len(engine.home_tenants()) <= 6:
        yield spec("healthLoss").path("health_loss").flat(-3).source("ability", "benzene", "quiet_noise")


from weiren_game.modifier_rules import register_modifier_provider as _regb
_regb("healthLoss", _benzene_loss_modifier)


def _benzene_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "benzene" or not engine._passive_available(tenant, "benzene.solitude_noise"):
        return
    if 3 <= len(engine.home_tenants()) <= 6:
        yield spec("sanityConsume").path("turn_end_consume").flat(-3).source("ability", "benzene", "quiet_noise")
    else:
        yield spec("sanityConsume").path("turn_end_consume").flat(3).source("ability", "benzene", "quiet_noise")


from weiren_game.modifier_rules import register_modifier_provider as _regbs
_regbs("sanityConsume", _benzene_sanity_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av1"

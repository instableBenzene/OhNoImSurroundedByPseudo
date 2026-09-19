"""房客档案：堤谧特（17 号，绝对无声）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from weiren_game.probability import resolve

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "demit", 17, TEXT["character.demit.name"], TEXT["character.demit.description"], "loner", "gentle", 3,
    (TEXT["character.demit.tag.0"], TEXT["character.demit.tag.1"], TEXT["character.demit.tag.2"]), (A("silent", TEXT["ability.silent.name"], TEXT["ability.silent.description"]),),
)

# ---------------------------------------------------------------- function
def resists_pseudo_active(
    engine: EngineProtocol, tenant: object, event_id: str, *, success_penalty: float
) -> bool:
    """默默无声：完全不受伪人主动技能影响（受全局避让修正约束）。

    使用处：pseudo_system._skill_respond_skill 的 lock 阶段。
    """
    if not engine._passive_available(tenant, f"{event_id}.demit"):
        return False
    from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers

    source = (TEXT["data.characters.demit.resists_pseudo_active.1"], TEXT["data.characters.demit.resists_pseudo_active.2"], TEXT["data.characters.demit.resists_pseudo_active.3"], TEXT["data.characters.demit.resists_pseudo_active.4"])
    ctx = {"engine": engine, "tenant": tenant, "event_id": event_id}
    value = calculate_modified_amount(
        0.0, collect_modifiers("chance", source, ctx)
    )
    guarantee = [1.0] if (value >= 1.0 and success_penalty <= 0) else []
    chance = resolve(value - success_penalty, guarantee)
    if engine._rng(f"{event_id}.demit.resist").random() < chance:
        engine._skill_outcome(tenant, f"{event_id}.demit", True)
        engine._log(TEXT["data.characters.demit.resists_pseudo_active.5"].format(p1=engine.state.pseudo_state.name))
        return True
    engine._skill_outcome(tenant, f"{event_id}.demit", False)
    return False


def _demit_resist_modifier(context: object):
    """默默无声：必定不受伪人主动能力影响（抵御）。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]; event_id = context.get("event_id", "")  # type: ignore[index]
    if not engine._passive_available(tenant, f"{event_id}.demit"):
        return
    yield (
        spec("chance").certain(1.0).match("all")
        .path("resist", "pseudo_active").source("ability", "demit", "silent")
    )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _demit_resist_modifier)

NODE_HOOKS = {"target_lock": resists_pseudo_active}

# 界面头像图标（内容自声明）。
AVATAR = "i-av4"

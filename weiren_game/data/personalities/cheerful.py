"""性格·开朗：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT


def start_of_turn_bond(engine: EngineProtocol, bonds: dict[str, int]) -> None:
    """开朗羁绊：回合初为全屋回复理智，高羁绊时额外减轻开朗者的侵蚀。"""
    cheerful = engine._bond_tier("cheerful", bonds.get("cheerful", 0))
    if not cheerful:
        return
    heal = {2: 1, 5: 2, 8: 5}[cheerful]
    for tenant in engine.home_tenants():
        engine._restore_sanity(tenant, heal, "cheerful_bond")
    if cheerful >= 8:
        for tenant in engine.home_tenants():
            if engine._is_personality(tenant, "cheerful"):
                engine._reduce_emotion_set(tenant, "erosion", 8, 8)


BOND_HOOKS = {
    "turn_start.bond_effects": start_of_turn_bond,
}


def end_sanity_cost(
    engine: EngineProtocol, tenant: object, cost: float, bonds: dict[str, int]
) -> float:
    """开朗羁绊：回合末自然理智消耗减免。"""
    cheerful = engine._bond_tier("cheerful", bonds.get("cheerful", 0))
    if cheerful:
        cost = max(0.0, cost - {2: 1, 5: 2, 8: 5}[cheerful])
    return cost


END_SANITY_COST = end_sanity_cost


def awakening_gain_multiplier(
    engine: EngineProtocol, tenant: object
) -> float:
    """开朗性格及其羁绊对觉醒情绪获取量的放大系数。"""
    if not engine._is_personality(tenant, "cheerful"):
        return 1.0
    bonus = .20
    tier = engine._bond_tier("cheerful")
    if tier >= 8:
        bonus += 1.00
    elif tier >= 5:
        bonus += .50
    return 1.0 + bonus


AWAKENING_MULTIPLIER = awakening_gain_multiplier


TIERS = (2, 5, 8)


def _cheerful_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    tier = engine._bond_tier("cheerful")
    if tier:
        yield spec("sanityConsume").path("turn_end_consume").flat(-{2: 1, 5: 2, 8: 5}[tier]).source("bond", "cheerful")


def _cheerful_awakening_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if not engine._is_personality(tenant, "cheerful"):
        return
    bonus = .20
    tier = engine._bond_tier("cheerful")
    if tier >= 8:
        bonus += 1.00
    elif tier >= 5:
        bonus += .50
    yield spec("awakeningGain").path("awakening").percent(bonus).source("personality", "cheerful")


from weiren_game.modifier_rules import register_modifier_provider as _regc
_regc("sanityConsume", _cheerful_sanity_modifier)
_regc("awakeningGain", _cheerful_awakening_modifier)
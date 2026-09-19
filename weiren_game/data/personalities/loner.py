"""性格·孤僻：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT


def health_protection(
    engine: EngineProtocol,
    tenant: object,
    amount: float,
    *,
    consume: bool,
) -> tuple[float, float]:
    """孤僻在生命/理智「消耗」时的减伤，以及孤僻羁绊的额外减伤。"""
    loner = engine._is_personality(tenant, "loner")
    reduction = .20 if (consume and loner) else 0.0
    loner_level = engine.bond_levels().get("loner", 0)
    if loner and (loner_level == 1 or loner_level >= 5):
        reduction += .50 if loner_level >= 5 else .20
    return reduction, 0.0


def end_sanity_cost(
    engine: EngineProtocol, tenant: object, cost: float, bonds: dict[str, int]
) -> float:
    """孤僻羁绊：孤僻者免消耗并回 10 理智，其余房客 +3。"""
    loner_level = bonds.get("loner", 0)
    if loner_level < 5:
        return cost
    if engine._is_personality(tenant, "loner"):
        engine._restore_sanity(tenant, 10, "loner_bond")
        return 0.0
    return cost + 3


def emotion_change_multiplier(
    engine: EngineProtocol, tenant: object, change: float
) -> float:
    """孤僻在消沉正向变化且未深陷孤僻羁绊时放大。"""
    if change <= 0 or not engine._is_personality(tenant, "loner"):
        return 1.0
    loner_level = engine.bond_levels().get("loner", 0)
    if loner_level in {1} or loner_level >= 5:
        return 1.0
    return 1.20


HEALTH_PROTECTION = health_protection
END_SANITY_COST = end_sanity_cost
EMOTION_CHANGE_MULTIPLIER = emotion_change_multiplier


def search_start(
    engine: EngineProtocol,
    tenant: object,
    turn_modifier: int,
    success_rate: float,
) -> tuple[int, float]:
    """孤僻羁绊：孤僻者单独行动更快且必然成功。"""
    if not engine._is_personality(tenant, "loner"):
        return turn_modifier, success_rate
    loner_level = engine.bond_levels().get("loner", 0)
    if loner_level not in {1} and loner_level < 5:
        return turn_modifier, success_rate
    turn_modifier -= 2 if loner_level >= 5 else 1
    return turn_modifier, 1.0


def active_tiers(level: int) -> list[int]:
    """孤僻羁绊：1 档激活，或 ≥5 档激活。"""
    if level == 1:
        return [1]
    if level >= 5:
        return [5]
    return []


def tier_at(level: int) -> int:
    """孤僻不在通用「达到即激活」的档位体系内。"""
    return 0


ACTIVE_TIERS = active_tiers
TIER_AT = tier_at


def _loner_turn_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]  # type: ignore[index]
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    if not engine._is_personality(tenant, "loner"):
        return
    level = engine.bond_levels().get("loner", 0)
    if level != 1 and level < 5:
        return
    yield spec("search").path("turn").flat(-2 if level >= 5 else -1).source("bond", "loner")


def _loner_success_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if not engine._is_personality(tenant, "loner"):
        return
    level = engine.bond_levels().get("loner", 0)
    if level != 1 and level < 5:
        return
    yield spec("chance").certain(1.0).path("search").source("bond", "loner")


from weiren_game.modifier_rules import register_modifier_provider as _regl
_regl("search", _loner_turn_modifier)
_regl("chance", _loner_success_modifier)


def _loner_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if engine.bond_levels().get("loner", 0) < 5:
        return
    if engine._is_personality(tenant, "loner"):
        engine._restore_sanity(tenant, 10, "loner_bond")
        yield spec("sanityConsume").path("turn_end_consume").final().max(0).source("bond", "loner")
    else:
        yield spec("sanityConsume").path("turn_end_consume").flat(3).source("bond", "loner")


def _loner_depression_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    change = context.get("change")
    if not change or change <= 0 or not engine._is_personality(tenant, "loner"):
        return
    level = engine.bond_levels().get("loner", 0)
    if level in {1} or level >= 5:
        return
    yield spec("depressionChange").path("depression").mul(1.20).source("personality", "loner")


from weiren_game.modifier_rules import register_modifier_provider as _reglo
_reglo("sanityConsume", _loner_sanity_modifier)
_reglo("depressionChange", _loner_depression_modifier)

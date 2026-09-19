"""性格·急躁：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT


def end_health_loss(engine: EngineProtocol, tenant: object) -> None:
    """急躁性格：按羁绊档位概率在回合末受到 5 生命伤害。"""
    if not engine._is_personality(tenant, "impatient"):
        return
    from weiren_game.data import EVENT_IDS

    tier = engine._bond_tier("impatient")
    chance = {0: .20, 2: .30, 4: .35, 6: .40, 8: .40}.get(tier, .20)
    if engine._rng(EVENT_IDS["impatient.health"], tenant.id).random() < chance:
        engine._damage_health(tenant, 5, "impatient_personality")


BOND_END_HEALTH = end_health_loss


def search_start(
    engine: EngineProtocol,
    tenant: object,
    turn_modifier: int,
    success_rate: float,
) -> tuple[int, float]:
    """急躁性格：搜索回合更短但成功率更低（有羁绊时更极端）。"""
    if not engine._is_personality(tenant, "impatient"):
        return turn_modifier, success_rate
    tier = engine._bond_tier("impatient")
    if tier:
        _chance, delta, rate_delta = {
            2: (.30, -2, -.15),
            4: (.35, -4, -.15),
            6: (.40, -6, -.10),
            8: (.40, -99, -.10),
        }[tier]
        return turn_modifier + delta, success_rate + rate_delta
    return turn_modifier - 1, success_rate - .20


def search_reset(
    engine: EngineProtocol,
    tenant: object,
    initial_turns: int,
    turn_modifier: int,
) -> tuple[int, int]:
    """急躁羁绊 8 档：搜索强制为 1 回合。"""
    if (
        engine._is_personality(tenant, "impatient")
        and engine._bond_tier("impatient") >= 8
    ):
        return 1, 0
    return initial_turns, turn_modifier


def on_activate(engine: EngineProtocol, tier: int) -> None:
    """急躁羁绊激活奖励：每激活新档获得一枚强心剂。"""
    engine._gain_item("stimulant")


TIERS = (2, 4, 6, 8)
ON_ACTIVATE = on_activate


HOOKS = {
    "search.parameters.reset": search_reset,
}


def _impatient_turn_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]  # type: ignore[index]
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    if not engine._is_personality(tenant, "impatient"):
        return
    tier = engine._bond_tier("impatient")
    delta = {2: -2, 4: -4, 6: -6, 8: -99}.get(tier, -1) if tier else -1
    yield spec("search").path("turn").flat(delta).source("personality", "impatient")


def _impatient_success_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if not engine._is_personality(tenant, "impatient"):
        return
    tier = engine._bond_tier("impatient")
    rate = {2: -.15, 4: -.15, 6: -.10, 8: -.10}.get(tier, -.20) if tier else -.20
    yield spec("chance").path("search").flat(rate).source("personality", "impatient")


from weiren_game.modifier_rules import register_modifier_provider as _regi
_regi("search", _impatient_turn_modifier)
_regi("chance", _impatient_success_modifier)

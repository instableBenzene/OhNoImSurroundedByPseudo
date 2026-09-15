"""性格·稳重：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol


def health_protection(
    engine: EngineProtocol,
    tenant: object,
    amount: float,
    *,
    consume: bool,
) -> tuple[float, float]:
    """稳重减伤与稳重羁绊的跨房客分担（固定量转嫁）。"""
    steady = engine._is_personality(tenant, "steady")
    reduction = .20 if (consume and steady) else 0.0
    transferred = 0.0
    tier = engine._bond_tier("steady")
    if tier == 2:
        reduction += .20 if steady else .10
    elif tier == 5:
        reduction += .50 if steady else .20
    elif tier >= 8:
        reduction += .60
        if not steady:
            # 非稳重房客同样获得 60% 减免；其中 50% 由稳重者分担。
            transferred = amount * .50
    return reduction, transferred


HEALTH_PROTECTION = health_protection


def share_receivers(
    engine: EngineProtocol, tenant: object
) -> list[object]:
    """稳重羁绊的固定量分担接收者（屋内其它稳重房客）。"""
    return [
        value
        for value in engine.home_tenants()
        if value.id != tenant.id and engine._is_personality(value, "steady")
    ]


TIERS = (2, 5, 8)
ROUND_UP = True


HOOKS = {"health.transfer_receivers": share_receivers}
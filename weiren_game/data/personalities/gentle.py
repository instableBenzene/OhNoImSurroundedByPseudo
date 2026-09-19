"""性格·温和：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT


def end_health_loss(engine: EngineProtocol, tenant: object) -> None:
    """温和性格：回合末额外流失 2 生命。"""
    if engine._is_personality(tenant, "gentle"):
        engine._loss_health(tenant, 2, "gentle_personality")


def scheduled_extra_interval(engine: EngineProtocol) -> int | None:
    """温和羁绊：每隔若干回合在访客队列中追加一位额外访客。"""
    return {3: 4, 6: 3, 9: 2}.get(engine._bond_tier("gentle"))


def active_supply(engine: EngineProtocol) -> bool:
    """温和羁绊激活时，名册为空的来访会转为「计入接纳」的补给。"""
    return engine._bond_tier("gentle") >= 3


def accept_healing(engine: EngineProtocol, accepted: object) -> None:
    """温和性格与羁绊：接纳访客时为屋内房客结算治愈效果。"""
    gentle = engine._bond_tier("gentle")
    home = engine.home_tenants()
    for tenant in home:
        if engine._is_personality(tenant, "gentle"):
            engine._restore_health(tenant, 5, "gentle")
    if gentle == 3:
        for tenant in home:
            if engine._is_personality(tenant, "gentle"):
                engine._restore_health(tenant, 5, "gentle_bond")
                engine._restore_sanity(tenant, 5, "gentle_bond")
    elif gentle == 6:
        for tenant in home:
            engine._restore_health(tenant, 5, "gentle_bond")
            engine._restore_sanity(tenant, 5, "gentle_bond")
            if engine._is_personality(tenant, "gentle") or (
                accepted and tenant.id == accepted.id
            ):
                engine._restore_health(tenant, 5, "gentle_bond_extra")
                engine._restore_sanity(tenant, 10, "gentle_bond_extra")
    elif gentle >= 9:
        for tenant in home:
            engine._restore_health(tenant, 15, "gentle_bond")
            engine._restore_sanity(tenant, 15, "gentle_bond")
    engine._after_health_changed()


BOND_END_HEALTH = end_health_loss


TIERS = (3, 6, 9)


HOOKS = {
    "visitor.extra_interval": scheduled_extra_interval,
    "visitor.supply": active_supply,
    "visitor.accept_healing": accept_healing,
}
"""生命/理智数值带来的效果与方法（高生命免疫等）。

由 lifecycle 的 allow/modify 微触发调用；不再散落在 condition/value 系统里。
"""

from __future__ import annotations


def _permanent_immunity(engine: object) -> bool:
    """a-10：房客常驻免疫创伤与紊乱（难度词条）。"""
    from weiren_game.data import DIFFICULTIES

    return bool(
        DIFFICULTIES[engine.state.meta.difficulty].get("trauma_disorder_immunity")
    )


def _consume_immunity(tenant: object) -> bool:
    """消耗一点「高生命免疫」充能；强度归零即自然移除。"""
    immunity = tenant.condition("high_health_immunity")
    if not immunity.active or immunity.intensity <= 0:
        return False
    immunity.intensity -= 1
    if immunity.intensity <= 0:
        tenant.clear_status("high_health_immunity")
    return True


def high_health_status_immunity(
    engine: object, tenant: object, source: str = ""
) -> bool:
    """创伤/紊乱的状态施加闸门（原稿：生命 ≥95 且无创伤/紊乱时，每回合首次免疫）。

    a-10 为无条件常驻；其余情况下先复核高生命条件，再消耗一点强度抵挡。
    """
    if not _permanent_immunity(engine):
        if tenant.health < 95 or tenant.trauma.active or tenant.disorder.active:
            return False
    return _consume_immunity(tenant)


def refresh_high_health_immunity(engine: object, tenant: object) -> None:
    """回合开始：满足「生命 ≥95 且无创伤/紊乱」则给予 1 强度 1 层。

    a-10 的常驻免疫已在入住时一次性给予，不在此处刷新。
    """
    if _permanent_immunity(engine):
        return
    if tenant.health >= 95 and not tenant.trauma.active and not tenant.disorder.active:
        tenant.set_status("high_health_immunity", intensity=1, layers=1)


def decay_high_health_immunity(engine: object, tenant: object) -> None:
    """回合末：未被消耗的免疫扣 1 层，层数归零即消失（a-10 常驻不衰减）。"""
    if _permanent_immunity(engine):
        return
    immunity = tenant.condition("high_health_immunity")
    if not immunity.active:
        return
    immunity.layers -= 1
    if immunity.layers <= 0:
        tenant.clear_status("high_health_immunity")


def grant_permanent_trauma_disorder_immunity(engine: object, tenant: object) -> None:
    """a-10：房客入住时一次性获得 99 点免疫充能（常驻免疫）。"""
    if _permanent_immunity(engine):
        tenant.set_status("high_health_immunity", intensity=99, layers=99)


__all__ = [
    "decay_high_health_immunity",
    "grant_permanent_trauma_disorder_immunity",
    "high_health_status_immunity",
    "refresh_high_health_immunity",
]

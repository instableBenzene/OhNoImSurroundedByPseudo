"""tag: anodyne（镇痛剂：为创伤/紊乱附加「额外效果免疫」若干回合）。

行为就近住在本模块：核心只按 tag 分发 `use`，不认识"镇痛剂"这件事
（规则见 `docs/DECISIONS.md` 的边界条目）。
"""

from __future__ import annotations

from weiren_game.data.lang import TEXT


def use(
    engine: object, item: object, tenant: object,
    inventory: object = None, spot: object = None, *, condition: str | None = None,
) -> None:
    """使用镇痛剂：为目标创伤/紊乱附加持续若干回合的额外效果免疫。"""
    from weiren_game.data import NODE_HOOKS
    from weiren_game.exceptions import RuleViolation

    choices = {"trauma": tenant.trauma, "disorder": tenant.disorder}
    if condition not in choices:
        active = [key for key, value in choices.items() if value.active]
        if not active:
            raise RuleViolation(TEXT["data.tags.anodyne.1"])
        condition = active[0]
    target = choices[condition]
    if not target.active or target.intensity > item.medical_max_intensity:
        raise RuleViolation(TEXT["data.tags.anodyne.2"])

    duration = None
    for hook in NODE_HOOKS.get("analgesic.duration", ()):
        duration = hook(item.item_id)
        if duration is not None:
            break
    if duration is None:
        raise RuleViolation(TEXT["data.tags.anodyne.3"])
    status_id = None
    for hook in NODE_HOOKS.get("analgesic.status_id", ()):
        status_id = hook(engine, condition)
        if status_id:
            break
    if status_id is None:
        raise RuleViolation(TEXT["data.tags.anodyne.4"])

    current = tenant.condition(status_id)
    if not (current.active and current.layers > duration):
        tenant.set_status(status_id, intensity=1, layers=duration)
    engine._spend_item_use(item.item_id, item, tenant, inventory=inventory, spot=spot)
    engine._log(TEXT["data.tags.anodyne.5"].format(
        p1=engine.character(tenant).name, p2=item.name,
        p3=engine.state.flow.turn + duration,
    ))


__all__ = ["use"]

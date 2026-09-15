"""性格·机敏：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol


def fragile_delta(engine: EngineProtocol, tenant: object) -> float:
    """机敏羁绊与机敏性格降低物品损坏率（返回需要减去的量）。"""
    bond = engine.bond_levels().get("keen", 0)
    delta = 0.0
    if bond >= 4:
        delta += .15
    elif bond >= 2:
        delta += .10
    if tenant and engine._is_personality(tenant, "keen") and bond >= 4:
        delta += .15
    return delta


TIERS = (2, 4)


def loot_quality_weights(engine: object, mission: object, tenant: object, quality_weights: list) -> None:
    """敏锐羁绊：提升蓝色及以上品质的掉落权重。"""
    if tenant is None:
        return
    keen = engine._is_personality(tenant, "keen")
    global_keen = int(engine.bond_levels().get("keen", 0))
    for quality, weight in enumerate(quality_weights):
        increase = .50 if keen and quality >= 3 else 0.0
        if 2 <= global_keen < 4 and keen and quality >= 3:
            increase += 1.0
        elif global_keen >= 4:
            if quality >= 3:
                increase += 1.0
            if quality >= 4:
                increase += 1.0
        quality_weights[quality] = weight * (1.0 + increase)


HOOKS = {
    "item.fragility_delta": fragile_delta,
    "loot.quality_weights": loot_quality_weights,
}

def _keen_fragile_modifier(context: object):
    """敏锐羁绊：降低易损概率。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant is None:
        return
    delta = fragile_delta(engine, tenant)
    if delta:
        yield (
            spec("chance").path("易损").flat(-float(delta))
            .source("性格", "敏锐")
        )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _keen_fragile_modifier)

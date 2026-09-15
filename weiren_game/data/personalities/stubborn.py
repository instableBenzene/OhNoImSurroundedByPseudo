"""性格·固执：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol


def search_base(
    engine: EngineProtocol, tenant: object, rng: object, turn_modifier: int
) -> int:
    """固执性格：搜索前随机延长 2~4 回合（代表不撞南墙不回头）。"""
    if engine._is_personality(tenant, "stubborn"):
        return turn_modifier + rng.randint(2, 4)
    return turn_modifier


def search_bond(
    engine: EngineProtocol,
    tenant: object,
    carry: int,
    success_rate: float,
    guaranteed: list[object],
) -> tuple[int, float]:
    """固执羁绊：按档位提高成功率并保底高级物资（容量改写见携带修饰器）。"""
    if not engine._is_personality(tenant, "stubborn"):
        return carry, success_rate
    level = engine.bond_levels().get("stubborn", 0)
    tier = level if level in {4, 7, 10} else 0
    if not tier:
        return carry, success_rate
    from weiren_game.data import EVENT_IDS

    success_rate += {4: .10, 7: .20, 10: .40}[tier]
    if tier >= 7:
        guaranteed.append(
            engine._random_item(
                minimum_quality=2,
                event_id=EVENT_IDS["stubborn.blue"],
                event_suffix=(tenant.id,),
            )
        )
    if tier >= 10:
        guaranteed.append(
            engine._random_item(
                minimum_quality=3,
                event_id=EVENT_IDS["stubborn.purple"],
                event_suffix=(tenant.id,),
            )
        )
    return carry, success_rate


def _stubborn_carry_modifier(context: object):
    """固执羁绊：按档位增加携带容量（无副作用，供界面与搜索共用）。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    if not engine._is_personality(tenant, "stubborn"):
        return
    level = engine.bond_levels().get("stubborn", 0)
    if level not in {4, 7, 10}:
        return
    yield (
        spec("search").path("携带").flat(float({4: 1, 7: 2, 10: 4}[level]))
        .source("性格", "固执")
    )


from weiren_game.modifier_rules import register_modifier_provider as _regc
_regc("search", _stubborn_carry_modifier)


def active_tiers(level: int) -> list[int]:
    """固执羁绊只在恰好 4/7/10 档激活。"""
    return [level] if level in {4, 7, 10} else []


def tier_at(level: int) -> int:
    """固执不在通用“达到即激活”的档位体系内。"""
    return 0


ACTIVE_TIERS = active_tiers
TIER_AT = tier_at


HOOKS = {
    "search.start.bond": search_bond,
}


def _stubborn_turn_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]  # type: ignore[index]
    tenant = context.get("tenant")  # type: ignore[union-attr]
    if tenant is None:
        return
    rng = context.get("rng")
    if rng is None:
        return
    if engine._is_personality(tenant, "stubborn"):
        yield spec("search").path("回合").flat(rng.randint(2, 4)).source("性格", "固执")


from weiren_game.modifier_rules import register_modifier_provider as _regs
_regs("search", _stubborn_turn_modifier)

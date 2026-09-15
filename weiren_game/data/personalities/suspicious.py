"""性格·多疑：性格/羁绊效果全部集中在本文件。"""

from weiren_game.types import EngineProtocol


def start_of_turn_bond(engine: EngineProtocol, bonds: dict[str, int]) -> None:
    """多疑羁绊：按档位生成多疑信息并让多疑者尝试识别假信息。"""
    suspicious = engine._bond_tier("suspicious", bonds.get("suspicious", 0))
    suspicious_tenants = [
        t for t in engine.home_tenants() if engine._is_personality(t, "suspicious")
    ]
    if suspicious == 2:
        engine._create_random_information(False, "多疑羁绊")
    elif suspicious == 4:
        engine._create_random_information(True, "多疑羁绊")
        engine._create_random_information(False, "多疑羁绊")
    elif suspicious >= 8:
        engine._create_random_information(True, "多疑羁绊")
        engine._create_random_information(True, "多疑羁绊")
        engine._create_random_information(False, "多疑羁绊")
    if suspicious >= 2 and suspicious < 4 and engine.state.flow.turn % 2 == 0:
        for tenant in suspicious_tenants:
            engine._discern_one_information(tenant, false_only=suspicious >= 4)
    if suspicious >= 4:
        for tenant in suspicious_tenants:
            engine._discern_one_information(tenant, false_only=True)
    if suspicious >= 8:
        for _tenant in suspicious_tenants:
            engine._create_random_information(False, "多疑房客的额外观察")


def health_protection(
    engine: EngineProtocol,
    tenant: object,
    amount: float,
    *,
    consume: bool,
) -> tuple[float, float]:
    """多疑在生命/理智“消耗”时获得小幅减伤。"""
    if consume and engine._is_personality(tenant, "suspicious"):
        return .05, 0.0
    return 0.0, 0.0


def emotion_change_multiplier(
    engine: EngineProtocol, tenant: object, change: float
) -> float:
    """多疑在消沉正向变化时放大。"""
    if change > 0 and engine._is_personality(tenant, "suspicious"):
        return 1.05
    return 1.0


def item_use_wasted(
    engine: EngineProtocol, tenant: object, item_id: str, item: object,
    inventory: object = None, spot: object = None,
) -> bool:
    """多疑房客使用物资时有 10% 概率浪费本次使用。"""
    if not engine._is_personality(tenant, "suspicious"):
        return False
    from weiren_game.data import EVENT_IDS

    if engine._rng(EVENT_IDS["item.suspicious"], tenant.id).random() >= .10:
        return False
    engine._spend_item_use(item_id, item, tenant, inventory=inventory, spot=spot)
    engine._log(f"{engine.character(tenant).name}疑心太重，物资被浪费。")
    return True


BOND_HOOKS = {
    "turn_start.bond_effects": start_of_turn_bond,
}
HEALTH_PROTECTION = health_protection
EMOTION_CHANGE_MULTIPLIER = emotion_change_multiplier


TIERS = (2, 4, 8)


def on_initial(engine: EngineProtocol) -> None:
    """多疑羁绊的初始信息发放（常驻效果的启动部分）。"""
    tier = engine._bond_tier("suspicious")
    for _ in range(2 if tier >= 8 else 1 if tier >= 4 else 0):
        engine._create_random_information(True, "多疑羁绊")
    if tier >= 2:
        engine._create_random_information(False, "多疑羁绊")


ON_INITIAL = on_initial


HOOKS = {"item.use_wasted": item_use_wasted}


def _suspicious_depression_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    change = context.get("change")
    if change and change > 0 and engine._is_personality(tenant, "suspicious"):
        yield spec("depressionChange").path("消沉").mul(1.05).source("性格", "多疑")


from weiren_game.modifier_rules import register_modifier_provider as _regsu
_regsu("depressionChange", _suspicious_depression_modifier)

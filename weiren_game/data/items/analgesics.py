"""大类：镇痛剂（原稿未给品质色，按药物层级保守取值）。"""

from ..types import I
from weiren_game.data.lang import TEXT

ITEMS = {
    "yuntongqu": I("yuntongqu", TEXT["item.yuntongqu.name"], "medical", 1, TEXT["item.yuntongqu.description"], ("medical_supply", "anodyne", "durability_consumable"), max_durability=1, use_cost=1, medical_max_intensity=3, source_note=TEXT["data.items.analgesics.module.1"]),
    "parecoxib": I("parecoxib", TEXT["item.parecoxib.name"], "medical", 3, TEXT["item.parecoxib.description"], ("medical_supply", "anodyne", "durability_consumable"), max_durability=5, use_cost=1, medical_max_intensity=6, source_note=TEXT["data.items.analgesics.module.2"]),
    "morphine": I("morphine", TEXT["item.morphine.name"], "medical", 5, TEXT["item.morphine.description"], ("medical_supply", "anodyne", "consumable"), consumable=True, medical_max_intensity=9, source_note=TEXT["data.items.analgesics.module.3"]),
}

# 镇痛剂持续时间（回合），与各物品说明一致。
USE_DURATIONS = {
    "yuntongqu": 2,
    "parecoxib": 3,
    "morphine": 10,
}


def suppress_extra_effect(engine: object, tenant: object, condition_name: str) -> bool:
    """镇痛生效判定：额外效果是否被压制（镇痛状态仍在即压）。"""
    analgesia = tenant.condition(f"analgesia_{condition_name}")
    return analgesia.active


def _suppress(engine: object, tenant: object, condition: str) -> bool:
    """镇痛 hook：按条件名判定是否压制。"""
    return suppress_extra_effect(engine, tenant, condition)


def _status_id(engine: object, condition: str) -> str:
    """返回该镇痛剂条件对应的状态 id。"""
    return f"analgesia_{condition}"


from weiren_game.condition import StatusDefinition, register_status_definition

register_status_definition(
    StatusDefinition(
        "analgesia_trauma", TEXT["status.analgesia_trauma.label"], "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="item:analgesics",
        nodes=frozenset({"status_applied.modify"}),
        suppresses_conditions=("trauma",),
        hook=_suppress,
     description=TEXT["status.analgesia_trauma.description"])
)
register_status_definition(
    StatusDefinition(
        "analgesia_disorder", TEXT["status.analgesia_disorder.label"], "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="item:analgesics",
        nodes=frozenset({"status_applied.modify"}),
        suppresses_conditions=("disorder",),
        hook=_suppress,
     description=TEXT["status.analgesia_disorder.description"])
)


def analgesic_duration(item_id: str) -> int | None:
    """返回镇痛剂持续时间（回合）；非镇痛剂返回 None。"""
    return USE_DURATIONS.get(item_id)


HOOKS = {"analgesic.duration": analgesic_duration, "analgesic.status_id": _status_id}

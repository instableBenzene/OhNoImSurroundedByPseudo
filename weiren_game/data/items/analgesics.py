"""大类：镇痛剂（原稿未给品质色，按药物层级保守取值）。"""

from ..types import I

ITEMS = {
    "yuntongqu": I("yuntongqu", "殒痛去", "medical", 1, "≤3级创伤/紊乱免疫额外效果2回合。", ("medical_supply", "anodyne", "durability_consumable"), max_durability=1, use_cost=1, medical_max_intensity=3, source_note="原稿未标品质；按低阶药设为绿色。"),
    "parecoxib": I("parecoxib", "帕瑞昔布注射液", "medical", 3, "≤6级创伤/紊乱免疫额外效果3回合。", ("medical_supply", "anodyne", "durability_consumable"), max_durability=5, use_cost=1, medical_max_intensity=6, source_note="原稿未标品质；按中阶药设为紫色。"),
    "morphine": I("morphine", "盐酸吗啡注射液", "medical", 5, "≤9级创伤/紊乱免疫额外效果10回合。", ("medical_supply", "anodyne", "consumable"), consumable=True, medical_max_intensity=9, source_note="原稿未标品质；按最高阶药设为红色。"),
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
        "analgesia_trauma", "镇痛（创伤）", "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="item:analgesics",
        nodes=frozenset({"status_applied.modify"}),
        suppresses_conditions=("trauma",),
        hook=_suppress,
     description="伤痛被麻药按住，暂时不再叫嚣。")
)
register_status_definition(
    StatusDefinition(
        "analgesia_disorder", "镇痛（紊乱）", "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="item:analgesics",
        nodes=frozenset({"status_applied.modify"}),
        suppresses_conditions=("disorder",),
        hook=_suppress,
     description="被药力压住的杂念，安静得近乎可疑。")
)


def analgesic_duration(item_id: str) -> int | None:
    """返回镇痛剂持续时间（回合）；非镇痛剂返回 None。"""
    return USE_DURATIONS.get(item_id)


HOOKS = {"analgesic.duration": analgesic_duration, "analgesic.status_id": _status_id}

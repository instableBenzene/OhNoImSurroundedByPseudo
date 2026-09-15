"""内容展示标签：把内部键（分类/tag/品质段位/地点分组）映射为界面显示名。

属于内容层：核心与前端不写死任何内容文案，统一从这里（或各内容模块）取。
"""

from __future__ import annotations


ACTIVE_USES_CHIP = "每回合 1 次"
BOND_TIER_NAMES = ("", "铜", "银", "金", "棱彩")

ITEM_CATEGORY_LABELS = {
    "medical": "医疗", "food": "食物", "tool": "工具", "craft": "工艺",
    "information": "信息载体", "character": "角色物品", "artworks": "艺术品",
}

# 标签中文名与设计稿（游戏资源.md）对齐；medical_supply 沿用「医疗物资」。
ITEM_TAG_LABELS = {
    "ammo": "弹药", "anodyne": "镇痛剂", "armor": "装甲", "book": "书籍",
    "can": "罐头", "consultation_carrier": "资讯刊物", "consumable": "消耗品",
    "craft": "工艺品", "drink": "饮料", "durability_consumable": "耐久度消耗品",
    "entertainment": "消遣物", "flintlock": "燧发枪", "food": "食物",
    "fragile": "易损品", "information_carrier": "信息载体", "medical_supply": "医疗物资",
    "medicine_kit": "医药箱", "placeholder": "占位符", "seasoning": "调味品",
    "shoes": "鞋类", "snack": "零食", "star_doll": "星形玩偶",
    "surgery_kit": "手术包", "tool": "工具", "walmart_bag": "购物袋",
}

QUALITY_TIER_LABELS = {
    "low": "蓝色及以下", "blue": "蓝色", "blue_plus": "蓝色及以上",
    "high": "紫色及以上", "purple": "紫色", "gold": "金色",
    "gold_plus": "金色及以上", "red": "红色",
}

LOCATION_GROUP_LABELS = {"medical": "医疗", "tool": "工具", "food": "食物", "mixed": "混合"}
LOCATION_GROUP_ICONS = {"medical": "i-cross", "tool": "i-tool", "food": "i-snack", "mixed": "i-gate"}


INFORMATION_KIND_LABELS = {
    "material_reward": "物资线索",
    "location_modifier": "地点修正",
    "state": "房客状态",
    "visit": "来访信息",
    "pseudo_skill": "伪人技能",
    "pseudo_visit": "伪人来访",
    "accusation": "指认",
    "human_false": "人类误报",
}


def information_kind_label(kind: str) -> str:
    return INFORMATION_KIND_LABELS.get(kind, kind)


# 可"装备"的 tag（用于下发物品的 equip 标志，前端不写死）。
EQUIP_TAGS = frozenset({"armor", "tool", "information_carrier", "craft"})

# tag -> 图标（物资图鉴/格子用；取首个命中的 tag，回退到分类图标）。
ITEM_TAG_ICONS = {
    "ammo": "i-bullet", "flintlock": "i-target", "armor": "i-armor", "book": "i-book",
    "drink": "i-drink", "food": "i-snack", "snack": "i-snack", "can": "i-snack",
    "seasoning": "i-snack", "medical_supply": "i-cross", "surgery_kit": "i-cross",
    "medicine_kit": "i-cross", "anodyne": "i-pill", "tool": "i-tool", "craft": "i-craft",
    "information_carrier": "i-note", "consultation_carrier": "i-note",
    "entertainment": "i-battery", "shoes": "i-armor", "star_doll": "i-doll",
    "walmart_bag": "i-bag", "placeholder": "i-snack",
}

# 图标优先顺序（越靠前越具象，避免被 information_carrier 等泛标签抢占）。
ITEM_TAG_ICON_PRIORITY = [
    "star_doll", "walmart_bag", "book", "ammo", "flintlock", "armor", "shoes",
    "drink", "anodyne", "medicine_kit", "surgery_kit", "medical_supply",
    "snack", "food", "can", "seasoning", "tool", "craft",
    "information_carrier", "consultation_carrier", "entertainment", "placeholder",
]


# ---- 内容层登记入口（DLC 装载器与内容模块使用；热切换时会被整体回滚） ----
def register_item_category_label(category: str, label: str) -> None:
    """登记一个物品分类的中文名（DLC 新分类）。"""
    ITEM_CATEGORY_LABELS[category] = label


def register_item_tag_label(tag: str, label: str) -> None:
    """登记一个物品 tag 的中文名（DLC 新 tag）。"""
    ITEM_TAG_LABELS[tag] = label


def register_item_tag_icon(tag: str, icon: str, *, priority: int | None = None) -> None:
    """登记 tag 图标；``priority`` 给出时插入优先序列表（越小越靠前）。"""
    ITEM_TAG_ICONS[tag] = icon
    if tag in ITEM_TAG_ICON_PRIORITY:
        ITEM_TAG_ICON_PRIORITY.remove(tag)
    if priority is None:
        ITEM_TAG_ICON_PRIORITY.append(tag)
    else:
        ITEM_TAG_ICON_PRIORITY.insert(max(0, min(int(priority), len(ITEM_TAG_ICON_PRIORITY))), tag)


def register_information_kind_label(kind: str, label: str) -> None:
    """登记一种信息类型的中文名（DLC 新信息类型）。"""
    INFORMATION_KIND_LABELS[kind] = label


def register_location_group(group: str, label: str, icon: str = "i-gate") -> None:
    """登记一个地点分组的中文名与图标（DLC 新分组）。"""
    LOCATION_GROUP_LABELS[group] = label
    LOCATION_GROUP_ICONS[group] = icon


def category_label(category: str) -> str:
    return ITEM_CATEGORY_LABELS.get(category, category)


def tag_label(tag: str) -> str:
    return ITEM_TAG_LABELS.get(tag, tag)


def tier_label(key: str) -> str:
    return QUALITY_TIER_LABELS.get(key, key)


def group_label(group: str) -> str:
    return LOCATION_GROUP_LABELS.get(group, group)


def group_icon(group: str) -> str:
    return LOCATION_GROUP_ICONS.get(group, "i-gate")


__all__ = [
    "ACTIVE_USES_CHIP",
    "BOND_TIER_NAMES",
    "ITEM_CATEGORY_LABELS", "ITEM_TAG_LABELS", "QUALITY_TIER_LABELS",
    "LOCATION_GROUP_LABELS", "LOCATION_GROUP_ICONS",
    "category_label", "tag_label", "tier_label", "group_label", "group_icon",
    "ITEM_TAG_ICONS", "ITEM_TAG_ICON_PRIORITY",
    "register_item_category_label", "register_item_tag_label", "register_item_tag_icon",
    "register_information_kind_label", "register_location_group",
]

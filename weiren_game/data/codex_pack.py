"""图鉴包（内容层，独立可导入）：羁绊档位/条件/基础效果、伪人技能、基础机制、地点展示。

本文件即"基础图鉴包"（类似 base 内容包）：核心与前端不写死图鉴文案，一律从这里取。
- 额外图鉴分节：:func:`register_section`（DLC 的 ``codex/`` 目录会调用它）。
- 物品关联：:func:`build_item_links` 扫描物品文本自动得到 物品→羁绊/角色/伪人 的跳转。
- 地点：:data:`LOCATION_ICONS` / :data:`LOCATION_TEXT` 覆盖地点图标与完整描述（取自设计稿）。
"""

from __future__ import annotations

from .codex_mechanics import MECHANICS
from weiren_game.data.lang import TEXT


# =========================================================== 羁绊（性格）
# 基础效果（只要拥有该性格即生效）。
PERSONALITY_BASE = {
    "cheerful": TEXT["data.codex_pack.PERSONALITY_BASE.cheerful"],
    "loner": TEXT["data.codex_pack.PERSONALITY_BASE.loner"],
    "keen": TEXT["data.codex_pack.PERSONALITY_BASE.keen"],
    "stubborn": TEXT["data.codex_pack.PERSONALITY_BASE.stubborn"],
    "steady": TEXT["data.codex_pack.PERSONALITY_BASE.steady"],
    "impatient": TEXT["data.codex_pack.PERSONALITY_BASE.impatient"],
    "gentle": TEXT["data.codex_pack.PERSONALITY_BASE.gentle"],
    "suspicious": TEXT["data.codex_pack.PERSONALITY_BASE.suspicious"],
}

# 特殊激活规则 / 取整规则。
PERSONALITY_REQUIREMENT = {
    "loner": TEXT["data.codex_pack.PERSONALITY_REQUIREMENT.loner"],
    "stubborn": TEXT["data.codex_pack.PERSONALITY_REQUIREMENT.stubborn"],
    "steady": TEXT["data.codex_pack.PERSONALITY_REQUIREMENT.steady"],
}

# 特殊档位（TIERS 为空时用于展示）。
PERSONALITY_TIER_HINTS = {
    "loner": (1, 5),
    "stubborn": (4, 7, 10),
}

# 每档效果（与设计稿逐档对应；主性格计数权重 1.5，副性格 1.0）。
PERSONALITY_TIER_TEXT = {
    "cheerful": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.cheerful.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.cheerful.1"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.cheerful.2"],
    ),
    "loner": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.loner.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.loner.1"],
    ),
    "keen": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.keen.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.keen.1"],
    ),
    "stubborn": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.stubborn.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.stubborn.1"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.stubborn.2"],
    ),
    "steady": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.steady.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.steady.1"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.steady.2"],
    ),
    "impatient": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.impatient.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.impatient.1"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.impatient.2"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.impatient.3"],
    ),
    "gentle": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.gentle.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.gentle.1"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.gentle.2"],
    ),
    "suspicious": (
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.suspicious.0"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.suspicious.1"],
        TEXT["data.codex_pack.PERSONALITY_TIER_TEXT.suspicious.2"],
    ),
}


# =========================================================== 伪人
PSEUDO_SKILLS = {
    "pseudo_benzene": (
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.0.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.0.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.1.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.1.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.2.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.2.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.3.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.3.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.4.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_benzene.4.1"]),
    ),
    "pseudo_onion": (
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.0.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.0.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.1.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.1.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.2.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.2.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.3.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.3.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.4.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.4.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.5.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.5.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.6.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_onion.6.1"]),
    ),
    "pseudo_fries": (
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.0.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.0.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.1.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.1.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.2.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.2.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.3.0"],
         TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.3.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.4.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.4.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.5.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.5.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.6.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.6.1"]),
        (TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.7.0"], TEXT["data.codex_pack.PSEUDO_SKILLS.pseudo_fries.7.1"]),
    ),
}
# =========================================================== 地点展示
# 每个地点的图标（更丰富、体现规模与类型差异）。
LOCATION_ICONS = {
    "county_hospital": "i-loc-med-big",
    "community_hospital": "i-loc-med-small",
    "pharmacy": "i-loc-pharmacy",
    "private_clinic": "i-loc-med-small",
    "bloodmobile": "i-loc-blood",
    "hardware_store": "i-loc-hardware",
    "ranger_station": "i-loc-tree",
    "police_station": "i-loc-shield",
    "gas_station": "i-loc-fuel",
    "swan_flagship": "i-loc-flagship",
    "convenience_store": "i-loc-store",
    "grocery": "i-loc-store",
    "food_cart": "i-loc-cart",
    "farmers_market": "i-loc-cart",
    "chinese_fast_food": "i-loc-food",
    "supermarket": "i-loc-crate",
    "night_market": "i-loc-lantern",
    "ordinary_home": "i-loc-house",
    "boarding_school": "i-loc-school",
    "corner_store": "i-loc-scales",
    "pawnshop": "i-loc-scales",
    "courier_station": "i-loc-package",
    "coach_station": "i-loc-bus",
    "community_center": "i-loc-people",
    "library": "i-loc-book",
}

# 设计稿中的完整描述（覆盖代码内的简版）。
LOCATION_TEXT = {
    "community_hospital": TEXT["data.codex_pack.LOCATION_TEXT.community_hospital"],
    "pharmacy": TEXT["data.codex_pack.LOCATION_TEXT.pharmacy"],
    "private_clinic": TEXT["data.codex_pack.LOCATION_TEXT.private_clinic"],
    "bloodmobile": TEXT["data.codex_pack.LOCATION_TEXT.bloodmobile"],
    "county_hospital": TEXT["data.codex_pack.LOCATION_TEXT.county_hospital"],
    "hardware_store": TEXT["data.codex_pack.LOCATION_TEXT.hardware_store"],
    "ranger_station": TEXT["data.codex_pack.LOCATION_TEXT.ranger_station"],
    "police_station": TEXT["data.codex_pack.LOCATION_TEXT.police_station"],
    "gas_station": TEXT["data.codex_pack.LOCATION_TEXT.gas_station"],
    "swan_flagship": TEXT["data.codex_pack.LOCATION_TEXT.swan_flagship"],
    "convenience_store": TEXT["data.codex_pack.LOCATION_TEXT.convenience_store"],
    "food_cart": TEXT["data.codex_pack.LOCATION_TEXT.food_cart"],
    "chinese_fast_food": TEXT["data.codex_pack.LOCATION_TEXT.chinese_fast_food"],
    "grocery": TEXT["data.codex_pack.LOCATION_TEXT.grocery"],
    "farmers_market": TEXT["data.codex_pack.LOCATION_TEXT.farmers_market"],
    "supermarket": TEXT["data.codex_pack.LOCATION_TEXT.supermarket"],
    "night_market": TEXT["data.codex_pack.LOCATION_TEXT.night_market"],
    "ordinary_home": TEXT["data.codex_pack.LOCATION_TEXT.ordinary_home"],
    "boarding_school": TEXT["data.codex_pack.LOCATION_TEXT.boarding_school"],
    "corner_store": TEXT["data.codex_pack.LOCATION_TEXT.corner_store"],
    "courier_station": TEXT["data.codex_pack.LOCATION_TEXT.courier_station"],
    "coach_station": TEXT["data.codex_pack.LOCATION_TEXT.coach_station"],
    "community_center": TEXT["data.codex_pack.LOCATION_TEXT.community_center"],
    "library": TEXT["data.codex_pack.LOCATION_TEXT.library"],
    "pawnshop": TEXT["data.codex_pack.LOCATION_TEXT.pawnshop"],
}




# =========================================================== 注册表
EXTRA_SECTIONS: list = []


def register_section(section: dict) -> None:
    """登记一个额外图鉴分节（DLC 的 codex/ 目录用）。"""
    if section and section not in EXTRA_SECTIONS:
        EXTRA_SECTIONS.append(section)


def reset_sections() -> None:
    """清空额外分节（内容热切换时回滚用）。"""
    EXTRA_SECTIONS.clear()


# =========================================================== 物品关联
def build_item_links(items: dict, personality_labels: dict, characters: dict, pseudos: dict) -> dict:
    """扫描物品文本，生成 物品 → 羁绊/角色/伪人 的关联（无需逐条维护）。"""
    char_names = {cid: c.name for cid, c in characters.items()}
    pseudo_names = {}
    for pid, p in pseudos.items():
        names = {p.name}
        human = characters.get(getattr(p, "human_character_id", ""))
        if human is not None:
            names.add(human.name)
        pseudo_names[pid] = names

    links: dict = {}
    for iid, item in items.items():
        blob = f"{item.name} {item.description}"
        entry = {"bonds": [], "characters": [], "pseudos": []}
        for key, label in personality_labels.items():
            if label and label in blob:
                entry["bonds"].append(key)
        for cid, name in char_names.items():
            if name and name in blob:
                entry["characters"].append(cid)
        for pid, names in pseudo_names.items():
            if any(name and name in blob for name in names):
                entry["pseudos"].append(pid)
        if any(entry.values()):
            links[iid] = entry
    return links

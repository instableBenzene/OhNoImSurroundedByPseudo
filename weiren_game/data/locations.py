"""搜索地点静态图鉴。"""

from .types import L, LocationDefinition
from weiren_game.data.lang import TEXT

ANY = ((), 5.0)
LOCATIONS = {
    "community_hospital": L("community_hospital", TEXT["location.community_hospital.name"], TEXT["location.community_hospital.description"], "medical", ((('medical_supply',), 95), ANY), quality_modifiers=(("low", 1.5),), tier=1),
    "pharmacy": L("pharmacy", TEXT["location.pharmacy.name"], TEXT["location.pharmacy.description"], "medical", ((('medical_supply',), 95), ANY), item_tag_modifiers=(("medicine_kit", 2.5),), tier=2),
    "private_clinic": L("private_clinic", TEXT["location.private_clinic.name"], TEXT["location.private_clinic.description"], "medical", ((('medical_supply',), 95), ANY), turn_delta=1, quality_modifiers=(("high", 2.0),), tier=3),
    "bloodmobile": L("bloodmobile", TEXT["location.bloodmobile.name"], TEXT["location.bloodmobile.description"], "medical", ((('medical_supply',), 75), (('food',), 25)), turn_delta=-3, behavior_delta=-3, quality_modifiers=(("low", 2.0),), tier=1),
    "county_hospital": L("county_hospital", TEXT["location.county_hospital.name"], TEXT["location.county_hospital.description"], "medical", ((('medical_supply',), 85), ((), 15)), turn_delta=2, behavior_delta=2, encounter_bonus=.15, quality_modifiers=(("high", 3.0),), fixed=True, tier=3),
    "hardware_store": L("hardware_store", TEXT["location.hardware_store.name"], TEXT["location.hardware_store.description"], "tool", ((('tool',), 90), ((), 10)), item_tag_modifiers=(("fragile", 2.5),), tier=2),
    "ranger_station": L("ranger_station", TEXT["location.ranger_station.name"], TEXT["location.ranger_station.description"], "tool", ((('tool',), 60), (('food',), 35), ((), 5)), turn_delta=-1, quality_modifiers=(("low", 2.0),), item_tag_modifiers=(("armor", 2.0),), tier=1),
    "police_station": L("police_station", TEXT["location.police_station.name"], TEXT["location.police_station.description"], "tool", ((('armor',), 35), (('tool',), 35), (('information_carrier',), 25), ((), 5)), encounter_bonus=-.10, quality_modifiers=(("high", 2.5),), tier=3),
    "gas_station": L("gas_station", TEXT["location.gas_station.name"], TEXT["location.gas_station.description"], "mixed", ((('tool',), 50), (('food',), 45), ((), 5)), turn_delta=-1, behavior_delta=-1, quality_modifiers=(("blue_plus", 1.5),), tier=2),
    "swan_flagship": L("swan_flagship", TEXT["location.swan_flagship.name"], TEXT["location.swan_flagship.description"], "tool", ((('tool',), 95), ((), 5)), turn_delta=2, behavior_delta=2, quality_modifiers=(("blue_plus", 3.0),), tier=3),
    "convenience_store": L("convenience_store", TEXT["location.convenience_store.name"], TEXT["location.convenience_store.description"], "food", ((('food',), 60), ((), 40)), turn_delta=-1, item_tag_modifiers=(("snack", 3.0),), fixed=True, tier=1),
    "food_cart": L("food_cart", TEXT["location.food_cart.name"], TEXT["location.food_cart.description"], "food", ((('food',), 95), ((), 5)), turn_delta=-3, behavior_delta=-3, quality_modifiers=(("low", 3.0),), tier=1),
    "chinese_fast_food": L("chinese_fast_food", TEXT["location.chinese_fast_food.name"], TEXT["location.chinese_fast_food.description"], "food", ((('food',), 95), ((), 5)), turn_delta=-1, quality_modifiers=(("blue", 2.0),), tier=2),
    "grocery": L("grocery", TEXT["location.grocery.name"], TEXT["location.grocery.description"], "food", ((('food',), 90), ((), 10)), tier=2),
    "farmers_market": L("farmers_market", TEXT["location.farmers_market.name"], TEXT["location.farmers_market.description"], "food", ((('food',), 80), (('information_carrier',), 15), ((), 5)), turn_delta=1, behavior_delta=1, tier=2),
    "supermarket": L("supermarket", TEXT["location.supermarket.name"], TEXT["location.supermarket.description"], "tool", ((('food',), 55), (('tool',), 40), ((), 5)), turn_delta=2, behavior_delta=2, fixed=True, tier=3),
    "night_market": L("night_market", TEXT["location.night_market.name"], TEXT["location.night_market.description"], "mixed", ((('food',), 75), (('tool',), 20), ((), 5)), turn_delta=1, behavior_delta=1, encounter_bonus=.10, item_tag_modifiers=(("snack", 2.5),), tier=2),
    "ordinary_home": L("ordinary_home", TEXT["location.ordinary_home.name"], TEXT["location.ordinary_home.description"], "mixed", ((('food',), 45), (('tool',), 45), ((), 10)), turn_delta=1, quality_modifiers=(("high", 1.5),), tier=2),
    "boarding_school": L("boarding_school", TEXT["location.boarding_school.name"], TEXT["location.boarding_school.description"], "mixed", ((('information_carrier',), 45), (('food',), 45), (('tool',), 10)), turn_delta=2, behavior_delta=2, quality_modifiers=(("high", 2.0),), tier=3),
    "corner_store": L("corner_store", TEXT["location.corner_store.name"], TEXT["location.corner_store.description"], "mixed", ((('food',), 65), (('tool',), 30), ((), 5)), quality_modifiers=(("low", 2.0),), tier=1),
    "courier_station": L("courier_station", TEXT["location.courier_station.name"], TEXT["location.courier_station.description"], "mixed", ((('food',), 40), (('tool',), 40), ((), 20)), turn_delta=3, behavior_delta=3, item_tag_modifiers=(("fragile", 3.0),), fixed=True, tier=3),
    "coach_station": L("coach_station", TEXT["location.coach_station.name"], TEXT["location.coach_station.description"], "mixed", ((('tool',), 40), (('food',), 40), (('information_carrier',), 20)), turn_delta=2, quality_modifiers=(("gold_plus", 2.0),), tier=3),
    "community_center": L("community_center", TEXT["location.community_center.name"], TEXT["location.community_center.description"], "mixed", ((('information_carrier',), 80), (('food',), 15), ((), 5)), turn_delta=1, behavior_delta=-1, quality_modifiers=(("low", 2.0),), tier=1),
    "library": L("library", TEXT["location.library.name"], TEXT["location.library.description"], "mixed", ((('information_carrier',), 95), ((), 5)), item_tag_modifiers=(("book", 3.0),), tier=2),
    "pawnshop": L("pawnshop", TEXT["location.pawnshop.name"], TEXT["location.pawnshop.description"], "mixed", ((('tool',), 55), (('information_carrier',), 40), ((), 5)), turn_delta=1, quality_modifiers=(("low", 2.0), ("red", 6.0)), item_tag_modifiers=(("craft", 3.0),), tier=3),
}
LOCATION_GROUPS = {
    group: tuple(key for key, value in LOCATIONS.items() if value.group == group)
    for group in {value.group for value in LOCATIONS.values()}
}

# 城郊小镇（内置区域包）：fixed=True 的地点必定出现在本局。
FIXED_LOCATIONS = tuple(key for key, value in LOCATIONS.items() if value.fixed)

# 内置区域包：城郊小镇（suburban_town）的生成配置。
# 基础组：每组必抽一个代表地点；其余空位按 MAP_DRAW_WEIGHTS 加权抽取。
# 用 list（可变）：内容/DLC 可追加分组，且对既有模块级绑定可见。
BASE_MAP_GROUPS: list[str] = ["medical", "food", "tool"]
MAP_DRAW_WEIGHTS: list[tuple[str, int]] = [
    ("medical", 20), ("food", 20), ("tool", 20), ("mixed", 40),
]


def register_map_group(group: str, weight: int = 20, *, required: bool = False) -> None:
    """把一个地点分组纳入开局抽取（DLC 新分组用）。

    ``required=True`` 表示本组每局必抽一个代表（与基础组同等待遇）。
    顺序按调用先后追加，因此不影响内置内容既有种子的抽取序列。
    """
    if required and group not in BASE_MAP_GROUPS:
        BASE_MAP_GROUPS.append(group)
    if not any(existing == group for existing, _ in MAP_DRAW_WEIGHTS):
        MAP_DRAW_WEIGHTS.append((group, int(weight)))


def register_location(location: LocationDefinition, *, replace: bool = False) -> None:
    """登记一个搜索地点（group 取定义自带的分组）。

    ``replace=True`` 时覆盖同 id 旧地点，并把它从原先所属分组里摘掉（内容包优先级用）。
    """
    if location.id in LOCATIONS and not replace:
        raise ValueError(TEXT["data.locations.register_location.1"].format(p1=location.id))
    if replace and location.id in LOCATIONS:
        old_group = LOCATIONS[location.id].group
        if old_group in LOCATION_GROUPS:
            LOCATION_GROUPS[old_group] = tuple(
                key for key in LOCATION_GROUPS[old_group] if key != location.id
            )
    LOCATIONS[location.id] = location
    if location.group not in LOCATION_GROUPS:
        LOCATION_GROUPS[location.group] = ()
    if location.id not in LOCATION_GROUPS[location.group]:
        LOCATION_GROUPS[location.group] += (location.id,)

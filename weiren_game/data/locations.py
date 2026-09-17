"""搜索地点静态图鉴。"""

from .types import L, LocationDefinition

ANY = ((), 5.0)
LOCATIONS = {
    "community_hospital": L("community_hospital", "街道社区医院", "基层医疗点，能轻松获取普适药物。", "medical", ((('medical_supply',), 95), ANY), quality_modifiers=(("low", 1.5),), tier=1),
    "pharmacy": L("pharmacy", "民营药房", "彻夜亮灯的非处方药房。", "medical", ((('medical_supply',), 95), ANY), item_tag_modifiers=(("medicine_kit", 2.5),), tier=2),
    "private_clinic": L("private_clinic", "私人诊所", "隐藏在商铺二楼的预约制诊所。", "medical", ((('medical_supply',), 95), ANY), turn_delta=1, quality_modifiers=(("high", 2.0),), tier=3),
    "bloodmobile": L("bloodmobile", "无偿献血车", "医疗与体力补给并存，但空间极其狭小。", "medical", ((('medical_supply',), 75), (('food',), 25)), turn_delta=-3, behavior_delta=-3, quality_modifiers=(("low", 2.0),), tier=1),
    "county_hospital": L("county_hospital", "县级综合医院", "庞大复杂的医疗枢纽，高级医疗物资汇聚地。", "medical", ((('medical_supply',), 85), ((), 15)), turn_delta=2, behavior_delta=2, encounter_bonus=.15, quality_modifiers=(("high", 3.0),), fixed=True, tier=3),
    "hardware_store": L("hardware_store", "民营五金店", "堆满日常消耗工具的街角老店。", "tool", ((('tool',), 90), ((), 10)), item_tag_modifiers=(("fragile", 2.5),), tier=2),
    "ranger_station": L("ranger_station", "护林员值班室", "位于郊区边缘林场的安静办公点。", "tool", ((('tool',), 60), (('food',), 35), ((), 5)), turn_delta=-1, quality_modifiers=(("low", 2.0),), item_tag_modifiers=(("armor", 2.0),), tier=1),
    "police_station": L("police_station", "乡镇派出所", "存放特殊防卫器具的高安保地点。", "tool", ((('armor',), 35), (('tool',), 35), (('information_carrier',), 25), ((), 5)), encounter_bonus=-.10, quality_modifiers=(("high", 2.5),), tier=3),
    "gas_station": L("gas_station", "加油站", "公路干线上的混杂补给枢纽。", "mixed", ((('tool',), 50), (('food',), 45), ((), 5)), turn_delta=-1, behavior_delta=-1, quality_modifiers=(("blue_plus", 1.5),), tier=2),
    "swan_flagship": L("swan_flagship", "斯旺浦旗舰店", "宽敞明亮的品牌直营店，产出顶配防具。", "tool", ((('tool',), 95), ((), 5)), turn_delta=2, behavior_delta=2, quality_modifiers=(("blue_plus", 3.0),), tier=3),
    "convenience_store": L("convenience_store", "便利店", "无论何时都亮着灯的日常补给站。", "food", ((('food',), 60), ((), 40)), turn_delta=-1, item_tag_modifiers=(("snack", 3.0),), fixed=True, tier=1),
    "food_cart": L("food_cart", "路边摊餐车", "街边随手可得、拿了就走的快捷补给。", "food", ((('food',), 95), ((), 5)), turn_delta=-3, behavior_delta=-3, quality_modifiers=(("low", 3.0),), tier=1),
    "chinese_fast_food": L("chinese_fast_food", "中式快餐店", "高效管饱，能快速恢复大量生命。", "food", ((('food',), 95), ((), 5)), turn_delta=-1, quality_modifiers=(("blue", 2.0),), tier=2),
    "grocery": L("grocery", "民营副食店", "陈旧的食品铺，存放调料与速食品。", "food", ((('food',), 90), ((), 10)), tier=2),
    "farmers_market": L("farmers_market", "郊区农贸市场", "面积庞大、气味复杂的市井市场。", "food", ((('food',), 80), (('information_carrier',), 15), ((), 5)), turn_delta=1, behavior_delta=1, tier=2),
    "supermarket": L("supermarket", "大型工农商超市", "极度消耗精力的物资海洋。", "tool", ((('food',), 55), (('tool',), 40), ((), 5)), turn_delta=2, behavior_delta=2, fixed=True, tier=3),
    "night_market": L("night_market", "夜市广场", "食物丰富但危机四伏的夜间广场。", "mixed", ((('food',), 75), (('tool',), 20), ((), 5)), turn_delta=1, behavior_delta=1, encounter_bonus=.10, item_tag_modifiers=(("snack", 2.5),), tier=2),
    "ordinary_home": L("ordinary_home", "普通民宅", "附近邻居家，几乎没有危险。", "mixed", ((('food',), 45), (('tool',), 45), ((), 10)), turn_delta=1, quality_modifiers=(("high", 1.5),), tier=2),
    "boarding_school": L("boarding_school", "寄宿制中学", "规矩森严但生机勃勃的学校。", "mixed", ((('information_carrier',), 45), (('food',), 45), (('tool',), 10)), turn_delta=2, behavior_delta=2, quality_modifiers=(("high", 2.0),), tier=3),
    "corner_store": L("corner_store", "街边杂货店", "充满生活气息的基础生活用品小铺。", "mixed", ((('food',), 65), (('tool',), 30), ((), 5)), quality_modifiers=(("low", 2.0),), tier=1),
    "courier_station": L("courier_station", "县快递驿站", "堆积如山的包裹构成盲盒物资。", "mixed", ((('food',), 40), (('tool',), 40), ((), 20)), turn_delta=3, behavior_delta=3, item_tag_modifiers=(("fragile", 3.0),), fixed=True, tier=3),
    "coach_station": L("coach_station", "长途客运汽车站", "信息和高级物资的集散地，极度危险。", "mixed", ((('tool',), 40), (('food',), 40), (('information_carrier',), 20)), turn_delta=2, quality_modifiers=(("gold_plus", 2.0),), tier=3),
    "community_center": L("community_center", "社区活动中心", "小镇居民的情报网中心。", "mixed", ((('information_carrier',), 80), (('food',), 15), ((), 5)), turn_delta=1, behavior_delta=-1, quality_modifiers=(("low", 2.0),), tier=1),
    "library": L("library", "公共图书馆", "获取知识与被动能力道具的稳定去处。", "mixed", ((('information_carrier',), 95), ((), 5)), item_tag_modifiers=(("book", 3.0),), tier=2),
    "pawnshop": L("pawnshop", "街角旧货典当铺", "藏着稀有工艺品与不可靠流言的旧货店。", "mixed", ((('tool',), 55), (('information_carrier',), 40), ((), 5)), turn_delta=1, quality_modifiers=(("low", 2.0), ("red", 6.0)), item_tag_modifiers=(("craft", 3.0),), tier=3),
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
        raise ValueError(f"地点 ID 重复：{location.id}")
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

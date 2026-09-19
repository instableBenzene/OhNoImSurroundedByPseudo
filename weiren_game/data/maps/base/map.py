"""默认地图：城郊小镇（屋子叫「城郊小屋」）。

``locations`` 是**显式名单**：本图包含全部内置搜索地点。
DLC 想把自己的地点加进城郊小镇，可以在 ``register(ctx)`` 里调
``ctx.register_map_location("base", "<地点id>")``，或者自带一张地图。
"""

from weiren_game.data.types import MapDefinition
from weiren_game.data.lang import TEXT

MAP = MapDefinition(
    "base",
    TEXT["map.base.name"],
    TEXT["map.base.shelter"],
    locations=(
        "community_hospital",
        "pharmacy",
        "private_clinic",
        "bloodmobile",
        "county_hospital",
        "hardware_store",
        "ranger_station",
        "police_station",
        "gas_station",
        "swan_flagship",
        "convenience_store",
        "food_cart",
        "chinese_fast_food",
        "grocery",
        "farmers_market",
        "supermarket",
        "night_market",
        "ordinary_home",
        "boarding_school",
        "corner_store",
        "courier_station",
        "coach_station",
        "community_center",
        "library",
        "pawnshop",
    ),
    draw_count=10,
    description=TEXT["data.maps.base.map.module.1"],
)

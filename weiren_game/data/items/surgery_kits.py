"""大类：创伤手术包（六档，医疗）。"""

from ..types import I

ITEMS = {
    "home_first_aid": I("home_first_aid", "家用急救包", "medical", 0, "治疗≤3级创伤：-1/-2。", ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=10, use_cost=3, medical_target="trauma", medical_max_intensity=3, reduce_intensity=1, reduce_layers=2),
    "suture_kit": I("suture_kit", "清创缝合手术包", "medical", 1, "治疗≤3级创伤：-2/-2。", ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=20, use_cost=4, medical_target="trauma", medical_max_intensity=3, reduce_intensity=2, reduce_layers=2),
    "field_surgery": I("field_surgery", "野外紧急用手术包", "medical", 2, "治疗≤6级创伤：-2/-3。", ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=30, use_cost=5, medical_target="trauma", medical_max_intensity=6, reduce_intensity=2, reduce_layers=3),
    "complex_surgery": I("complex_surgery", "复杂器械手术包", "medical", 3, "治疗≤6级创伤：-4/-3。", ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=50, use_cost=7, medical_target="trauma", medical_max_intensity=6, reduce_intensity=4, reduce_layers=3),
    "precision_surgery": I("precision_surgery", "精密器械手术包", "medical", 4, "治疗≤9级创伤：-4/-4。", ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=70, use_cost=8, medical_target="trauma", medical_max_intensity=9, reduce_intensity=4, reduce_layers=4),
    "nebula_surgery": I("nebula_surgery", "星云手术包", "medical", 5, "治疗≤10级创伤：-6/-5。", ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=100, use_cost=10, medical_target="trauma", medical_max_intensity=10, reduce_intensity=6, reduce_layers=5, source_note="汇总表误写为星尘手术包；采用正文名称。"),
}

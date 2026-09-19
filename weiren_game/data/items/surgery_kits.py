"""大类：创伤手术包（六档，医疗）。"""

from ..types import I
from weiren_game.data.lang import TEXT

ITEMS = {
    "home_first_aid": I("home_first_aid", TEXT["item.home_first_aid.name"], "medical", 0, TEXT["item.home_first_aid.description"], ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=10, use_cost=3, medical_target="trauma", medical_max_intensity=3, reduce_intensity=1, reduce_layers=2),
    "suture_kit": I("suture_kit", TEXT["item.suture_kit.name"], "medical", 1, TEXT["item.suture_kit.description"], ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=20, use_cost=4, medical_target="trauma", medical_max_intensity=3, reduce_intensity=2, reduce_layers=2),
    "field_surgery": I("field_surgery", TEXT["item.field_surgery.name"], "medical", 2, TEXT["item.field_surgery.description"], ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=30, use_cost=5, medical_target="trauma", medical_max_intensity=6, reduce_intensity=2, reduce_layers=3),
    "complex_surgery": I("complex_surgery", TEXT["item.complex_surgery.name"], "medical", 3, TEXT["item.complex_surgery.description"], ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=50, use_cost=7, medical_target="trauma", medical_max_intensity=6, reduce_intensity=4, reduce_layers=3),
    "precision_surgery": I("precision_surgery", TEXT["item.precision_surgery.name"], "medical", 4, TEXT["item.precision_surgery.description"], ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=70, use_cost=8, medical_target="trauma", medical_max_intensity=9, reduce_intensity=4, reduce_layers=4),
    "nebula_surgery": I("nebula_surgery", TEXT["item.nebula_surgery.name"], "medical", 5, TEXT["item.nebula_surgery.description"], ("medical_supply", "surgery_kit", "durability_consumable"), max_durability=100, use_cost=10, medical_target="trauma", medical_max_intensity=10, reduce_intensity=6, reduce_layers=5, source_note=TEXT["data.items.surgery_kits.module.1"]),
}

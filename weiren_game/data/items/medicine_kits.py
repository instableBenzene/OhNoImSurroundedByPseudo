"""大类：紊乱药箱（六档，医疗）。"""

from ..types import I
from weiren_game.data.lang import TEXT

ITEMS = {
    "portable_medicine": I("portable_medicine", TEXT["item.portable_medicine.name"], "medical", 0, TEXT["item.portable_medicine.description"], ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=10, use_cost=3, medical_target="disorder", medical_max_intensity=3, reduce_intensity=1, reduce_layers=2),
    "home_medicine": I("home_medicine", TEXT["item.home_medicine.name"], "medical", 1, TEXT["item.home_medicine.description"], ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=20, use_cost=4, medical_target="disorder", medical_max_intensity=3, reduce_intensity=2, reduce_layers=2),
    "field_medicine": I("field_medicine", TEXT["item.field_medicine.name"], "medical", 2, TEXT["item.field_medicine.description"], ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=30, use_cost=5, medical_target="disorder", medical_max_intensity=6, reduce_intensity=2, reduce_layers=3),
    "emergency_medicine": I("emergency_medicine", TEXT["item.emergency_medicine.name"], "medical", 3, TEXT["item.emergency_medicine.description"], ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=50, use_cost=7, medical_target="disorder", medical_max_intensity=6, reduce_intensity=4, reduce_layers=3),
    "meteor_plan": I("meteor_plan", TEXT["item.meteor_plan.name"], "medical", 4, TEXT["item.meteor_plan.description"], ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=70, use_cost=8, medical_target="disorder", medical_max_intensity=9, reduce_intensity=4, reduce_layers=4),
    "rescue_cart": I("rescue_cart", TEXT["item.rescue_cart.name"], "medical", 5, TEXT["item.rescue_cart.description"], ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=100, use_cost=10, medical_target="disorder", medical_max_intensity=10, reduce_intensity=6, reduce_layers=5),
}

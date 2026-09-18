"""大类：紊乱药箱（六档，医疗）。"""

from ..types import I

ITEMS = {
    "portable_medicine": I("portable_medicine", "便携药盒", "medical", 0, "治疗≤3级紊乱：-1/-2。", ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=10, use_cost=3, medical_target="disorder", medical_max_intensity=3, reduce_intensity=1, reduce_layers=2),
    "home_medicine": I("home_medicine", "家用药箱", "medical", 1, "治疗≤3级紊乱：-2/-2。", ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=20, use_cost=4, medical_target="disorder", medical_max_intensity=3, reduce_intensity=2, reduce_layers=2),
    "field_medicine": I("field_medicine", "野外用药系列组合", "medical", 2, "治疗≤6级紊乱：-2/-3。", ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=30, use_cost=5, medical_target="disorder", medical_max_intensity=6, reduce_intensity=2, reduce_layers=3),
    "emergency_medicine": I("emergency_medicine", "急救药箱", "medical", 3, "治疗≤6级紊乱：-4/-3。", ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=50, use_cost=7, medical_target="disorder", medical_max_intensity=6, reduce_intensity=4, reduce_layers=3),
    "meteor_plan": I("meteor_plan", "「星殒急救方案」", "medical", 4, "治疗≤9级紊乱：-4/-4。", ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=70, use_cost=8, medical_target="disorder", medical_max_intensity=9, reduce_intensity=4, reduce_layers=4),
    "rescue_cart": I("rescue_cart", "抢救车", "medical", 5, "治疗≤10级紊乱：-6/-5。", ("medical_supply", "medicine_kit", "durability_consumable"), max_durability=100, use_cost=10, medical_target="disorder", medical_max_intensity=10, reduce_intensity=6, reduce_layers=5),
}

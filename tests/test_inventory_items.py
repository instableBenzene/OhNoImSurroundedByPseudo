"""背包/仓库槽位、堆叠、使用与医疗公式。

合并自原 inventory_plot / inventory_slots / stacking / medical_tags 及物品相关用例。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from weiren_game.engine import GameEngine
from weiren_game.exceptions import RuleViolation
from weiren_game.data import ITEMS
from weiren_game.items import ItemInstance
from weiren_game.models import Condition


def action_engine(seed: str, difficulty: str = "a0") -> GameEngine:
    engine = GameEngine.new_game(
        seed=seed, difficulty=difficulty, max_turns=20, pseudo_id="pseudo_benzene",
    )
    engine.state.flow.turn = 1
    engine.state.flow.phase = "action"
    engine.state.house.tenants.clear()
    engine.state.world.visitors.visitor_pool.clear()
    engine.state.world.events.door_events.clear()
    engine.state.house.information.clear()
    engine.state.house.inventory.items.clear()
    return engine


class InventoryTests(unittest.TestCase):
    def test_stacking_merge_consume_and_obtain_range(self) -> None:
        engine = action_engine("stacking")
        engine._gain_item("simple_food", 20)          # stack_size = 16
        counts = sorted(v.count for v in engine.state.house.inventory if v.item_id == "simple_food")
        self.assertEqual(counts, [4, 16])
        engine._gain_item("suture_kit", 3)            # 耐久品永不合并
        self.assertEqual(len([v for v in engine.state.house.inventory if v.item_id == "suture_kit"]), 3)
        engine.state.house.inventory.consume("simple_food", 5)
        self.assertEqual(engine.state.house.inventory.count("simple_food"), 15)
        original = ITEMS["simple_food"]
        try:
            ITEMS["simple_food"] = replace(original, obtain_range=(5, 5))
            for index in range(3):
                engine._gain_loot_item("simple_food", "test.range", index)
            self.assertEqual(engine.state.house.inventory.count("simple_food"), 30)
        finally:
            ITEMS["simple_food"] = original

    def test_slots_move_equip_unequip_transfer(self) -> None:
        engine = action_engine("slots")
        first = engine._add_tenant("hkw")
        second = engine._add_tenant("bigstar")
        engine._gain_item("flashlight")
        engine.move_item(container="warehouse", from_slot=0, to_slot=10)
        self.assertIsNotNone(engine.state.house.inventory.at_plot(10))
        engine.equip_item(first.id, "flashlight", target_slot=3)
        self.assertIsNotNone(first.inventory.at_plot(3))
        engine.transfer_item(first.id, second.id, "flashlight", slot=3, target_slot=1)
        self.assertIsNone(first.inventory.at_plot(3))
        self.assertIsNotNone(second.inventory.at_plot(1))
        engine.unequip_item(second.id, "flashlight", slot=1, target_slot=8)
        self.assertIsNotNone(engine.state.house.inventory.at_plot(8))

    def test_use_exact_slot_bag_and_warehouse(self) -> None:
        engine = action_engine("use-from-bag")
        tenant = engine._add_tenant("hkw")
        engine._gain_item("simple_food", 3)
        engine.equip_item(tenant.id, "simple_food", target_slot=2)
        engine.use_item("simple_food", tenant.id, source_tenant=tenant.id, slot=2)
        self.assertEqual(tenant.inventory.at_plot(2).count, 2)   # 用后留在原格
        engine._gain_item("water")
        engine.equip_item(tenant.id, "water", target_slot=1)
        engine.use_item("water", tenant.id, source_tenant=tenant.id, slot=1)
        self.assertIsNone(tenant.inventory.at_plot(1))            # 消耗品用掉即消失
        engine._gain_item("pancake")
        engine.equip_item(tenant.id, "pancake", target_slot=1)
        engine._gain_item("pancake")
        engine.equip_item(tenant.id, "pancake", target_slot=3)
        untouched, used = tenant.inventory.at_plot(1), tenant.inventory.at_plot(3)
        engine.use_item("pancake", tenant.id, source_tenant=tenant.id, slot=3)
        self.assertLess(used.durability, untouched.durability)    # 精确扣被拖那格

        # 仓库同理：不带 slot 取最靠前，带 slot 时精确扣玩家点的那一件。
        engine.state.house.inventory.items.clear()
        engine.state.house.inventory.add(ItemInstance("W1", "pancake", durability=10), plot=0)
        engine.state.house.inventory.add(ItemInstance("W2", "pancake", durability=10), plot=8)
        front, chosen = engine.state.house.inventory.at_plot(0), engine.state.house.inventory.at_plot(8)
        engine.use_item("pancake", tenant.id, slot=8)
        self.assertEqual(front.durability, 10)
        self.assertLess(chosen.durability, 10)

    def test_capacity_overflow_and_range_guard(self) -> None:
        engine = action_engine("capacity")
        tenant = engine._add_tenant("tear")
        base = engine._search_carry(tenant)
        engine._gain_item("walmart_bag")
        engine.equip_item(tenant.id, "walmart_bag")
        capacity = engine.tenant_carry_capacity(tenant)
        self.assertEqual(capacity, base + 5)
        for _ in range(capacity - 1):
            engine._gain_item("simple_food")
            engine.equip_item(tenant.id, "simple_food")
        before = engine.state.house.inventory.count("simple_food")
        engine.unequip_item(tenant.id, "walmart_bag")
        self.assertEqual(engine.tenant_carry_capacity(tenant), base)
        self.assertLess(len(tenant.inventory.items), capacity)
        self.assertGreater(engine.state.house.inventory.count("simple_food"), before)  # 溢出回仓库
        engine._gain_item("flashlight")
        with self.assertRaises(RuleViolation):
            engine.equip_item(tenant.id, "flashlight", target_slot=99)

    def test_medical_treatment_formula(self) -> None:
        engine = action_engine("medical")
        tenant = engine._add_tenant("hkw")
        engine._gain_item("home_first_aid")   # max_intensity=3, use_cost=3, 耐久 10
        tenant.trauma = Condition(2, 3)
        with patch.object(engine, "_rng", return_value=SimpleNamespace(random=lambda: 0.99)):
            engine.use_item("home_first_aid", tenant.id)
        self.assertEqual(tenant.trauma.intensity, 1)          # 范围内必中
        self.assertEqual(engine.state.house.inventory.earliest(
            lambda v: v.item_id == "home_first_aid").durability, 7)

        tenant.trauma = Condition(5, 3)                        # 越 2 级：成功率 2/(2+2)=50%
        with patch.object(engine, "_rng", return_value=SimpleNamespace(random=lambda: 0.2)):
            engine.use_item("home_first_aid", tenant.id)
        self.assertEqual(tenant.trauma.intensity, 4)
        self.assertEqual(engine.state.house.inventory.earliest(
            lambda v: v.item_id == "home_first_aid").durability, 2)  # 10 - 3 - ceil(3*1.25^2)

    def test_books_passives_and_group_count(self) -> None:
        engine = action_engine("books")
        tenant = engine._add_tenant("hkw")
        tenant.inventory.add(ItemInstance("B1", "bls_book", durability=25))
        for _ in range(4):
            engine._settle_held_items()
        self.assertFalse(tenant.has_ability("bls"))
        engine._settle_held_items()
        self.assertTrue(tenant.has_ability("bls"))            # 第 5 次结算习得


if __name__ == "__main__":
    unittest.main()

"""分层状态模型：Condition / Inventory / Tenant / GameState / 印记。

合并自原 strict_conditions / strict_tenant / strict_state / layered_state / marks。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest

from weiren_game.ability import AbilityState
from weiren_game.condition import Condition, EMOTION_DEFINITIONS, STATUS_DEFINITIONS
from weiren_game.data import GAME_VERSION
from weiren_game.engine import GameEngine
from weiren_game.items import Inventory, ItemInstance
from weiren_game.models import GameState
from weiren_game.pseudo import PseudoRuntime
from weiren_game.session import GameFlowState, InstancePool, SaveMetadata
from weiren_game.tenant import TenantState, status_caps
from weiren_game import data


class StateModelTests(unittest.TestCase):
    def test_condition_model(self) -> None:
        self.assertTrue(Condition(2, 3).active)
        self.assertFalse(Condition(3, 0).active)
        self.assertEqual(Condition(3, 0), Condition())          # 任一为 0 即归零
        self.assertEqual(Condition(50, 200), Condition(10, 99))  # 默认上限
        self.assertEqual(Condition.from_dict(Condition(4, 6).to_dict()), Condition(4, 6))
        with self.assertRaises(TypeError):
            Condition.from_dict({"intensity": 1, "layers": 1, "ghost": True})

    def test_emotion_and_status_registry(self) -> None:
        erosion = [k for k, v in EMOTION_DEFINITIONS.items() if v.kind == "erosion"]
        awakening = [k for k, v in EMOTION_DEFINITIONS.items() if v.kind == "awakening"]
        self.assertEqual((len(erosion), len(awakening)), (6, 6))
        self.assertTrue(EMOTION_DEFINITIONS["reason"].is_rare)
        self.assertFalse(EMOTION_DEFINITIONS["happiness"].is_rare)
        self.assertEqual(STATUS_DEFINITIONS["shock"].intensity_max, 4)
        self.assertEqual(status_caps("shock"), (4, 99))
        self.assertEqual(status_caps("no_such_status"), (10, 99))

    def test_inventory_model(self) -> None:
        bag = Inventory()
        bag.add(ItemInstance("i1", "chain_vest", durability=5))
        bag.add(ItemInstance("i2", "flashlight"))
        bag.add(ItemInstance("i3", "garlic", count=16))
        self.assertEqual([v.item_id for v in bag], ["chain_vest", "flashlight", "garlic"])
        self.assertEqual([v.plot for v in bag], [0, 1, 2])
        self.assertIs(bag.earliest(lambda v: v.item_id == "flashlight"), bag.instance("i2"))
        self.assertEqual(Inventory.from_dict(bag.to_dict()).to_dict(), bag.to_dict())
        with self.assertRaises(ValueError):
            ItemInstance("bad", "garlic", count=0)

    def test_tenant_model(self) -> None:
        with self.assertRaises(ValueError):
            TenantState(id="", character_id="x")
        tenant = TenantState(id="T1", character_id="dragon")
        tenant.set_status("shock", intensity=9, layers=2)
        self.assertEqual(tenant.conditions["shock"], Condition(4, 2))  # 按定义上限夹取
        tenant.set_status("irritation", intensity=0, layers=0)
        self.assertNotIn("irritation", tenant.conditions)
        tenant.abilities.append(AbilityState("call_friends"))
        self.assertTrue(tenant.has_ability("call_friends"))
        tenant.set_status("trauma", intensity=2, layers=7)
        discovered = TenantState.from_dict(tenant.to_dict())
        self.assertEqual(discovered, tenant)
        raw = tenant.to_dict()
        raw["ghost"] = True
        with self.assertRaises(TypeError):
            TenantState.from_dict(raw)

    def test_tenant_container_roundtrip(self) -> None:
        """角色专属容器（自定义 UI 的专属状态）：进存档→读回；没声明/坏数据一律丢弃。"""
        from dataclasses import dataclass, field

        from weiren_game.tenant import CONTAINER_TYPES, register_container_type

        @dataclass
        class ProbeBox:
            """测试用容器：一格东西 + 一个台阶计数。"""

            name: str = ""
            step: int = 0
            tags: list = field(default_factory=list)

            def to_dict(self) -> dict:
                return {"name": self.name, "step": self.step, "tags": list(self.tags)}

            @classmethod
            def from_dict(cls, raw: dict) -> "ProbeBox":
                return cls(
                    name=str(raw.get("name", "")),
                    step=int(raw.get("step", 0)),
                    tags=[str(x) for x in raw.get("tags", ())],
                )

        register_container_type("dragon", "probe_box", ProbeBox)
        try:
            tenant = TenantState(id="T1", character_id="dragon")
            tenant.containers["probe_box"] = ProbeBox("sweet_food", 2, ["食物"])
            raw = tenant.to_dict()
            self.assertEqual(TenantState.from_dict(raw), tenant)
            raw["containers"]["ghost_box"] = {"step": 1}      # 没声明过的 key → 丢弃
            self.assertEqual(TenantState.from_dict(raw).containers, tenant.containers)
            raw["containers"]["probe_box"] = "坏数据"          # 坏数据 → 丢弃，不炸
            self.assertEqual(TenantState.from_dict(raw).containers, {})
        finally:
            CONTAINER_TYPES.pop(("dragon", "probe_box"), None)

    def test_game_state_layers_and_pseudo_facade(self) -> None:
        state = GameState(
            meta=SaveMetadata(version=GAME_VERSION, seed="s", difficulty="a0"),
            flow=GameFlowState(turn=7, phase="action", game_over=True, victory=True),
            pseudo_state=PseudoRuntime(
                pseudo_instance_id=1, scenario_id="pseudo_onion", name="深潜者祭司-洋葱"
            ),
        )
        state.house.inventory.add(ItemInstance("H1", "garlic", count=3))
        state.world.visitors.next_pseudo_turn = 7
        state.pseudo_state.revealed = True
        state.pseudo_state.known = True
        state.pseudo_state.whisper_marks = 4
        raw = state.to_dict()
        restored = GameState.from_dict(raw)
        self.assertEqual(restored.to_dict(), raw)
        self.assertEqual(restored.pseudo_state.scenario().whisper_marks, 4)
        self.assertTrue(restored.pseudo_state.known)
        raw["ghost"] = True
        with self.assertRaises(ValueError):
            GameState.from_dict(raw)
        with self.assertRaises(ValueError):
            GameFlowState(phase="no-such-phase")
        pool = InstancePool()
        self.assertEqual((pool.allocate_tenant(), pool.allocate_item()), (1, 1))

    def test_marks_model(self) -> None:
        engine = GameEngine.new_game(seed="marks")
        engine.state.house.tenants.clear()
        star = engine._add_tenant("bigstar")
        first = engine._gain_mark(star, "star", 2.0)
        second = engine._gain_mark(star, "star", 3.0)
        self.assertLess(first.mark_instance_id, second.mark_instance_id)
        self.assertEqual(engine._consume_mark(star, "star", 3.0), 3.0)
        self.assertEqual(engine._mark_count(star, "star"), 2.0)  # 优先消耗最早实例
        ling = engine._add_tenant("zero329")
        engine._gain_mark(ling, "alert", 5)
        self.assertEqual(engine._mark_count(ling, "alert"), 3.0)  # 定义上限
        erebus = engine._add_tenant("erebus")
        before = [v.value for v in erebus.marks.instances_of("fate")]
        self.assertFalse(engine._set_mark_external(erebus, "fate", 5.0))  # 外部锁定
        self.assertEqual([v.value for v in erebus.marks.instances_of("fate")], before)


if __name__ == "__main__":
    unittest.main()

"""回合流程：门口规则、回溯/存档、完整对局、访客容量与日志。

合并自原 engine 主流程 / logs / global_events 用例。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import tempfile
import unittest
from pathlib import Path

from weiren_game.engine import GameEngine, RuleViolation
from weiren_game.models import Condition, DoorEvent


def clear_door(engine: GameEngine, accept: bool = False) -> None:
    while engine._pending_choice is not None:
        engine.choose_discover(engine._pending_choice["options"][0])
    while engine.state.world.events.door_events and not engine.state.flow.game_over:
        event = engine.state.world.events.door_events[0]
        if event.kind == "human":
            returning = bool(event.metadata.get("returning_tenant_id"))
            has_room = len(engine.living_tenants()) < 10
            engine.handle_next_door_event("accept" if accept and (returning or has_room) else "reject")
        else:
            engine.handle_next_door_event()


def bare_engine(seed: str) -> GameEngine:
    engine = GameEngine.new_game(seed, "a0")
    engine.state.house.tenants.clear()
    engine.state.world.visitors.visitor_pool.clear()
    engine.state.world.events.door_events.clear()
    engine.state.house.information.clear()
    engine.state.flow.turn = 1
    engine.state.flow.phase = "action"
    return engine


class RoundFlowTests(unittest.TestCase):
    def test_door_rule_and_global_events(self) -> None:
        engine = GameEngine.new_game("door-rule")
        engine.start_turn()
        self.assertTrue(engine.state.world.events.door_events)
        with self.assertRaisesRegex(RuleViolation, "门外仍有未处理事件"):
            engine.end_turn()

        events = bare_engine("global-events")
        events._set_global_event("test.evt", 3.0, 2)
        self.assertEqual(events._global_event_value("test.evt", 1.0), 3.0)
        events._decay_global_events()
        self.assertTrue(events._global_event_active("test.evt"))
        events._decay_global_events()
        self.assertFalse(events._global_event_active("test.evt"))
        events._set_global_event("test.once", 1.0, 5)
        events._consume_global_event("test.once")
        self.assertFalse(events._global_event_active("test.once"))

    def test_discover_is_atomic(self) -> None:
        engine = GameEngine.new_game("atomic")
        engine.state.house.tenants.clear()
        options = engine.discover(("a", "b", "c"), count=2)
        with self.assertRaises(RuleViolation):
            engine.start_turn()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuleViolation):
                engine.save(Path(folder) / "should-not-be-written.json")
        engine.choose_discover(options[0])
        engine.start_turn()

    def test_rewind_and_save_load(self) -> None:
        engine = GameEngine.new_game("rewind")
        before = engine.state.to_dict(include_history=False)
        engine.start_turn()
        clear_door(engine, accept=True)
        self.assertNotEqual(before, engine.state.to_dict(include_history=False))
        engine.rewind_one_turn()
        self.assertEqual(before, engine.state.to_dict(include_history=False))

        saved = GameEngine.new_game("save-roundtrip", "a1")
        saved.start_turn()
        clear_door(saved, accept=True)
        saved.state.house.tenants[saved.home_tenants()[0].id].trauma = Condition(2, 3)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            saved.save(path)
            loaded = GameEngine.load(path)
        self.assertEqual(
            saved.state.to_dict(include_history=False),
            loaded.state.to_dict(include_history=False),
        )
        self.assertEqual(saved.state.log.action_log, loaded.state.log.action_log)

    def test_full_playthrough_and_invariants(self) -> None:
        engine = GameEngine.new_game("full-playthrough", "a0", max_turns=12)
        safety = 0
        while not engine.state.flow.game_over and safety < 20:
            safety += 1
            engine.start_turn()
            clear_door(engine, accept=True)
            if not engine.state.flow.game_over:
                engine.end_turn()
            engine.assert_invariants()
        self.assertTrue(engine.state.flow.game_over)
        self.assertLessEqual(engine.state.flow.turn, 12)
        self.assertTrue(engine.state.flow.victory, engine.state.flow.ending)

    def test_visitor_capacity_and_rejection(self) -> None:
        engine = bare_engine("capacity")
        for _ in range(10):
            engine._add_tenant("hkw")
        engine.state.world.events.door_events.append(DoorEvent(
            "human", "访客", "容量测试", visitor_id="dragonboat",
        ))
        with self.assertRaisesRegex(RuleViolation, "最多容纳10名"):
            engine.handle_next_door_event("accept")

        rejected = bare_engine("double-reject")
        for attempt in range(2):
            if attempt and "dragonboat" in rejected.state.world.visitors.visitor_pool:
                rejected.state.world.visitors.visitor_pool.remove("dragonboat")
            rejected.state.world.events.door_events.append(DoorEvent(
                "human", "访客", "连续拒绝", visitor_id="dragonboat",
            ))
            rejected.handle_next_door_event("reject")
        self.assertEqual(rejected.state.world.visitors.visitor_rejections["dragonboat"], 2)
        self.assertNotIn("dragonboat", rejected.state.world.visitors.visitor_pool)

    def test_log_separation(self) -> None:
        engine = GameEngine.new_game(seed="logs")
        visible = "\n".join(engine.drain_messages())
        self.assertIn("天色已暗", visible)
        self.assertNotIn("本局伪人", visible)
        full = engine.full_log_text()
        self.assertIn("本局伪人", full)
        engine._log("公开消息", shown=True)
        engine._log("内部消息", shown=False)
        self.assertEqual(engine.drain_messages(), ["公开消息"])
        self.assertIn("内部消息", engine.full_log_text())
        for index in range(600):
            engine._record_action("stress", index=index)
        self.assertGreaterEqual(len(engine.state.log.action_log), 600)


if __name__ == "__main__":
    unittest.main()

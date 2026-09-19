"""难度档位、开局补给/属性、随机开局、访客日历与发现机制。"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest

from weiren_game.data import (
    DIFFICULTIES, DIFFICULTY_INFO, PSEUDOS, CHARACTERS,
)
from weiren_game.engine import GameEngine, RuleViolation


class DifficultyAndStartTests(unittest.TestCase):
    def test_new_levels_effects(self) -> None:
        self.assertEqual(DIFFICULTIES["a7"]["start_fortune_delta"], -3)
        self.assertEqual(DIFFICULTIES["a-7"]["start_fortune_delta"], 3)
        self.assertEqual(DIFFICULTIES["a8"]["start_vital_pct"], -0.20)
        self.assertEqual(DIFFICULTIES["a-8"]["start_vital_max_pct"], 0.20)
        self.assertEqual(DIFFICULTIES["a9"]["start_depression_delta"], 100.0)
        self.assertEqual(DIFFICULTIES["a-9"]["start_depression_delta"], -100.0)
        self.assertEqual(DIFFICULTIES["a10"]["start_condition_trauma_disorder"], 1)
        self.assertEqual(DIFFICULTIES["a-10"]["trauma_disorder_immunity"], 1)

        lowered = GameEngine.new_game(seed="diff-a8", difficulty="a8", max_turns=20)
        for tenant in lowered.home_tenants():
            self.assertAlmostEqual(tenant.health, 80.0)
            self.assertIn(round(tenant.sanity), (40, 80))
        raised = GameEngine.new_game(seed="diff-am8", difficulty="a-8", max_turns=20)
        for tenant in raised.home_tenants():
            self.assertAlmostEqual(tenant.max_health, 120.0)
            self.assertAlmostEqual(tenant.max_sanity, 120.0)
            self.assertAlmostEqual(tenant.health, 120.0)
        for key, expected in (("a9", 100.0), ("a-9", -100.0)):
            engine = GameEngine.new_game(seed="diff-" + key.replace("-", "m"), difficulty=key, max_turns=20)
            for tenant in engine.home_tenants():
                self.assertAlmostEqual(tenant.depression, expected)
        injured = GameEngine.new_game(seed="diff-a10", difficulty="a10", max_turns=20)
        for tenant in injured.home_tenants():
            self.assertEqual(int(tenant.trauma.active) + int(tenant.disorder.active), 1)
        immune = GameEngine.new_game(seed="diff-am10", difficulty="a-10", max_turns=20)
        target = immune.home_tenants()[0]
        self.assertEqual(target.condition("high_health_immunity").intensity, 99)
        self.assertFalse(immune._set_condition(target, target.trauma, 5, 5, "测试"))

    def test_start_loot_and_fortune(self) -> None:
        engine = GameEngine.new_game(seed="loot", difficulty="a0", max_turns=20)
        self.assertEqual(
            dict(engine._start_loot_schedule(0)),
            {"food": 2, "medical": 1, "tool": 1, "carrier": 1},
        )
        self.assertEqual(sum(c for _, c in engine._start_loot_schedule(1)), 6)
        self.assertEqual(sum(c for _, c in engine._start_loot_schedule(-1)), 4)
        for key, expected in (("a7", -4.0), ("a-7", 4.0)):
            game = GameEngine.new_game(seed="diff-fortune-" + key.replace("-", "m"), difficulty=key, max_turns=20)
            value = game._apply_modifiers("search", 0.0, ("setup", "luck"), {"tenant": None, "rng": None})
            self.assertEqual(value, expected)   # 全局 fortune_delta 与本池时运叠加
        leak = GameEngine.new_game(seed="diff-leak", difficulty="a7", max_turns=20)
        value = leak._apply_modifiers("search", 0.0, ("search", "luck", "hkw"), {"tenant": None, "rng": None})
        self.assertEqual(value, -1.0)           # 本池时运不漏进搜索

        def units(difficulty: str) -> int:
            game = GameEngine.new_game(seed="diff-supply", difficulty=difficulty, max_turns=20)
            return sum(v.count for v in game.state.house.inventory.items)
        self.assertGreater(units("a-7"), units("a7"))

    def test_difficulty_info_entries(self) -> None:
        entries = {entry["id"]: entry for entry in DIFFICULTY_INFO}
        self.assertEqual(entries["a7"]["kind"], "hard")
        self.assertEqual(entries["a-8"]["kind"], "easy")
        self.assertTrue(any("开局物资时运" in line for line in entries["a7"]["added"]))
        for key in ("a7", "a-7", "a8", "a-8", "a9", "a-9", "a10", "a-10"):
            self.assertEqual(
                GameEngine.new_game(seed="accept-" + key, difficulty=key, max_turns=20).state.meta.difficulty,
                key,
            )

    def test_random_start_and_auto_ban(self) -> None:
        first = GameEngine.new_game(seed="random-start", random_pseudo=True)
        second = GameEngine.new_game(seed="random-start", random_pseudo=True)
        self.assertEqual(first.state.pseudo_state.scenario_id, second.state.pseudo_state.scenario_id)
        self.assertEqual(
            sorted(first.state.world.disabled_characters),
            sorted(second.state.world.disabled_characters),
        )
        pseudo_def = PSEUDOS[first.state.pseudo_state.scenario_id]
        self.assertNotIn(pseudo_def.human_character_id, first.state.world.disabled_characters)
        self.assertTrue(set(first.state.world.disabled_characters) <= set(CHARACTERS))
        self.assertTrue(set(first.state.world.disabled_characters).isdisjoint({"dragon", "bigstar", "tear"}))
        with self.assertRaises(RuleViolation):
            GameEngine.new_game(seed="ban-big-three", disabled_character_ids=["dragon"])
        plain = GameEngine.new_game(seed="plain")
        self.assertEqual(plain.state.pseudo_state.scenario_id, "pseudo_benzene")
        self.assertEqual(plain.state.world.disabled_characters, [])

    def test_visit_calendar_and_locations(self) -> None:
        first = GameEngine.new_game(seed="calendar-1")
        second = GameEngine.new_game(seed="calendar-1")
        self.assertEqual(first._roll_next_pseudo_visit(1), second._roll_next_pseudo_visit(1))
        self.assertLessEqual(first.state.world.visitors.next_pseudo_turn, 13)
        locations = GameEngine.new_game(seed="location-generation").state.world.locations.available_locations
        self.assertEqual(len(set(locations)), 10)
        self.assertTrue(
            {"county_hospital", "convenience_store", "supermarket", "courier_station"} <= set(locations)
        )

    def test_discover_constraints(self) -> None:
        engine = GameEngine.new_game(seed="discover")
        options = engine.discover(["sun", "moon", "star", "cloud", "wind"], constraint=lambda v: v != "sun")
        self.assertEqual(len(options), 3)
        self.assertNotIn("sun", options)
        pool = ["dragon", "bigstar", "tear", "benzene", "wrongwave", "erebus", "six71", "jiugu", "fries", "zero329", "peach", "rose"]
        for index in range(4):
            game = GameEngine.new_game(seed=f"start-guarantee-{index}")
            picked = game.discover(pool, count=3, required=("dragon", "bigstar", "tear"))
            self.assertTrue(set(picked) & {"dragon", "bigstar", "tear"})
        with self.assertRaises(RuleViolation):
            GameEngine.new_game(seed="discover-invalid", start_choices=["stone"])


if __name__ == "__main__":
    unittest.main()

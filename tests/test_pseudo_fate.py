"""三位伪人机制与厄瑞玻斯命运牌。

合并自原 pseudo / fate / fries / onion 用例。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import patch

from weiren_game.data import PSEUDOS
from weiren_game.data.characters import erebus as erebus_module
from weiren_game.engine import GameEngine
from weiren_game.items import ItemInstance
from weiren_game.lifecycle import AbilityLaunch
from weiren_game.models import Condition, DoorEvent, Information, SearchMission


def bare_engine(seed: str, pseudo_id: str = "pseudo_benzene") -> GameEngine:
    engine = GameEngine.new_game(seed, "a0", pseudo_id=pseudo_id)
    engine.state.house.tenants.clear()
    engine.state.world.visitors.visitor_pool.clear()
    engine.state.world.events.door_events.clear()
    engine.state.house.information.clear()
    engine.state.flow.turn = 1
    engine.state.flow.phase = "action"
    return engine


def clear_door(engine: GameEngine, accept: bool = False) -> None:
    while engine._pending_choice is not None:
        engine.choose_discover(engine._pending_choice["options"][0])
    while engine.state.world.events.door_events and not engine.state.flow.game_over:
        event = engine.state.world.events.door_events[0]
        if event.kind == "human":
            has_room = len(engine.living_tenants()) < 10
            engine.handle_next_door_event("accept" if accept and has_room else "reject")
        else:
            engine.handle_next_door_event()


def expellable_of(engine: GameEngine, tenant_id: int) -> tuple[bool, bool]:
    """读 web 状态下发的「驱逐」按钮门控，确保前端只是消费后端判定。"""
    from weiren_game.web_ui import build_state

    for row in build_state(engine)["tenants"]:
        if row["id"] == tenant_id:
            return bool(row["expellable"]), bool(row["expel_risk"])
    return False, False


class PseudoTests(unittest.TestCase):
    def test_three_pseudos_and_mutual_exclusivity(self) -> None:
        for pseudo_id in PSEUDOS:
            engine = GameEngine.new_game(f"one-round-{pseudo_id}", pseudo_id=pseudo_id)
            engine.start_turn()
            clear_door(engine, accept=True)
            if not engine.state.flow.game_over:
                engine.end_turn()
            engine.assert_invariants()
            present = [t.character_id for t in engine.living_tenants()] + engine.state.world.visitors.visitor_pool
            self.assertNotIn(PSEUDOS[pseudo_id].human_character_id, present)

    def test_benzene_marks_breakthrough_and_liberation(self) -> None:
        from weiren_game.data.pseudos.pseudo_benzene import cast_curse, visit, visitor_mark

        engine = bare_engine("benzene", "pseudo_benzene")
        engine._add_tenant("hkw")
        engine.state.pseudo_state.revealed = True
        engine.state.pseudo_state.fear_marks = 5
        with patch.object(engine, "_rng", return_value=SimpleNamespace(random=lambda: 0.0)):
            visitor_mark(engine)
        self.assertEqual((engine.state.pseudo_state.curse_count, engine.state.pseudo_state.fear_marks), (1, 0))

        capped = bare_engine("benzene-cap", "pseudo_benzene")
        for _ in range(6):
            capped._add_tenant("hkw")
        capped.state.pseudo_state.revealed = True
        capped.state.pseudo_state.visit_count = 99
        visit(capped)
        self.assertFalse(capped.state.flow.game_over)

        safe = GameEngine.new_game("liberation")
        safe.state.pseudo_state.revealed = True
        for _ in range(7):   # 连续无死亡 7 次 → 解放
            for tenant in safe.home_tenants():
                tenant.max_health = tenant.health = 1000
            safe.state.pseudo_state.fear_marks = 2
            cast_curse(safe)
        self.assertTrue(safe.state.flow.game_over and safe.state.flow.victory)

        # 驱逐视同屋内死亡（仅播报不同）：推进突破计数并打断「早交班」。
        expel = bare_engine("benzene-expel", "pseudo_benzene")
        victim = expel._add_tenant("hkw")
        expel.state.pseudo_state.revealed = True
        expel._expel_tenant(victim, "测试")
        self.assertEqual(expel.state.pseudo_state.deaths_since_last_visit, 1)
        self.assertTrue(expel.state.pseudo_state.death_since_last_curse)

    def test_onion_no_auto_whisper_liberation_and_echo(self) -> None:
        from weiren_game.data.pseudos.pseudo_onion import cast_whisper

        engine = bare_engine("onion", "pseudo_onion")
        for character_id in ("hkw", "dragonboat", "whitedragon"):
            engine._add_tenant(character_id)
        engine._resolve_pseudo_visit()
        engine._resolve_pseudo_visit()
        self.assertTrue(engine.state.pseudo_state.revealed)
        self.assertEqual(engine.state.pseudo_state.whisper_count, 0)
        self.assertFalse(engine.state.flow.game_over)

        safe = GameEngine.new_game("onion-safe", pseudo_id="pseudo_onion")
        safe.state.flow.turn = 1
        safe.state.flow.phase = "action"
        safe.state.pseudo_state.revealed = True
        for tenant in safe.home_tenants():
            tenant.set_status("calm_onion", intensity=1, layers=1)
        cast_whisper(safe)
        cast_whisper(safe)
        self.assertTrue(safe.state.pseudo_state.liberated and safe.state.flow.victory)

        echo = bare_engine("onion-echo", "pseudo_onion")
        first = echo._add_tenant("hkw")
        second = echo._add_tenant("dragonboat")
        first.irritation = Condition(1, 2)
        echo.state.pseudo_state.revealed = True
        echo.state.flow.phase = "turn_end"
        echo._settle_base_end_effects()
        self.assertAlmostEqual(first.sanity, 95.8)   # 每名烦躁者 +5% 理智消耗
        self.assertAlmostEqual(second.sanity, 95.8)

    def test_fries_accusation_clone_fortune_and_hermit(self) -> None:
        from weiren_game.data.pseudos.pseudo_fries import performance

        engine = GameEngine.new_game("fries", pseudo_id="pseudo_fries")
        engine.state.flow.turn = 2
        engine.state.flow.phase = "action"
        target = engine.home_tenants()[0]
        engine.state.pseudo_state.kidnapped_snapshot = asdict(target)
        engine.state.pseudo_state.infiltrator_id = target.id
        engine.state.pseudo_state.infiltration_turns = 2
        target.is_pseudo = True
        target.pseudo_source = "fries"
        # 屋主「直接驱逐」按钮门控：纯查询，由后端下发，前端只消费（无证据 → 不出按钮）。
        self.assertEqual(expellable_of(engine, target.id), (False, False))
        for index in range(3):
            engine.state.house.information.append(Information(
                info_instance_id=f"X{index}", title="指认", text="可疑", status="pending",
                gained_turn=2, expires_turn=7, truth=True, kind="pseudo_inhome",
                target_ids=[target.id],
            ))
        # 3 条待验证 → 可驱逐，但同时下发「可能误判」的风险标志。
        self.assertEqual(expellable_of(engine, target.id), (True, True))
        engine.accuse(target.id)
        restored = engine.state.house.tenants[target.id]
        self.assertFalse(restored.is_pseudo)
        self.assertEqual((engine.state.pseudo_state.expelled_count, restored.health), (1, 80))
        # 指认后证据失效 → 按钮收回。
        self.assertEqual(expellable_of(engine, target.id), (False, False))

        clone = bare_engine("fries-fortune", "pseudo_fries")
        fake = clone._add_tenant("hkw")
        fake.is_pseudo = True
        fake.pseudo_source = "fries"
        clone.start_search(fake.id, "county_hospital")
        self.assertEqual(clone.state.world.missions[0].fortune, -5)

        blocked = bare_engine("fries-hermit", "pseudo_fries")
        clone2 = blocked._add_tenant("hkw")
        blocked._add_tenant("dragonboat")
        clone2.is_pseudo = True
        clone2.pseudo_source = "fries"
        blocked.state.pseudo_state.infiltrator_id = clone2.id
        blocked._set_global_event("suppress.pseudo.cast", 1.0, 99)
        with patch.object(blocked, "_rng", return_value=SimpleNamespace(random=lambda: 0.0)):
            performance(blocked)
        self.assertFalse(blocked.state.house.information)
        self.assertEqual(blocked.state.pseudo_state.performance_count, 0)

    def test_fate_cards(self) -> None:
        fool = bare_engine("fool")
        fool.state.world.visitors.next_pseudo_turn = 99
        erebus_module.apply_fate_card(fool, 0, False, None)
        fool.state.flow.turn = 2
        fool._queue_scheduled_visitors()
        self.assertEqual(
            len([e for e in fool.state.world.events.door_events if e.kind == "pseudo"]), 2
        )

        sun = bare_engine("sun")
        sun.state.house.information.extend([
            Information("I1", "真", "真", "pending", 1, 6, truth=True),
            Information("I2", "假", "假", "pending", 1, 6, truth=False),
        ])
        erebus_module.apply_fate_card(sun, 19, True, None)
        self.assertEqual(
            (sun.state.house.information[0].status, sun.state.house.information[1].status),
            ("confirmed", "refuted"),
        )

        world = bare_engine("world")
        erebus = world._add_tenant("erebus")
        erebus_module.apply_fate_card(world, 21, True, None)
        self.assertTrue(world._pseudo_actions_suppressed())
        self.assertFalse(world._pseudo_capability("cast"))
        self.assertTrue(erebus.ability_state("draw_fate").disabled)

        hermit = bare_engine("hermit", "pseudo_benzene")
        hermit._add_tenant("hkw")
        hermit.state.pseudo_state.revealed = True
        hermit.state.pseudo_state.fear_marks = 7
        erebus_module.apply_fate_card(hermit, 9, False, None)
        self.assertEqual(hermit.state.pseudo_state.fear_marks, 20)
        erebus_module.apply_fate_card(hermit, 9, True, None)
        self.assertEqual(hermit.state.pseudo_state.fear_marks, 0)


class FriesExposureTest(unittest.TestCase):
    """薯条暴露值：识破回敬不得触发新的里程碑指认（否则自我放大）。"""

    def test_backlash_does_not_spawn_accusations(self) -> None:
        from weiren_game.data.pseudos import pseudo_fries

        engine = bare_engine("fries-exposure", "pseudo_fries")
        tenant = engine._add_tenant("hkw")
        pseudo = engine.state.pseudo_state
        pseudo.infiltrator_id = tenant.id

        before = len(engine.state.house.information)
        for _ in range(20):  # 20 次识破回敬 = 300 暴露值
            pseudo_fries.add_exposure(engine, 15, "虚假信息被识破", spawn=False)
        self.assertEqual(len(engine.state.house.information), before)
        self.assertGreaterEqual(pseudo.exposure, 25)  # 仍推进炼狱扳机

        # 自然来源照旧：每累计 5 层产生 1 条待验证指认。
        pseudo_fries.add_exposure(engine, 5, "回合结束")
        self.assertEqual(len(engine.state.house.information), before + 1)


if __name__ == "__main__":
    unittest.main()

"""搜索：确定性、返程结算、固定随机序列、携带容量与濒死。"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from weiren_game.engine import GameEngine
from weiren_game.items import ItemInstance
from weiren_game.models import SearchMission


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


def bare_engine(seed: str, pseudo_id: str = "pseudo_benzene") -> GameEngine:
    engine = GameEngine.new_game(seed, "a0", pseudo_id=pseudo_id)
    engine.state.house.tenants.clear()
    engine.state.world.visitors.visitor_pool.clear()
    engine.state.world.events.door_events.clear()
    engine.state.house.information.clear()
    engine.state.flow.turn = 1
    engine.state.flow.phase = "action"
    return engine


class SearchTests(unittest.TestCase):
    def test_same_seed_is_deterministic(self) -> None:
        first = GameEngine.new_game("repeatable", "a0")
        second = GameEngine.new_game("repeatable", "a0")
        self.assertEqual(first.state.world.visitors.visitor_pool, second.state.world.visitors.visitor_pool)
        self.assertEqual(
            [t.character_id for t in first.home_tenants()],
            [t.character_id for t in second.home_tenants()],
        )
        for engine in (first, second):
            engine.start_turn()
            clear_door(engine)
            engine.start_search(engine.home_tenants()[0].id, "convenience_store")
        self.assertEqual(first.state.world.missions[0], second.state.world.missions[0])
        self.assertEqual(first.state.house.inventory, second.state.house.inventory)

    def test_search_returns_at_next_turn_start(self) -> None:
        engine = GameEngine.new_game("search-return")
        engine.start_turn()
        clear_door(engine)
        tenant = engine.home_tenants()[0]
        engine.start_search(tenant.id, "convenience_store")
        mission = engine.state.world.missions[0]
        mission.actual_search_turns = mission.elapsed_search_turns + 1
        mission.remain_search_turns = 1
        mission.attacked_pseudos = [engine.state.pseudo_state.scenario_id]
        expected = mission.rewards[:]
        before: dict[str, int] = {}
        for value in engine.state.house.inventory:
            before[value.item_id] = before.get(value.item_id, 0) + value.count
        engine.end_turn()
        engine.start_turn()
        self.assertTrue(engine.state.house.tenants[tenant.id].at_home)
        self.assertFalse(engine.state.world.missions)
        for item_id in set(expected):
            self.assertGreaterEqual(
                engine.state.house.inventory.count(item_id) - before.get(item_id, 0),
                expected.count(item_id),
            )

    def test_recompute_reuses_sequence_and_strict_less_than(self) -> None:
        engine = GameEngine.new_game("search-recalculate")
        engine.start_turn()
        clear_door(engine)
        tenant = engine.home_tenants()[0]
        engine.start_search(tenant.id, engine.state.world.locations.available_locations[0])
        mission = engine.state.world.missions[0]
        sequence, rate, rewards = mission.random_sequence[:], mission.search_success_rate, mission.rewards[:]
        mission.search_success_rate = rate - .20
        engine._recalculate_search(mission)
        self.assertEqual(mission.random_sequence, sequence)
        mission.search_success_rate = rate
        engine._recalculate_search(mission)
        self.assertEqual((mission.random_sequence, mission.rewards), (sequence, rewards))

        strict = bare_engine("search-strict")
        actor = strict._add_tenant("hkw")
        probe = SearchMission(
            tenant_id=actor.id, location_id="county_hospital",
            search_turns=1, search_behavior_count=1,
            carry_capacity=1, search_success_rate=.50, random_sequence=[.50],
        )
        strict._recalculate_search(probe)
        self.assertEqual((probe.success_behavior_indices, probe.rewards), ([], []))

    def test_capacity_turns_and_near_death(self) -> None:
        engine = bare_engine("carry-search")
        tenant = engine._add_tenant("tear")
        engine._gain_item("walmart_bag")
        engine.equip_item(tenant.id, "walmart_bag")
        engine.start_search(tenant.id, "county_hospital")
        mission = engine.state.world.missions[0]
        self.assertEqual(mission.carry_capacity, engine.tenant_carry_capacity(tenant))
        self.assertGreaterEqual(mission.base_search_turns, 6)   # [容量×0.75]+1
        self.assertLessEqual(mission.base_search_turns, 10)     # [容量×1.5]

        dying = bare_engine("near-death")
        target = dying._add_tenant("hkw")
        target.health = -1
        target.at_home = False
        target.inventory.add(ItemInstance("A1", "chain_vest", durability=50))
        lost = SearchMission(tenant_id=target.id, location_id="county_hospital", rewards=["water"])
        with patch.object(dying, "_rng", return_value=SimpleNamespace(random=lambda: 0.0)):
            dying._resolve_search_return(lost, target)
        self.assertEqual((target.health, target.shock, target.shock_layers), (0, 1, 2))
        self.assertFalse(target.inventory.items)
        self.assertFalse(lost.rewards)


if __name__ == "__main__":
    unittest.main()

"""Deterministic non-interactive smoke runs for all three pseudo scenarios."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

# Make ``python tools/smoke_simulation.py`` work from any current directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from weiren_game.engine import GameEngine, RuleViolation
from weiren_game.data.characters import erebus as erebus_module


def heal_home(engine: GameEngine) -> None:
    """让机器人按简单优先级使用医疗与食物（每回合最多 3 次）。"""
    uses = 0
    for tenant in sorted(
        engine.home_tenants(), key=lambda t: (t.health, -t.sanity)
    ):
        if uses >= 3:
            break
        for item_id, condition in (
            ("home_first_aid", tenant.trauma.intensity >= 3),
            ("portable_medicine", tenant.disorder.intensity >= 3),
            ("simple_food", tenant.health <= 45),
            ("water", tenant.health <= 30),
        ):
            if condition and uses < 3:
                try:
                    engine.use_item(item_id, tenant.id)
                    uses += 1
                except RuleViolation:
                    continue


def counter_onion(engine: GameEngine) -> None:
    """洋葱局：用减压物资清除烦躁，优先保持屋内不被烦躁占优。"""
    pseudo = engine.state.pseudo_state
    if pseudo.scenario_id != "pseudo_onion" or not pseudo.revealed:
        return
    uses = 0
    for tenant in engine.home_tenants():
        if uses >= 3:
            break
        if not tenant.irritation.active:
            continue
        for item_id in ("gum", "weird_beans", "chips", "chocolate_bar"):
            if engine.state.house.inventory.count(item_id) <= 0:
                continue
            try:
                engine.use_item(item_id, tenant.id)
                uses += 1
                break
            except RuleViolation:
                continue


def equip_basics(engine: GameEngine) -> None:
    """给屋内房客装备最基础的常用物（装甲/书籍/购物袋等）。"""
    for tenant in engine.home_tenants():
        held = {held.item_id for held in tenant.inventory.items}
        for item_id in (
            "ghillie_suit", "polar_jacket", "motocross_helmet",
            "chain_vest", "walmart_bag", "nebula_legend",
            "bls_book", "plants_book", "disaster_book", "walkman",
        ):
            if item_id in held:
                continue
            if engine.state.house.inventory.count(item_id) <= 0:
                continue
            try:
                engine.equip_item(tenant.id, item_id)
                held.add(item_id)
            except RuleViolation:
                continue


def use_active_abilities(engine: GameEngine) -> None:
    """按房客机制触发一套保守的基础主动技能策略。"""
    home = engine.home_tenants()

    def attempt(
        actor: object,
        *,
        ability_id: str | None = None,
        target_id: str | None = None,
        option: str | None = None,
    ) -> None:
        try:
            engine.use_ability(
                actor.id,
                target_id=target_id,
                ability_id=ability_id,
                option=option,
            )
        except RuleViolation:
            return

    for actor in home:
        character_id = actor.character_id
        if character_id == "fries":
            attempt(actor, ability_id="deep_thought")
        elif character_id == "sandwhite":
            if any(value.sanity <= 60 for value in home):
                attempt(actor, ability_id="encourage")
        elif character_id == "dragon":
            if len(home) <= 6 and actor.sanity >= 40:
                attempt(actor, ability_id="call_friends")
        elif character_id == "rose":
            if engine._mark_count(actor, "demon") >= 1:
                if actor.sanity <= 50:
                    attempt(actor, ability_id="rose_recover", option="sanity")
                elif actor.health <= 60:
                    attempt(actor, ability_id="rose_recover", option="health")
        elif character_id == "benzene":
            wounded = sorted(
                (
                    value for value in home if value.id != actor.id
                    and (value.trauma.active or value.disorder.active)
                ),
                key=lambda value: (
                    -(value.trauma.intensity * value.trauma.layers
                      + value.disorder.intensity * value.disorder.layers),
                    value.id,
                ),
            )
            if wounded:
                target = wounded[0]
                option = "trauma" if target.trauma.active else "disorder"
                attempt(
                    actor, ability_id="emergency_treatment",
                    target_id=target.id, option=option,
                )
        elif character_id == "zero329":
            pending = [
                info for info in engine.state.house.information
                if info.status == "pending"
                and info.kind in {"material_reward", "location_modifier"}
            ]
            if pending and engine._mark_count(actor, "alert") >= 1:
                attempt(actor, ability_id="information_collect")
        elif character_id == "onion":
            irritable = sorted(
                (
                    value for value in home
                    if value.irritation.active and value.id != actor.id
                ),
                key=lambda value: (
                    -value.irritation.layers, value.id,
                ),
            )
            if irritable:
                attempt(
                    actor, ability_id="emotion_strip",
                    target_id=irritable[0].id,
                )
def search_cap(engine: GameEngine) -> int:
    """按伪人局势决定本回合最多可派几名搜索者。"""
    pseudo = engine.state.pseudo_state
    home_count = len(engine.home_tenants())
    if pseudo.scenario_id == "pseudo_benzene":
        threshold = max(1.0, min(6.0, 3.0 + .5 * pseudo.visit_count))
        keep = int(threshold) + 2  # 屋里留出足够安全余量
    elif pseudo.scenario_id == "pseudo_onion":
        keep = 3
    else:  # fries：搜索即可能被绑架，谨慎出人
        keep = 3
    return max(0, min(2, home_count - keep))


def try_search(engine: GameEngine) -> None:
    """派健康度足够的房客外出搜索，直至达到本回合上限。"""
    cap = search_cap(engine)
    if cap <= 0:
        return
    candidates = [
        tenant for tenant in engine.home_tenants()
        if (
            not tenant.shock
            and tenant.trauma.intensity < 6
            and tenant.disorder.intensity < 6
            and tenant.search_locked_until < engine.state.flow.turn
            and tenant.health >= 45
            and tenant.sanity >= 30
        )
    ]
    candidates.sort(key=lambda t: (t.health + t.sanity, t.character_id), reverse=True)
    for tenant in candidates:
        if len(engine.state.world.missions) >= cap:
            break
        try:
            engine.start_search(tenant.id, engine.state.world.locations.available_locations[0])
        except RuleViolation:
            continue


def play(
    seed: str,
    pseudo_id: str | None = None,
    max_turns: int = 32,
    *,
    random_pseudo: bool = False,
    log_dir: Path | None = None,
) -> GameEngine:
    if random_pseudo:
        engine = GameEngine.new_game(
            seed, "a2", max_turns=max_turns, random_pseudo=True
        )
    else:
        engine = GameEngine.new_game(
            seed, "a2", max_turns=max_turns, pseudo_id=pseudo_id
        )
    safety = 0
    while not engine.state.flow.game_over and safety < max_turns + 5:
        safety += 1
        engine.start_turn()
        while engine._pending_choice is not None:
            engine.choose_discover(engine._pending_choice["options"][0])
        while engine.state.world.events.door_events and not engine.state.flow.game_over:
            event = engine.state.world.events.door_events[0]
            returning = bool(event.metadata.get("returning_tenant_id"))
            has_room = len(engine.living_tenants()) < 10
            decision = "accept" if event.kind == "human" and (returning or has_room) else "reject"
            engine.handle_next_door_event(decision if event.kind == "human" else "inspect")
        if engine.state.flow.game_over:
            break
        heal_home(engine)
        counter_onion(engine)
        equip_basics(engine)
        use_active_abilities(engine)
        while engine._pending_choice is not None:
            engine.choose_discover(engine._pending_choice["options"][0])
        if engine._pending_ability:
            erebus = next(
                (value for value in engine.home_tenants()
                 if value.character_id == "erebus"),
                None,
            )
            if erebus is not None:
                erebus_module.cancel_fate(engine, erebus.id)
            else:
                engine._pending_ability.clear()
        try_search(engine)
        # 行动过程（技能等）可能补充新的门口事件，全部处理完才能收尾。
        door_safety = 0
        while engine.state.world.events.door_events and not engine.state.flow.game_over and door_safety < 20:
            door_safety += 1
            event = engine.state.world.events.door_events[0]
            returning = bool(event.metadata.get("returning_tenant_id"))
            has_room = len(engine.living_tenants()) < 10
            decision = "accept" if event.kind == "human" and (returning or has_room) else "reject"
            engine.handle_next_door_event(decision if event.kind == "human" else "inspect")
        if engine.state.flow.game_over:
            break
        engine.end_turn()
        engine.assert_invariants()
    if not engine.state.flow.game_over:
        raise AssertionError(
            f"simulation did not end: {seed}/{engine.state.pseudo_state.scenario_id}"
        )
    if log_dir is not None:
        target_dir = log_dir / engine.state.pseudo_state.scenario_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"{seed}.txt").write_text(
            engine.export_full_log(), encoding="utf-8"
        )
    return engine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument(
        "--random-pseudo",
        action="store_true",
        help="每局按种子随机伪人（不再固定遍历三种伪人）",
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=None,
        help="使用数值种子 seed-base .. seed-base+seeds-1（默认 smoke-<伪人>-<i>）",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=PROJECT_ROOT / "logs" / "smoke"
        / datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        help="整局 log 输出目录（每场一个文件）",
    )
    args = parser.parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)
    if args.random_pseudo:
        outcomes: dict[str, dict[bool, int]] = {}
        base = 0 if args.seed_base is None else args.seed_base
        for index in range(args.seeds):
            seed = str(base + index)
            result = play(seed, random_pseudo=True, log_dir=args.log_dir)
            pseudo_id = result.state.pseudo_state.scenario_id
            stats = outcomes.setdefault(pseudo_id, {True: 0, False: 0})
            stats[result.state.flow.victory] += 1
        for pseudo_id, stats in outcomes.items():
            print(
                f"{pseudo_id}: 分配{sum(stats.values())}局 "
                f"victories={stats[True]}, defeats={stats[False]}"
            )
    else:
        for pseudo_id in ("pseudo_benzene", "pseudo_onion", "pseudo_fries"):
            endings = {True: 0, False: 0}
            for index in range(args.seeds):
                seed = f"smoke-{pseudo_id}-{index}"
                result = play(seed, pseudo_id, log_dir=args.log_dir)
                endings[result.state.flow.victory] += 1
            print(f"{pseudo_id}: victories={endings[True]}, defeats={endings[False]}")
    print(f"log 输出目录：{args.log_dir}")


if __name__ == "__main__":
    main()

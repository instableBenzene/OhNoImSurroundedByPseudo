"""Chinese interactive terminal client for the rules engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .data import (
    BOND_DESCRIPTIONS,
    CHARACTERS,
    DEFAULT_PSEUDO,
    DIFFICULTIES,
    INFORMATION_TEMPLATES,
    ITEMS,
    LOCATIONS,
    PERSONALITY_LABELS,
    PSEUDOS,
    QUALITY_NAMES,
    CODEX_SECTIONS,
)
from .engine import GameEngine, RuleViolation
from .data.items import item_is_directly_usable, item_is_house_object
from weiren_game.text import render_markup
from weiren_game.data.lang import TEXT


DEFAULT_SAVE = Path("savegame.json")


def _configure_console() -> None:
    """将标准输出与错误流配置为 UTF-8 编码。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def _print_messages(engine: GameEngine) -> None:
    """打印并排空引擎的全部待处理消息。"""
    for message in engine.drain_messages():
        print(message)


def _choose(prompt: str, values: list[str], *, allow_blank: bool = False) -> str | None:
    """读取用户输入，返回合法编号或 ID；允许空值时返回 None。"""
    while True:
        raw = input(prompt).strip()
        if not raw and allow_blank:
            return None
        if raw in values:
            return raw
        if raw.isdigit() and 1 <= int(raw) <= len(values):
            return values[int(raw) - 1]
        print(TEXT["cli._choose.1"])


def _yes(prompt: str) -> bool:
    """判断用户确认输入是否属于是类应答（1/y/是 等）。"""
    return input(prompt).strip().lower() in {"1", "y", "yes", TEXT["cli._yes.1"], TEXT["cli._yes.2"]}


def _home_ids(engine: GameEngine, *, exclude: str | None = None) -> list[str]:
    """返回屋内房客 ID 列表，可排除指定房客。"""
    return [tenant.id for tenant in engine.home_tenants() if tenant.id != exclude]


def show_status(engine: GameEngine) -> None:
    """逐行打印引擎提供的当前局面状态。"""
    print("\n" + "\n".join(engine.status_lines()))


def show_inventory(engine: GameEngine) -> None:
    """打印屋内物资清单及各物资的耐久说明。"""
    print(TEXT["cli.show_inventory.1"])
    for index, line in enumerate(engine.inventory_lines(), 1):
        print(f"  {index}. {line}")


def show_locations(engine: GameEngine) -> None:
    """打印本局可搜索的地点列表。"""
    print(TEXT["cli.show_locations.1"])
    for index, line in enumerate(engine.location_lines(), 1):
        print(f"  {index}. {line}")


def show_codex(engine: GameEngine) -> None:
    """打印原稿内容总览：角色、物资、地点、信息、命运抽牌与伪人。"""
    print(TEXT["cli.show_codex.1"])
    for line in engine.codex_lines():
        print("  " + line)

    print(TEXT["cli.show_codex.2"])
    for character in sorted(CHARACTERS.values(), key=lambda value: value.source_id):
        state = TEXT["cli.show_codex.3"] if character.available else TEXT["cli.show_codex.4"]
        personalities = (
            f"{PERSONALITY_LABELS.get(character.primary, character.primary)}-"
            f"{PERSONALITY_LABELS.get(character.secondary, character.secondary)}"
        )
        print(
            TEXT["cli.show_codex.5"].format(p1=character.source_id, p2=character.tenant_id, p3=character.name, p4=state, p5=personalities, p6=character.carry)
        )
        print(f"      {render_markup(character.description, ansi=sys.stdout.isatty())}")
        if character.tags:
            print(TEXT["cli.show_codex.6"] + "、".join(character.tags))
        for ability in character.passives:
            print(TEXT["cli.show_codex.7"].format(p1=ability.name, p2=render_markup(ability.description, ansi=sys.stdout.isatty())))
        for ability in character.actives:
            print(TEXT["cli.show_codex.8"].format(p1=ability.name, p2=render_markup(ability.description, ansi=sys.stdout.isatty())))
        if character.source_note:
            print(TEXT["cli.show_codex.9"].format(p1=character.source_note))

    print(TEXT["cli.show_codex.10"])
    for key, description in BOND_DESCRIPTIONS.items():
        print(f"  {PERSONALITY_LABELS[key]}：{description}")

    print(TEXT["cli.show_codex.11"])
    category_labels = {
        "medical": TEXT["cli.show_codex.12"], "food": TEXT["cli.show_codex.13"], "tool": TEXT["cli.show_codex.14"],
        "craft": TEXT["cli.show_codex.15"], "information": TEXT["cli.show_codex.16"], "character": TEXT["cli.show_codex.17"],
    }
    categories = list(dict.fromkeys(item.category for item in ITEMS.values()))
    for category in categories:
        print(f"  【{category_labels.get(category, category)}】")
        for item in (value for value in ITEMS.values() if value.category == category):
            traits: list[str] = [QUALITY_NAMES[item.quality]]
            if item.max_durability:
                traits.append(TEXT["cli.show_codex.18"].format(p1=item.max_durability))
            if item.stack_size > 1:
                traits.append(TEXT["cli.show_codex.19"].format(p1=item.stack_size))
            if not item.searchable:
                traits.append(TEXT["cli.show_codex.20"])
            print(f"    {item.item_id} / {item.name}（{'；'.join(traits)}）：{render_markup(item.description, ansi=sys.stdout.isatty())}")
            print(TEXT["cli.show_codex.21"] + "、".join(item.tags))
            if item.flavor and item.flavor_shown:
                for paragraph in render_markup(item.flavor, ansi=sys.stdout.isatty()).splitlines():
                    print(f"      {paragraph}")
            if item.source_note:
                print(TEXT["cli.show_codex.22"].format(p1=item.source_note))

    print(TEXT["cli.show_codex.23"])
    for index, location in enumerate(LOCATIONS.values(), 1):
        fixed = TEXT["cli.show_codex.24"] if location.fixed else ""
        print(
            TEXT["cli.show_codex.25"].format(p1=index, p2=location.id, p3=location.name, p4=location.group, p5=fixed, p6=location.turn_delta, p7=location.behavior_delta, p8=location.encounter_bonus)
        )
        print(f"      {render_markup(location.description, ansi=sys.stdout.isatty())}")

    print(TEXT["cli.show_codex.26"])
    for index, info in enumerate(INFORMATION_TEMPLATES.values(), 1):
        print(f"  {index:02d}. {info.id} / {info.name} [{info.kind}]：{render_markup(info.description, ansi=sys.stdout.isatty())}")
        effects = [
            TEXT["cli.show_codex.27"].format(p1=info.pending) if info.pending else "",
            TEXT["cli.show_codex.28"].format(p1=info.confirmed) if info.confirmed else "",
            TEXT["cli.show_codex.29"].format(p1=info.refuted) if info.refuted else "",
        ]
        if any(effects):
            print("      " + "；".join(value for value in effects if value))

    for section in CODEX_SECTIONS:
        section(engine)

    from weiren_game.condition import EMOTION_DEFINITIONS, STATUS_DEFINITIONS

    print(TEXT["cli.show_codex.30"])
    for status in STATUS_DEFINITIONS.values():
        if status.description and status.show("description"):
            print(f"  {status.label}：{render_markup(status.description, ansi=sys.stdout.isatty())}")
    for emotion in EMOTION_DEFINITIONS.values():
        kind = TEXT["cli.show_codex.31"] if emotion.kind == "erosion" else TEXT["cli.show_codex.32"]
        if emotion.description and emotion.show("description"):
            print(f"  {emotion.label}（{kind}）：{render_markup(emotion.description, ansi=sys.stdout.isatty())}")
    from weiren_game.data import CHARACTER_MARKS

    for marks in CHARACTER_MARKS.values():
        for mark in marks:
            if mark.description:
                print(f"  {mark.label}：{render_markup(mark.description, ansi=sys.stdout.isatty())}")

    print(TEXT["cli.show_codex.33"])
    for key, pseudo in PSEUDOS.items():
        print(TEXT["cli.show_codex.34"].format(p1=key, p2=pseudo.name, p3=pseudo.human_character_id))
        print(f"      {render_markup(pseudo.description, ansi=sys.stdout.isatty())}")
        print(TEXT["cli.show_codex.35"].format(p1=render_markup(pseudo.breakthrough, ansi=sys.stdout.isatty())))
        print(TEXT["cli.show_codex.36"].format(p1=render_markup(pseudo.liberation, ansi=sys.stdout.isatty())))


def handle_door(engine: GameEngine) -> None:
    """处理下一个门口事件；人形访客询问接纳或拒绝，其余按回车推进。"""
    if not engine.state.world.events.door_events:
        print(TEXT["cli.handle_door.1"])
        return
    event = engine.state.world.events.door_events[0]
    print(f"\n【{event.title}】\n{event.description}")
    if event.kind == "human":
        while True:
            choice = input(TEXT["cli.handle_door.2"]).strip().lower()
            if choice in {"1", "accept", "a", TEXT["cli.handle_door.3"]}:
                engine.handle_next_door_event("accept")
                break
            if choice in {"2", "reject", "r", TEXT["cli.handle_door.4"]}:
                engine.handle_next_door_event("reject")
                break
            print(TEXT["cli.handle_door.5"])
    else:
        input(TEXT["cli.handle_door.6"])
        engine.handle_next_door_event()
    _print_messages(engine)


def start_search(engine: GameEngine) -> None:
    """选择可外出的房客、地点与携带物资并发起一次搜索。"""
    candidates = [
        tenant for tenant in engine.home_tenants()
        if not tenant.shock
        and not (tenant.trauma.intensity == 6 and engine._condition_extra_effect_active(tenant, "trauma"))
        and not (tenant.disorder.intensity == 6 and engine._condition_extra_effect_active(tenant, "disorder"))
        and tenant.search_locked_until < engine.state.flow.turn and tenant.skip_until_turn < engine.state.flow.turn
    ]
    if not candidates:
        print(TEXT["cli.start_search.1"])
        return
    print(TEXT["cli.start_search.2"])
    ids = []
    for index, tenant in enumerate(candidates, 1):
        ids.append(tenant.id)
        character = engine.character(tenant)
        print(TEXT["cli.start_search.3"].format(p1=index, p2=tenant.id, p3=character.name, p4=engine.tenant_carry_capacity(tenant), p5=tenant.health, p6=tenant.sanity))
    tenant_id = _choose(TEXT["cli.start_search.4"], ids)
    if not tenant_id:
        return

    show_locations(engine)
    location_id = _choose(TEXT["cli.start_search.5"], engine.state.world.locations.available_locations)
    if not location_id:
        return
    tenant = engine.state.house.tenants[tenant_id]
    bag_names = "、".join(
        ITEMS[value.item_id].name for value in tenant.inventory.items
    ) or TEXT["cli.start_search.6"]
    print(
        TEXT["cli.start_search.7"].format(p1=engine.character(tenant).name, p2=bag_names)
    )
    engine.start_search(tenant_id, location_id)
    _print_messages(engine)


def use_item(engine: GameEngine) -> None:
    """选择物资与目标房客并执行一次使用。"""
    house_ids = list(dict.fromkeys(
        value.item_id for value in engine.state.house.inventory
    ))
    # 只列“可直接使用”的物资；装备/携带/屋内物件由内容规则排除。
    item_ids = [item_id for item_id in house_ids if item_is_directly_usable(item_id)]
    if not item_ids:
        print(TEXT["cli.use_item.1"])
        return
    print(TEXT["cli.use_item.2"])
    for index, item_id in enumerate(item_ids, 1):
        print(f"  {index}. {item_id}: {ITEMS[item_id].name} — {ITEMS[item_id].description}")
    item_id = _choose(TEXT["cli.use_item.3"], item_ids)
    if not item_id:
        return
    show_status(engine)
    target_id = _choose(TEXT["cli.use_item.4"], _home_ids(engine))
    condition = None
    if "anodyne" in ITEMS[item_id].tags:
        condition = _choose(TEXT["cli.use_item.5"], ["trauma", "disorder"])
    engine.use_item(item_id, target_id, condition)
    _print_messages(engine)


def equip_item(engine: GameEngine) -> None:
    """为房客装备装甲、书籍或角色专属携带物。"""
    house_ids = list(dict.fromkeys(
        value.item_id for value in engine.state.house.inventory
    ))
    # 装备/携带类：不可直接使用、且不是屋内物件。
    equippable = [
        key for key in house_ids
        if not item_is_directly_usable(key) and not item_is_house_object(key)
    ]
    if not equippable:
        print(TEXT["cli.equip_item.1"])
        return
    print(TEXT["cli.equip_item.2"])
    for index, key in enumerate(equippable, 1):
        print(f"  {index}. {key}: {ITEMS[key].name} — {ITEMS[key].description}")
    item_id = _choose(TEXT["cli.equip_item.3"], equippable)
    show_status(engine)
    tenant_id = _choose(TEXT["cli.equip_item.4"], _home_ids(engine))
    engine.equip_item(tenant_id or "", item_id or "")
    _print_messages(engine)


def unequip_item(engine: GameEngine) -> None:
    """选择房客并卸下其一件常驻装备。"""
    candidates = [tenant for tenant in engine.home_tenants() if tenant.inventory.items]
    if not candidates:
        print(TEXT["cli.unequip_item.1"])
        return
    ids = [tenant.id for tenant in candidates]
    for index, tenant in enumerate(candidates, 1):
        print(f"  {index}. {tenant.id} {engine.character(tenant).name}：" + "、".join(ITEMS[h.item_id].name for h in tenant.inventory.items))
    tenant_id = _choose(TEXT["cli.unequip_item.2"], ids)
    tenant = engine.state.house.tenants[tenant_id or ""]
    held_ids = [held.item_id for held in tenant.inventory.items]
    for index, key in enumerate(held_ids, 1):
        print(f"  {index}. {key}: {ITEMS[key].name}")
    item_id = _choose(TEXT["cli.unequip_item.3"], held_ids)
    engine.unequip_item(tenant.id, item_id or "")
    _print_messages(engine)


def _choose_target(engine: GameEngine, exclude: str | None = None) -> str | None:
    """在屋内房客中交互选择目标 ID，无候选项时返回 None。"""
    choices = _home_ids(engine, exclude=exclude)
    if not choices:
        return None
    print(TEXT["cli._choose_target.1"])
    for index, tenant_id in enumerate(choices, 1):
        tenant = engine.state.house.tenants[tenant_id]
        print(f"  {index}. {tenant.id} {engine.character(tenant).name}")
    return _choose(TEXT["cli._choose_target.2"], choices)



def use_ability(engine: GameEngine) -> None:
    """选择使用者、主动能力、目标与附加选项后执行，并处理命运抽牌结算。"""
    actors = [tenant for tenant in engine.home_tenants() if engine.character(tenant).actives and not tenant.abilities_disabled]
    if not actors:
        print(TEXT["cli.use_ability.1"])
        return
    print(TEXT["cli.use_ability.2"])
    actor_ids = []
    for index, tenant in enumerate(actors, 1):
        actor_ids.append(tenant.id)
        print(f"  {index}. {tenant.id} {engine.character(tenant).name}")
    actor_id = _choose(TEXT["cli.use_ability.3"], actor_ids)
    if not actor_id:
        return
    abilities = engine.available_abilities(actor_id)
    for index, (key, name, description) in enumerate(abilities, 1):
        print(f"  {index}. {key}: {name} — {description}")
    ability_id = _choose(TEXT["cli.use_ability.4"], [value[0] for value in abilities])
    ability = next(value for value in engine.character(engine.state.house.tenants[actor_id]).actives if value.id == ability_id)
    from weiren_game.data import ABILITY_TARGET_OPTIONS

    def _collect(current, owner_id):
        """按能力的目标规格收集输入（内容自描述，CLI 不写死内容 id）。"""
        picked_target = None
        picked_option = None
        picked_amount = None
        if current.target in {"tenant", "tenant_condition", "other_tenant"}:
            picked_target = _choose_target(engine, owner_id if current.target == "other_tenant" else None)
            if picked_target is None:
                print(TEXT["cli._collect.1"])
                return None
        if current.target == "amount":
            owner = engine.state.house.tenants[owner_id]
            maximum = engine._mark_count(owner, current.amount_mark) if current.amount_mark else 99
            raw = input(f"{current.amount_label or '数量'}（1~{maximum}） > ").strip()
            picked_amount = int(raw) if raw.isdigit() else 1
            # 选项允许带第 3、4 项（图标/说明，只给图形界面用）：这里只取前两项。
            for option in current.options:
                value, label = option[0], option[1]
                if _yes(f"{label}？[y/N] > "):
                    picked_option = value
                    break
        elif current.target in {"resource", "tenant_condition"} and current.options:
            labels = "，".join(f"[{i}] {option[1]}" for i, option in enumerate(current.options, 1))
            picked_option = _choose(labels + " > ", [option[0] for option in current.options])
            if picked_option is None:
                return None
        elif current.target == "information":
            provider = ABILITY_TARGET_OPTIONS.get(current.id)
            candidates = list(provider(engine, engine.state.house.tenants[owner_id])) if provider else []
            if not candidates:
                print(TEXT["cli._collect.2"])
                return None
            for index, item in enumerate(candidates, 1):
                print(f"  {index}. {item['label']}")
            pick = _choose(TEXT["cli._collect.3"], list(range(1, len(candidates) + 1)))
            if pick is None:
                return None
            picked_option = candidates[pick - 1]["value"]
        return (picked_target, picked_option, picked_amount)

    picked = _collect(ability, actor_id)
    if picked is None:
        return
    target_id, option, amount = picked
    copied_ability_id = None
    secondary_target_id = None
    secondary_option = None
    secondary_amount = None
    if ability.nested_option and option == ability.nested_option:
        source_tenant = engine.state.house.tenants.get(target_id or "")
        copied_abilities = [
            value for value in engine.character(source_tenant).actives if value.id != ability.id
        ] if source_tenant else []
        if not copied_abilities:
            print(TEXT["cli.use_ability.5"])
            return
        print(TEXT["cli.use_ability.6"])
        for index, copied in enumerate(copied_abilities, 1):
            print(f"  {index}. {copied.id}: {copied.name} — {copied.description}")
        copied_ability_id = _choose(TEXT["cli.use_ability.7"], [value.id for value in copied_abilities])
        if copied_ability_id is None:
            return
        copied = next(value for value in copied_abilities if value.id == copied_ability_id)
        sub = _collect(copied, source_tenant.id)
        if sub is None:
            print(TEXT["cli.use_ability.8"])
            return
        secondary_target_id, secondary_option, secondary_amount = sub
    result = engine.use_ability(
        actor_id, target_id, ability_id, option, amount,
        copied_ability_id, secondary_target_id, secondary_option, secondary_amount,
    )
    if engine._pending_interaction is not None:
        engine._pending_interaction(engine)
    _print_messages(engine)
    return result


def show_information(engine: GameEngine) -> None:
    """按状态优先级打印当前全部信息。"""
    if not engine.state.house.information:
        print(TEXT["cli.show_information.1"])
        return
    print(TEXT["cli.show_information.2"])
    priority = {"confirmed": 0, "pending": 1, "refuted": 2, "expired": 3}
    for info in sorted(engine.state.house.information, key=lambda value: (priority.get(value.status, 9), value.info_instance_id)):
        print(TEXT["cli.show_information.3"].format(p1=info.info_instance_id, p2=engine.information_text(info), p3=info.gained_turn))


def accuse(engine: GameEngine) -> None:
    """让玩家指认一名屋内房客为伪人。"""
    show_status(engine)
    target_id = _choose_target(engine)
    if target_id:
        engine.accuse(target_id)
        _print_messages(engine)


HELP = TEXT["cli.module.1"].strip()


def _option_label(engine: GameEngine, value: object) -> str:
    """待选项的展示名：性格 / 角色 / 物资按注册表取，取不到就原样。"""
    if isinstance(value, str):
        if value in PERSONALITY_LABELS:
            return PERSONALITY_LABELS[value]
        character = CHARACTERS.get(value)
        if character is not None:
            return character.name
        item = ITEMS.get(value)
        if item is not None:
            return item.name
    return str(value)


def _resolve_pending_choice(engine: GameEngine) -> None:
    """走完待选（开局选人 / discover / 内容发起的选择）。

    与网页端**同一条通道**（`engine._pending_choice` → `choose_discover`）；
    终端此前完全没接它，等于内容发起的待选在 CLI 里走不下去
    （抽牌、自选性格这类流程都由它交给玩家）。
    """
    while engine._pending_choice is not None:
        pending = engine._pending_choice
        options = list(pending.get("options", ()))
        if not options:
            engine._clear_pending_choice()
            return
        print("\n" + str(pending.get("prompt") or TEXT["cli.pending.1"]))
        for index, value in enumerate(options, 1):
            print("  %d. %s" % (index, _option_label(engine, value)))
        pick = _choose(TEXT["cli.pending.2"], list(range(1, len(options) + 1)))
        if pick is None:
            return
        if pending.get("kind") == "start_choice":
            engine.commit_start_choice(options[pick - 1])
        else:
            engine.choose_discover(options[pick - 1])
        _print_messages(engine)


def run(engine: GameEngine, save_path: Path) -> int:
    """运行终端主循环直至胜负分晓，返回进程退出码。"""
    _print_messages(engine)
    print(TEXT["cli.run.1"])
    print(TEXT["cli.run.2"])
    while not engine.state.flow.game_over:
        _resolve_pending_choice(engine)
        if engine.state.flow.phase != "action":
            engine.resume_to_action()
            _print_messages(engine)
            if engine.state.flow.game_over:
                break
        try:
            command = input(TEXT["cli.run.3"]).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(TEXT["cli.run.4"])
            return 0
        try:
            if command in {"status", "s", TEXT["cli.run.5"], "1"}:
                show_status(engine)
            elif command in {"inventory", "inv", TEXT["cli.run.6"]}:
                show_inventory(engine)
            elif command in {"door", "d", TEXT["cli.run.7"], "2"}:
                handle_door(engine)
            elif command in {"search", TEXT["cli.run.8"], "3"}:
                start_search(engine)
            elif command in {"item", "i", TEXT["cli.run.9"], "4"}:
                use_item(engine)
            elif command in {"equip", TEXT["cli.run.10"]}:
                equip_item(engine)
            elif command in {"unequip", TEXT["cli.run.11"]}:
                unequip_item(engine)
            elif command in {"ability", "a", TEXT["cli.run.12"], "5"}:
                use_ability(engine)
            elif command in {"info", TEXT["cli.run.13"], "6"}:
                show_information(engine)
            elif command in {"accuse", TEXT["cli.run.14"]}:
                accuse(engine)
            elif command in {"locations", TEXT["cli.run.17"]}:
                show_locations(engine)
            elif command in {"codex", TEXT["cli.run.18"], TEXT["cli.run.19"]}:
                show_codex(engine)
            elif command in {"save", TEXT["cli.run.20"], "7"}:
                engine.save(save_path); _print_messages(engine)
            elif command in {"rewind", TEXT["cli.run.21"], "8"}:
                engine.rewind_one_turn(); _print_messages(engine)
            elif command in {"end", "e", TEXT["cli.run.22"], "9"}:
                engine.end_turn(); _print_messages(engine)
            elif command in {"quit", "q", "exit", TEXT["cli.run.23"]}:
                print(TEXT["cli.run.24"])
                return 0
            elif command in {"help", "h", "?", TEXT["cli.run.25"], "0"}:
                print("\n" + HELP)
            else:
                print(TEXT["cli.run.26"])
        except RuleViolation as exc:
            print(TEXT["cli.run.27"].format(p1=exc))
    _print_messages(engine)
    print("\n" + (TEXT["cli.run.28"] if engine.state.flow.victory else TEXT["cli.run.29"]))
    print(engine.state.flow.ending)
    print(TEXT["cli.run.30"].format(p1=engine.state.flow.turn, p2=engine.state.meta.seed))
    return 0 if engine.state.flow.victory else 1


def build_parser() -> argparse.ArgumentParser:
    """解析命令行参数并返回参数对象。"""
    parser = argparse.ArgumentParser(description=TEXT["cli.build_parser.1"])
    parser.add_argument("--seed", help=TEXT["cli.build_parser.2"])
    parser.add_argument("--difficulty", choices=DIFFICULTIES, default="a0", help=TEXT["cli.build_parser.3"])
    parser.add_argument("--pseudo", choices=PSEUDOS, default=None, help=TEXT["cli.build_parser.4"])
    parser.add_argument("--disable", default="", help=TEXT["cli.build_parser.5"])
    parser.add_argument("--max-turns", type=int, default=32, help=TEXT["cli.build_parser.6"])
    parser.add_argument("--save", type=Path, default=DEFAULT_SAVE, help=TEXT["cli.build_parser.7"])
    parser.add_argument("--load", type=Path, help=TEXT["cli.build_parser.8"])
    parser.add_argument("--list-content", action="store_true", help=TEXT["cli.build_parser.9"])
    return parser


def main(argv: list[str] | None = None) -> int:
    """程序入口：配置控制台、新建或读取存档并进入游戏主循环。"""
    _configure_console()
    from weiren_game.dlc import load_configured_dlc

    load_configured_dlc()  # 启动装载：按总配置 pack_order（含优先级）装载内容包。
    args = build_parser().parse_args(argv)
    try:
        if args.list_content:
            engine = GameEngine.new_game(
                seed=args.seed or "content-list",
                difficulty=args.difficulty,
                max_turns=args.max_turns,
                pseudo_id=args.pseudo or DEFAULT_PSEUDO,
                random_pseudo=args.pseudo is None,
            )
            show_codex(engine)
            return 0
        disabled = [value.strip() for value in args.disable.replace("，", ",").split(",") if value.strip()]
        engine = GameEngine.load(args.load) if args.load else GameEngine.new_game(
            seed=args.seed, difficulty=args.difficulty, max_turns=args.max_turns,
            pseudo_id=args.pseudo or DEFAULT_PSEUDO,
            random_pseudo=args.pseudo is None,
            disabled_character_ids=disabled,
        )
        return run(engine, args.save)
    except (RuleViolation, OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(TEXT["cli.main.1"].format(p1=exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

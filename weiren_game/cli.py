"""Chinese interactive terminal client for the rules engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .data import (
    BOND_DESCRIPTIONS,
    CHARACTERS,
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
        print("请输入列表中的编号或ID。")


def _yes(prompt: str) -> bool:
    """判断用户确认输入是否属于是类应答（1/y/是 等）。"""
    return input(prompt).strip().lower() in {"1", "y", "yes", "是", "好"}


def _home_ids(engine: GameEngine, *, exclude: str | None = None) -> list[str]:
    """返回屋内房客 ID 列表，可排除指定房客。"""
    return [tenant.id for tenant in engine.home_tenants() if tenant.id != exclude]


def show_status(engine: GameEngine) -> None:
    """逐行打印引擎提供的当前局面状态。"""
    print("\n" + "\n".join(engine.status_lines()))


def show_inventory(engine: GameEngine) -> None:
    """打印屋内物资清单及各物资的耐久说明。"""
    print("\n物资：")
    for index, line in enumerate(engine.inventory_lines(), 1):
        print(f"  {index}. {line}")


def show_locations(engine: GameEngine) -> None:
    """打印本局可搜索的地点列表。"""
    print("\n本局可搜索地点（原稿规定每局生成10个）：")
    for index, line in enumerate(engine.location_lines(), 1):
        print(f"  {index}. {line}")


def show_codex(engine: GameEngine) -> None:
    """打印原稿内容总览：角色、物资、地点、信息、命运抽牌与伪人。"""
    print("\n原稿内容总览：")
    for line in engine.codex_lines():
        print("  " + line)

    print("\n房客角色（按原稿编号）：")
    for character in sorted(CHARACTERS.values(), key=lambda value: value.source_id):
        state = "可用" if character.available else "原稿缺失占位"
        personalities = (
            f"{PERSONALITY_LABELS.get(character.primary, character.primary)}-"
            f"{PERSONALITY_LABELS.get(character.secondary, character.secondary)}"
        )
        print(
            f"  {character.source_id:02d}. {character.tenant_id} / {character.name} [{state}] "
            f"性格：{personalities}；携带：{character.carry}"
        )
        print(f"      {render_markup(character.description, ansi=sys.stdout.isatty())}")
        if character.tags:
            print("      标签：" + "、".join(character.tags))
        for ability in character.passives:
            print(f"      被动·{ability.name}：{render_markup(ability.description, ansi=sys.stdout.isatty())}")
        for ability in character.actives:
            print(f"      主动·{ability.name}：{render_markup(ability.description, ansi=sys.stdout.isatty())}")
        if character.source_note:
            print(f"      原稿说明：{character.source_note}")

    print("\n八类性格羁绊：")
    for key, description in BOND_DESCRIPTIONS.items():
        print(f"  {PERSONALITY_LABELS[key]}：{description}")

    print("\n全部物资：")
    category_labels = {
        "medical": "医疗物资", "food": "食物", "tool": "工具",
        "craft": "工艺品", "information": "信息载体", "character": "角色专属",
    }
    categories = list(dict.fromkeys(item.category for item in ITEMS.values()))
    for category in categories:
        print(f"  【{category_labels.get(category, category)}】")
        for item in (value for value in ITEMS.values() if value.category == category):
            traits: list[str] = [QUALITY_NAMES[item.quality]]
            if item.max_durability:
                traits.append(f"耐久{item.max_durability}")
            if item.stack_size > 1:
                traits.append(f"每组{item.stack_size}")
            if not item.searchable:
                traits.append("不可自然搜索")
            print(f"    {item.item_id} / {item.name}（{'；'.join(traits)}）：{render_markup(item.description, ansi=sys.stdout.isatty())}")
            print("      标签：" + "、".join(item.tags))
            if item.flavor and item.flavor_shown:
                for paragraph in render_markup(item.flavor, ansi=sys.stdout.isatty()).splitlines():
                    print(f"      {paragraph}")
            if item.source_note:
                print(f"      原稿说明：{item.source_note}")

    print("\n全部搜索地点（每局从中生成10个）：")
    for index, location in enumerate(LOCATIONS.values(), 1):
        fixed = "；固定出现" if location.fixed else ""
        print(
            f"  {index:02d}. {location.id} / {location.name} [{location.group}{fixed}] "
            f"搜索回合{location.turn_delta:+d}，行为次数{location.behavior_delta:+d}，"
            f"遭遇率{location.encounter_bonus:+.0%}"
        )
        print(f"      {render_markup(location.description, ansi=sys.stdout.isatty())}")

    print("\n全部信息模板：")
    for index, info in enumerate(INFORMATION_TEMPLATES.values(), 1):
        print(f"  {index:02d}. {info.id} / {info.name} [{info.kind}]：{render_markup(info.description, ansi=sys.stdout.isatty())}")
        effects = [
            f"待验证：{info.pending}" if info.pending else "",
            f"已证实：{info.confirmed}" if info.confirmed else "",
            f"已证伪：{info.refuted}" if info.refuted else "",
        ]
        if any(effects):
            print("      " + "；".join(value for value in effects if value))

    for section in CODEX_SECTIONS:
        section(engine)

    from weiren_game.condition import EMOTION_DEFINITIONS, STATUS_DEFINITIONS

    print("\n状态、情绪与印记：")
    for status in STATUS_DEFINITIONS.values():
        if status.description and status.show("description"):
            print(f"  {status.label}：{render_markup(status.description, ansi=sys.stdout.isatty())}")
    for emotion in EMOTION_DEFINITIONS.values():
        kind = "侵蚀" if emotion.kind == "erosion" else "觉醒"
        if emotion.description and emotion.show("description"):
            print(f"  {emotion.label}（{kind}）：{render_markup(emotion.description, ansi=sys.stdout.isatty())}")
    from weiren_game.data import CHARACTER_MARKS

    for marks in CHARACTER_MARKS.values():
        for mark in marks:
            if mark.description:
                print(f"  {mark.label}：{render_markup(mark.description, ansi=sys.stdout.isatty())}")

    print("\n三类伪人：")
    for key, pseudo in PSEUDOS.items():
        print(f"  {key}: {pseudo.name}（对应人类：{pseudo.human_character_id}）")
        print(f"      {render_markup(pseudo.description, ansi=sys.stdout.isatty())}")
        print(f"      突破：{render_markup(pseudo.breakthrough, ansi=sys.stdout.isatty())}")
        print(f"      解放：{render_markup(pseudo.liberation, ansi=sys.stdout.isatty())}")


def handle_door(engine: GameEngine) -> None:
    """处理下一个门口事件；人形访客询问接纳或拒绝，其余按回车推进。"""
    if not engine.state.world.events.door_events:
        print("门外没有事件。")
        return
    event = engine.state.world.events.door_events[0]
    print(f"\n【{event.title}】\n{event.description}")
    if event.kind == "human":
        while True:
            choice = input("[1] 接纳  [2] 拒绝  > ").strip().lower()
            if choice in {"1", "accept", "a", "接纳"}:
                engine.handle_next_door_event("accept")
                break
            if choice in {"2", "reject", "r", "拒绝"}:
                engine.handle_next_door_event("reject")
                break
            print("请输入1或2。")
    else:
        input("按回车处理这个事件……")
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
        print("没有能够外出搜索的房客。")
        return
    print("\n选择房客：")
    ids = []
    for index, tenant in enumerate(candidates, 1):
        ids.append(tenant.id)
        character = engine.character(tenant)
        print(f"  {index}. {tenant.id} {character.name}（携带{engine.tenant_carry_capacity(tenant)}，生命{tenant.health:.0f}/理智{tenant.sanity:.0f}）")
    tenant_id = _choose("房客编号或ID > ", ids)
    if not tenant_id:
        return

    show_locations(engine)
    location_id = _choose("地点编号或ID > ", engine.state.world.locations.available_locations)
    if not location_id:
        return
    tenant = engine.state.house.tenants[tenant_id]
    bag_names = "、".join(
        ITEMS[value.item_id].name for value in tenant.inventory.items
    ) or "空背包"
    print(
        f"{engine.character(tenant).name}将携带背包出发：{bag_names}。"
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
        print("目前没有可直接使用的物资。")
        return
    print("\n可用物资：")
    for index, item_id in enumerate(item_ids, 1):
        print(f"  {index}. {item_id}: {ITEMS[item_id].name} — {ITEMS[item_id].description}")
    item_id = _choose("物资编号或ID > ", item_ids)
    if not item_id:
        return
    show_status(engine)
    target_id = _choose("目标房客编号或ID > ", _home_ids(engine))
    condition = None
    if "anodyne" in ITEMS[item_id].tags:
        condition = _choose("作用状态 [1] trauma创伤 [2] disorder紊乱 > ", ["trauma", "disorder"])
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
        print("物资栏中没有装甲、书籍或角色专属携带物。")
        return
    print("\n选择装备：")
    for index, key in enumerate(equippable, 1):
        print(f"  {index}. {key}: {ITEMS[key].name} — {ITEMS[key].description}")
    item_id = _choose("装备编号或ID > ", equippable)
    show_status(engine)
    tenant_id = _choose("装备给哪位房客 > ", _home_ids(engine))
    engine.equip_item(tenant_id or "", item_id or "")
    _print_messages(engine)


def unequip_item(engine: GameEngine) -> None:
    """选择房客并卸下其一件常驻装备。"""
    candidates = [tenant for tenant in engine.home_tenants() if tenant.inventory.items]
    if not candidates:
        print("没有房客携带常驻装备。")
        return
    ids = [tenant.id for tenant in candidates]
    for index, tenant in enumerate(candidates, 1):
        print(f"  {index}. {tenant.id} {engine.character(tenant).name}：" + "、".join(ITEMS[h.item_id].name for h in tenant.inventory.items))
    tenant_id = _choose("选择房客 > ", ids)
    tenant = engine.state.house.tenants[tenant_id or ""]
    held_ids = [held.item_id for held in tenant.inventory.items]
    for index, key in enumerate(held_ids, 1):
        print(f"  {index}. {key}: {ITEMS[key].name}")
    item_id = _choose("卸下哪件装备 > ", held_ids)
    engine.unequip_item(tenant.id, item_id or "")
    _print_messages(engine)


def _choose_target(engine: GameEngine, exclude: str | None = None) -> str | None:
    """在屋内房客中交互选择目标 ID，无候选项时返回 None。"""
    choices = _home_ids(engine, exclude=exclude)
    if not choices:
        return None
    print("\n选择目标：")
    for index, tenant_id in enumerate(choices, 1):
        tenant = engine.state.house.tenants[tenant_id]
        print(f"  {index}. {tenant.id} {engine.character(tenant).name}")
    return _choose("目标编号或ID > ", choices)



def use_ability(engine: GameEngine) -> None:
    """选择使用者、主动能力、目标与附加选项后执行，并处理命运抽牌结算。"""
    actors = [tenant for tenant in engine.home_tenants() if engine.character(tenant).actives and not tenant.abilities_disabled]
    if not actors:
        print("屋内没有可用主动能力。")
        return
    print("\n拥有主动能力的房客：")
    actor_ids = []
    for index, tenant in enumerate(actors, 1):
        actor_ids.append(tenant.id)
        print(f"  {index}. {tenant.id} {engine.character(tenant).name}")
    actor_id = _choose("使用者编号或ID > ", actor_ids)
    if not actor_id:
        return
    abilities = engine.available_abilities(actor_id)
    for index, (key, name, description) in enumerate(abilities, 1):
        print(f"  {index}. {key}: {name} — {description}")
    ability_id = _choose("能力编号或ID > ", [value[0] for value in abilities])
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
                print("没有合法目标。")
                return None
        if current.target == "amount":
            owner = engine.state.house.tenants[owner_id]
            maximum = engine._mark_count(owner, current.amount_mark) if current.amount_mark else 99
            raw = input(f"{current.amount_label or '数量'}（1~{maximum}） > ").strip()
            picked_amount = int(raw) if raw.isdigit() else 1
            for value, label in current.options:
                if _yes(f"{label}？[y/N] > "):
                    picked_option = value
                    break
        elif current.target in {"resource", "tenant_condition"} and current.options:
            labels = "，".join(f"[{i}] {label}" for i, (_v, label) in enumerate(current.options, 1))
            picked_option = _choose(labels + " > ", [v for v, _l in current.options])
            if picked_option is None:
                return None
        elif current.target == "information":
            provider = ABILITY_TARGET_OPTIONS.get(current.id)
            candidates = list(provider(engine, engine.state.house.tenants[owner_id])) if provider else []
            if not candidates:
                print("没有可选信息。")
                return None
            for index, item in enumerate(candidates, 1):
                print(f"  {index}. {item['label']}")
            pick = _choose("信息编号 > ", list(range(1, len(candidates) + 1)))
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
            print("该目标没有可安全模仿的主动能力。")
            return
        print("\n选择要调用的原主动能力：")
        for index, copied in enumerate(copied_abilities, 1):
            print(f"  {index}. {copied.id}: {copied.name} — {copied.description}")
        copied_ability_id = _choose("能力编号或ID > ", [value.id for value in copied_abilities])
        if copied_ability_id is None:
            return
        copied = next(value for value in copied_abilities if value.id == copied_ability_id)
        sub = _collect(copied, source_tenant.id)
        if sub is None:
            print("被调用能力没有合法输入。")
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
        print("目前没有信息。")
        return
    print("\n信息：")
    priority = {"confirmed": 0, "pending": 1, "refuted": 2, "expired": 3}
    for info in sorted(engine.state.house.information, key=lambda value: (priority.get(value.status, 9), value.info_instance_id)):
        print(f"  {info.info_instance_id} {engine.information_text(info)}（第{info.gained_turn}回合获得）")


def accuse(engine: GameEngine) -> None:
    """让玩家指认一名屋内房客为伪人。"""
    show_status(engine)
    target_id = _choose_target(engine)
    if target_id:
        engine.accuse(target_id)
        _print_messages(engine)


def lock_personality(engine: GameEngine) -> None:
    """固定满足条件房客的性格与携带量（条件由内容模块声明）。"""
    from weiren_game.data.characters import CHARACTER_MODULES

    candidates = []
    for tenant in engine.home_tenants():
        module = CHARACTER_MODULES.get(tenant.character_id)
        check = getattr(module, "CAN_LOCK_PERSONALITY", None)
        if check is not None and check(engine, tenant):
            candidates.append(tenant)
    if not candidates:
        print("屋内没有可以固定自我的房客。")
        return
    engine.lock_personality(candidates[0].id)
    _print_messages(engine)


HELP = """
玩家行动：
  status      查看房客、伪人、状态、印记和羁绊
  inventory   查看全部物资及逐件耐久
  door        处理下一个门口事件
  search      指派本回合唯一一次搜索
  item        使用医疗、食物或角色物资
  equip       装备装甲、书籍或专属携带物
  unequip     卸下常驻装备
  ability     使用主动能力（含命运抽牌）
  info        查看信息
  accuse      凭1条实锤或3条疑点指认屋内伪人
  lock        混达到10层理智后固定性格与携带量
  locations   查看本局10个搜索地点
  codex       查看原稿内容覆盖与三类伪人条件
  save        保存完整状态
  rewind      回溯到本回合开始前
  end         结束回合（门外事件/未结算命运抽牌会阻止）
  quit        退出游戏（不会自动保存）
  help        显示帮助
""".strip()


def run(engine: GameEngine, save_path: Path) -> int:
    """运行终端主循环直至胜负分晓，返回进程退出码。"""
    _print_messages(engine)
    print("\n《完蛋，我被伪人包围了！？》— Python完整规则终端版")
    print("输入 help 查看操作；输入 codex 可核对原稿内容覆盖。")
    while not engine.state.flow.game_over:
        if engine.state.flow.phase != "action":
            engine.resume_to_action()
            _print_messages(engine)
            if engine.state.flow.game_over:
                break
        try:
            command = input("\n行动 [status/inventory/door/search/item/equip/ability/info/accuse/end/help] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出游戏；本次退出不会自动保存。")
            return 0
        try:
            if command in {"status", "s", "状态", "1"}:
                show_status(engine)
            elif command in {"inventory", "inv", "物资栏"}:
                show_inventory(engine)
            elif command in {"door", "d", "门", "2"}:
                handle_door(engine)
            elif command in {"search", "搜索", "3"}:
                start_search(engine)
            elif command in {"item", "i", "物资", "4"}:
                use_item(engine)
            elif command in {"equip", "装备"}:
                equip_item(engine)
            elif command in {"unequip", "卸下"}:
                unequip_item(engine)
            elif command in {"ability", "a", "能力", "5"}:
                use_ability(engine)
            elif command in {"info", "信息", "6"}:
                show_information(engine)
            elif command in {"accuse", "指认"}:
                accuse(engine)
            elif command in {"lock", "固定", "固定自我"}:
                lock_personality(engine)
            elif command in {"locations", "地点"}:
                show_locations(engine)
            elif command in {"codex", "图鉴", "内容"}:
                show_codex(engine)
            elif command in {"save", "保存", "7"}:
                engine.save(save_path); _print_messages(engine)
            elif command in {"rewind", "回溯", "8"}:
                engine.rewind_one_turn(); _print_messages(engine)
            elif command in {"end", "e", "结束", "9"}:
                engine.end_turn(); _print_messages(engine)
            elif command in {"quit", "q", "exit", "退出"}:
                print("已退出游戏；本次退出不会自动保存。")
                return 0
            elif command in {"help", "h", "?", "帮助", "0"}:
                print("\n" + HELP)
            else:
                print("未知操作。输入 help 查看命令。")
        except RuleViolation as exc:
            print(f"无法执行：{exc}")
    _print_messages(engine)
    print("\n" + ("★ 胜利 ★" if engine.state.flow.victory else "× 失败 ×"))
    print(engine.state.flow.ending)
    print(f"最终回合：{engine.state.flow.turn}；游戏种子：{engine.state.meta.seed}")
    return 0 if engine.state.flow.victory else 1


def build_parser() -> argparse.ArgumentParser:
    """解析命令行参数并返回参数对象。"""
    parser = argparse.ArgumentParser(description="《完蛋，我被伪人包围了！？》完整规则终端版")
    parser.add_argument("--seed", help="指定可复现的游戏种子")
    parser.add_argument("--difficulty", choices=DIFFICULTIES, default="a0", help="难度")
    parser.add_argument("--pseudo", choices=PSEUDOS, default=None, help="本局伪人场景；不指定时按种子随机")
    parser.add_argument("--disable", default="", help="逗号分隔的禁用房客ID；伪人候选者不可禁用")
    parser.add_argument("--max-turns", type=int, default=32, help="坚持到日出的回合数")
    parser.add_argument("--save", type=Path, default=DEFAULT_SAVE, help="存档路径")
    parser.add_argument("--load", type=Path, help="读取存档（版本与内容包需与当前一致）")
    parser.add_argument("--list-content", action="store_true", help="列出完整内容数量后退出")
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
                pseudo_id=args.pseudo or "pseudo_benzene",
                random_pseudo=args.pseudo is None,
            )
            show_codex(engine)
            return 0
        disabled = [value.strip() for value in args.disable.replace("，", ",").split(",") if value.strip()]
        engine = GameEngine.load(args.load) if args.load else GameEngine.new_game(
            seed=args.seed, difficulty=args.difficulty, max_turns=args.max_turns,
            pseudo_id=args.pseudo or "pseudo_benzene",
            random_pseudo=args.pseudo is None,
            disabled_character_ids=disabled,
        )
        return run(engine, args.save)
    except (RuleViolation, OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(f"无法启动游戏：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

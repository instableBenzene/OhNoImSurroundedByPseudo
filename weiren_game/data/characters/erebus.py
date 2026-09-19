"""房客档案：厄瑞玻斯（7 号）。

厄瑞玻斯掌握「命运抽牌」能力，其专属 22 张命运牌一并保存在本文件。
"""

from ..types import A, CharacterDefinition, MarkDefinition
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.marks import MarkInstance
from weiren_game.global_event import GlobalEventDefinition, register_global_event
from weiren_game.modifier_rules import register_modifier_provider
from .erebus_fate_symbols import ORIENTATION_SYMBOLS, SYMBOLS as FATE_SYMBOLS

from dataclasses import dataclass
from weiren_game.data.lang import TEXT


@dataclass(frozen=True)
class FateCard:
    """一张命运牌的正/逆位文本（仅厄瑞玻斯使用，随本模块一起增减）。"""

    number: int
    name: str
    upright: str
    reversed: str

# 命运牌带来的全局事件：id / 名称 / 图标 / 点开可见的说明（内容层填写）。
_FATE_EVENTS = (
    ("guard.rewind", TEXT["data.characters.erebus._FATE_EVENTS.0.1"], "i-clock",
     TEXT["data.characters.erebus._FATE_EVENTS.0.3"]),
    ("visitor.extra_pseudo", TEXT["data.characters.erebus._FATE_EVENTS.1.1"], "i-person",
     TEXT["data.characters.erebus._FATE_EVENTS.1.3"]),
    ("visitor.supply", TEXT["data.characters.erebus._FATE_EVENTS.2.1"], "i-bag",
     TEXT["data.characters.erebus._FATE_EVENTS.2.3"]),
    ("fate.priestess", TEXT["data.characters.erebus._FATE_EVENTS.3.1"], "i-emotion",
     TEXT["data.characters.erebus._FATE_EVENTS.3.3"]),
    ("breakthrough.adjust", TEXT["data.characters.erebus._FATE_EVENTS.4.1"], "i-seal",
     TEXT["data.characters.erebus._FATE_EVENTS.4.3"]),
    ("visitor.extra", TEXT["data.characters.erebus._FATE_EVENTS.5.1"], "i-person",
     TEXT["data.characters.erebus._FATE_EVENTS.5.3"]),
    ("visitor.suppress", TEXT["data.characters.erebus._FATE_EVENTS.6.1"], "i-hand",
     TEXT["data.characters.erebus._FATE_EVENTS.6.3"]),
    ("encounter.rate.multiplier", TEXT["data.characters.erebus._FATE_EVENTS.7.1"], "i-target",
     TEXT["data.characters.erebus._FATE_EVENTS.7.3"]),
    ("fate.hanged.health_to_sanity", TEXT["data.characters.erebus._FATE_EVENTS.8.1"], "i-emotion",
     TEXT["data.characters.erebus._FATE_EVENTS.8.3"]),
    ("fate.hanged.sanity_to_health", TEXT["data.characters.erebus._FATE_EVENTS.9.1"], "i-cross",
     TEXT["data.characters.erebus._FATE_EVENTS.9.3"]),
    ("item.fragile.multiplier", TEXT["data.characters.erebus._FATE_EVENTS.10.1"], "i-gear",
     TEXT["data.characters.erebus._FATE_EVENTS.10.3"]),
    ("item.durability.multiplier", TEXT["data.characters.erebus._FATE_EVENTS.11.1"], "i-tool",
     TEXT["data.characters.erebus._FATE_EVENTS.11.3"]),
    ("search.fortune_delta", TEXT["data.characters.erebus._FATE_EVENTS.12.1"], "i-search",
     TEXT["data.characters.erebus._FATE_EVENTS.12.3"]),
    ("search.turn_delta", TEXT["data.characters.erebus._FATE_EVENTS.13.1"], "i-clock",
     TEXT["data.characters.erebus._FATE_EVENTS.13.3"]),
    ("fate.auto_discern", TEXT["data.characters.erebus._FATE_EVENTS.14.1"], "i-info",
     TEXT["data.characters.erebus._FATE_EVENTS.14.3"]),
    ("information.false_lock", TEXT["data.characters.erebus._FATE_EVENTS.15.1"], "i-note",
     TEXT["data.characters.erebus._FATE_EVENTS.15.3"]),
)
for _event_id, _event_label, _event_icon, _event_desc in _FATE_EVENTS:
    register_global_event(
        GlobalEventDefinition(
            id=_event_id,
            label=_event_label,
            icon=_event_icon,
            description=_event_desc,
            source_id="ability:draw_fate@erebus",
        )
    )

register_status_definition(
    StatusDefinition(
        "deceive_world",
        TEXT["status.deceive_world.label"],
        "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description=TEXT["status.deceive_world.description"])
)
register_status_definition(
    StatusDefinition(
        "great_seal",
        TEXT["status.great_seal.label"],
        "other",
        shown=frozenset({"icon", "description"}),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description=TEXT["status.great_seal.description"])
)
register_status_definition(
    StatusDefinition(
        "wheel_choice",
        TEXT["status.wheel_choice.label"],
        "other",
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description=TEXT["status.wheel_choice.description"])
)
register_status_definition(
    StatusDefinition(
        "wheel_hidden",
        TEXT["status.wheel_hidden.label"],
        "other",
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description=TEXT["status.wheel_hidden.description"])
)
register_status_definition(
    StatusDefinition(
        "hanged_man_upright",
        TEXT["status.hanged_man_upright.label"],
        "other",
        intensity_max=3,
        layers_max=99,
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description=TEXT["status.hanged_man_upright.description"])
)
register_status_definition(
    StatusDefinition(
        "hanged_man_reversed",
        TEXT["status.hanged_man_reversed.label"],
        "other",
        intensity_max=3,
        layers_max=99,
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description=TEXT["status.hanged_man_reversed.description"])
)

CHARACTER = CharacterDefinition(
    "erebus", 7, TEXT["character.erebus.name"], TEXT["character.erebus.description"],
    "suspicious", "steady", 3, (TEXT["character.erebus.tag.0"], TEXT["character.erebus.tag.1"], TEXT["character.erebus.tag.2"], TEXT["character.erebus.tag.3"], TEXT["character.erebus.tag.4"]),
    (A("divination_instinct", TEXT["ability.divination_instinct.name"], TEXT["ability.divination_instinct.description"]),),
    # 限制交给 chips（STYLE §12 规则 3）：`per_turn=True` 就是"每回合 1 次"的实现，正文不再重复写。
    (A("draw_fate", TEXT["ability.draw_fate.name"],
       TEXT["ability.draw_fate.description"],
       "fate", chips=(TEXT["ability.draw_fate.chip.0"],), per_turn=True),),
)

# 隐藏实现：厄瑞玻斯的 22 张命运牌以印记实例表示（每个实例 value=牌号）。
MARKS = (
    MarkDefinition(
        id="fate",
        label=TEXT["mark.fate.label"],
        acquisition=TEXT["mark.fate.acquisition"],
        minimum=0,
        maximum=22,
        externally_locked=True,
     description=TEXT["mark.fate.description"]),
)


def detail_slot(engine: EngineProtocol, tenant: object) -> list[dict]:
    """详情页小面板：命运牌（按**张数**计，印记实例存的是牌号）+「伟大的封印」期间的明月。"""
    cards = len(tenant.marks.instances_of("fate"))
    rows: list[dict] = [{
        "kind": "bar",
        "label": TEXT["data.characters.erebus.detail_slot.1"],
        "value": cards,
        "max": 22,
        "hint": TEXT["data.characters.erebus.detail_slot.2"],
    }]
    if tenant.condition("great_seal").active:
        rows.append({
            "kind": "glyph",
            # 角色自带图形（不借资源包贴图）：月与星点，随主题色描线。
            "svg": ('<circle cx="12" cy="12" r="8"/><circle cx="9.6" cy="9.8" r="1"/>'
                    '<circle cx="14" cy="14.4" r="1.4"/><circle cx="14.6" cy="8.6" r=".8"/>'
                    '<path d="M12 4v16"/>'),
            "label": TEXT["data.characters.erebus.detail_slot.3"],
            "hint": TEXT["data.characters.erebus.detail_slot.4"],
        })
    return rows


DETAIL_SLOT = detail_slot


def initial_setup(engine: object, tenant: object) -> None:
    """厄瑞玻斯入住时播种 22 张命运牌印记（不触发印记节点）。"""
    if tenant.character_id != "erebus":
        return
    if tenant.marks.instances_of("fate"):
        return
    for number in range(22):
        tenant.marks.add(
            MarkInstance(engine.state.ids.allocate_mark(), "fate", float(number))
        )

FATE: dict[int, FateCard] = {
    0: FateCard(0, TEXT["fate.0.name"], TEXT["fate.0.upright"], TEXT["fate.0.reversed"]),
    1: FateCard(1, TEXT["fate.1.name"], TEXT["fate.1.upright"], TEXT["fate.1.reversed"]),
    2: FateCard(2, TEXT["fate.2.name"], TEXT["fate.2.upright"], TEXT["fate.2.reversed"]),
    3: FateCard(3, TEXT["fate.3.name"], TEXT["fate.3.upright"], TEXT["fate.3.reversed"]),
    4: FateCard(4, TEXT["fate.4.name"], TEXT["fate.4.upright"], TEXT["fate.4.reversed"]),
    5: FateCard(5, TEXT["fate.5.name"], TEXT["fate.5.upright"], TEXT["fate.5.reversed"]),
    6: FateCard(6, TEXT["fate.6.name"], TEXT["fate.6.upright"], TEXT["fate.6.reversed"]),
    7: FateCard(7, TEXT["fate.7.name"], TEXT["fate.7.upright"], TEXT["fate.7.reversed"]),
    8: FateCard(8, TEXT["fate.8.name"], TEXT["fate.8.upright"], TEXT["fate.8.reversed"]),
    9: FateCard(9, TEXT["fate.9.name"], TEXT["fate.9.upright"], TEXT["fate.9.reversed"]),
    10: FateCard(10, TEXT["fate.10.name"], TEXT["fate.10.upright"], TEXT["fate.10.reversed"]),
    11: FateCard(11, TEXT["fate.11.name"], TEXT["fate.11.upright"], TEXT["fate.11.reversed"]),
    12: FateCard(12, TEXT["fate.12.name"], TEXT["fate.12.upright"], TEXT["fate.12.reversed"]),
    13: FateCard(13, TEXT["fate.13.name"], TEXT["fate.13.upright"], TEXT["fate.13.reversed"]),
    14: FateCard(14, TEXT["fate.14.name"], TEXT["fate.14.upright"], TEXT["fate.14.reversed"]),
    15: FateCard(15, TEXT["fate.15.name"], TEXT["fate.15.upright"], TEXT["fate.15.reversed"]),
    16: FateCard(16, TEXT["fate.16.name"], TEXT["fate.16.upright"], TEXT["fate.16.reversed"]),
    17: FateCard(17, TEXT["fate.17.name"], TEXT["fate.17.upright"], TEXT["fate.17.reversed"]),
    18: FateCard(18, TEXT["fate.18.name"], TEXT["fate.18.upright"], TEXT["fate.18.reversed"]),
    19: FateCard(19, TEXT["fate.19.name"], TEXT["fate.19.upright"], TEXT["fate.19.reversed"]),
    20: FateCard(20, TEXT["fate.20.name"], TEXT["fate.20.upright"], TEXT["fate.20.reversed"]),
    21: FateCard(21, TEXT["fate.21.name"], TEXT["fate.21.upright"], TEXT["fate.21.reversed"]),
}

# 哪些牌需要玩家**指定一名房客**（正/逆位各自不同）：目前全副牌只有死神·正位读 `target_id`
# （`_card_13:504`），逆位是随机房客、不需要输入。以后哪张牌开始读 target_id，就往这里加一条。
NEEDS_TARGET: dict[int, tuple[str, ...]] = {13: ("upright",)}

# ---------------------------------------------------------------- modifier
def maybe_discern_pending(engine: EngineProtocol, info: object) -> bool:
    """占卜直觉：获得待验证信息时 5% 概率立即识破。

    返回是否触发；触发后信息在调用方流程中继续结算。
    使用处：information_system._create_random_information。
    """
    erebus = next(
        (value for value in engine.home_tenants() if value.character_id == "erebus"),
        None,
    )
    if (
        erebus
        and engine._passive_available(erebus, "erebus.info")
        and engine._rng(_event_id("erebus.discern")).random() < .05
    ):
        engine._verify_information_object(info)
        return True
    return False


# ---------------------------------------------------------------- function
def draw_fate(engine: EngineProtocol, actor_id: str) -> list[dict]:
    """命运抽牌：从牌堆抽取三张候选牌并记录待结算选项。"""
    from weiren_game.exceptions import RuleViolation

    actor = engine._require_home_tenant(actor_id)
    if actor.character_id != "erebus":
        raise RuleViolation(TEXT["data.characters.erebus.draw_fate.1"])
    ability = actor.ability_state("draw_fate")
    if ability is not None and ability.disabled:
        raise RuleViolation(TEXT["data.characters.erebus.draw_fate.2"])
    if engine._pending_ability:
        raise RuleViolation(TEXT["data.characters.erebus.draw_fate.3"])
    deck = [
        int(value.value) for value in actor.marks.instances_of("fate")
        if int(value.value) != 20 or engine.state.pseudo_state.revealed
    ]
    if len(deck) < 3:
        raise RuleViolation(TEXT["data.characters.erebus.draw_fate.4"])
    numbers = engine.discover(
        deck,
        count=3,
        event_id=_event_id("fate.draw"),
        event_suffix=(actor.id,),
    )
    choose_orientation = actor.condition("wheel_choice").active
    hidden = actor.condition("wheel_hidden").active
    actor.clear_status("wheel_choice")
    actor.clear_status("wheel_hidden")
    orientation_rng = engine._rng(_event_id("fate.orientation"), actor.id)
    options = []
    for number in numbers:
        orientation = (
            None
            if choose_orientation
            else ("upright" if orientation_rng.random() < .50 else "reversed")
        )
        options.append({
            "number": number,
            "orientation": orientation,
            "hidden": hidden,
            "requires_orientation": choose_orientation,
        })
    engine._pending_ability = options
    engine._pending_interaction = resolve_interaction
    shown = "、".join(
        (TEXT["data.characters.erebus.draw_fate.5"] if hidden else FATE[value["number"]].name)
        + (
            TEXT["data.characters.erebus.draw_fate.6"] if value["orientation"] is None
            else TEXT["data.characters.erebus.draw_fate.7"] if value["orientation"] == "upright" else TEXT["data.characters.erebus.draw_fate.8"]
        )
        for value in options
    )
    engine._log(TEXT["data.characters.erebus.draw_fate.9"].format(p1=shown))
    return [dict(value) for value in options]


def cancel_fate(engine: EngineProtocol, actor_id: str) -> None:
    """反悔命运抽牌：降低最大生命并累计反悔次数。"""
    from weiren_game.exceptions import RuleViolation

    actor = engine._require_home_tenant(actor_id)
    engine._clear_pending_choice()
    if actor.character_id != "erebus" or not engine._pending_ability:
        raise RuleViolation(TEXT["data.characters.erebus.cancel_fate.1"])
    count = actor.condition("deceive_world").intensity + 1
    loss = (15, 25, 35)[min(2, count - 1)]
    actor.max_health = max(1, actor.max_health - loss)
    actor.health = min(actor.health, actor.max_health)
    engine._pending_ability.clear()
    engine._pending_interaction = None
    if count >= 3:
        actor.clear_status("deceive_world")
        actor.set_status("great_seal", intensity=1, layers=99)
        ability = actor.ability_state("draw_fate")
        if ability is not None:
            ability.disabled = True
    else:
        actor.set_status("deceive_world", intensity=count, layers=99)
    engine._record_action("fate_cancel", actor=actor.id, regrets=count)
    engine._log(TEXT["data.characters.erebus.cancel_fate.2"].format(p1=loss, p2=count))


def resolve_fate(
    engine: EngineProtocol,
    actor_id: str,
    card_number: int,
    *,
    orientation: str | None = None,
    target_id: str | None = None,
    sacrifice_item_id: str | None = None,
) -> None:
    """校验所选命运牌与正逆位后应用牌面效果。"""
    from weiren_game.exceptions import RuleViolation
    from ..items import ITEMS

    actor = engine._require_home_tenant(actor_id)
    if actor.character_id != "erebus":
        raise RuleViolation(TEXT["data.characters.erebus.resolve_fate.1"])
    engine._clear_pending_choice()
    option = next(
        (
            value for value in engine._pending_ability
            if value["number"] == card_number
        ),
        None,
    )
    if not option:
        raise RuleViolation(TEXT["data.characters.erebus.resolve_fate.2"])
    selected_orientation = option["orientation"]
    if sacrifice_item_id:
        item = ITEMS.get(sacrifice_item_id)
        if (
            not item
            or item.quality < 3
            or engine.state.house.inventory.count(sacrifice_item_id) <= 0
        ):
            raise RuleViolation(TEXT["data.characters.erebus.resolve_fate.3"])
        if orientation not in {"upright", "reversed"}:
            raise RuleViolation(TEXT["data.characters.erebus.resolve_fate.4"])
        engine._take_item(sacrifice_item_id)
        selected_orientation = orientation
    elif option.get("requires_orientation"):
        if orientation not in {"upright", "reversed"}:
            raise RuleViolation(TEXT["data.characters.erebus.resolve_fate.5"])
        selected_orientation = orientation
    if selected_orientation not in {"upright", "reversed"}:
        raise RuleViolation(TEXT["data.characters.erebus.resolve_fate.6"])
    upright = selected_orientation == "upright"
    engine._pending_ability.clear()
    engine._pending_interaction = None
    apply_fate_card(engine, card_number, upright, target_id)
    engine._record_action(
        "fate", actor=actor.id, card=card_number,
        orientation=selected_orientation, target=target_id,
    )
    card = FATE[card_number]
    engine._log(
        TEXT["data.characters.erebus.resolve_fate.7"].format(p1=card_number, p2=card.name, p3='正位' if upright else '逆位', p4=card.upright if upright else card.reversed)
    )


# ---------------------------------------------------------------- fate skills
# 每张命运牌是一个「技能」（正/逆位在函数内分支）；命运抽牌是调用它们的固定技能。

def _card_0(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """愚者：正位回溯守卫；逆位额外伪人到访。"""
    if upright:
        engine._set_global_event("guard.rewind", 1.0, 99)
        for tenant in engine.home_tenants():
            if tenant.character_id == "erebus":
                tenant.marks.remove_value("fate", 0.0)
                break
        return
    if engine._pseudo_enters_house():
        engine._set_global_event("visitor.extra_pseudo", 1.0, 2)
        engine.state.world.visitors.next_pseudo_turn = min(
            engine.state.world.visitors.next_pseudo_turn,
            engine.state.flow.turn + 1,
        )
    else:
        engine._log(TEXT["data.characters.erebus._card_0.1"])


def _card_1(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """魔术师：下次访客转为补给（正位常规 / 逆位仅白色物品）。"""
    engine._set_global_event("visitor.supply", 1.0 if upright else 2.0, 99)


def _card_2(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """女祭司：回合末理智消耗倍率（正位 0、逆位 2）。"""
    engine._set_global_event("fate.priestess", 0.0 if upright else 2.0, 1)


def _card_3(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """女皇：全员回复/失去 5 生命。"""
    for tenant in engine.home_tenants():
        (engine._restore_health if upright else engine._loss_health)(tenant, 5, TEXT["data.characters.erebus._card_3.1"])


def _card_4(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """皇帝：突破阈值调整（正位 -1、逆位 +1）。"""
    engine._set_global_event("breakthrough.adjust", -1.0 if upright else 1.0, 99)


def _card_5(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """教皇：消沉乘区（正位 ×0.85、逆位 ×1.15）。"""
    for tenant in engine.home_tenants():
        tenant.depression *= .85 if upright else 1.15


def _card_6(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """恋人：正位额外访客、逆位取消下一次访客。"""
    if upright:
        engine._set_global_event("visitor.extra", 1.0, 2)
    else:
        engine._set_global_event("visitor.suppress", 1.0, 2)


def _card_7(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """战车：遭遇率倍率（正位 0.5、逆位 1.5）。"""
    engine._set_global_event("encounter.rate.multiplier", .5 if upright else 1.5, 1)


def _card_8(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """力量：正位减轻创伤/紊乱，逆位加重。"""
    for tenant in engine.home_tenants():
        for condition in (tenant.trauma, tenant.disorder):
            if upright:
                engine._recover_condition(condition, 1, 1)
            else:
                engine._add_condition(tenant, condition, 1, 1, TEXT["data.characters.erebus._card_8.1"])


def _card_9(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """隐者：正位把伪人印记砍到 0；逆位把伪人印记补充到 20。"""
    target = 0 if upright else 20
    if engine._set_pseudo_marks(target):
        engine._log(TEXT["data.characters.erebus._card_9.1"].format(p1=target))


def _card_10(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """命运之轮：允许屋主决定正逆；逆位隐藏牌名。"""
    actor = next(
        (value for value in engine.home_tenants() if value.character_id == "erebus"),
        None,
    )
    if actor is None:
        return
    actor.set_status("wheel_choice", intensity=1, layers=99)
    if not upright:
        actor.set_status("wheel_hidden", intensity=1, layers=99)


def _card_11(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """正义：正位驱逐伪人替身；逆位随机驱逐一名房客。"""
    if upright:
        # 只对"已经在屋内"的伪人生效：`infiltrator_id` 在绑架时就写入，人可能还在外。
        if engine.pseudo_in_house():
            handler = engine._pseudo_handler("expel_infiltrator")
            if handler is not None:
                handler(engine, TEXT["data.characters.erebus._card_11.1"])
        else:
            engine._log(TEXT["data.characters.erebus._card_11.2"])
        return
    home = engine.home_tenants()
    if home:
        engine._expel_tenant(
            engine._rng(_event_id("fate.justice")).choice(home), TEXT["data.characters.erebus._card_11.3"]
        )


def _card_12(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """倒吊人：正位生命消耗转理智流失；逆位理智消耗转生命流失。"""
    if upright:
        engine._set_global_event("fate.hanged.health_to_sanity", 1.0, 1)
    else:
        engine._set_global_event("fate.hanged.sanity_to_health", 1.0, 1)


def _card_13(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """死神：正位净化目标全部状态；逆位给随机房客施加休克。"""
    if upright:
        target = engine._require_home_tenant(target_id)
        target.trauma.clear()
        target.disorder.clear()
        target.shock = target.shock_layers = 0
        for condition in target.conditions.values():
            condition.clear()
        return
    home = engine.home_tenants()
    if home:
        target = engine._rng(_event_id("fate.death")).choice(home)
        target.shock = max(1, target.shock)
        target.shock_layers = max(2, target.shock_layers)


def _card_14(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """节制：易损/耐久倍率（正位 0.5、逆位 2.0）。"""
    engine._set_global_event("item.fragile.multiplier", .5 if upright else 2.0, 1)
    engine._set_global_event("item.durability.multiplier", .5 if upright else 2.0, 1)


def _card_15(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """恶魔：搜索时运 ±3。"""
    engine._set_global_event("search.fortune_delta", 3.0 if upright else -3.0, 1)


def _card_16(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """塔：给全员施加倒吊人（顺/逆位）。"""
    status_id = "hanged_man_upright" if upright else "hanged_man_reversed"
    for tenant in engine.home_tenants():
        tenant.set_status(status_id, intensity=1, layers=99)


def _card_17(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """星星：搜索回合修正（正位 -2、逆位 +2）。"""
    engine._set_global_event("search.turn_delta", -2.0 if upright else 2.0, 1)


def _card_18(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """月亮：最高理智者 -10（正位）或最低理智者 +10（逆位）。"""
    home = engine.home_tenants()
    if not home:
        return
    target = (
        max(home, key=lambda value: (value.sanity, value.id))
        if upright
        else min(home, key=lambda value: (value.sanity, value.id))
    )
    (engine._consume_sanity if upright else engine._restore_sanity)(target, 10, TEXT["data.characters.erebus._card_18.1"])


def _card_19(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """太阳：正位自动识破；逆位锁定假信息概率。"""
    if upright:
        engine._set_global_event("fate.auto_discern", 0.0, 3)
        for info in list(engine.state.house.information):
            if info.status == "pending":
                engine._verify_information_object(info)
    else:
        engine._set_global_event("information.false_lock", 0.0, 3)


def _card_20(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """审判：正位召回人类原型；逆位禁用随机房客能力。"""
    if upright:
        from weiren_game.data import PSEUDOS

        counterpart = PSEUDOS[engine.state.pseudo_state.scenario_id].human_character_id
        if (
            counterpart not in engine.state.world.visitors.visitor_pool
            and not any(
                tenant.character_id == counterpart
                for tenant in engine.living_tenants()
            )
        ):
            engine.state.world.visitors.visitor_pool.insert(0, counterpart)
        return
    home = engine.home_tenants()
    if home:
        target = engine._rng(_event_id("fate.judgement")).choice(home)
        target.abilities_disabled = target.passives_disabled = True


def _card_21(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """世界：压制伪人 5 回合并使命运抽牌失效。"""
    engine._suppress_pseudo(5)
    for tenant in engine.home_tenants():
        if tenant.character_id != "erebus":
            continue
        ability = tenant.ability_state("draw_fate")
        if ability is not None:
            ability.disabled = True
        tenant.set_status("great_seal", intensity=1, layers=99)
        break


# 牌号 → 技能函数（每个函数内含正/逆位实现，即 22×2=44 个效果）。
FATE_SKILLS: dict[int, object] = {
    0: _card_0, 1: _card_1, 2: _card_2, 3: _card_3, 4: _card_4,
    5: _card_5, 6: _card_6, 7: _card_7, 8: _card_8, 9: _card_9,
    10: _card_10, 11: _card_11, 12: _card_12, 13: _card_13, 14: _card_14,
    15: _card_15, 16: _card_16, 17: _card_17, 18: _card_18, 19: _card_19,
    20: _card_20, 21: _card_21,
}


def apply_fate_card(engine: EngineProtocol, number: int, upright: bool, target_id: str | None) -> None:
    """按牌号与正逆位调用对应的命运牌技能。"""
    handler = FATE_SKILLS.get(number)
    if handler is not None:
        handler(engine, upright, target_id)


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "draw_fate": (
        lambda engine, actor, **kwargs: draw_fate(engine, actor.id)
    ),
}


# ---------------------------------------------------------------- runtime
def sun_auto_discern(engine: object, info: object) -> bool:
    """太阳（正位）：激活期间新生成的信息自动被识破。"""
    if engine.state.world.global_events.active("fate.auto_discern"):
        engine._verify_information_object(info)
        return True
    return False


def on_pending_information(engine: object, info: object) -> None:
    """新待验证信息生成后的厄瑞玻斯被动（太阳识破 / 占卜直觉）。"""
    if sun_auto_discern(engine, info):
        return
    maybe_discern_pending(engine, info)


INFORMATION_CREATED = on_pending_information


def apply_health_consume_conversion(
    engine: object, tenant: object, amount: float, source: str
):
    """倒吊人（顺位）：生命消耗改由理智流失承担；未激活返回 None。"""
    if engine.state.world.global_events.active("fate.hanged.health_to_sanity"):
        return engine._loss_sanity(tenant, amount, TEXT["data.characters.erebus.apply_health_consume_conversion.1"].format(p1=source))
    return None


def apply_sanity_consume_conversion(
    engine: object, tenant: object, amount: float, source: str
):
    """倒吊人（逆位）：理智消耗改由生命流失承担；未激活返回 None。"""
    if engine.state.world.global_events.active("fate.hanged.sanity_to_health"):
        return engine._loss_health(tenant, amount, TEXT["data.characters.erebus.apply_sanity_consume_conversion.1"].format(p1=source))
    return None


def next_health_consume_multiplier(engine: object, tenant: object) -> float:
    """倒吊人生命消耗倍率（顺位 1.5 / 逆位 3.0），触发后强度 -1。"""
    for status_id, multiplier in (
        ("hanged_man_upright", 1.5),
        ("hanged_man_reversed", 3.0),
    ):
        debuff = tenant.condition(status_id)
        if not debuff.active:
            continue
        remaining = debuff.intensity - 1
        if remaining <= 0:
            tenant.clear_status(status_id)
        else:
            tenant.set_status(status_id, intensity=remaining, layers=debuff.layers)
        return multiplier
    return 1.0


HOOKS = {
    "value.health_consume.convert": apply_health_consume_conversion,
    "value.health_consume.multiplier": next_health_consume_multiplier,
    "value.sanity_consume.convert": apply_sanity_consume_conversion,
}


def _priestess_sanity_modifier(context: object):
    """女祭司：回合末理智消耗（正位收束 0 / 逆位最终百分比 +100%）。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    value = engine._global_event_value("fate.priestess", 1.0)
    if value == 0.0:
        yield spec("sanityConsume").path("turn_end_consume").final().max(0).source("ability", "erebus", "fate", "priestess")
    elif value > 1.0:
        yield spec("sanityConsume").path("turn_end_consume").final().percent(value - 1.0).source("ability", "erebus", "fate", "priestess")


from weiren_game.modifier_rules import register_modifier_provider as _regp
_regp("sanityConsume", _priestess_sanity_modifier)

def _hanged_consume_modifier(context: object):
    """高塔/倒吊人：生命消耗乘区（顺 1.5 / 逆 3.0），触发后强度 -1。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    for status_id, multiplier in (("hanged_man_upright", 1.5), ("hanged_man_reversed", 3.0)):
        debuff = tenant.condition(status_id)
        if not debuff.active:
            continue
        remaining = debuff.intensity - 1
        if remaining <= 0:
            tenant.clear_status(status_id)
        else:
            debuff.intensity = remaining
        yield spec("healthConsume").path("consume").mul(multiplier).source("ability", "erebus", "fate", "tower")
        break


from weiren_game.modifier_rules import register_modifier_provider as _regh
_regh("healthConsume", _hanged_consume_modifier)


# ---------------------------------------------------------------- 内容自描述
def _fate_search_modifier(context: object):
    """星星/恶魔：搜索回合与时运（读运行时修饰值）。"""
    from weiren_game.data import EVENT_IDS
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    turns = engine._global_event_value("search.turn_delta", 0.0)
    if turns:
        yield spec("search").path("turn").flat(int(turns)).source("ability", "erebus", "fate")
    fortune = engine._global_event_value("search.fortune_delta", 0.0)
    if fortune:
        positive = engine._rng(EVENT_IDS["modifier.fortune_roll"]).random() < .75
        yield (
            spec("search").path("luck").flat(int(fortune if positive else -fortune))
            .source("ability", "erebus", "fate")
        )


register_modifier_provider("search", _fate_search_modifier)


def codex_summary(engine):
    """图鉴统计行：由引擎汇总各内容的自描述。"""
    return [TEXT["data.characters.erebus.codex_summary.1"].format(p1=len(FATE))]


CODEX_SUMMARY = codex_summary


def codex_section(engine) -> None:
    """图鉴详情：命运抽牌牌组。"""
    print(TEXT["data.characters.erebus.codex_section.1"])
    for number, card in FATE.items():
        print(f"  {number:02d}. {card.name}")
        print(TEXT["data.characters.erebus.codex_section.2"].format(p1=card.upright))
        print(TEXT["data.characters.erebus.codex_section.3"].format(p1=card.reversed))


CODEX_SECTION = codex_section


def resolve_interaction(engine) -> None:
    """命运抽牌的交互结算 UI（与前端无关，经 engine.ui 交互）。"""
    from weiren_game.content import CONTENT

    ui = engine.ui
    items = CONTENT.items()
    options = engine._pending_ability
    if not options:
        return
    actor_id = next(
        (tenant.id for tenant in engine.home_tenants() if tenant.character_id == "erebus"),
        None,
    )
    requires_orientation = any(option.get("requires_orientation") for option in options)
    hidden = any(option.get("hidden") for option in options)

    def _label(option):
        number = option["number"]
        name = TEXT["data.characters.erebus._label.1"] if hidden else f"{number}. {FATE[number].name}"
        orientation = (
            TEXT["data.characters.erebus._label.2"] if option["orientation"] is None
            else TEXT["data.characters.erebus._label.3"] if option["orientation"] == "upright" else TEXT["data.characters.erebus._label.4"]
        )
        return f"{name}（{orientation}）"

    card_options = [
        (option["number"], f"{index}. {_label(option)}")
        for index, option in enumerate(options, 1)
    ]
    if ui.confirm(TEXT["data.characters.erebus.resolve_interaction.1"]):
        cancel_fate(engine, actor_id)
        return
    forced_orientation = None
    if requires_orientation:
        forced_orientation = ui.choose(
            TEXT["data.characters.erebus.resolve_interaction.2"],
            [("upright", TEXT["data.characters.erebus.resolve_interaction.3"]), ("reversed", TEXT["data.characters.erebus.resolve_interaction.4"])],
        )
        if hidden:
            ui.message(TEXT["data.characters.erebus.resolve_interaction.5"])
            card_options = [
                (option["number"], f"{index}. {FATE[option['number']].name}（{'正位' if forced_orientation == 'upright' else '逆位'}）")
                for index, option in enumerate(options, 1)
            ]
    card_number = ui.choose(TEXT["data.characters.erebus.resolve_interaction.6"], card_options)
    orientation = forced_orientation
    sacrifice = None
    premium = [
        key for key in dict.fromkeys(
            value.item_id for value in engine.state.house.inventory
        )
        if items[key].quality >= 3
    ]
    if premium and ui.confirm(TEXT["data.characters.erebus.resolve_interaction.7"]):
        sacrifice = ui.choose(TEXT["data.characters.erebus.resolve_interaction.8"], [(key, items[key].name) for key in premium])
        orientation = ui.choose(TEXT["data.characters.erebus.resolve_interaction.9"], [("upright", TEXT["data.characters.erebus.resolve_interaction.10"]), ("reversed", TEXT["data.characters.erebus.resolve_interaction.11"])])
    target_id = None
    selected = next(value for value in options if value["number"] == card_number)
    effective_orientation = orientation or selected["orientation"]
    if card_number == 13 and effective_orientation == "upright":
        target_id = ui.choose_target(engine)
    resolve_fate(
        engine, actor_id, card_number,
        orientation=orientation, target_id=target_id, sacrifice_item_id=sacrifice,
    )


INTERACTIONS = {"draw_fate": resolve_interaction}


def _erebus_of(engine):
    """返回屋内的厄瑞玻斯（用于命运抽牌结算）。"""
    return next((t for t in engine.home_tenants() if t.character_id == "erebus"), None)


def build_fate_view(engine) -> dict | None:
    """命运抽牌的通用待处理视图（内容自描述：提示 / 选项 / 是否可取消）。"""
    options = getattr(engine, "_pending_ability", None)
    if not options:
        return None
    hidden = any(option.get("hidden") for option in options)
    # 初始只给牌面（不揭示正/逆位）：正逆位文本供悬浮查看，方向在后续步骤决定。
    views = []
    for option in options:
        card = FATE[int(option["number"])]
        views.append({
            "number": int(option["number"]),
            "name": TEXT["data.characters.erebus.build_fate_view.1"] if hidden else card.name,
            "display": TEXT["data.characters.erebus.build_fate_view.2"] if hidden else f"{int(option['number']):02d} {card.name}",
            # 牌面符号：内容自带图形（见 erebus_fate_symbols.py），前端画在卡片的图标位上。
            "svg": "" if hidden else FATE_SYMBOLS.get(int(option["number"]), ""),
            "upright": card.upright,
            "reversed": card.reversed,
            "hidden": bool(hidden),
            "orientation": option["orientation"],
            "requires_orientation": bool(option.get("requires_orientation")),
        })
    required = [i for i, option in enumerate(options) if option.get("requires_orientation")]
    choices = [["upright", TEXT["data.characters.erebus.build_fate_view.3"]], ["reversed", TEXT["data.characters.erebus.build_fate_view.4"]]]
    # 需要选人的牌 + 候选（只给 id 与名字；头像/生命/理智由 web_ui 投影成房客卡）。
    needs = [int(option["number"]) for option in options if int(option["number"]) in NEEDS_TARGET]
    return {
        "prompt": TEXT["data.characters.erebus.build_fate_view.5"],
        "options": views,
        "title": TEXT["data.characters.erebus.build_fate_view.6"],
        "settle": TEXT["data.characters.erebus.build_fate_view.7"],
        "cancel_prompt": TEXT["data.characters.erebus.build_fate_view.8"],
        "cancel": TEXT["data.characters.erebus.build_fate_view.9"],
        # 需要玩家指定正逆位的选项（如「命运之轮」）：方向选择独立于上交物资。
        "orientation": {
            "required": required, "choices": choices,
            # 方向也要符号：前端那一步要和"选牌"同一套卡片，两张卡各配一个符号。
            "symbols": dict(ORIENTATION_SYMBOLS),
            "prompt": TEXT["data.characters.erebus.build_fate_view.10"],
        },
        # 可选的"上交物资改定牌面"规格（内容自描述，前端通用渲染）。
        "submit": {
            "title": TEXT["data.characters.erebus.build_fate_view.11"],
            "label": TEXT["data.characters.erebus.build_fate_view.12"],
            "min_quality": 3,
            "choices": choices,
        },
        # 上供那一步的出口：**槽里放了东西就是上供，空着直接继续就是不上供**——
        # 不再先问一句"是否上供"（那会把一件事拆成两个窗口）。
        "proceed": TEXT["data.characters.erebus.build_fate_view.13"],
        "proceed_hint": TEXT["data.characters.erebus.build_fate_view.14"],
        # 需要指定房客的牌：前端在"方向之后、揭晓之前"插一步，用现成的房客卡来选。
        "target": {
            "numbers": needs,
            "required_by": {str(number): list(NEEDS_TARGET[number]) for number in needs},
            "prompt": TEXT["data.characters.erebus.build_fate_view.15"],
            "candidates": [
                {"value": tenant.id, "label": engine.character(tenant).name}
                for tenant in engine.home_tenants()
            ],
        },
        "upright_label": TEXT["data.characters.erebus.build_fate_view.16"], "reversed_label": TEXT["data.characters.erebus.build_fate_view.17"],
    }


def resolve_fate_view(engine, value) -> None:
    """value 可以是选项下标，或 ``{"index","item_id","orientation"}``；None 表示取消。"""
    from weiren_game.exceptions import RuleViolation

    actor = _erebus_of(engine)
    options = getattr(engine, "_pending_ability", None)
    if actor is None or not options:
        return
    if value is None:
        cancel_fate(engine, actor.id)
        return
    index = value
    item_id = None
    orientation = None
    target_id = None
    if isinstance(value, dict):
        index = value.get("index")
        item_id = value.get("item_id") or None
        orientation = value.get("orientation") or None
        target_id = value.get("target_id") or None
    if index is None:
        raise RuleViolation(TEXT["data.characters.erebus.resolve_fate_view.1"])
    option = options[int(index)]
    if item_id:
        # 上交物资：必须指定方向（由 resolve_fate 校验）。
        chosen = orientation
    elif option.get("requires_orientation"):
        # 命运之轮等：允许（且必须）指定方向，无需物资。
        chosen = orientation
    else:
        chosen = option["orientation"]
    resolve_fate(
        engine, actor.id, int(option["number"]),
        orientation=chosen, target_id=target_id, sacrifice_item_id=item_id,
    )


PENDING_VIEW = (build_fate_view, resolve_fate_view)

# 界面头像图标（内容自声明）。
AVATAR = "i-av7"


def CODEX_EXTRA() -> list:
    """图鉴补充：厄瑞玻斯的命运牌 —— 先是 22 张的**牌面符号**（缺的留空，方便核对），再是正/逆位表。"""
    cards = sorted(FATE.values(), key=lambda c: c.number)
    symbols = [
        {"label": f"{card.number:02d} {card.name}", "svg": FATE_SYMBOLS.get(card.number, "")}
        for card in cards
    ]
    # 顺手把两个方向符号也摆进同一面墙（同一套画法，便于一起核对）。
    symbols += [
        {"label": TEXT["data.characters.erebus.CODEX_EXTRA.1"].format(p1=label), "svg": ORIENTATION_SYMBOLS.get(key, "")}
        for key, label in (("upright", TEXT["data.characters.erebus.CODEX_EXTRA.2"]), ("reversed", TEXT["data.characters.erebus.CODEX_EXTRA.3"]))
    ]
    rows = [[f"{card.number:02d} {card.name}", card.upright, card.reversed] for card in cards]
    return [
        {"title": TEXT["data.characters.erebus.CODEX_EXTRA.4"], "symbols": symbols},
        {"title": TEXT["data.characters.erebus.CODEX_EXTRA.5"], "table": {"columns": [TEXT["data.characters.erebus.CODEX_EXTRA.6"], TEXT["data.characters.erebus.CODEX_EXTRA.7"], TEXT["data.characters.erebus.CODEX_EXTRA.8"]], "rows": rows}},
    ]

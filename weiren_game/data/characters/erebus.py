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


@dataclass(frozen=True)
class FateCard:
    """一张命运牌的正/逆位文本（仅厄瑞玻斯使用，随本模块一起增减）。"""

    number: int
    name: str
    upright: str
    reversed: str

# 命运牌带来的全局事件：id / 名称 / 图标 / 点开可见的说明（内容层填写）。
_FATE_EVENTS = (
    ("guard.rewind", "愚者·回溯守卫", "i-clock",
     "危机再临一次时，退回本回合开始前的状态。"),
    ("visitor.extra_pseudo", "愚者逆·额外伪人来访", "i-person",
     "本回合伪人还会再来一次。"),
    ("visitor.supply", "魔术师·神秘的补给", "i-bag",
     "下一位来访者改为送来一批补给。"),
    ("fate.priestess", "女祭司·理智倍率", "i-emotion",
     "本回合结算时，理智消耗被命运牌改写。"),
    ("breakthrough.adjust", "皇帝·突破调整", "i-seal",
     "本回合伪人的突破判定被改写。"),
    ("visitor.extra", "恋人正·额外访客", "i-person",
     "本回合额外增加一名访客。"),
    ("visitor.suppress", "恋人逆·访客压制", "i-hand",
     "下一次访客来访被取消。"),
    ("encounter.rate.multiplier", "战车·遭遇率", "i-target",
     "本回合搜索途中遭遇伪人的概率被改写。"),
    ("fate.hanged.health_to_sanity", "倒吊人顺·生命转理智", "i-emotion",
     "本回合结束时，生命与理智互相置换。"),
    ("fate.hanged.sanity_to_health", "倒吊人逆·理智转生命", "i-cross",
     "本回合结束时，理智反过来补充生命。"),
    ("item.fragile.multiplier", "节制·易损倍率", "i-gear",
     "本回合物品的易损概率被改写。"),
    ("item.durability.multiplier", "节制·耐久倍率", "i-tool",
     "本回合物品的耐久消耗被改写。"),
    ("search.fortune_delta", "恶魔·搜索时运", "i-search",
     "本回合搜索的时运提高或降低。"),
    ("search.turn_delta", "星星·搜索回合", "i-clock",
     "本回合外出搜索所需的回合数被改写。"),
    ("fate.auto_discern", "太阳正·自动识破", "i-info",
     "新出现的信息会被立刻核实。"),
    ("information.false_lock", "太阳逆·假信息锁定", "i-note",
     "这段时间里出现的信息更可能是假的。"),
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
        "欺骗世界",
        "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description="用一个弥天大谎，把自己从死亡里暂时摘出来。")
)
register_status_definition(
    StatusDefinition(
        "great_seal",
        "伟大的封印",
        "other",
        shown=frozenset({"icon", "description"}),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description="牌堆已经封死，命运不再给出第二次机会。")
)
register_status_definition(
    StatusDefinition(
        "wheel_choice",
        "命运之轮·改定",
        "other",
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description="命运的指针停在你手上，由你决定这张牌的正与逆。")
)
register_status_definition(
    StatusDefinition(
        "wheel_hidden",
        "命运之轮·隐匿",
        "other",
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description="牌面被雾气蒙住，只有翻开的瞬间才知道结局。")
)
register_status_definition(
    StatusDefinition(
        "hanged_man_upright",
        "倒吊人（顺位）",
        "other",
        intensity_max=3,
        layers_max=99,
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description="承受的一切，暂时从身体挪去了别处。")
)
register_status_definition(
    StatusDefinition(
        "hanged_man_reversed",
        "倒吊人（逆位）",
        "other",
        intensity_max=3,
        layers_max=99,
        shown=frozenset(),
        source_id="ability:draw_fate@erebus",
        permanent=True,
     description="精神的重量，被硬生生压回到血肉之躯上。")
)

CHARACTER = CharacterDefinition(
    "erebus", 7, "厄瑞玻斯", "17岁白发女高中生，热衷于占卜术。",
    "suspicious", "steady", 3, ("高中生", "16-18岁", "女性", "白发", "神秘学研究者"),
    (A("divination_instinct", "占卜直觉", "厄瑞玻斯在屋内时，获得待验证信息时，有5%可能识破该信息。"),),
    # 限制交给 chips（STYLE §12 规则 3）：`per_turn=True` 就是"每回合 1 次"的实现，正文不再重复写。
    (A("draw_fate", "命运抽牌",
       "· 从命运牌堆随机抽 **3 张**不同的牌，各自 **50%** 确定为【正位】或【逆位】。"
       "· 屋主从中选 **1 张**并立即结算。"
       "· 结算前可**上交**一件紫色及以上品质的物资，改定该牌的【正位】/【逆位】。"
       "· 结算前可**反悔**取消本次选牌：最大生命上限依次降低 **15 / 25 / 35**；累计反悔 **3 次**后，本局该能力失效。",
       "fate", chips=("每回合 1 次",), per_turn=True),),
)

# 隐藏实现：厄瑞玻斯的 22 张命运牌以印记实例表示（每个实例 value=牌号）。
MARKS = (
    MarkDefinition(
        id="fate",
        label="命运牌-厄瑞玻斯",
        acquisition="角色自带 22 张（隐藏机制，不对外展示）。",
        minimum=0,
        maximum=22,
        externally_locked=True,
     description="一小叠只属于它的命运，翻开前谁也不知道正逆。"),
)


def detail_slot(engine: EngineProtocol, tenant: object) -> list[dict]:
    """详情页小面板：命运牌（按**张数**计，印记实例存的是牌号）+「伟大的封印」期间的明月。"""
    cards = len(tenant.marks.instances_of("fate"))
    rows: list[dict] = [{
        "kind": "bar",
        "label": "命运牌",
        "value": cards,
        "max": 22,
        "hint": "牌堆随抽牌与牌面效果增减。",
    }]
    if tenant.condition("great_seal").active:
        rows.append({
            "kind": "glyph",
            # 角色自带图形（不借资源包贴图）：月与星点，随主题色描线。
            "svg": ('<circle cx="12" cy="12" r="8"/><circle cx="9.6" cy="9.8" r="1"/>'
                    '<circle cx="14" cy="14.4" r="1.4"/><circle cx="14.6" cy="8.6" r=".8"/>'
                    '<path d="M12 4v16"/>'),
            "label": "明月",
            "hint": "厄瑞玻斯-正在杀出月球",
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
    0: FateCard(0, "愚者", "避免下一次突破，回溯到该回合开始并取消伪人来访；之后移出牌堆。", "下一回合伪人连续来访2次。"),
    1: FateCard(1, "魔术师", "下一位访客替换为神秘补给。", "下一位访客也替换为神秘补给（原稿带问号，按字面执行）。"),
    2: FateCard(2, "女祭司", "本回合所有房客回合末理智消耗为0。", "本回合所有房客回合末理智消耗+100%。"),
    3: FateCard(3, "女皇", "所有房客回复5生命。", "所有房客流失5生命。"),
    4: FateCard(4, "皇帝", "伪人下一次来访的突破难度降低。", "伪人下一次来访的突破难度提高。"),
    5: FateCard(5, "教皇", "所有房客消沉值-15%。", "所有房客消沉值+15%。"),
    6: FateCard(6, "恋人", "下一回合额外来访一人。", "取消下一次访客来访。"),
    7: FateCard(7, "战车", "本回合搜索遭遇伪人概率×50%。", "本回合搜索遭遇伪人概率×150%。"),
    8: FateCard(8, "力量", "所有房客创伤与紊乱-1/-1。", "所有房客创伤与紊乱+1/+1。"),
    9: FateCard(9, "隐者", "将伪人的印记削减到 0。", "将伪人的印记补充到 20。"),
    10: FateCard(10, "命运之轮", "下一次抽牌可指定牌面方向。", "下一次抽牌在指定方向前隐藏牌名。"),
    11: FateCard(11, "正义", "立即驱逐一名屋内伪人。", "立即驱逐一名随机房客。"),
    12: FateCard(12, "倒吊人", "本回合生命消耗转化为等量理智流失。", "本回合理智消耗转化为等量生命流失。"),
    13: FateCard(13, "死神", "指定一名房客，移除全部状态。", "随机房客获得1强度、2层休克。"),
    14: FateCard(14, "节制", "本回合易损概率-50%，耐久消耗-50%。", "本回合易损概率+100%，耐久消耗+100%。"),
    15: FateCard(15, "恶魔", "本回合搜索75%时运+3，否则-3。", "本回合搜索75%时运-3，否则+3。"),
    16: FateCard(16, "高塔", "全员下一次生命消耗+50%。", "全员下一次生命消耗+200%。"),
    17: FateCard(17, "星星", "本回合搜索回合数-2。", "本回合搜索回合数+2。"),
    18: FateCard(18, "月亮", "屋内理智最高者-10理智。", "屋内理智最低者+10理智。"),
    19: FateCard(19, "太阳", "接下来3回合待验证信息直接被识破。", "接下来3回合虚假信息增多且无法验证。"),
    20: FateCard(20, "审判", "初访后可抽；后续访客中加入伪人的人类对应形态。", "随机房客的主动与被动能力整局失效。"),
    21: FateCard(21, "世界", "伪人5回合不能行动，本局命运抽牌失效。", "伪人5回合不能行动，本局命运抽牌失效。"),
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
        raise RuleViolation("只有厄瑞玻斯可以发动命运抽牌。")
    ability = actor.ability_state("draw_fate")
    if ability is not None and ability.disabled:
        raise RuleViolation("本局命运牌堆已经失效。")
    if engine._pending_ability:
        raise RuleViolation("必须先处理当前抽出的牌。")
    deck = [
        int(value.value) for value in actor.marks.instances_of("fate")
        if int(value.value) != 20 or engine.state.pseudo_state.revealed
    ]
    if len(deck) < 3:
        raise RuleViolation("牌堆中可用牌不足三张。")
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
        ("未知牌" if hidden else FATE[value["number"]].name)
        + (
            "（方向待指定）" if value["orientation"] is None
            else "（正位）" if value["orientation"] == "upright" else "（逆位）"
        )
        for value in options
    )
    engine._log(f"命运抽牌：{shown}。请选择其中一张结算，也可反悔。")
    return [dict(value) for value in options]


def cancel_fate(engine: EngineProtocol, actor_id: str) -> None:
    """反悔命运抽牌：降低最大生命并累计反悔次数。"""
    from weiren_game.exceptions import RuleViolation

    actor = engine._require_home_tenant(actor_id)
    engine._clear_pending_choice()
    if actor.character_id != "erebus" or not engine._pending_ability:
        raise RuleViolation("当前没有可反悔的命运抽牌。")
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
    engine._log(f"厄瑞玻斯反悔：最大生命上限降低{loss}；累计{count}/3次。")


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
        raise RuleViolation("只有厄瑞玻斯可以结算命运牌。")
    engine._clear_pending_choice()
    option = next(
        (
            value for value in engine._pending_ability
            if value["number"] == card_number
        ),
        None,
    )
    if not option:
        raise RuleViolation("这张牌不在本次抽取结果中。")
    selected_orientation = option["orientation"]
    if sacrifice_item_id:
        item = ITEMS.get(sacrifice_item_id)
        if (
            not item
            or item.quality < 3
            or engine.state.house.inventory.count(sacrifice_item_id) <= 0
        ):
            raise RuleViolation("改定牌面需要交出一件紫色及以上物资。")
        if orientation not in {"upright", "reversed"}:
            raise RuleViolation("交出物资后必须指定upright或reversed。")
        engine._take_item(sacrifice_item_id)
        selected_orientation = orientation
    elif option.get("requires_orientation"):
        if orientation not in {"upright", "reversed"}:
            raise RuleViolation("命运之轮要求先指定本次抽牌的正位或逆位。")
        selected_orientation = orientation
    if selected_orientation not in {"upright", "reversed"}:
        raise RuleViolation("这张牌还没有确定正逆位。")
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
        f"命运牌结算：{card_number}. {card.name}"
        f"（{'正位' if upright else '逆位'}）——{card.upright if upright else card.reversed}"
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
        engine._log("本局伪人没有到访行为，愚人逆位的「额外到访」未生效。")


def _card_1(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """魔术师：下次访客转为补给（正位常规 / 逆位仅白色物品）。"""
    engine._set_global_event("visitor.supply", 1.0 if upright else 2.0, 99)


def _card_2(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """女祭司：回合末理智消耗倍率（正位 0、逆位 2）。"""
    engine._set_global_event("fate.priestess", 0.0 if upright else 2.0, 1)


def _card_3(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """女皇：全员回复/失去 5 生命。"""
    for tenant in engine.home_tenants():
        (engine._restore_health if upright else engine._loss_health)(tenant, 5, "女皇")


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
                engine._add_condition(tenant, condition, 1, 1, "力量逆位")


def _card_9(engine: EngineProtocol, upright: bool, target_id: str | None) -> None:
    """隐者：正位把伪人印记砍到 0；逆位把伪人印记补充到 20。"""
    target = 0 if upright else 20
    if engine._set_pseudo_marks(target):
        engine._log(f"隐者将伪人的印记改写为 {target:g}。")


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
                handler(engine, "正义")
        else:
            engine._log("屋内目前没有可被正义驱逐的伪人。")
        return
    home = engine.home_tenants()
    if home:
        engine._expel_tenant(
            engine._rng(_event_id("fate.justice")).choice(home), "正义逆位"
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
    (engine._consume_sanity if upright else engine._restore_sanity)(target, 10, "月亮")


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
        return engine._loss_sanity(tenant, amount, f"{source}（倒吊人）")
    return None


def apply_sanity_consume_conversion(
    engine: object, tenant: object, amount: float, source: str
):
    """倒吊人（逆位）：理智消耗改由生命流失承担；未激活返回 None。"""
    if engine.state.world.global_events.active("fate.hanged.sanity_to_health"):
        return engine._loss_health(tenant, amount, f"{source}（倒吊人）")
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
        yield spec("sanityConsume").path("回合末消耗").final().max(0).source("角色技能", "厄瑞玻斯", "命运", "女祭司")
    elif value > 1.0:
        yield spec("sanityConsume").path("回合末消耗").final().percent(value - 1.0).source("角色技能", "厄瑞玻斯", "命运", "女祭司")


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
        yield spec("healthConsume").path("消耗").mul(multiplier).source("角色技能", "厄瑞玻斯", "命运", "高塔")
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
        yield spec("search").path("回合").flat(int(turns)).source("角色技能", "厄瑞玻斯", "命运")
    fortune = engine._global_event_value("search.fortune_delta", 0.0)
    if fortune:
        positive = engine._rng(EVENT_IDS["modifier.fortune_roll"]).random() < .75
        yield (
            spec("search").path("时运").flat(int(fortune if positive else -fortune))
            .source("角色技能", "厄瑞玻斯", "命运")
        )


register_modifier_provider("search", _fate_search_modifier)


def codex_summary(engine):
    """图鉴统计行：由引擎汇总各内容的自描述。"""
    return [f"命运牌 {len(FATE)} 张（厄瑞玻斯）"]


CODEX_SUMMARY = codex_summary


def codex_section(engine) -> None:
    """图鉴详情：命运抽牌牌组。"""
    print("\n命运抽牌（厄瑞玻斯）：")
    for number, card in FATE.items():
        print(f"  {number:02d}. {card.name}")
        print(f"      正位：{card.upright}")
        print(f"      逆位：{card.reversed}")


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
        name = "未知牌" if hidden else f"{number}. {FATE[number].name}"
        orientation = (
            "方向待指定" if option["orientation"] is None
            else "正位" if option["orientation"] == "upright" else "逆位"
        )
        return f"{name}（{orientation}）"

    card_options = [
        (option["number"], f"{index}. {_label(option)}")
        for index, option in enumerate(options, 1)
    ]
    if ui.confirm("是否反悔并取消本次抽牌？"):
        cancel_fate(engine, actor_id)
        return
    forced_orientation = None
    if requires_orientation:
        forced_orientation = ui.choose(
            "命运之轮要求指定本次牌面 > ",
            [("upright", "正位"), ("reversed", "逆位")],
        )
        if hidden:
            ui.message("方向确定后，牌名显现：")
            card_options = [
                (option["number"], f"{index}. {FATE[option['number']].name}（{'正位' if forced_orientation == 'upright' else '逆位'}）")
                for index, option in enumerate(options, 1)
            ]
    card_number = ui.choose("选择一张牌结算 > ", card_options)
    orientation = forced_orientation
    sacrifice = None
    premium = [
        key for key in dict.fromkeys(
            value.item_id for value in engine.state.house.inventory
        )
        if items[key].quality >= 3
    ]
    if premium and ui.confirm("是否交出一件紫色及以上物资来改定所选牌的正逆位？"):
        sacrifice = ui.choose("交出物资 > ", [(key, items[key].name) for key in premium])
        orientation = ui.choose("选择方向 > ", [("upright", "正位"), ("reversed", "逆位")])
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
            "name": "未知牌" if hidden else card.name,
            "display": "未知牌" if hidden else f"{int(option['number']):02d} {card.name}",
            # 牌面符号：内容自带图形（见 erebus_fate_symbols.py），前端画在卡片的图标位上。
            "svg": "" if hidden else FATE_SYMBOLS.get(int(option["number"]), ""),
            "upright": card.upright,
            "reversed": card.reversed,
            "hidden": bool(hidden),
            "orientation": option["orientation"],
            "requires_orientation": bool(option.get("requires_orientation")),
        })
    required = [i for i, option in enumerate(options) if option.get("requires_orientation")]
    choices = [["upright", "正位"], ["reversed", "逆位"]]
    # 需要选人的牌 + 候选（只给 id 与名字；头像/生命/理智由 web_ui 投影成房客卡）。
    needs = [int(option["number"]) for option in options if int(option["number"]) in NEEDS_TARGET]
    return {
        "prompt": "命运抽牌：选择一张结算",
        "options": views,
        "title": "命运抽牌",
        "settle": "结算此牌",
        "cancel_prompt": "是否反悔并取消本次抽牌？",
        "cancel": "反悔取消",
        # 需要玩家指定正逆位的选项（如「命运之轮」）：方向选择独立于上交物资。
        "orientation": {
            "required": required, "choices": choices,
            # 方向也要符号：前端那一步要和"选牌"同一套卡片，两张卡各配一个符号。
            "symbols": dict(ORIENTATION_SYMBOLS),
            "prompt": "请选择这张牌的正位或逆位",
        },
        # 可选的"上交物资改定牌面"规格（内容自描述，前端通用渲染）。
        "submit": {
            "title": "上交物资（可选）",
            "label": "上交一件紫色及以上物资，改定所选牌的正逆位",
            "min_quality": 3,
            "choices": choices,
        },
        # 上供那一步的出口：**槽里放了东西就是上供，空着直接继续就是不上供**——
        # 不再先问一句"是否上供"（那会把一件事拆成两个窗口）。
        "proceed": "继续",
        "proceed_hint": "把物资拖进上面的槽＝上供，可以改定正逆位；直接继续＝不上供。",
        # 需要指定房客的牌：前端在"方向之后、揭晓之前"插一步，用现成的房客卡来选。
        "target": {
            "numbers": needs,
            "required_by": {str(number): list(NEEDS_TARGET[number]) for number in needs},
            "prompt": "选择一名房客",
            "candidates": [
                {"value": tenant.id, "label": engine.character(tenant).name}
                for tenant in engine.home_tenants()
            ],
        },
        "upright_label": "正位", "reversed_label": "逆位",
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
        raise RuleViolation("请选择一张命运牌。")
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
        {"label": f"方向 {label}", "svg": ORIENTATION_SYMBOLS.get(key, "")}
        for key, label in (("upright", "正位"), ("reversed", "逆位"))
    ]
    rows = [[f"{card.number:02d} {card.name}", card.upright, card.reversed] for card in cards]
    return [
        {"title": "牌面符号", "symbols": symbols},
        {"title": "命运牌", "table": {"columns": ["牌", "正位", "逆位"], "rows": rows}},
    ]

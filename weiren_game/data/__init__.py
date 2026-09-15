"""游戏内容包：静态图鉴统一从这里导出。

规则引擎只依赖本包顶层名称；内容按领域拆分到子模块，角色档案一人一文件
（``data/characters/``）。
"""

from __future__ import annotations

from .types import (
    A,
    AbilityDefinition,
    CharacterDefinition,
    I,
    InformationTemplate,
    ItemDefinition,
    L,
    LocationDefinition,
    MarkDefinition,
    PseudoDefinition,
)
from .characters import (
    ABILITY_DISPATCH,
    ABILITY_INTERACTIONS,
    ABILITY_TARGET_OPTIONS,
    CHARACTER_CODEX_EXTRA,
    PENDING_VIEWS,
    ABILITY_FAILED_HOOKS,
    ABILITY_USED_HOOKS,
    CHARACTER_NODE_HOOKS,
    CHARACTER_VALUE_HOOKS,
    CHARACTER_DEATH_HOOKS,
    CHARACTER_MODULES,
    CHARACTER_MARKS,
    CHARACTER_DETAIL_SLOTS,
    CHARACTERS,
    CODEX_SECTIONS,
    CODEX_SUMMARY_HOOKS,
    HEALTH_CHANGED_HOOKS,
    INFORMATION_CREATED_HOOKS,
    MARK_CONSUMED_HOOKS,
    MARK_GAINED_HOOKS,
    MARK_REACHED_HOOKS,
    NODE_HOOKS,
    SEARCH_REWARD_HOOKS,
    PROTECTED_STARTERS,
    TURN_START_HOOKS,
    register_character,
    register_character_module,
)
from .information import (
    INFORMATION_STATE_EFFECTS,
    INFORMATION_TEMPLATES,
    LOCATION_INFORMATION_MODIFIERS,
    register_information_template,
    register_location_modifier,
    register_state_effect,
)
from .items import (
    CATEGORIES,
    ITEMS,
    ITEM_HOOKS,
    ITEM_EFFECTS,
    START_LOOT_TABLE,
    apply_item_tags,
    category_of,
    items_of_category,
    register_item,
)
from .locations import (
    ANY,
    BASE_MAP_GROUPS,
    FIXED_LOCATIONS,
    LOCATION_GROUPS,
    LOCATIONS,
    MAP_DRAW_WEIGHTS,
    register_location,
)
from .pseudos import (
    PSEUDO_CARD_SLOTS,
    PSEUDO_MODULES,
    PSEUDOS,
    SCENARIO_HANDLERS,
    register_pseudo,
)
from .resourcepack import (
    RESOURCE_SYMBOLS,
    RESOURCE_THEME,
    register_symbols,
    register_theme,
)
from .tags import TAG_BEHAVIORS, register_tag_module

GAME_VERSION = "2.1.0"
# 默认伪人：由伪人模块自声明 DEFAULT_PSEUDO，否则取首个可用。
DEFAULT_PSEUDO = next(
    (module.DEFINITION.id for module in PSEUDO_MODULES.values()
     if getattr(module, "DEFAULT_PSEUDO", False)),
    next(iter(PSEUDOS), ""),
)
DEFAULT_MAP_PACK = "suburban_town"

# 随机事件 ID 映射表：event_id 使用整数编号（按事件域分段），字符串事件
# 名的静态部分在此登记；带实例后缀的动态事件由基础编号派生。
EVENT_IDS = {
    "pseudo.calendar": 1001,
    "world.locations": 1101,
    "start.loot": 1201,
    "start.discover": 1202,
    "visitor.queue": 2001,
    "smartphone.info": 2101,
    "search.parameters": 4001,
    "search.behavior": 4002,
    "loot.quality": 4101,
    "loot.item": 4102,
    "loot.tags": 4103,
    "information.spawn": 6001,
    "ability.fail": 7001,
    "passive.roll": 7002,
    "emotion.self": 8001,
    "status.self": 8002,
}

# 高号段随机事件（信息/情绪/命运/角色等动态事件），与基础事件同表。
EVENT_IDS.update({
    "information.type": 9001,
    "information.truth": 9002,
    "information.location": 9003,
    "information.state.targets": 9004,
    "information.visit.offset": 9005,
    "information.human.false": 9006,
    "information.returning.target": 9007,
    "information.returning.offset": 9008,
    "information.search_return.target": 9009,
    "information.search_return.offset": 9010,
    "information.pseudo_skill.id": 9011,
    "information.accusation.target": 9012,
    "information.emotion.target": 9013,
    "information.emotion.type": 9014,
    "information.emotion.duration": 9015,
    "fries.accusation.false": 9016,
    "fries.performance": 9017,
    "fries.performance.targets": 9018,
    "fries.performance.duration": 9019,
    "fries.mind.targets": 9020,
    "fries.mind_play": 9021,
    "modifier.fortune_roll": 9022,
    "erebus.discern": 9023,
    "fate.justice": 9024,
    "fate.death": 9025,
    "fate.judgement": 9026,
    "zero329.detect.pseudo": 9027,
    "polar.avoid": 9101,
    "condition.set": 9102,
    "condition.worsen": 9103,
    "condition.extend": 9104,
    "status.self.intensity": 9105,
    "status.self.layer": 9106,
    "emotion.self.intensity": 9107,
    "emotion.self.layer": 9108,
    "onion.irritation.extra": 9109,
    "health.recover.intensity": 9110,
    "health.recover.layer": 9111,
    "impatient.health": 9112,
    "walkman.break": 9113,
    "shock.apply": 9114,
    "shock.death": 9115,
    "shock.layers": 9116,
    "depression.leave": 9117,
    "item.suspicious": 9118,
    "item.fragile": 9119,
    "medical": 9120,
    "garlic.passive": 9121,
    "information.discern": 9122,
    "information.auto_verify": 9123,
    "pseudo.encounter": 9124,
    "benzene.curse.status": 9125,
    "benzene.curse.target": 9223,
    "benzene.curse.layer": 9224,
    "onion.low_sanity": 9126,
    "onion.low_sanity.target": 9127,
    "fries.trigger": 9128,
    "search.near_death": 9129,
    "held.search.break": 9130,
    "tool.return": 9131,
    "water": 9132,
    "beans": 9133,
    "chaos.personality": 9201,
    "dragon.visitor": 9202,
    "fate.orientation": 9203,
    "fate.draw": 9204,
    "onion.calm": 9205,
    "sandwhite.heal": 9206,
    "sandwhite.ordinary.search_reward": 9207,
    "zero329.info": 9208,
    "fries.persona": 9209,
    "fries.human.extra": 9210,
    "fries.human.persona": 9211,
    "stubborn.blue": 9212,
    "stubborn.purple": 9213,
    "book.plants": 9214,
    "fries.human.reward": 9215,
    "sandwhite.extra": 9216,
    "jiugu.reward": 9217,
    "looting.food": 9218,
    "liu.reward": 9219,
    "supply": 9220,
    "emotion.adjust": 9221,
    "emotion.select": 9222,
})

QUALITY_NAMES = ("白色", "绿色", "蓝色", "紫色", "金色", "红色")

# 搜索返程规则说明（供界面展示；与 search_system._resolve_search_return 的实际结算对应）。
SEARCH_RETURN_NOTE = "返程：基础 10 生命伤害 / 10 理智伤害；既有创伤、紊乱与侵蚀情绪会恶化并延长。"
QUALITY_WEIGHTS = (20.0, 30.0, 30.0, 15.0, 4.5, 0.5)

# 情绪定义与中文名的唯一来源在 weiren_game/condition.py（EMOTION_DEFINITIONS）。
# 下列 label 表由它派生，避免两处维护。
from weiren_game.condition import EMOTION_DEFINITIONS  # noqa: E402

EROSION_EMOTIONS = {
    key: value.label
    for key, value in EMOTION_DEFINITIONS.items()
    if value.kind == "erosion" and value.rarity == "common"
}
AWAKENING_EMOTIONS = {
    key: value.label
    for key, value in EMOTION_DEFINITIONS.items()
    if value.kind == "awakening" and value.rarity == "common"
}
RARE_EMOTIONS = {
    key: value.label
    for key, value in EMOTION_DEFINITIONS.items()
    if value.rarity == "rare"
}

_DIFFICULTY_BASE = {
    "label": "",
    "end_sanity_bonus": 0.0,
    "damage_multiplier": 1.0,
    "pseudo_start_chance": .15,
    "pseudo_step": .15,
    "fortune_delta": 0,
    "start_tenants_delta": 0,
    "search_turn_delta": 0,
    "search_behavior_delta": 0,
    # 仅作用于「开局补给」这个池子的时运加成（可与 a4/a-4 的 fortune_delta 叠加）。
    "start_fortune_delta": 0,
    "start_loot_draws": 0,
    # 开局房客的当前生命/理智百分比变化（a8）与其最大值的百分比变化（a-8）。
    "start_vital_pct": 0.0,
    "start_vital_max_pct": 0.0,
    # 开局房客的初始消沉值与开局异常状态（a9 / a10）。
    "start_depression_delta": 0.0,
    "start_condition_trauma_disorder": 0,
    # a-10：房客常驻免疫创伤与紊乱（布尔闸门）。
    "trauma_disorder_immunity": 0,
}
# 每一档新增的限制/增益词条。正向难度 aN 继承 a1..aN；负向 a-N 继承 a-1..a-N。
_POSITIVE_TOKENS: dict[int, dict[str, object]] = {
    1: {"end_sanity_bonus": 1.0},
    2: {"damage_multiplier": 1.1},
    3: {"pseudo_start_chance": .20, "pseudo_step": .20},
    4: {"fortune_delta": -1},
    5: {"start_tenants_delta": -1},
    6: {"search_turn_delta": 1, "search_behavior_delta": -1},
    # a7：开局补给更差（时运 -3、少掉 1 次）。
    7: {"start_fortune_delta": -3, "start_loot_draws": -1},
    # a8：开局房客当前生命/理智 -20%。
    8: {"start_vital_pct": -0.20},
    # a9：开局房客初始消沉值 +100。
    9: {"start_depression_delta": 100.0},
    # a10：房客被接纳时附带 1/99 的创伤或紊乱。
    10: {"start_condition_trauma_disorder": 1},
}
_NEGATIVE_TOKENS: dict[int, dict[str, object]] = {
    1: {"end_sanity_bonus": -1.0},
    2: {"damage_multiplier": .9},
    3: {"pseudo_start_chance": .10, "pseudo_step": .10},
    4: {"fortune_delta": 1},
    5: {"start_tenants_delta": 1},
    6: {"search_turn_delta": -1, "search_behavior_delta": 1},
    # a-7：开局补给更好（时运 +3、多掉 1 次）。
    7: {"start_fortune_delta": 3, "start_loot_draws": 1},
    # a-8：开局房客最大生命/理智 +20%。
    8: {"start_vital_max_pct": 0.20, "start_vital_pct": 0.20},
    # a-9：开局房客初始消沉值 -100。
    9: {"start_depression_delta": -100.0},
    # a-10：房客常驻免疫创伤与紊乱。
    10: {"trauma_disorder_immunity": 1},
}
_DIFFICULTY_LABELS = {
    1: "高压消耗", 2: "重创来袭", 3: "高频来袭", 4: "流年不利",
    5: "冷清开局", 6: "行程紧张", 7: "补给紧缺", 8: "虚弱开局",
    9: "心绪低沉", 10: "带伤开局",
}
_DIFFICULTY_LABELS_NEGATIVE = {
    1: "低压消耗", 2: "钝化创伤", 3: "缓步来袭", 4: "时来运转",
    5: "热闹开局", 6: "行程宽裕", 7: "补给充裕", 8: "康健开局",
    9: "心境明快", 10: "百毒不侵",
}


def _merge_tokens(target: dict[str, object], token: dict[str, object]) -> None:
    """把词条合成进配置：倍率相乘，其余字段相加/覆盖（伪人步长取词条值）。"""
    for key, value in token.items():
        if key.startswith("pseudo_"):
            target[key] = float(value)
        elif key == "damage_multiplier":
            target[key] = float(target[key]) * float(value)
        else:
            target[key] = float(target[key]) + float(value)


_MAX_DIFFICULTY_LEVEL = max(
    max(_POSITIVE_TOKENS, default=0), max(_NEGATIVE_TOKENS, default=0)
)
DIFFICULTIES: dict[str, dict[str, object]] = {"a0": dict(_DIFFICULTY_BASE, label="标准")}
for level in range(1, _MAX_DIFFICULTY_LEVEL + 1):
    positive = dict(_DIFFICULTY_BASE)
    negative = dict(_DIFFICULTY_BASE)
    for index in range(1, level + 1):
        if index in _POSITIVE_TOKENS:
            _merge_tokens(positive, _POSITIVE_TOKENS[index])
        if index in _NEGATIVE_TOKENS:
            _merge_tokens(negative, _NEGATIVE_TOKENS[index])
    DIFFICULTIES[f"a{level}"] = dict(
        positive, label=_DIFFICULTY_LABELS.get(level, f"a{level}")
    )
    DIFFICULTIES[f"a-{level}"] = dict(
        negative, label=_DIFFICULTY_LABELS_NEGATIVE.get(level, f"a-{level}")
    )
WORSEN_PROBABILITIES = (1.00, .80, .60, 0.0, .50, .40, 0.0, .35, .30, 0.0)
EXTEND_PROBABILITIES = (1.00, .90, .80, .70, .70, .65, .65, .60, .60, .80)
STATUS_PRIMARY_LOSS = (0, 1, 2, 5, 10, 15, 20, 30, 40, 60, 80)
STATUS_SECONDARY_LOSS = (0, 0, 0, 0, 5, 10, 20, 30, 40, 80, 100)

_DIFFICULTY_TOKEN_TEXT = {
    "end_sanity_bonus": lambda v: f"回合结束理智 {v:+g}",
    "damage_multiplier": lambda v: f"受到伤害 ×{v:g}",
    "pseudo_start_chance": lambda v: f"伪人首次到访概率 {v:.0%}",
    "pseudo_step": lambda v: f"伪人后续到访概率 {v:.0%}",
    "fortune_delta": lambda v: f"幸运 {v:+g}",
    "start_tenants_delta": lambda v: f"初始房客 {v:+g}",
    "search_turn_delta": lambda v: f"搜索耗时 {v:+g} 回合",
    "search_behavior_delta": lambda v: f"搜索期间行为 {v:+g}",
    "start_fortune_delta": lambda v: f"开局物资时运 {v:+g}",
    "start_loot_draws": lambda v: f"开局掉落次数 {v:+g}",
    "start_vital_pct": lambda v: f"开局房客生命/理智 {v:+.0%}",
    "start_vital_max_pct": lambda v: f"开局房客最大生命/理智 {v:+.0%}",
    "start_depression_delta": lambda v: f"开局消沉值 {v:+g}",
    "start_condition_trauma_disorder": lambda v: "房客被接纳时附带 1/99 的创伤或紊乱",
    "trauma_disorder_immunity": lambda v: "房客常驻免疫创伤与紊乱",
}
_DIFFICULTY_ORDER = (
    [f"a-{n}" for n in range(_MAX_DIFFICULTY_LEVEL, 0, -1)]
    + ["a0"]
    + [f"a{n}" for n in range(1, _MAX_DIFFICULTY_LEVEL + 1)]
)


def _describe_difficulty_tokens(tokens: dict) -> list:
    """把某档新增的词条翻译为中文说明（供界面展示）。"""
    lines = []
    for key, value in tokens.items():
        formatter = _DIFFICULTY_TOKEN_TEXT.get(key)
        if formatter:
            lines.append(formatter(value))
    return lines


DIFFICULTY_INFO: list = []
for _key in _DIFFICULTY_ORDER:
    _level = 0 if _key == "a0" else int(_key[1:])
    if _level > 0:
        _added = _describe_difficulty_tokens(_POSITIVE_TOKENS[_level])
        _kind = "hard"
    elif _level < 0:
        _added = _describe_difficulty_tokens(_NEGATIVE_TOKENS[-_level])
        _kind = "easy"
    else:
        _added, _kind = [], "neutral"
    DIFFICULTY_INFO.append({
        "id": _key, "level": _level, "label": DIFFICULTIES[_key]["label"],
        "kind": _kind, "added": _added,
    })


BOND_DESCRIPTIONS = {
    "cheerful": "2/5/8：降低理智消耗、全员回复理智并强化开朗房客昂扬。",
    "loner": "仅1或≥5：孤僻房客搜索更快且必定成功，高层级排斥非孤僻房客。",
    "keen": "2/4：降低易损概率，提高紫色与金色以上物资权重。",
    "stubborn": "恰好4/7/10：增加容量、成功率并给予蓝/紫品质必得物资。",
    "steady": "2/5/8：降低生命消耗与伤害，最高层级会重分配部分伤害。",
    "impatient": "2/4/6/8：搜索更快但更危险；首次激活各档获得强心剂。",
    "gentle": "3/6/9：更频繁来访，接纳时治疗更多房客。",
    "suspicious": "2/4/8：取得并识破更多信息。",
}


def validate_catalogue() -> None:
    """自检静态图鉴的字段约束。

    不假定任何具体内容存在（不校验数量下限/固定集合），以便内容可插拔；
    只校验与内容多少无关的结构性约束。
    """
    source_ids = [c.source_id for c in CHARACTERS.values()]
    assert len(source_ids) == len(set(source_ids))
    assert all(isinstance(value, int) and value > 0 for value in source_ids)
    for item in ITEMS.values():
        assert 0 <= item.quality <= 5 and item.tags


# 性格/羁绊注册表所在模块（唯一来源；DLC 经 register_personality_module 追加）。
from .personalities import PERSONALITIES, PERSONALITY_LABELS  # noqa: F401

# 展示用的特殊性格键（不属于常规性格、不参与羁绊）。
PERSONALITY_LABELS.update({"dynamic": "混沌", "unknown": "未定"})


validate_catalogue()

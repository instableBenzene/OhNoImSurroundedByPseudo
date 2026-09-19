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
    CHARACTER_CONTAINERS,
    CHARACTER_PANELS,
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
    START_LOOT_CATEGORIES,
    START_LOOT_RECIPE,
    apply_item_tags,
    category_of,
    items_of_category,
    register_item,
)
from .maps import BASE_MAP_ID, MAPS, MapDefinition, register_map, register_map_location
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
from weiren_game.data.lang import TEXT

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

QUALITY_NAMES = (TEXT["data.__init__.QUALITY_NAMES.0"], TEXT["data.__init__.QUALITY_NAMES.1"], TEXT["data.__init__.QUALITY_NAMES.2"], TEXT["data.__init__.QUALITY_NAMES.3"], TEXT["data.__init__.QUALITY_NAMES.4"], TEXT["data.__init__.QUALITY_NAMES.5"])

# 搜索返程规则说明（供界面展示；与 search_system._resolve_search_return 的实际结算对应）。
SEARCH_RETURN_NOTE = TEXT["data.__init__.SEARCH_RETURN_NOTE"]
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
    1: TEXT["data.__init__._DIFFICULTY_LABELS.1"], 2: TEXT["data.__init__._DIFFICULTY_LABELS.2"], 3: TEXT["data.__init__._DIFFICULTY_LABELS.3"], 4: TEXT["data.__init__._DIFFICULTY_LABELS.4"],
    5: TEXT["data.__init__._DIFFICULTY_LABELS.5"], 6: TEXT["data.__init__._DIFFICULTY_LABELS.6"], 7: TEXT["data.__init__._DIFFICULTY_LABELS.7"], 8: TEXT["data.__init__._DIFFICULTY_LABELS.8"],
    9: TEXT["data.__init__._DIFFICULTY_LABELS.9"], 10: TEXT["data.__init__._DIFFICULTY_LABELS.10"],
}
_DIFFICULTY_LABELS_NEGATIVE = {
    1: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.1"], 2: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.2"], 3: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.3"], 4: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.4"],
    5: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.5"], 6: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.6"], 7: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.7"], 8: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.8"],
    9: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.9"], 10: TEXT["data.__init__._DIFFICULTY_LABELS_NEGATIVE.10"],
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
DIFFICULTIES: dict[str, dict[str, object]] = {"a0": dict(_DIFFICULTY_BASE, label=TEXT["data.__init__.module.1"])}
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
    "end_sanity_bonus": lambda v: TEXT["data.__init__.module.2"].format(p1=v),
    "damage_multiplier": lambda v: TEXT["data.__init__.module.3"].format(p1=v),
    "pseudo_start_chance": lambda v: TEXT["data.__init__.module.4"].format(p1=v),
    "pseudo_step": lambda v: TEXT["data.__init__.module.5"].format(p1=v),
    "fortune_delta": lambda v: TEXT["data.__init__.module.6"].format(p1=v),
    "start_tenants_delta": lambda v: TEXT["data.__init__.module.7"].format(p1=v),
    "search_turn_delta": lambda v: TEXT["data.__init__.module.8"].format(p1=v),
    "search_behavior_delta": lambda v: TEXT["data.__init__.module.9"].format(p1=v),
    "start_fortune_delta": lambda v: TEXT["data.__init__.module.10"].format(p1=v),
    "start_loot_draws": lambda v: TEXT["data.__init__.module.11"].format(p1=v),
    "start_vital_pct": lambda v: TEXT["data.__init__.module.12"].format(p1=v),
    "start_vital_max_pct": lambda v: TEXT["data.__init__.module.13"].format(p1=v),
    "start_depression_delta": lambda v: TEXT["data.__init__.module.14"].format(p1=v),
    "start_condition_trauma_disorder": lambda v: TEXT["data.__init__.module.15"],
    "trauma_disorder_immunity": lambda v: TEXT["data.__init__.module.16"],
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
    "cheerful": TEXT["data.__init__.BOND_DESCRIPTIONS.cheerful"],
    "loner": TEXT["data.__init__.BOND_DESCRIPTIONS.loner"],
    "keen": TEXT["data.__init__.BOND_DESCRIPTIONS.keen"],
    "stubborn": TEXT["data.__init__.BOND_DESCRIPTIONS.stubborn"],
    "steady": TEXT["data.__init__.BOND_DESCRIPTIONS.steady"],
    "impatient": TEXT["data.__init__.BOND_DESCRIPTIONS.impatient"],
    "gentle": TEXT["data.__init__.BOND_DESCRIPTIONS.gentle"],
    "suspicious": TEXT["data.__init__.BOND_DESCRIPTIONS.suspicious"],
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
PERSONALITY_LABELS.update({"dynamic": TEXT["data.__init__.module.17"], "unknown": TEXT["data.__init__.module.18"]})


validate_catalogue()

"""住户的严格运行时状态模型。

``TenantState`` 是引擎与各系统操作的唯一房客运行时对象：状态统一收进
``conditions``（创伤/紊乱/休克、侵蚀/觉醒/稀有情绪），物品归 ``Inventory``，
技能归 ``abilities``，回合类限制归 ``action_locks``/``turn_counters``。

静态身份与初始值归属角色目录；角色专属机制（人格、性格锁、角色印记与参数）
最终归各自角色模块。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ability import AbilityState
from .condition import (
    ALL_EMOTIONS,
    Condition,
    EMOTION_DEFINITIONS,
    STATUS_DEFINITIONS,
)
from .items import Inventory, ItemInstance
from .marks import MarkPool


PRIMARY_PERSONALITY_WEIGHT = 1.5
SHOCK_INTENSITY_MAX = 4


def status_caps(status_id: str) -> tuple[int, int]:
    """返回已知状态定义的上限（intensity_max, layers_max）。"""

    definition = STATUS_DEFINITIONS.get(status_id) or EMOTION_DEFINITIONS.get(status_id)
    if definition is None:
        return (10, 99)
    return (definition.intensity_max, definition.layers_max)


@dataclass
class TenantState:
    """单个住户的运行时状态。

    ``id`` 来自共享 ``InstancePool``，对每个存档唯一；``character_id``
    仅指回静态角色目录条目。
    """

    id: int
    character_id: str
    health: float = 100.0
    sanity: float = 100.0
    max_health: float = 100.0
    max_sanity: float = 100.0
    alive: bool = True
    at_home: bool = True
    temporarily_away: bool = False
    return_turn: int = 0
    leave_count: int = 0
    is_pseudo: bool = False
    pseudo_source: str | None = None
    copied_from: str | None = None
    conditions: dict[str, Condition] = field(default_factory=dict)
    personalities: dict[str, float] = field(default_factory=dict)
    inventory: Inventory = field(default_factory=Inventory)
    abilities: list[AbilityState] = field(default_factory=list)
    marks: MarkPool = field(default_factory=MarkPool)
    action_locks: dict[str, int] = field(default_factory=dict)
    turn_counters: dict[str, int] = field(default_factory=dict)
    # --- 通用隐藏数值（消沉值；回合计数已归 turn_counters） ----------------
    depression: float = 0.0
    # --- 搜索期间的临时修饰（由搜索系统与角色模块读写） -------------------
    search_bonus: float = 0.0
    fortune_bonus: int = 0
    # --- 通用失效/行动封锁标记 ----------------------------------------------
    abilities_disabled: bool = False
    passives_disabled: bool = False
    return_event_pending: bool = False

    def __post_init__(self) -> None:
        """校验房客 ID 与角色 ID 均非空，否则抛出 ValueError。"""
        if not self.id:
            raise ValueError("tenant id cannot be empty")
        if not self.character_id:
            raise ValueError("tenant character_id cannot be empty")

    @property
    def home_turns(self) -> int:
        """入住回合计数（存于 turn_counters）。"""
        return self.turn_counters.get("home_turns", 0)

    @home_turns.setter
    def home_turns(self, value: int) -> None:
        """设置入住回合计数。"""
        self.turn_counters["home_turns"] = int(value)

    @property
    def skip_until_turn(self) -> int:
        """“无法行动”锁到期回合（存于 action_locks["all"]）。"""
        return self.action_locks.get("all", 0)

    @skip_until_turn.setter
    def skip_until_turn(self, value: int) -> None:
        """设置“无法行动”锁到期回合。"""
        self.action_locks["all"] = int(value)

    @property
    def search_locked_until(self) -> int:
        """搜索锁到期回合（存于 action_locks["search"]）。"""
        return self.action_locks.get("search", 0)

    @search_locked_until.setter
    def search_locked_until(self, value: int) -> None:
        """设置搜索锁到期回合。"""
        self.action_locks["search"] = int(value)

    def condition(self, status_id: str) -> Condition:
        """按状态 ID 获取或创建对应的 Condition 实例。"""

        if status_id not in self.conditions:
            self.conditions[status_id] = Condition()
        return self.conditions[status_id]

    def set_status(self, status_id: str, *, intensity: int = 1, layers: int = 1) -> None:
        """设置状态，按注册定义上限钳制强度与层数；无效则移除该状态。"""

        intensity_max, layers_max = status_caps(status_id)
        # 先用 0/0 构造，避免 Condition.__post_init__ 的默认上限(10)提前夹掉
        # 强度上限 >10 的状态（如高生命免疫的充能强度 99）。
        value = Condition()
        value.intensity = int(intensity)
        value.layers = int(layers)
        value.clamp(intensity_max=intensity_max, layers_max=layers_max)
        if value.active:
            self.conditions[status_id] = value
        else:
            self.conditions.pop(status_id, None)

    def clear_status(self, status_id: str) -> None:
        """移除指定状态。"""
        self.conditions.pop(status_id, None)

    def personality_weight(self, personality_id: str) -> float:
        """返回指定人格的权重（未设置时为 0.0）。"""
        return self.personalities.get(personality_id, 0.0)

    def has_ability(self, ability_id: str) -> bool:
        """判断住户是否持有指定技能 ID。"""
        return any(state.ability_id == ability_id for state in self.abilities)

    def ability_states(self, ability_id: str) -> list[AbilityState]:
        """返回指定技能 ID 的全部技能状态。"""
        return [state for state in self.abilities if state.ability_id == ability_id]

    def ability_state(self, ability_id: str) -> AbilityState | None:
        """返回指定技能 ID 的首个技能状态，未持有则返回 None。"""
        return next(
            (state for state in self.abilities if state.ability_id == ability_id),
            None,
        )

    def carried(self, item_id: str) -> int:
        """返回背包中该物品 ID 的累计数量。"""
        return self.inventory.count(item_id)

    def locked_until(self, action_kind: str) -> int:
        """返回该行动被锁定的到期回合（0 表示未锁定）。"""

        return self.action_locks.get(action_kind, 0)

    # ---- 状态便捷属性：读写统一收进 conditions -----------------------------
    @property
    def trauma(self) -> Condition:
        """创伤状态（conditions["trauma"]）。"""
        return self.condition("trauma")

    @trauma.setter
    def trauma(self, value: Condition) -> None:
        """整体替换创伤状态。"""
        self.conditions["trauma"] = value

    @property
    def disorder(self) -> Condition:
        """紊乱状态（conditions["disorder"]）。"""
        return self.condition("disorder")

    @disorder.setter
    def disorder(self, value: Condition) -> None:
        """整体替换紊乱状态。"""
        self.conditions["disorder"] = value

    @property
    def irritation(self) -> Condition:
        """烦躁情绪状态。"""
        return self.condition("irritation")

    @irritation.setter
    def irritation(self, value: Condition) -> None:
        """整体替换烦躁情绪状态。"""
        self.conditions["irritation"] = value

    @property
    def reason(self) -> Condition:
        """理智（稀有觉醒）情绪状态。"""
        return self.condition("reason")

    @reason.setter
    def reason(self, value: Condition) -> None:
        """整体替换理智情绪状态。"""
        self.conditions["reason"] = value

    @property
    def madness(self) -> Condition:
        """癫狂（稀有侵蚀）情绪状态。"""
        return self.condition("madness")

    @madness.setter
    def madness(self, value: Condition) -> None:
        """整体替换癫狂情绪状态。"""
        self.conditions["madness"] = value

    # 休克仍以旧的双整数接口暴露；其真实存储是 conditions["shock"]。
    @property
    def shock(self) -> int:
        """休克强度。"""
        return self.condition("shock").intensity

    @shock.setter
    def shock(self, value: int) -> None:
        """设置休克强度（0..4，与定义上限一致）。"""
        self.condition("shock").intensity = max(
            0, min(SHOCK_INTENSITY_MAX, int(value))
        )

    @property
    def shock_layers(self) -> int:
        """休克层数。"""
        return self.condition("shock").layers

    @shock_layers.setter
    def shock_layers(self, value: int) -> None:
        """设置休克层数（0..99）。"""
        self.condition("shock").layers = max(0, min(99, int(value)))

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "TenantState":
        """从字典还原 TenantState，并递归还原嵌套的状态对象。"""
        data = dict(raw)
        data["conditions"] = {
            key: Condition.from_dict(value)
            for key, value in dict(data.get("conditions", {})).items()
        }
        data["personalities"] = {
            key: float(value)
            for key, value in dict(data.get("personalities", {})).items()
        }
        data["inventory"] = Inventory.from_dict(data.get("inventory", {}))
        data["abilities"] = [
            AbilityState.from_dict(entry)
            for entry in list(data.get("abilities", []))
        ]
        data["marks"] = MarkPool.from_dict(data.get("marks", {}))
        data["action_locks"] = {
            key: int(value)
            for key, value in dict(data.get("action_locks", {})).items()
        }
        data["turn_counters"] = {
            key: int(value)
            for key, value in dict(data.get("turn_counters", {})).items()
        }
        return cls(**data)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典，嵌套对象一并转为字典。"""
        return {
            "id": self.id,
            "character_id": self.character_id,
            "health": self.health,
            "sanity": self.sanity,
            "max_health": self.max_health,
            "max_sanity": self.max_sanity,
            "alive": self.alive,
            "at_home": self.at_home,
            "temporarily_away": self.temporarily_away,
            "return_turn": self.return_turn,
            "leave_count": self.leave_count,
            "is_pseudo": self.is_pseudo,
            "pseudo_source": self.pseudo_source,
            "copied_from": self.copied_from,
            "conditions": {
                key: value.to_dict()
                for key, value in self.conditions.items()
            },
            "personalities": dict(self.personalities),
            "inventory": self.inventory.to_dict(),
            "abilities": [state.to_dict() for state in self.abilities],
            "marks": self.marks.to_dict(),
            "action_locks": dict(self.action_locks),
            "turn_counters": dict(self.turn_counters),
            "depression": self.depression,
            "search_bonus": self.search_bonus,
            "fortune_bonus": self.fortune_bonus,
            "abilities_disabled": self.abilities_disabled,
            "passives_disabled": self.passives_disabled,
            "return_event_pending": self.return_event_pending,
        }


__all__ = [
    "ALL_EMOTIONS",
    "PRIMARY_PERSONALITY_WEIGHT",
    "SHOCK_INTENSITY_MAX",
    "TenantState",
    "ItemInstance",
    "status_caps",
]

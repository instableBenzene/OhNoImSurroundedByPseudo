"""Serializable state objects for the complete rules implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any

from .data import DEFAULT_PSEUDO, GAME_VERSION
from .session import GameFlowState, InstancePool, RoundActionState, SaveMetadata
from .pseudo import PseudoRuntime
from .condition import Condition
from .global_event import GlobalEventState
from .items import Inventory
from .tenant import TenantState
from weiren_game.data.lang import TEXT

# 设计约定：不要把特殊角色独有的字段直接加入通用 TenantState
# （reason/madness/personas/性格锁定/角色专属印记、状态或技能参数等）。
# 角色专属运行时状态统一由各角色档案文件声明（data/characters/<id>.py 的
# Runtime 容器，随 GameState 挂载）；通用房客只保留公共字段。

@dataclass
class SearchMission:
    """一次搜索任务本身的状态；携带物一律从派出房客的背包实时读取。"""

    tenant_id: int
    location_id: str
    base_search_turns: int = 4
    search_turns: int = 4
    search_behavior_count: int = 4
    carry_capacity: int = 3
    search_success_rate: float = 0.5
    random_sequence: list[float] = field(default_factory=list)
    success_behavior_indices: list[int] = field(default_factory=list)
    bag_full_behavior_index: int | None = None
    actual_search_turns: int = 4
    elapsed_search_turns: int = 0
    remain_search_turns: int = 4
    rewards: list[str] = field(default_factory=list)
    guaranteed_rewards: list[str] = field(default_factory=list)
    attacked_pseudos: list[str] = field(default_factory=list)   #一次搜索至多遭遇一次伪人；保存已经遭遇的伪人ID。
    search_start_turn: int = 0
    search_instance_id: int = 0
    fortune: int = 0
    loot_modifiers: list[dict[str, float]] = field(default_factory=list)
    loot_context: dict[str, float] = field(default_factory=dict)
    is_finished: bool = False
    captured: bool = False
    reports: list[str] = field(default_factory=list)  # 返程时播报的搜索期间事件

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SearchMission":
        """将存档字典反序列化为 SearchMission。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, Any]:
        """将搜索任务状态序列化为字典。"""
        return asdict(self)


@dataclass
class DoorEvent:
    kind: str
    title: str
    description: str
    visitor_id: str | None = None
    pseudo_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)      #新版本所有游戏数据都必须严格定义，不允许使用 dict[str, Any] 作为未定义数据或不同系统之间的临时传递容器。


@dataclass
class Information:
    info_instance_id: int
    title: str
    text: str
    status: str
    gained_turn: int
    expires_turn: int
    truth: bool = True
    kind: str = "visit"
    subtype: str = ""
    source: str = TEXT["models.module.1"]
    template_id: str | None = None
    location_id: str | None = None
    target_ids: list[int] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    verified_turn: int | None = None
    resolved: bool = False
#Information 可以作为统一实体保留当前大部分明确字段。与 DoorEvent 的 metadata 不同，这些字段的语义已经基本确定，而且 Information 类型数量有限，因此不必为了避免少量未使用字段而拆分多个实体。重点检查 data: dict[str, Any]：将其中已经确定的类型专属参数正式定义；只有确实无法统一、且未来确实存在扩展需求的数据才允许进入 data。


# PseudoRuntime（weiren_game/pseudo.py）：通用进度 common + 各场景子状态。
# 目前仍保留旧式扁平属性转发（state.pseudo_state.<field> 经 __getattr__
# 转发到归属子状态）；后续应改为直接读 common / scenario 子状态。


@dataclass
class VisitorState:
    """Door-side flow: who is waiting outside and how often they were turned away."""

    visitor_pool: list[str] = field(default_factory=list)
    visitor_rejections: dict[str, int] = field(default_factory=dict)
    # Pseudo arrivals follow a scheduled calendar; this counter belongs to the
    # visitor/pseudo scheduling system.
    next_pseudo_turn: int = 3

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "VisitorState":
        """将访客状态字典反序列化为 VisitorState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, Any]:
        """将访客状态序列化为字典。"""
        return asdict(self)


@dataclass
class LocationState:
    """The ten locations available this run."""

    available_locations: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LocationState":
        """将地点状态字典反序列化为 LocationState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, Any]:
        """将本局可用地点序列化为字典。"""
        return asdict(self)


@dataclass
class GameEventState:
    """Events waiting at the door plus rule event counters."""

    door_events: list[DoorEvent] = field(default_factory=list)
    event_counters: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "GameEventState":
        """将事件字典反序列化为 GameEventState，含门口事件解析。"""
        return cls(
            door_events=[DoorEvent(**item) for item in raw.get("door_events", [])],
            event_counters=dict(raw.get("event_counters", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """将门口事件与事件计数序列化为字典。"""
        return {
            "door_events": [asdict(item) for item in self.door_events],
            "event_counters": dict(self.event_counters),
        }


@dataclass
class WorldState:
    """Everything that happens outside the house doors."""

    visitors: VisitorState = field(default_factory=VisitorState)
    locations: LocationState = field(default_factory=LocationState)
    events: GameEventState = field(default_factory=GameEventState)
    global_events: GlobalEventState = field(default_factory=GlobalEventState)
    # Role pool shaping performed at game creation.
    disabled_characters: list[str] = field(default_factory=list)
    # Search missions describe tenants currently outside; owned by SearchSystem.
    missions: list[SearchMission] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "WorldState":
        """将世界状态字典反序列化为 WorldState 及各子状态。"""
        return cls(
            visitors=VisitorState.from_dict(raw.get("visitors", {})),
            locations=LocationState.from_dict(raw.get("locations", {})),
            events=GameEventState.from_dict(raw.get("events", {})),
            global_events=GlobalEventState.from_dict(raw.get("global_events", {})),
            disabled_characters=list(raw.get("disabled_characters", [])),
            missions=[
                SearchMission.from_dict(item)
                for item in raw.get("missions", [])
            ],
        )

    def to_dict(self) -> dict[str, Any]:
        """将门外世界与搜索任务状态序列化为字典。"""
        return {
            "visitors": self.visitors.to_dict(),
            "locations": self.locations.to_dict(),
            "events": self.events.to_dict(),
            "global_events": self.global_events.to_dict(),
            "disabled_characters": list(self.disabled_characters),
            "missions": [mission.to_dict() for mission in self.missions],
        }


@dataclass
class BondState:
    """Active personality bonds inside the house."""

    activated_bonds: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BondState":
        """将羁绊状态字典反序列化为 BondState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, Any]:
        """将激活羁绊列表序列化为字典。"""
        return asdict(self)


@dataclass
class HouseState:
    """Everything owned by the house: tenants, shared inventory and clues."""

    tenants: dict[int, TenantState] = field(default_factory=dict)
    inventory: Inventory = field(default_factory=Inventory)
    information: list[Information] = field(default_factory=list)
    bonds: BondState = field(default_factory=BondState)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "HouseState":
        """将房屋状态字典反序列化为 HouseState，含房客与信息。"""
        return cls(
            tenants={
                int(key): TenantState.from_dict(value)
                for key, value in raw.get("tenants", {}).items()
            },
            inventory=Inventory.from_dict(raw.get("inventory", {})),
            information=[
                Information(**item)
                for item in raw.get("information", [])
            ],
            bonds=BondState.from_dict(raw.get("bonds", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """将房客、物资与信息等房屋状态序列化为字典。"""
        return {
            "tenants": {
                key: tenant.to_dict() if hasattr(tenant, "to_dict") else asdict(tenant)
                for key, tenant in self.tenants.items()
            },
            "inventory": self.inventory.to_dict(),
            "information": [asdict(item) for item in self.information],
            "bonds": self.bonds.to_dict(),
        }


@dataclass
class SessionLogState:
    """Replay snapshots and action history kept outside the rules state."""

    history: list[dict[str, Any]] = field(default_factory=list)
    current_turn_actions: list[dict[str, Any]] = field(default_factory=list)
    action_log: list[dict[str, Any]] = field(default_factory=list)
    # 完整对局日志（含未公开记录）：随存档持久化，供读档后回看与导出。
    entries: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SessionLogState":
        """将回放日志字典反序列化为 SessionLogState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, Any]:
        """将回放与行动历史序列化为字典。"""
        return asdict(self)


class GameState:
    """分层运行时状态：meta/flow/round/ids/world/house/pseudo_state/
    角色容器/effects/log，不再提供旧版平铺属性门面。"""

    def __init__(
        self,
        *,
        meta: SaveMetadata,
        flow: GameFlowState | None = None,
        round: RoundActionState | None = None,
        ids: InstancePool | None = None,
        world: WorldState | None = None,
        house: HouseState | None = None,
        pseudo_state: PseudoRuntime | None = None,
        log: SessionLogState | None = None,
    ) -> None:
        """创建分层 GameState，缺省容器以默认状态补齐。"""
        object.__setattr__(self, "meta", meta)
        object.__setattr__(self, "flow", flow or GameFlowState())
        object.__setattr__(self, "round", round or RoundActionState())
        object.__setattr__(self, "ids", ids or InstancePool())
        object.__setattr__(self, "world", world or WorldState())
        object.__setattr__(self, "house", house or HouseState())
        object.__setattr__(
            self,
            "pseudo_state",
            pseudo_state
            or PseudoRuntime(pseudo_instance_id=1, scenario_id=DEFAULT_PSEUDO),
        )
        object.__setattr__(self, "log", log or SessionLogState())

    def to_dict(self, include_history: bool = True) -> dict[str, Any]:
        """严格序列化：将各分层状态汇总为存档字典，可排除历史日志。"""
        data = {
            "meta": self.meta.to_dict(),
            "flow": self.flow.to_dict(),
            "round": self.round.to_dict(),
            "ids": self.ids.to_dict(),
            "world": self.world.to_dict(),
            "house": self.house.to_dict(),
            "pseudo_state": self.pseudo_state.to_dict(),
        }
        if include_history:
            data["log"] = self.log.to_dict()
        else:
            data["log"] = {
                "history": [],
                "current_turn_actions": [],
                "action_log": [],
            }
        return data

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "GameState":
        """严格反序列化：由字典构造分层 GameState，未知字段将报错。"""
        allowed = {
            "meta",
            "flow",
            "round",
            "ids",
            "world",
            "house",
            "pseudo_state",
            "log",
        }
        unknown = set(raw) - allowed
        if unknown:
            raise ValueError(f"unknown GameState field: {sorted(unknown)}")
        return cls(
            meta=SaveMetadata.from_dict(raw["meta"]),
            flow=GameFlowState.from_dict(raw.get("flow", {})),
            round=RoundActionState.from_dict(raw.get("round", {})),
            ids=InstancePool.from_dict(raw.get("ids", {})),
            world=WorldState.from_dict(raw.get("world", {})),
            house=HouseState.from_dict(raw.get("house", {})),
            pseudo_state=PseudoRuntime.from_dict(raw.get("pseudo_state", {})),
            log=SessionLogState.from_dict(raw.get("log", {})),
        )



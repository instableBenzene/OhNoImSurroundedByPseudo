"""会话级严格状态。

``SaveMetadata`` 只保存存档封套所需数据；``GameFlowState`` 只保存回合与流程
进度；``InstancePool`` 是全部实体实例 ID 的唯一分配器：每类实体各自维护
从 1 递增的独立 int 池。同类实例的编号只受“同类创建顺序”影响，不会因为
其他实体类型（物品/信息/搜索…）插入而变化，从而保证相同对局行为下实例
ID 与随机素材稳定可控。
"""

from __future__ import annotations

from dataclasses import dataclass


NEW_GAME_VERSION = "2.1.0"
PHASES = ("created", "turn_start", "action", "between_turns", "turn_end", "finished")


@dataclass(frozen=True)
class SaveMetadata:
    """存档封套元数据：版本、随机种子与难度。"""

    version: str
    seed: str
    difficulty: str
    # 对局启动时启用的内容包清单（含内置 base 包）。包集合在对局期间不可变，
    # 读档时若与当前启动集合不一致将拒绝载入。
    packs: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "SaveMetadata":
        """从字典还原 SaveMetadata。"""
        allowed = {"version", "seed", "difficulty", "packs"}
        unknown = set(raw) - allowed
        if unknown:
            raise TypeError(f"unknown SaveMetadata field: {sorted(unknown)}")
        return cls(
            version=str(raw["version"]),
            seed=str(raw["seed"]),
            difficulty=str(raw["difficulty"]),
            packs=tuple(raw.get("packs") or ()),
        )

    def to_dict(self) -> dict[str, str]:
        """序列化为普通字典。"""
        return {
            "version": self.version,
            "seed": self.seed,
            "difficulty": self.difficulty,
            "packs": list(self.packs),
        }


@dataclass
class GameFlowState:
    """回合与流程进度状态（当前回合、阶段、上限与结局标记）。"""

    turn: int = 0
    phase: str = "created"
    max_turns: int = 12
    game_over: bool = False
    victory: bool = False
    ending: str = ""

    def __post_init__(self) -> None:
        """校验 phase 属于预定义阶段集合，否则抛出 ValueError。"""
        if self.phase not in PHASES:
            raise ValueError(f"unknown phase: {self.phase}")

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "GameFlowState":
        """从字典还原 GameFlowState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "turn": self.turn,
            "phase": self.phase,
            "max_turns": self.max_turns,
            "game_over": self.game_over,
            "victory": self.victory,
            "ending": self.ending,
        }


@dataclass
class InstancePool:
    """所有实体实例 ID 的唯一分配器。

    每类实体（房客/物品/信息/搜索/伪人）持有独立的从 1 递增的 int 池，
    跨类型的创建顺序互不影响；静态内容 id（character_id/item_id/场景键）
    仍是字符串，与本类实例 id 分离。
    """

    tenant: int = 1
    item: int = 1
    information: int = 1
    search: int = 1
    pseudo: int = 1
    mark: int = 1

    def allocate_tenant(self) -> int:
        """分配下一个房客实例 ID（从 1 起递增）。"""
        identifier = self.tenant
        self.tenant += 1
        return identifier

    def allocate_item(self) -> int:
        """分配下一个物品实例 ID（从 1 起递增）。"""
        identifier = self.item
        self.item += 1
        return identifier

    def allocate_information(self) -> int:
        """分配下一个信息实例 ID（从 1 起递增）。"""
        identifier = self.information
        self.information += 1
        return identifier

    def allocate_search(self) -> int:
        """分配下一个搜索任务实例 ID（从 1 起递增）。"""
        number = self.search
        self.search += 1
        return number

    def allocate_pseudo(self) -> int:
        """分配下一个伪人运行时实例 ID（从 1 起递增）。"""
        identifier = self.pseudo
        self.pseudo += 1
        return identifier

    def allocate_mark(self) -> int:
        """分配下一个印记实例 ID（从 1 起递增）。"""
        identifier = self.mark
        self.mark += 1
        return identifier

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "InstancePool":
        """从字典还原 InstancePool。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, int]:
        """序列化为普通字典。"""
        return {
            "tenant": self.tenant,
            "item": self.item,
            "information": self.information,
            "search": self.search,
            "pseudo": self.pseudo,
            "mark": self.mark,
        }


@dataclass
class RoundActionState:
    """每个回合开始时重置的限制与计数。"""

    searched_this_turn: bool = False
    item_uses_this_turn: int = 0

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "RoundActionState":
        """从字典还原 RoundActionState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "searched_this_turn": self.searched_this_turn,
            "item_uses_this_turn": self.item_uses_this_turn,
        }

"""技能运行时状态。

静态定义保留在数据目录中；租户只存储 ``AbilityState``：当前持有的技能、
获取途径（原生/复制/窃取/借用/转化）以及运行时冷却。两个租户可持有相同
技能 ID，但状态相互独立。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AcquisitionKind = Literal["original", "copied", "stolen", "borrowed", "transformed", "learned"]


@dataclass
class AbilityState:
    """单个技能实例的运行时状态。"""

    ability_id: str
    acquisition: AcquisitionKind = "original"
    source_character_id: str | None = None
    cooldown_until: int = 0
    used_this_turn: bool = False
    disabled: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "AbilityState":
        """从字典还原 AbilityState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "ability_id": self.ability_id,
            "acquisition": self.acquisition,
            "source_character_id": self.source_character_id,
            "cooldown_until": self.cooldown_until,
            "used_this_turn": self.used_this_turn,
            "disabled": self.disabled,
        }

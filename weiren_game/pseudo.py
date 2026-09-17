"""各剧本伪人的运行时状态。

通用进度（已揭露、来访、压制、解放）属于每个剧本；其余数字归使用它的剧本
模块所有。引擎通过恰好包含一个剧本专属子状态的 ``PseudoRuntime`` 协调。
"""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields as dataclass_fields
from typing import Any
from weiren_game.data.pseudos import PSEUDO_MODULES



@dataclass
class PseudoCommonState:
    """剧本通用进度：揭露、已知、来访次数与解放标记。

    ``revealed`` 是**机制**门控（初访已发生：内容层多个被动以它为"初访后"判据）；
    ``known`` 只是**对外可见性**（初访前技能生效、玩家已看到结果）。
    """

    revealed: bool = False
    known: bool = False
    visit_count: int = 0
    liberated: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "PseudoCommonState":
        """从字典还原 PseudoCommonState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "revealed": self.revealed,
            "known": self.known,
            "visit_count": self.visit_count,
            "liberated": self.liberated,
        }


@dataclass
class PseudoRuntime:
    """单个剧本伪人的完整运行时状态。

    ``scenario_id`` 是静态场景定义键（``pseudo_<场景>``），用于查伪人注册表
    与场景处理器；``pseudo_instance_id`` 是该局伪人运行时实例的 int 编号
    （统一实例 id 体系，当前一局一个伪人，为将来多伪人同局预留）。

    场景专属状态统一放在 ``states``（key=去掉 ``pseudo_`` 前缀），由各场景模块
    暴露的 ``State`` 类构造，不再为内置场景硬编码字段，也不再使用 ``extra``。
    """

    pseudo_instance_id: int
    scenario_id: str
    name: str = ""
    common: PseudoCommonState = field(default_factory=PseudoCommonState)
    states: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """按场景模块暴露的 State 类补建当前场景子状态。"""
        suffix = self._scenario_attr()
        if suffix in self.states:
            return
        module = PSEUDO_MODULES.get(self.scenario_id)
        state_class = getattr(module, "State", None) if module else None
        if state_class is None:
            raise ValueError(
                f"pseudo module {self.scenario_id} must expose a State dataclass"
            )
        self.states[suffix] = state_class()

    def scenario(self) -> Any:
        """返回当前剧本对应的专属子状态。"""
        return self.states.get(self._scenario_attr())

    def _scenario_attr(self) -> str:
        """返回当前剧本内部子状态的属性名（去掉 pseudo_ 前缀）。"""
        if not self.scenario_id.startswith("pseudo_"):
            raise ValueError(
                f"invalid scenario_id: {self.scenario_id}"
            )
        return self.scenario_id[len("pseudo_"):]

    # 兼容层：为旧调用点保留扁平属性访问（``state.pseudo_state.<field>``）。
    # common 字段与当前场景 State 的字段都可直接读写；后续应改读
    # common / scenario() 子状态。
    _COMMON_FIELDS = frozenset(
        {"revealed", "known", "visit_count", "liberated"}
    )

    def __getattr__(self, name: str) -> Any:
        """按旧式扁平访问将字段转发到所属子状态。"""
        if name in self._COMMON_FIELDS:
            return getattr(self.common, name)
        for state in self.__dict__.get("states", {}).values():
            if hasattr(state, name):
                return getattr(state, name)
        # 非当前场景的字段：返回该字段在对应场景 State 中的默认值（兼容旧扁平访问）。
        for module in PSEUDO_MODULES.values():
            state_class = getattr(module, "State", None)
            if state_class is None:
                continue
            for entry in dataclass_fields(state_class):
                if entry.name != name:
                    continue
                if entry.default is not MISSING:
                    return entry.default
                if entry.default_factory is not MISSING:
                    return entry.default_factory()
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """按旧式扁平赋值将字段写入所属子状态。"""
        if name in self._COMMON_FIELDS:
            object.__setattr__(self.common, name, value)
            return
        for state in self.__dict__.get("states", {}).values():
            if hasattr(state, name):
                object.__setattr__(state, name, value)
                return
        object.__setattr__(self, name, value)

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "PseudoRuntime":
        """从字典还原 PseudoRuntime，并还原各子状态。"""
        data = dict(raw)
        data["pseudo_instance_id"] = int(data.get("pseudo_instance_id", 1))
        data["scenario_id"] = str(data.get("scenario_id", ""))
        data["common"] = PseudoCommonState.from_dict(data.get("common", {}))
        module = PSEUDO_MODULES.get(data["scenario_id"])
        state_class = getattr(module, "State", None) if module else None
        states: dict[str, Any] = {}
        if state_class is not None:
            states = {
                key: state_class.from_dict(value)
                for key, value in dict(data.get("states", {})).items()
            }
        data["states"] = states
        return cls(**data)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典，子状态一并转为字典。"""
        return {
            "pseudo_instance_id": self.pseudo_instance_id,
            "scenario_id": self.scenario_id,
            "name": self.name,
            "common": self.common.to_dict(),
            "states": {
                key: state.to_dict() if hasattr(state, "to_dict") else state
                for key, state in self.states.items()
            },
        }

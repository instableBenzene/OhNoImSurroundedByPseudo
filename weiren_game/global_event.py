"""全局事件模型（世界级“条件”）。

结构模仿 ``condition.py``：静态定义（``GlobalEventDefinition``）+ 注册表
（``GLOBAL_EVENT_DEFINITIONS`` + ``register_global_event``）+ 运行实例
（``GlobalEventInstance``，含数值 ``value`` 与剩余回合 ``layers``）。

全局事件不绑定房客，挂在“世界”上；回合末 ``layers -= 1``，归 0 移除。
额外回合初/末效果由定义的 ``nodes`` + ``hook`` 声明，供调度器扫描。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GlobalEventDefinition:
    """一种全局事件的静态描述。"""

    id: str
    label: str
    # 界面展示：图标 id 与"点开看到的内容"（内容层填；缺省由界面回退）。
    icon: str = "i-clock"
    description: str = ""
    layers_max: int = 99
    shown: frozenset[str] = frozenset({"icon", "layers"})
    source_id: str | None = None
    # 需要额外回合初/末效果时声明节点；hook 在对应节点被调用。
    nodes: frozenset[str] = frozenset()
    hook: object | None = None


GLOBAL_EVENT_DEFINITIONS: dict[str, GlobalEventDefinition] = {}


def register_global_event(definition: GlobalEventDefinition) -> None:
    """注册一个全局事件定义（覆盖同 id 旧定义）。"""
    GLOBAL_EVENT_DEFINITIONS[definition.id] = definition


# 「情绪显现」的世界级事件键前缀：某情绪被看穿后，它对**所有房客**可见若干回合。
EMOTION_REVEAL_PREFIX = "emotion.reveal."


def emotion_reveal_event(emotion_key: str) -> str:
    """返回某情绪的「情绪显现」全局事件键（唯一来源，读写都走它）。"""
    return f"{EMOTION_REVEAL_PREFIX}{emotion_key}"


@dataclass
class GlobalEventInstance:
    """一个全局事件实例：数值（如倍率/贡献）与剩余回合。"""

    value: float = 0.0
    layers: int = 0

    @property
    def active(self) -> bool:
        """是否仍在生效（剩余回合 > 0）。"""
        return self.layers > 0

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "GlobalEventInstance":
        """从字典还原 GlobalEventInstance。"""
        return cls(
            value=float(raw.get("value", 0.0)),
            layers=int(raw.get("layers", 0)),
        )

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {"value": self.value, "layers": self.layers}


@dataclass
class GlobalEventState:
    """世界持有的全局事件实例表：event_id → GlobalEventInstance。"""

    events: dict[str, GlobalEventInstance] = field(default_factory=dict)

    def set(self, event_id: str, value: float = 0.0, layers: int = 1) -> None:
        """设置/刷新一个全局事件（取较长剩余回合）。"""
        definition = GLOBAL_EVENT_DEFINITIONS.get(event_id)
        cap = definition.layers_max if definition else 99
        current = self.events.get(event_id)
        new_layers = max(layers, current.layers if current else 0)
        self.events[event_id] = GlobalEventInstance(
            value=float(value), layers=max(0, min(cap, int(new_layers)))
        )

    def instance(self, event_id: str) -> GlobalEventInstance | None:
        """返回指定事件的实例（无则 None）。"""
        return self.events.get(event_id)

    def active(self, event_id: str) -> bool:
        """指定事件是否生效。"""
        instance = self.events.get(event_id)
        return instance is not None and instance.active

    def value_of(self, event_id: str, default: float = 0.0) -> float:
        """返回生效事件的数值，未生效则返回默认值。"""
        instance = self.events.get(event_id)
        if instance is None or not instance.active:
            return default
        return instance.value

    def consume(self, event_id: str) -> GlobalEventInstance | None:
        """移除并返回指定事件实例（一次性消费）。"""
        return self.events.pop(event_id, None)

    def decay(self) -> None:
        """回合末衰减：所有事件剩余回合 -1，归 0 移除。"""
        for event_id in list(self.events):
            instance = self.events[event_id]
            instance.layers -= 1
            if instance.layers <= 0:
                del self.events[event_id]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "GlobalEventState":
        """从字典还原全局事件表。"""
        return cls(
            events={
                str(key): GlobalEventInstance.from_dict(value)
                for key, value in dict(raw.get("events", {})).items()
            }
        )

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "events": {
                key: value.to_dict() for key, value in self.events.items()
            }
        }


__all__ = [
    "EMOTION_REVEAL_PREFIX",
    "GLOBAL_EVENT_DEFINITIONS",
    "GlobalEventDefinition",
    "GlobalEventInstance",
    "GlobalEventState",
    "emotion_reveal_event",
    "register_global_event",
]

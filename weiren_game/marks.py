"""印记实例与印记池。

每个印记都是独立实例（唯一 ``mark_instance_id``），因为一个角色可能持有多种、
多个印记，且未来可能有针对“单个印记实例”的特殊玩法。默认消耗从
``mark_instance_id`` 最小的实例开始，可跨实例续扣。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MarkInstance:
    """单个印记实例：唯一编号 + 印记种类 + 数值（层数/数量）。"""

    mark_instance_id: int
    mark_id: str
    value: float = 1.0

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "MarkInstance":
        """从字典还原 MarkInstance。"""
        return cls(
            mark_instance_id=int(raw["mark_instance_id"]),
            mark_id=str(raw["mark_id"]),
            value=float(raw.get("value", 1.0)),
        )

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "mark_instance_id": self.mark_instance_id,
            "mark_id": self.mark_id,
            "value": self.value,
        }


@dataclass
class MarkPool:
    """一名房客持有的全部印记实例（按实例编号升序保存）。"""

    items: list[MarkInstance] = field(default_factory=list)

    def add(self, instance: MarkInstance) -> MarkInstance:
        """加入一个印记实例并按实例编号排序。"""
        self.items.append(instance)
        self.items.sort(key=lambda value: value.mark_instance_id)
        return instance

    def instances_of(self, mark_id: str) -> list[MarkInstance]:
        """返回指定种类的印记实例（编号升序）。"""
        return [value for value in self.items if value.mark_id == mark_id]

    def count(self, mark_id: str) -> float:
        """累计指定种类的印记数值。"""
        return float(sum(value.value for value in self.items if value.mark_id == mark_id))

    def remove_value(self, mark_id: str, value: float) -> bool:
        """移除指定种类中数值等于 value 的一个实例（用于牌面移除）。"""
        for instance in self.items:
            if instance.mark_id == mark_id and instance.value == value:
                self.items.remove(instance)
                return True
        return False

    def consume(self, mark_id: str, amount: float) -> float:
        """按实例编号从小到大消耗指定印记，返回实际消耗量。"""
        remaining = float(amount)
        if remaining <= 0:
            return 0.0
        consumed = 0.0
        for instance in self.instances_of(mark_id):
            if remaining <= 0:
                break
            take = min(instance.value, remaining)
            instance.value -= take
            remaining -= take
            consumed += take
            if instance.value <= 0:
                self.items.remove(instance)
        return consumed

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "MarkPool":
        """从字典还原 MarkPool。"""
        pool = cls(
            items=[
                MarkInstance.from_dict(entry)
                for entry in list(raw.get("items", []))
            ]
        )
        pool.items.sort(key=lambda value: value.mark_instance_id)
        return pool

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {"items": [value.to_dict() for value in self.items]}


__all__ = ["MarkInstance", "MarkPool"]

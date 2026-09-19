"""物品实例与有序背包的存储。

每个物品都是自带身份、数量、耐久与阅读进度的 ``ItemInstance``；租户与房屋
共用 ``Inventory``。列表顺序即槽位顺序，可据此直接判断“最早装备的护甲”
等规则，无需额外的装备列表。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable, Iterator
from typing import Callable


@dataclass
class ItemInstance:
    """单个物品实例，含唯一实例 ID 与运行时数量、耐久和持有回合。"""

    item_instance_id: int
    item_id: str
    count: int = 1
    # 0 means "not a durable item"; positive values are current durability.
    durability: int = 0
    held_turns: int = 0
    # 所在容器的槽位（格子）编号；0 为最靠前/最早生效的格。
    plot: int = 0

    def __post_init__(self) -> None:
        """校验数量至少为 1、耐久不可为负。"""
        if self.count < 1:
            raise ValueError("item instance count must be at least 1")
        if self.durability < 0:
            raise ValueError("item instance durability cannot be negative")
        if self.plot < 0:
            raise ValueError("item instance plot cannot be negative")

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "ItemInstance":
        """从字典还原 ItemInstance。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "item_instance_id": self.item_instance_id,
            "item_id": self.item_id,
            "count": self.count,
            "durability": self.durability,
            "held_turns": self.held_turns,
            "plot": self.plot,
        }


@dataclass
class Inventory:
    """有序的物品实例集合；列表顺序即槽位顺序。

    可堆叠的数量可共享同一实例，而不同实例始终保留各自的耐久。
    """

    items: list[ItemInstance] = field(default_factory=list)

    def __iter__(self) -> Iterator[ItemInstance]:
        """迭代内部物品实例列表。"""
        return iter(self.items)

    def __len__(self) -> int:
        """返回物品实例的数量。"""
        return len(self.items)

    def add(self, item: ItemInstance, *, plot: int | None = None) -> None:
        """把物品放进背包：未指定槽位时自动取最小空闲格。

        加入后会按槽位顺序重排列表，保证列表首项就是 plot 最小的物品。
        """
        if plot is None:
            item.plot = self._next_free_slot()
        else:
            # 指定槽位时若已被占用，则把原占用者挪到最小空闲格，避免重复 plot。
            item.plot = max(0, int(plot))
            other = next(
                (value for value in self.items if value.plot == item.plot), None
            )
            if other is not None:
                other.plot = self._next_free_slot_excluding({other})
        self.items.append(item)
        self.items.sort(key=lambda value: value.plot)

    def move_to(self, instance: "ItemInstance", plot: int) -> None:
        """把已有实例移动到指定槽位；目标被占用时与原占用者交换槽位。"""
        target = max(0, int(plot))
        if instance.plot == target:
            return
        other = next(
            (value for value in self.items if value is not instance and value.plot == target),
            None,
        )
        previous = instance.plot
        instance.plot = target
        if other is not None:
            other.plot = previous
        self.items.sort(key=lambda value: value.plot)

    def _next_free_slot_excluding(self, excluded: set["ItemInstance"]) -> int:
        """返回未被其余实例占用的最小槽位（最多跳过 99 格）。"""
        used = {value.plot for value in self.items if value not in excluded}
        for slot in range(100):
            if slot not in used:
                return slot
        return max(used, default=-1) + 1

    def at_plot(self, plot: int) -> "ItemInstance | None":
        """按槽位编号返回对应实例，空格返回 None。"""
        return next((value for value in self.items if value.plot == int(plot)), None)

    def _next_free_slot(self) -> int:
        """返回当前容器中最小的空闲槽位编号。"""
        used = {value.plot for value in self.items}
        slot = 0
        while slot in used:
            slot += 1
        return slot

    def instance(self, instance_id: str) -> ItemInstance | None:
        """按实例 ID 查找物品，未找到返回 None。"""
        return next((value for value in self.items if value.item_instance_id == instance_id), None)

    def remove(self, instance_id: str) -> ItemInstance | None:
        """按实例 ID 移除并返回该物品，不存在则返回 None。"""
        for index, value in enumerate(self.items):
            if value.item_instance_id == instance_id:
                return self.items.pop(index)
        return None

    def remove_first(self, item_id: str) -> ItemInstance | None:
        """移除槽位最靠前的指定物品实例并返回，未持有则返回 None。"""
        for index, value in enumerate(self.items):
            if value.item_id == item_id:
                return self.items.pop(index)
        return None

    def consume(self, item_id: str, amount: int = 1) -> int:
        """按“单位”消耗物品：可堆叠就减 count，归零才移除实例；返回实际消耗数。"""
        consumed = 0
        for instance in list(self.items):
            if instance.item_id != item_id:
                continue
            take = min(instance.count, amount - consumed)
            instance.count -= take
            consumed += take
            if instance.count <= 0:
                self.items.remove(instance)
            if consumed >= amount:
                break
        return consumed

    def count(self, item_id: str) -> int:
        """统计指定物品 ID 的累计数量。"""
        return sum(value.count for value in self.items if value.item_id == item_id)

    def earliest(self, predicate: Callable[[ItemInstance], bool]) -> ItemInstance | None:
        """返回槽位顺序中首个满足条件的物品，无则返回 None。"""
        return next((value for value in self.items if predicate(value)), None)

    def all_with(self, predicate: Callable[[ItemInstance], bool]) -> list[ItemInstance]:
        """返回所有满足条件的物品实例。"""
        return [value for value in self.items if predicate(value)]

    def by_item_id(self, item_id: str) -> list[ItemInstance]:
        """返回指定物品 ID 的全部实例。"""
        return [value for value in self.items if value.item_id == item_id]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "Inventory":
        """从字典还原 Inventory，并逐项还原物品实例。"""
        entries = raw.get("items", ())
        if not isinstance(entries, Iterable):
            raise ValueError("inventory items must be a list")
        inventory = cls(items=[ItemInstance.from_dict(entry) for entry in entries])
        inventory.items.sort(key=lambda value: value.plot)
        return inventory

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {"items": [value.to_dict() for value in self.items]}


__all__ = ["Inventory", "ItemInstance"]

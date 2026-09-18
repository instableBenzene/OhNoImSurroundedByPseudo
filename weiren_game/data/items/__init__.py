"""物资内容包：按 md 大类拆分，并加载 tags/*.json 的外部 tag 文件。

扩展方式：
- 新增一类物品：在 ``data/items/`` 下加一个模块并在本文件登记，或直接
  调用 :func:`register_item` 注册（可在游戏运行期调用）；
- 给已有/新增物品打 tag：在 ``data/items/tags/`` 下新建
  ``<tag名>.json``，内容为 item_id 或物品名称组成的数组，文件内列出的
  物品都会自动获得与文件名相同的 tag。
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from ..types import ItemDefinition
from pathlib import Path

from .._discovery import discover_modules

# md 中的物资大类（顺序即文档顺序）。
CATEGORY_ORDER = (
    "surgery_kits",
    "medicine_kits",
    "analgesics",
    "food",
    "tools_armor",
    "information_carriers",
    "character_items",
)
# 自动发现物品分类文件；按 CATEGORY_ORDER 排序（新分类追加在后面）。
_DISCOVERED_CATEGORIES = discover_modules(__name__, Path(__file__).parent, require="ITEMS")
_CATEGORY_MODULES: dict[str, object] = {
    name: _DISCOVERED_CATEGORIES[name]
    for name in CATEGORY_ORDER
    if name in _DISCOVERED_CATEGORIES
}
for _name, _module in _DISCOVERED_CATEGORIES.items():
    _CATEGORY_MODULES.setdefault(_name, _module)

# 大类 → item_id 列表（保留登记顺序）。
CATEGORY_ITEMS: dict[str, dict[str, ItemDefinition]] = {}
ITEMS: dict[str, ItemDefinition] = {}
for category, _category_module in _CATEGORY_MODULES.items():
    module_items = _category_module.ITEMS
    CATEGORY_ITEMS[category] = dict(module_items)
    ITEMS.update(module_items)

# 兼容别名：CATEGORIES == CATEGORY_ITEMS（大类名 → 该类的物品表）。
CATEGORIES = CATEGORY_ITEMS

# 各物品文件声明的生命周期 hook（与物品对象紧贴）：
# item_id -> {node -> {condition/effect name -> function}}
ITEM_HOOKS: dict[str, dict[str, dict[str, object]]] = {}
for _module in _CATEGORY_MODULES.values():
    for item_id, node_map in getattr(_module, "ITEM_HOOKS", {}).items():
        ITEM_HOOKS.setdefault(item_id, {}).update(node_map)

# 指名物的 on_use 效果注册表：各物品文件声明、此处聚合（与对象紧贴）。
ITEM_EFFECTS: dict[str, object] = {}
for _module in _CATEGORY_MODULES.values():
    ITEM_EFFECTS.update(getattr(_module, "ITEM_EFFECTS", {}))

# 开局战利品池：按类别给出候选物品，new_game 用种子系统从各池抽取。
START_LOOT_TABLE: dict[str, tuple[str, ...]] = {
    "food": (
        "simple_food", "common_food", "tasty_food", "garlic",
        "water", "pancake", "luncheon_meat",
    ),
    "medical": ("home_first_aid", "portable_medicine"),
    "tool": ("flashlight", "compass", "sports_shoes"),
    "carrier": ("smartphone", "newspaper", "video_tape"),
}
START_LOOT_TABLE = {
    label: tuple(item_id for item_id in ids if item_id in ITEMS)
    for label, ids in START_LOOT_TABLE.items()
}


# 应用设计稿风味文本（id -> flavor）。
from dataclasses import replace as _replace
from .flavor import ITEM_FLAVOR as _ITEM_FLAVOR

for _flavor_id, _flavor_text in _ITEM_FLAVOR.items():
    _definition = ITEMS.get(_flavor_id)
    if _definition is None:
        continue
    _updated = _replace(_definition, flavor=_flavor_text)
    ITEMS[_flavor_id] = _updated
    for _members in CATEGORY_ITEMS.values():
        if _flavor_id in _members:
            _members[_flavor_id] = _updated

def register_item(item: ItemDefinition, *, category: str, replace: bool = False) -> None:
    """登记一件新物资（运行期可调用）。

    ``replace=True`` 时覆盖同 id 旧定义，并把它从原先所属分类里摘掉（内容包优先级用）。
    """
    if item.item_id in ITEMS and not replace:
        raise ValueError(f"物品 ID 重复：{item.item_id}")
    if replace:
        for members in CATEGORY_ITEMS.values():
            members.pop(item.item_id, None)
    if category not in CATEGORY_ITEMS:
        CATEGORY_ITEMS[category] = {}
    ITEMS[item.item_id] = item
    CATEGORY_ITEMS[category][item.item_id] = item


def items_of_category(category: str) -> list[ItemDefinition]:
    """按大类返回其中全部物品（保持登记顺序）。"""
    return list(CATEGORY_ITEMS.get(category, {}).values())


def category_of(item_id: str) -> str | None:
    """返回物品所属大类，未登记返回 None。"""
    for category, members in CATEGORY_ITEMS.items():
        if item_id in members:
            return category
    return None


def apply_item_tags(tag: str, entries: Iterable[str]) -> None:
    """把给定 tag 合并进所有命中条目（item_id 或物品名称）的 ItemDefinition。"""
    name_to_id = {item.name: item.item_id for item in ITEMS.values()}
    for entry in entries:
        item_id = entry if entry in ITEMS else name_to_id.get(entry)
        if item_id is None:
            continue  # 引用的物品可能已被移除；跳过以支持内容可插拔
        current = ITEMS[item_id]
        if tag not in current.tags:
            ITEMS[item_id] = replace(current, tags=current.tags + (tag,))


def _load_tag_files() -> None:
    """读取 tags/*.json：文件名即 tag，内容为 item_id 或物品名称。"""
    tag_dir = Path(__file__).parent / "tags"
    if not tag_dir.is_dir():
        return
    for path in sorted(tag_dir.glob("*.json")):
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"tag 文件无法解析：{path}（{exc}）") from exc
        apply_item_tags(path.stem, entries or ())


_load_tag_files()


# ---------------------------------------------------------------- usage rules
_REQUIRE_EQUIP_IDS = frozenset({"walkman"})
_HOUSE_OBJECT_IDS = frozenset({"gramophone"})
_CARRIED_ONLY_IDS = frozenset(
    {"flashlight", "compass", "crowbar", "sports_shoes", "walmart_bag", "flintlock"}
)

def item_requires_equip(item_id: str) -> bool:
    """使用前必须装备到房客背包（书本/装甲/随身听）。"""
    item = ITEMS[item_id]
    return item_id in _REQUIRE_EQUIP_IDS or bool(
        set(item.tags).intersection({"book", "armor"})
    )


def item_is_house_object(item_id: str) -> bool:
    """屋主物品栏持续生效、不可使用/装备的屋内物件。"""
    return item_id in _HOUSE_OBJECT_IDS


def item_is_carried_only(item_id: str) -> bool:
    """只能装入背包携带、无法直接使用的工具。"""
    return item_id in _CARRIED_ONLY_IDS


def item_is_directly_usable(item_id: str) -> bool:
    """该物资能否被直接使用（否则属于需装备/携带/屋内物件）。

    规则由内容派生，避免各处再维护一份"哪些 id 不能用"的排除名单。
    """
    if (
        item_requires_equip(item_id)
        or item_is_carried_only(item_id)
        or item_is_house_object(item_id)
    ):
        return False
    item = ITEMS[item_id]
    if item.on_use and item.on_use in ITEM_EFFECTS:
        return True
    spec = item_gain_info_spec(item_id)
    if spec is not None and not spec.get("keep"):
        return True
    return bool(item.medical_target) or ("anodyne" in item.tags)


# 获得即兑换为信息的载体规格：{item_id: spec}
# spec 键：truth/false（每获得 1 件的生成数）、kinds（None=默认）、
# keep（False=不保留实物）、log（兑换提示文案，None=无）。
ON_GAIN_INFO_SPECS: dict[str, dict[str, object]] = {
    "newspaper": {
        "truth": 0,
        "false": 1,
        "kinds": ("material_reward", "visit"),
        "keep": False,
        "log": "已自动兑换为信息。",
    },
    "medical_newspaper": {
        "truth": 1,
        "false": 1,
        "kinds": ("material_reward", "location_modifier"),
        "keep": False,
        "log": "已自动兑换为信息。",
    },
    "video_tape": {
        "truth": 3,
        "false": 0,
        "kinds": None,
        "keep": False,
        "log": "已自动兑换为信息。",
    },
    "smartphone": {
        "truth": 0,
        "false": 10,
        "kinds": None,
        "keep": True,
        "log": None,
    },
}


def item_gain_info_spec(item_id: str) -> dict[str, object] | None:
    """返回「获得时兑换信息」的规格；普通物品返回 None。"""
    return ON_GAIN_INFO_SPECS.get(item_id)


# 全局物品节点 hook（与具体 item_id 无关，如护甲/传说书）：并入 NODE_HOOKS。
from ..characters import NODE_HOOKS as _NODE_HOOKS

for _module in _CATEGORY_MODULES.values():
    for _node, _hooks in getattr(_module, "HOOKS", {}).items():
        _table = _NODE_HOOKS.setdefault(_node, [])
        for _hook in (_hooks if isinstance(_hooks, (tuple, list)) else (_hooks,)):
            if _hook not in _table:
                _table.append(_hook)

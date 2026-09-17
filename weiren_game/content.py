"""内容管理器：核心与内容包之间的统一边界（ContentManager）。

内容包集合在“启动时/新开局前”即确定，对局期间不变（存档记录启用清单，
读档启动配置不一致会拒绝）。本管理器封装现有 ``data`` 包的全部
``register_*`` 入口并追踪已启用包，DLC 装载器与内置 base 包都经由它登记；
核心对主目录（角色/物品/地点/伪人）统一经 CONTENT 视图读取。支持运行期
热切换包集合：``ensure_captured()`` 在**装载任何内容包之前**懒抓一次 base 快照
（不能放在模块级 —— 效果内核的 provider 由 ``systems/*`` 导入时登记，早抓会漏），
``restore_base()`` 将其回滚（配合 :func:`weiren_game.dlc.reload_dlc` 即可免重启装卸 DLC）。
"""

from __future__ import annotations

from . import data


BASE_PACK = "base"

# 资源包容器所在的模块（外观包可**独立**于内容包回滚/套用）。
RESOURCE_MODULE = "weiren_game.data.resourcepack"


class ContentManager:
    """内容注册/查询的统一入口。"""

    def __init__(self) -> None:
        """绑定共享内容包并初始化已装载包名单。"""
        # 内置包 base 在启动时始终启用；DLC 包由装载器追加登记。
        self.packs: list[str] = [BASE_PACK]
        # 运行期热切换 DLC 所需：base 快照（含各注册表与全局事件）。
        self._snapshot: list[tuple[object, object]] = []
        self._resource_snapshot: list[tuple[object, object]] = []
        # 内容包装载完成后的"外观基线"：独立资源包以它为起点（低→高叠加）。
        self._resource_baseline: list[tuple[object, object]] | None = None
        self._global_events: dict = {}
        # base 快照是否已抓取（**懒抓**：必须在任何内容包装载之前，见 ensure_captured）。
        self._captured = False

    def ensure_base(self) -> None:
        """校验内置 base 内容包在位；缺失视为启动失败。"""
        if BASE_PACK not in self.packs:
            raise RuntimeError("内置 base 内容包缺失，无法开始游戏。")

    # ------------------------------------------------------------ registration
    def register_character(self, definition: object, *, replace: bool = False) -> None:
        """登记一位房客档案（``replace`` 允许高位内容包覆盖同 id）。"""
        data.register_character(definition, replace=replace)

    def register_character_module(self, character_id: str, module: object) -> None:
        """登记角色行为模块。"""
        data.register_character_module(character_id, module)

    def register_item(self, item: object, *, category: str, replace: bool = False) -> None:
        """登记一件物资（``replace`` 允许高位内容包覆盖同 id）。"""
        data.register_item(item, category=category, replace=replace)

    def register_item_hook(self, item_id: str, node_map: object) -> None:
        """登记一件物资的生命周期 hook（与共享 ITEM_HOOKS 原位合并）。"""
        from .data.items import ITEM_HOOKS

        ITEM_HOOKS.setdefault(item_id, {}).update(node_map)

    def register_item_effect(self, item_id: str, effect: object) -> None:
        """登记一件指名物的 on_use 效果。"""
        from .data.items import ITEM_EFFECTS

        ITEM_EFFECTS[item_id] = effect

    def register_location(self, location: object, *, replace: bool = False) -> None:
        """登记一个地点（``replace`` 允许高位内容包覆盖同 id）。"""
        data.register_location(location, replace=replace)

    def register_information_template(self, template: object, *, replace: bool = False) -> None:
        """登记一条信息模板（``replace`` 允许高位内容包覆盖同 id）。"""
        data.register_information_template(template, replace=replace)

    def register_location_modifier(self, template_id: str, modifier: object) -> None:
        """登记地点信息修正。"""
        data.register_location_modifier(template_id, modifier)

    def register_pseudo(self, module: object, *, replace: bool = False) -> None:
        """登记一个伪人场景模块（``replace`` 允许高位内容包覆盖同 id）。"""
        data.register_pseudo(module, replace=replace)

    def register_tag_module(self, tag: str, module: object) -> None:
        """登记一个 tag 的行为模块。"""
        from .data.tags import register_tag_module as _register

        _register(tag, module)

    def register_personality_module(self, personality_id: str, module: object) -> None:
        """登记一个性格（羁绊）模块（base 与 DLC 共用同一注册路径）。"""
        from .data.personalities import register_personality_module as _register

        _register(personality_id, module)

    def register_status_definition(self, definition: object) -> None:
        """登记一个状态定义。"""
        from .condition import register_status_definition as _register

        _register(definition)

    def register_emotion_definition(self, definition: object) -> None:
        """登记一个情绪定义（同步键集合、显现标记与 data 层标签表）。"""
        from .condition import register_emotion_definition as _register

        _register(definition)

    def register_map_group(self, group: str, weight: int = 20, *, required: bool = False) -> None:
        """把一个地点分组纳入开局抽取。"""
        from .data.locations import register_map_group as _register

        _register(group, weight, required=required)

    def register_location_group(self, group: str, label: str, icon: str = "i-gate") -> None:
        """登记一个地点分组的中文名与图标。"""
        from .data.labels import register_location_group as _register

        _register(group, label, icon)

    def register_item_tag_label(self, tag: str, label: str) -> None:
        """登记一个物品 tag 的中文名。"""
        from .data.labels import register_item_tag_label as _register

        _register(tag, label)

    def register_item_category_label(self, category: str, label: str) -> None:
        """登记一个物品分类的中文名。"""
        from .data.labels import register_item_category_label as _register

        _register(category, label)

    def register_map_location(self, map_id: str, location_id: str) -> None:
        """把某个地点加进已有地图的名单（DLC 想让自己的地点进"城郊小镇"时用）。"""
        from .data.maps import register_map_location as _register

        _register(str(map_id), str(location_id))

    def register_item_tag_icon(self, tag: str, icon: str, *, priority: int | None = None) -> None:
        """登记 tag 图标（可选优先序）。"""
        from .data.labels import register_item_tag_icon as _register

        _register(tag, icon, priority=priority)

    def register_information_kind_label(self, kind: str, label: str) -> None:
        """登记一种信息类型的中文名。"""
        from .data.labels import register_information_kind_label as _register

        _register(kind, label)

    def register_resource_pack(self, module: object, *, pack: str = "") -> None:
        """登记一个资源包模块（贴图零件 ``SYMBOLS`` + 主题 ``THEME``）。

        一般资源包/DLC 只允许覆盖"材质色调/字体"；语义色、品质色、羁绊位阶与尺寸
        （``resourcepack.LOCKED_TOKENS``）由 base 提供、不可改。
        """
        from .data.resourcepack import register_pack_module as _register

        _register(module, pack=pack)

    def apply_item_tags(self, tag: str, entries: object) -> None:
        """把 tag 合并进命中物品。"""
        from .data.items import apply_item_tags as _apply

        _apply(tag, entries)

    # ------------------------------------------------------- hot reload (DLC)
    def ensure_captured(self) -> None:
        """确保 base 快照已抓取（幂等）；**必须在装载任何内容包之前调用**。

        快照要涵盖"base 全部登记完毕"的那一刻。不能改成 ``content.py`` 的模块级：
        效果内核的 provider 由 ``systems/*`` 在**导入时**登记，而 ``systems``
        通常比 ``content`` 晚导入 —— 早抓就会漏掉它们，回滚时反而把 base 抹掉。
        """
        if not self._captured:
            self.capture_base()

    def capture_base(self) -> None:
        """记录内置 base 的当前注册状态，供运行期装卸 DLC 时回滚。"""
        import importlib

        snapshot: list[tuple[object, object]] = []
        resource_snapshot: list[tuple[object, object]] = []
        for module_name, attributes in _BASE_CONTAINERS:
            module = importlib.import_module(module_name)
            for name in attributes:
                container = getattr(module, name, None)
                if container is not None:
                    snapshot.append((container, _clone(container)))
                    if module_name == RESOURCE_MODULE:
                        resource_snapshot.append((container, _clone(container)))
        from .global_event import GLOBAL_EVENT_DEFINITIONS

        self._snapshot = snapshot
        self._resource_snapshot = resource_snapshot
        self._global_events = _clone(GLOBAL_EVENT_DEFINITIONS)
        self._captured = True

    def restore_resourcepack_base(self) -> None:
        """只把**资源包容器**回滚到 base（外观包可独立于内容包热切换）。"""
        for container, saved in self._resource_snapshot:
            if isinstance(container, dict):
                container.clear()
                container.update(_clone(saved))
            elif isinstance(container, list):
                container[:] = _clone(saved)
            elif isinstance(container, set):
                container.clear()
                container.update(_clone(saved))

    def overlay_resourcepack_base(self) -> None:
        """把**内置材质**（``data/resourcepack/``）重新盖到当前资源包容器上。

        用途：让 ``base`` 在**资源包清单**里也能调位次 —— 从低到高套用，轮到 ``base``
        时执行一次本方法，于是排在 base 下方的资源包改不动内置材质定义的东西，
        而排在 base 上方的资源包可以覆盖。``css`` 不重复叠加（基线里已经有）。
        """
        from .data.resourcepack import apply_base_material

        apply_base_material(css=False)

    def capture_resourcepack_baseline(self) -> None:
        """记录"内容包装载完之后"的资源包状态，作为独立资源包的叠加起点。"""
        self._resource_baseline = [
            (container, _clone(container)) for container, _ in self._resource_snapshot
        ]

    def restore_resourcepack_baseline(self) -> None:
        """把资源包容器回滚到**外观基线**（没有基线时退回 base 材质）。"""
        for container, saved in (self._resource_baseline or self._resource_snapshot):
            if isinstance(container, dict):
                container.clear()
                container.update(_clone(saved))
            elif isinstance(container, list):
                container[:] = _clone(saved)
            elif isinstance(container, set):
                container.clear()
                container.update(_clone(saved))

    def restore_base(self) -> None:
        """把注册表恢复到 base 快照（撤销所有 DLC 登记）并重置包清单。"""
        if not self._captured:
            # 还没抓过快照就没有可回滚的东西。**不要**在这里补抓：
            # 此刻的注册表可能已经含 DLC 内容，补抓会把它们当成 base。
            return
        for container, saved in self._snapshot:
            if isinstance(container, dict):
                container.clear()
                container.update(_clone(saved))
            elif isinstance(container, list):
                container[:] = _clone(saved)
            elif isinstance(container, set):
                container.clear()
                container.update(_clone(saved))
        from .global_event import GLOBAL_EVENT_DEFINITIONS

        GLOBAL_EVENT_DEFINITIONS.clear()
        GLOBAL_EVENT_DEFINITIONS.update(_clone(self._global_events))
        self.packs = [BASE_PACK]
        self._resource_baseline = None

    def overlay_base(self) -> None:
        """让 base **重新赢过**当前注册表里它已有的键（包优先级用）。

        装载顺序是"低优先级 → 高优先级"，因此在 base 所处的位置调用本方法，即可让
        排在 base 下方的包无法覆盖内置内容；base 上方（更高优先级）的包之后再装，
        仍可正常覆盖。只处理 id 键（dict/set），列表型 hook 序列不参与覆盖。
        """
        for container, saved in self._snapshot:
            if isinstance(container, dict) and isinstance(saved, dict):
                for key, value in saved.items():
                    current = container.get(key)
                    # 嵌套注册表（如 CATEGORY_ITEMS[类别][id]）只合并一层，
                    # 避免把低位包在同一层里新增的条目一起抹掉。
                    if isinstance(value, dict) and isinstance(current, dict):
                        for inner_key, inner_value in value.items():
                            current[inner_key] = _clone(inner_value)
                    else:
                        container[key] = _clone(value)
            elif isinstance(container, set) and isinstance(saved, set):
                container.update(_clone(saved))

    def set_packs(self, order: object) -> None:
        """按给定顺序（高→低优先级）设置启用包清单；base 恒存在（缺失则垫底）。"""
        ordered: list[str] = []
        for name in order or ():
            name = str(name)
            if name not in ordered:
                ordered.append(name)
        if BASE_PACK not in ordered:
            ordered.append(BASE_PACK)
        self.packs = ordered

    def pack_order(self) -> tuple[str, ...]:
        """返回启用包清单（**高→低优先级**，含 base）。"""
        return tuple(self.packs)

    # ---------------------------------------------------------------- queries
    def characters(self) -> dict:
        """房客档案目录（角色 id → 定义）。"""
        return data.CHARACTERS

    def character_modules(self) -> dict:
        """角色行为模块目录（角色 id → 模块）。"""
        from .data.characters import CHARACTER_MODULES

        return CHARACTER_MODULES

    def items(self) -> dict:
        """物资目录（item_id → 定义）。"""
        return data.ITEMS

    def item_hooks(self) -> dict:
        """物品生命周期 hook 目录（item_id → node → hooks）。"""
        from .data.items import ITEM_HOOKS

        return ITEM_HOOKS

    def item_effects(self) -> dict:
        """指名物 on_use 效果目录（item_id → 效果函数）。"""
        from .data.items import ITEM_EFFECTS

        return ITEM_EFFECTS

    def locations(self) -> dict:
        """地点目录（location_id → 定义）。"""
        return data.LOCATIONS

    def pseudos(self) -> dict:
        """伪人场景目录（场景键 → 定义）。"""
        return data.PSEUDOS

    def scenario_handlers(self) -> dict:
        """伪人场景处理器目录（场景键 → HANDLERS）。"""
        return data.SCENARIO_HANDLERS

    def status_definitions(self) -> dict:
        """状态定义目录（状态 id → 定义）。"""
        from .condition import STATUS_DEFINITIONS

        return STATUS_DEFINITIONS

    def emotion_definitions(self) -> dict:
        """情绪定义目录（情绪 id → 定义）。"""
        from .condition import EMOTION_DEFINITIONS

        return EMOTION_DEFINITIONS

    def tag_behaviors(self) -> dict:
        """tag 行为模块目录（tag → 模块）。"""
        return data.TAG_BEHAVIORS

    def event_ids(self) -> dict:
        """随机事件 ID 表。"""
        return data.EVENT_IDS

    def register_pack(self, name: str) -> None:
        """登记一个已装载的内容包名。"""
        if name == BASE_PACK:
            return
        if name not in self.packs:
            self.packs.append(name)

    def manifest(self) -> tuple[str, ...]:
        """返回当前启动的启用包清单（含内置 base 包，按名排序）。"""
        return tuple(sorted(self.packs))

    def validate_catalogue(self) -> None:
        """自检当前内容目录。"""
        data.validate_catalogue()


# 全局唯一内容管理器（DLC/内置包共用同一实例）。
CONTENT = ContentManager()


def _clone(value: object) -> object:
    """复制容器（dict/list/set），叶子对象共享；用于可重复的 base 快照。"""
    if isinstance(value, dict):
        return {key: _clone(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return set(value)
    return value


# 需要快照/回滚的注册表（模块全路径 -> 属性名）。
# **新增注册表必须登记在这里**，否则卸载 DLC 后仍会残留（历史上漏过
# ABILITY_TARGET_OPTIONS / CHARACTER_CODEX_EXTRA / 状态·情绪定义 / 图鉴静态表 /
# 效果内核的修饰器·闸门表）。
_BASE_CONTAINERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("weiren_game.data.characters", (
        "CHARACTER_MODULES", "CHARACTERS", "ABILITY_DISPATCH", "ABILITY_INTERACTIONS",
        "ABILITY_TARGET_OPTIONS", "CHARACTER_CODEX_EXTRA", "PROTECTED_STARTERS",
        "PENDING_VIEWS", "CODEX_SUMMARY_HOOKS", "CODEX_SECTIONS", "SEARCH_REWARD_HOOKS",
        "TURN_START_HOOKS", "CHARACTER_VALUE_HOOKS", "CHARACTER_NODE_HOOKS",
        "HEALTH_CHANGED_HOOKS", "ABILITY_USED_HOOKS", "ABILITY_FAILED_HOOKS",
        "MARK_GAINED_HOOKS", "MARK_CONSUMED_HOOKS", "MARK_REACHED_HOOKS", "NODE_HOOKS",
        "CHARACTER_DEATH_HOOKS", "CHARACTER_MARKS", "CHARACTER_DETAIL_SLOTS",
        "CHARACTER_CONTAINERS", "CHARACTER_PANELS", "INFORMATION_CREATED_HOOKS",
    )),
    ("weiren_game.data.items", (
        "CATEGORY_ITEMS", "ITEMS", "ITEM_HOOKS", "ITEM_EFFECTS",
        "START_LOOT_TABLE", "ON_GAIN_INFO_SPECS",
    )),
    ("weiren_game.data.locations", (
        "LOCATIONS", "LOCATION_GROUPS", "BASE_MAP_GROUPS", "MAP_DRAW_WEIGHTS",
        "MAPS",
    )),
    ("weiren_game.data.information", (
        "INFORMATION_TEMPLATES", "LOCATION_INFORMATION_MODIFIERS", "INFORMATION_STATE_EFFECTS",
    )),
    ("weiren_game.data.pseudos", (
        "PSEUDOS", "PSEUDO_MODULES", "SCENARIO_HANDLERS", "PSEUDO_CARD_SLOTS",
    )),
    ("weiren_game.data.tags", ("TAG_BEHAVIORS",)),
    ("weiren_game.data.personalities", (
        "PERSONALITY_MODULES", "PERSONALITY_LABELS", "PERSONALITIES",
        "BOND_TURN_START_HOOKS", "HEALTH_PROTECTION_HOOKS", "END_SANITY_COST_HOOKS",
        "BOND_END_HEALTH_HOOKS", "AWAKENING_MULTIPLIER_HOOKS", "EMOTION_CHANGE_HOOKS",
    )),
    ("weiren_game.data.labels", (
        "ITEM_CATEGORY_LABELS", "ITEM_TAG_LABELS", "LOCATION_GROUP_LABELS",
        "LOCATION_GROUP_ICONS", "INFORMATION_KIND_LABELS",
        "ITEM_TAG_ICONS", "ITEM_TAG_ICON_PRIORITY",
    )),
    ("weiren_game.data.codex_pack", (
        "EXTRA_SECTIONS", "PERSONALITY_BASE", "PERSONALITY_REQUIREMENT",
        "PERSONALITY_TIER_HINTS", "PERSONALITY_TIER_TEXT", "PSEUDO_SKILLS",
        "LOCATION_ICONS", "LOCATION_TEXT",
    )),
    ("weiren_game.condition", (
        "STATUS_DEFINITIONS", "EMOTION_DEFINITIONS",
        "ALL_EMOTIONS", "EROSION_EMOTIONS", "AWAKENING_EMOTIONS",
    )),
    # 角色专属容器的**类型表**（内容角色模块的 `CONTAINERS` 声明驱动）：
    # 它决定存档里的容器能不能被反序列化，所以同样随包装卸回滚。
    ("weiren_game.tenant", ("CONTAINER_TYPES",)),
    # 效果内核（通道 / 闸门）的登记表：静态修饰器、条件式 provider、闸门与 provider。
    # 它们同样"由内容登记"，只是登记的是数值修正而不是定义对象；不纳入快照就会在
    # 卸载后残留，而且是**静默地多算一次**（同一效果被结算 N 次）。
    ("weiren_game.modifier_rules", (
        "MODIFIER_REGISTRY", "MODIFIER_PROVIDERS", "GATE_REGISTRY", "GATE_PROVIDERS",
    )),
    # 资源包：贴图零件（SVG）+ 主题（CSS 变量 / 追加样式）。
    (RESOURCE_MODULE, ("RESOURCE_SYMBOLS", "RESOURCE_THEME", "RESOURCE_ASSETS")),
    # data 包根的派生 label 表（由 condition 同步维护，回滚时一并还原）。
    ("weiren_game.data", ("EROSION_EMOTIONS", "AWAKENING_EMOTIONS", "RARE_EMOTIONS")),
)

# base 快照**不在这里抓**：效果内核的 provider 由 `systems/*` 在导入时登记，
# 而它们通常比 `content` 晚导入 —— 早抓会漏掉它们，回滚时反而把 base 抹掉。
# 改为在任何内容包装载之前懒抓一次（`dlc.py` 的 `CONTENT.ensure_captured()`）。


__all__ = ["BASE_PACK", "CONTENT", "RESOURCE_MODULE", "ContentManager"]

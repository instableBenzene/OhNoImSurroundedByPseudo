"""房客档案聚合：自动发现同目录下的角色模块（放入/移除文件即插即拔）。"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from ..types import CharacterDefinition

# 自动发现：目录下每个暴露 CHARACTER 的模块都会登记，无需手写清单。
CHARACTER_MODULES: dict[str, object] = {}
for _info in sorted(pkgutil.iter_modules([str(Path(__file__).parent)]), key=lambda item: item.name):
    if _info.name.startswith("_"):
        continue
    _module = importlib.import_module(f"{__name__}.{_info.name}")
    _definition = getattr(_module, "CHARACTER", None)
    if _definition is not None:
        CHARACTER_MODULES[_definition.tenant_id] = _module

# CHARACTERS 按原稿编号（source_id）排序，保持开局池的确定性顺序；
# CHARACTER_MODULES 保持文件名字典序（hook 列表顺序依赖它）。
CHARACTERS: dict[str, CharacterDefinition] = {
    character_id: CHARACTER_MODULES[character_id].CHARACTER
    for character_id in sorted(
        CHARACTER_MODULES,
        key=lambda cid: CHARACTER_MODULES[cid].CHARACTER.source_id,
    )
}

# 不可被禁用的开局核心角色：由各角色模块自声明 PROTECTED_STARTER。
# 用 set（可变）以便 DLC 登记与热切换回滚。
PROTECTED_STARTERS: set[str] = {
    character_id for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "PROTECTED_STARTER", False)
}


def register_character(character: CharacterDefinition, *, replace: bool = False) -> None:
    """登记一位新角色档案（角色 ID 需唯一）。

    ``replace=True`` 时覆盖同 id 旧档案（内容包优先级用：高位包替换低位包/内置的角色）。
    """
    if character.tenant_id in CHARACTERS:
        if not replace:
            raise ValueError(f"角色 ID 重复：{character.tenant_id}")
    CHARACTERS[character.tenant_id] = character


# 主动能力调度注册表：character_id → {ability_id: handler}。
ABILITY_DISPATCH: dict[str, dict[str, object]] = {
    character_id: dict(module.ACTIVE_DISPATCH)
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "ACTIVE_DISPATCH", None)
}

# 内容自描述的通用注册表（移除某个角色模块时自动随之消失）：
#   ABILITY_INTERACTIONS：ability_id → 交互结算 UI（由内容声明）
#   PENDING_VIEWS：待处理交互视图 (build, resolve)（由内容声明）
#   CODEX_SUMMARY_HOOKS / CODEX_SECTIONS：图鉴的统计行与详细展示段
ABILITY_INTERACTIONS: dict[str, object] = {}
# 目标候选提供者：ability_id -> fn(engine, actor) -> [{"value","label","desc"}]
ABILITY_TARGET_OPTIONS: dict[str, object] = {}
# 角色图鉴补充内容：character_id -> fn() -> [{"title","entries":[(name,text)]}]
CHARACTER_CODEX_EXTRA: dict[str, object] = {}
PENDING_VIEWS: list[tuple] = []
CODEX_SUMMARY_HOOKS: list[object] = []
CODEX_SECTIONS: list[object] = []
for _decl_module in CHARACTER_MODULES.values():
    ABILITY_INTERACTIONS.update(getattr(_decl_module, "INTERACTIONS", {}))
    ABILITY_TARGET_OPTIONS.update(getattr(_decl_module, "TARGET_OPTIONS", {}))
    _extra = getattr(_decl_module, "CODEX_EXTRA", None)
    if _extra is not None:
        CHARACTER_CODEX_EXTRA[_decl_module.__name__.rsplit(".", 1)[-1]] = _extra
    _pending_view = getattr(_decl_module, "PENDING_VIEW", None)
    if _pending_view is not None:
        PENDING_VIEWS.append(_pending_view)
    _summary = getattr(_decl_module, "CODEX_SUMMARY", None)
    if _summary is not None:
        CODEX_SUMMARY_HOOKS.append(_summary)
    _section = getattr(_decl_module, "CODEX_SECTION", None)
    if _section is not None:
        CODEX_SECTIONS.append(_section)

# 搜索保底钩子：角色模块若提供 SEARCH_REWARD，则由 search 节点查表调用。
SEARCH_REWARD_HOOKS: dict[str, object] = {
    character_id: getattr(module, "SEARCH_REWARD", None)
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "SEARCH_REWARD", None) is not None
}

# 回合初房客实例钩子：角色模块若提供 TURN_START，则由 round_effects 的
# 回合初实例节点按房客查表调用（统一签名 engine, tenant）。
TURN_START_HOOKS: dict[str, object] = {
    character_id: getattr(module, "TURN_START", None)
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "TURN_START", None) is not None
}

# 数值变动钩子：角色模块若提供 VALUE_HOOKS（按节点名映射处理函数），则由
# value_system 的各数值结算点查表调用。节点名约定见各角色模块声明。
CHARACTER_VALUE_HOOKS: dict[str, dict[str, object]] = {
    character_id: dict(getattr(module, "VALUE_HOOKS"))
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "VALUE_HOOKS", None)
}

# 能力/事件级节点钩子（伪人流程、ability_launch 等）：character_id → 节点名 → 函数。
CHARACTER_NODE_HOOKS: dict[str, dict[str, object]] = {
    character_id: dict(getattr(module, "NODE_HOOKS"))
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "NODE_HOOKS", None)
}

# 生命数值变动后的角色光环（如苯环重症监护即时判定）。
HEALTH_CHANGED_HOOKS: list[object] = [
    getattr(module, "HEALTH_CHANGED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "HEALTH_CHANGED", None) is not None
]

# 主动能力结果节点：默认成功；私有失败标记存在时走 FAILED。
ABILITY_USED_HOOKS: list[object] = [
    getattr(module, "ON_ABILITY_USED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "ON_ABILITY_USED", None) is not None
]
ABILITY_FAILED_HOOKS: list[object] = [
    getattr(module, "ON_ABILITY_FAILED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "ON_ABILITY_FAILED", None) is not None
]

# 印记节点：获得 / 消耗 / 达到阈值。
MARK_GAINED_HOOKS: list[object] = [
    getattr(module, "ON_MARK_GAINED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "ON_MARK_GAINED", None) is not None
]
MARK_CONSUMED_HOOKS: list[object] = [
    getattr(module, "ON_MARK_CONSUMED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "ON_MARK_CONSUMED", None) is not None
]
MARK_REACHED_HOOKS: list[object] = [
    getattr(module, "ON_MARK_REACHED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "ON_MARK_REACHED", None) is not None
]

# 通用内容节点：模块的 ``HOOKS = {node: fn|(fn, ...)}`` 合并到此表。
NODE_HOOKS: dict[str, list[object]] = {}
for _module in CHARACTER_MODULES.values():
    for _node, _hooks in getattr(_module, "HOOKS", {}).items():
        _table = NODE_HOOKS.setdefault(_node, [])
        for _hook in (_hooks if isinstance(_hooks, (tuple, list)) else (_hooks,)):
            if _hook not in _table:
                _table.append(_hook)

# 房客死亡节点：角色光环/被动的死亡响应（如苯环 ICU 刷新）。
CHARACTER_DEATH_HOOKS: list[object] = [
    getattr(module, "TENANT_DEATH")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "TENANT_DEATH", None) is not None
]

# 角色 → 印记定义（获得条件/上下限/特殊用法，声明在各自档案文件）。
CHARACTER_MARKS: dict[str, tuple[object, ...]] = {
    character_id: tuple(getattr(module, "MARKS", ()))
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "MARKS", None)
}

# 角色 → 详情页小面板（头像右侧那片公共区域）：内容声明放什么（印记/进度条/文本/标签）。
# 声明 DETAIL_SLOT 的角色按自己的来；没声明的回退为"展示自己的印记"。
CHARACTER_DETAIL_SLOTS: dict[str, object] = {
    character_id: getattr(module, "DETAIL_SLOT", None)
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "DETAIL_SLOT", None) is not None
}

# 角色专属容器：模块声明 `CONTAINERS = {"<key>": <类>}`（自定义 UI 的专属状态放这里）。
# 声明表纳入 `_BASE_CONTAINERS` 快照；类型表（供存档反序列化）登记进 `weiren_game.tenant`。
CHARACTER_CONTAINERS: dict[str, dict[str, type]] = {
    character_id: dict(getattr(module, "CONTAINERS", {}))
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "CONTAINERS", None)
}

# 角色专属面板（自定义 UI）：模块声明 `PANEL = (build_view, resolve_action)`。
#   build_view(engine, tenant) -> dict | None    视图（条目词表与 DETAIL_SLOT 同一套）
#   resolve_action(engine, tenant, action, *, slot=None, item_id=None, source=None)
# 面板"开着没有"是**纯展示状态**（前端记），后端只负责下发视图与转交动作；
# 核心不认识面板里的任何具体概念（田 / 水 / 成熟都不在核心词表里）。
CHARACTER_PANELS: dict[str, object] = {
    character_id: getattr(module, "PANEL", None)
    for character_id, module in CHARACTER_MODULES.items()
    if getattr(module, "PANEL", None) is not None
}

from weiren_game.tenant import register_container_type as _register_container_type

for _container_owner, _container_map in CHARACTER_CONTAINERS.items():
    for _container_key, _container_cls in _container_map.items():
        _register_container_type(_container_owner, _container_key, _container_cls)


# 新待验证信息生成后的角色被动（如厄瑞玻斯太阳识破/占卜直觉）。
INFORMATION_CREATED_HOOKS: list[object] = [
    getattr(module, "INFORMATION_CREATED")
    for module in CHARACTER_MODULES.values()
    if getattr(module, "INFORMATION_CREATED", None) is not None
]


def register_character_module(character_id: str, module: object) -> None:
    """登记角色档案模块对象（供成本/门槛与能力调度注册表读取）。"""
    CHARACTER_MODULES[character_id] = module
    ABILITY_INTERACTIONS.update(getattr(module, "INTERACTIONS", {}))
    ABILITY_TARGET_OPTIONS.update(getattr(module, "TARGET_OPTIONS", {}))
    _extra = getattr(module, "CODEX_EXTRA", None)
    if _extra is not None:
        CHARACTER_CODEX_EXTRA[character_id] = _extra
    _pending_view = getattr(module, "PENDING_VIEW", None)
    if _pending_view is not None and _pending_view not in PENDING_VIEWS:
        PENDING_VIEWS.append(_pending_view)
    _summary = getattr(module, "CODEX_SUMMARY", None)
    if _summary is not None and _summary not in CODEX_SUMMARY_HOOKS:
        CODEX_SUMMARY_HOOKS.append(_summary)
    _section = getattr(module, "CODEX_SECTION", None)
    if _section is not None and _section not in CODEX_SECTIONS:
        CODEX_SECTIONS.append(_section)
    dispatch = getattr(module, "ACTIVE_DISPATCH", None)
    if dispatch:
        ABILITY_DISPATCH[character_id] = dict(dispatch)
    turn_start = getattr(module, "TURN_START", None)
    if turn_start is not None:
        TURN_START_HOOKS[character_id] = turn_start
    search_reward = getattr(module, "SEARCH_REWARD", None)
    if search_reward is not None:
        SEARCH_REWARD_HOOKS[character_id] = search_reward
    if getattr(module, "PROTECTED_STARTER", False):
        PROTECTED_STARTERS.add(character_id)
    value_hooks = getattr(module, "VALUE_HOOKS", None)
    if value_hooks:
        CHARACTER_VALUE_HOOKS[character_id] = dict(value_hooks)
    node_hooks = getattr(module, "NODE_HOOKS", None)
    if node_hooks:
        CHARACTER_NODE_HOOKS[character_id] = dict(node_hooks)
    death_hook = getattr(module, "TENANT_DEATH", None)
    if death_hook is not None and death_hook not in CHARACTER_DEATH_HOOKS:
        CHARACTER_DEATH_HOOKS.append(death_hook)
    info_hook = getattr(module, "INFORMATION_CREATED", None)
    if info_hook is not None and info_hook not in INFORMATION_CREATED_HOOKS:
        INFORMATION_CREATED_HOOKS.append(info_hook)
    health_hook = getattr(module, "HEALTH_CHANGED", None)
    if health_hook is not None and health_hook not in HEALTH_CHANGED_HOOKS:
        HEALTH_CHANGED_HOOKS.append(health_hook)
    marks = getattr(module, "MARKS", None)
    if marks:
        CHARACTER_MARKS[character_id] = tuple(marks)
    slot = getattr(module, "DETAIL_SLOT", None)
    if slot is not None:
        CHARACTER_DETAIL_SLOTS[character_id] = slot
    containers = getattr(module, "CONTAINERS", None)
    if containers:
        CHARACTER_CONTAINERS[character_id] = dict(containers)
        for container_key, container_cls in dict(containers).items():
            _register_container_type(character_id, container_key, container_cls)
    panel = getattr(module, "PANEL", None)
    if panel is not None:
        CHARACTER_PANELS[character_id] = panel
    used_hook = getattr(module, "ON_ABILITY_USED", None)
    if used_hook is not None and used_hook not in ABILITY_USED_HOOKS:
        ABILITY_USED_HOOKS.append(used_hook)
    failed_hook = getattr(module, "ON_ABILITY_FAILED", None)
    if failed_hook is not None and failed_hook not in ABILITY_FAILED_HOOKS:
        ABILITY_FAILED_HOOKS.append(failed_hook)
    for attr, table in (
        ("ON_MARK_GAINED", MARK_GAINED_HOOKS),
        ("ON_MARK_CONSUMED", MARK_CONSUMED_HOOKS),
        ("ON_MARK_REACHED", MARK_REACHED_HOOKS),
    ):
        hook = getattr(module, attr, None)
        if hook is not None and hook not in table:
            table.append(hook)
    for node, node_hooks in getattr(module, "HOOKS", {}).items():
        table = NODE_HOOKS.setdefault(node, [])
        for hook in (
            node_hooks if isinstance(node_hooks, (tuple, list)) else (node_hooks,)
        ):
            if hook not in table:
                table.append(hook)


# 遭遇修正 provider：把角色/性格的 pseudo_encounter_penalty 转为 chance 修饰器。
def _encounter_penalty_modifier(context: object):
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    hook = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get(
        "pseudo_encounter_penalty"
    )
    if hook is None:
        return
    value = hook(engine, tenant)
    if value:
        yield (
            spec("chance").path("遭遇").flat(-float(value))
            .source("归属", tenant.character_id)
        )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _encounter_penalty_modifier)

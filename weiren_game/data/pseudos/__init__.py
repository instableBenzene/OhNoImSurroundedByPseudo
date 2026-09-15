"""伪人档案聚合：一个文件对应一类伪人（参照房客的 one-file-per-person）。"""

from ..types import PseudoDefinition

from pathlib import Path

from .._discovery import discover_modules

_DISCOVERED = discover_modules(__name__, Path(__file__).parent, require="DEFINITION")

PSEUDOS: dict[str, PseudoDefinition] = {
    module.DEFINITION.id: module.DEFINITION for module in _DISCOVERED.values()
}

# 伪人模块对象注册表。
PSEUDO_MODULES: dict[str, object] = {
    module.DEFINITION.id: module for module in _DISCOVERED.values()
}

# 场景处理器注册表：pseudo_id → {handler名: callable}，来自各伪人模块的
# HANDLERS。伪人协调器应通过本表调用，而不是 if pseudo.pseudo_instance_id == ... 分支。
SCENARIO_HANDLERS: dict[str, dict[str, object]] = {
    pseudo_id: dict(getattr(module, "HANDLERS", {}))
    for pseudo_id, module in PSEUDO_MODULES.items()
}

# 伪人 → 袖珍卡小面板：内容声明在门口那张卡里额外放什么（印记/进度条/文本/标签）。
PSEUDO_CARD_SLOTS: dict[str, object] = {
    pseudo_id: getattr(module, "CARD_SLOT", None)
    for pseudo_id, module in PSEUDO_MODULES.items()
    if getattr(module, "CARD_SLOT", None) is not None
}


def _merge_node_hooks(module: object) -> None:
    """把伪人模块声明的通用节点钩子并入 NODE_HOOKS。"""
    from ..characters import NODE_HOOKS

    for node, hooks in getattr(module, "NODE_HOOKS", {}).items():
        table = NODE_HOOKS.setdefault(node, [])
        for hook in (hooks if isinstance(hooks, (tuple, list)) else (hooks,)):
            if hook not in table:
                table.append(hook)


for _module in PSEUDO_MODULES.values():
    _merge_node_hooks(_module)


def register_pseudo(module: object, *, replace: bool = False) -> None:
    """登记一类新伪人模块（须暴露 DEFINITION）。

    ``replace=True`` 时覆盖同 id（内容包优先级用）。注意节点钩子只增不删——
    被替换的将是「定义与处理器」，旧模块声明的通用节点钩子不会被撤销。
    """
    definition: PseudoDefinition = module.DEFINITION
    if definition.id in PSEUDOS and not replace:
        raise ValueError(f"伪人 ID 重复：{definition.id}")
    PSEUDOS[definition.id] = definition
    PSEUDO_MODULES[definition.id] = module
    SCENARIO_HANDLERS[definition.id] = dict(getattr(module, "HANDLERS", {}))
    slot = getattr(module, "CARD_SLOT", None)
    if slot is not None:
        PSEUDO_CARD_SLOTS[definition.id] = slot
    _merge_node_hooks(module)

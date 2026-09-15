"""性格/羁绊效果模块：一人一文件，按节点声明，系统只查表。

- 中文名：base 八类常规性格写在 ``PERSONALITY_LABELS``；DLC 性格由模块自带
  ``LABEL``（缺省回退为 id，保证界面按中文名取值不会 KeyError）。
- ``PERSONALITIES`` 用 list（可变）：DLC 注册后对既有模块级绑定同样可见，
  顺序 = base 之后追加（随机抽取的确定性以 base 顺序为准，勿改）。
- base 自动发现与 DLC 装载**共用** :func:`register_personality_module` 一条路径。
"""

from pathlib import Path

from .._discovery import discover_modules

# 八类常规性格的中文名（顺序即 PERSONALITIES 顺序）。
PERSONALITY_LABELS: dict[str, str] = {
    "cheerful": "开朗", "loner": "孤僻", "keen": "机敏", "stubborn": "固执",
    "steady": "稳重", "impatient": "急躁", "gentle": "温和", "suspicious": "多疑",
}
# 常规性格键（参与羁绊）；展示用的特殊键由 data/__init__.py 追加到 LABELS。
PERSONALITIES: list[str] = list(PERSONALITY_LABELS)

PERSONALITY_MODULES: dict[str, object] = {}
BOND_TURN_START_HOOKS: dict[str, object] = {}
HEALTH_PROTECTION_HOOKS: dict[str, object] = {}
END_SANITY_COST_HOOKS: dict[str, object] = {}
BOND_END_HEALTH_HOOKS: dict[str, object] = {}
AWAKENING_MULTIPLIER_HOOKS: dict[str, object] = {}
EMOTION_CHANGE_HOOKS: dict[str, object] = {}

from ..characters import NODE_HOOKS as _NODE_HOOKS

# 单值 hook 属性 → 对应查表。
_HOOK_ATTRS = (
    ("HEALTH_PROTECTION", HEALTH_PROTECTION_HOOKS),
    ("END_SANITY_COST", END_SANITY_COST_HOOKS),
    ("BOND_END_HEALTH", BOND_END_HEALTH_HOOKS),
    ("AWAKENING_MULTIPLIER", AWAKENING_MULTIPLIER_HOOKS),
    ("EMOTION_CHANGE_MULTIPLIER", EMOTION_CHANGE_HOOKS),
)


def register_personality_module(personality_id: str, module: object) -> None:
    """登记一个性格模块（base 发现与 DLC 装载共用；同 id 覆盖）。"""
    PERSONALITY_MODULES[personality_id] = module
    for node_id, node_map in getattr(module, "BOND_HOOKS", {}).items():
        if node_id == "turn_start.bond_effects":
            BOND_TURN_START_HOOKS[personality_id] = node_map
    for attr, table in _HOOK_ATTRS:
        value = getattr(module, attr, None)
        if value is not None:
            table[personality_id] = value
    for node, hooks in getattr(module, "HOOKS", {}).items():
        node_table = _NODE_HOOKS.setdefault(node, [])
        for hook in (hooks if isinstance(hooks, (tuple, list)) else (hooks,)):
            if hook not in node_table:
                node_table.append(hook)
    PERSONALITY_LABELS.setdefault(
        personality_id, getattr(module, "LABEL", "") or personality_id
    )
    if personality_id not in PERSONALITIES:
        PERSONALITIES.append(personality_id)


# base：同目录每个 .py 即一类性格（顺序按文件名，影响注册顺序）。
for _id, _module in discover_modules(__name__, Path(__file__).parent).items():
    register_personality_module(_id, _module)


# 性格减伤 → healthConsume/healthDamage 修饰器（按 consume 分流）。
def _health_protection_modifier(context: object):
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    consume = bool(context.get("consume"))
    reduction = 0.0
    for hook in HEALTH_PROTECTION_HOOKS.values():
        added, _shared = hook(engine, tenant, 0.0, consume=consume)
        reduction += added
    if reduction <= 0:
        return
    if consume:
        yield spec("healthConsume").path("消耗").percent(-reduction).source("羁绊", "减伤")
    else:
        yield spec("healthDamage").path("伤害").percent(-reduction).source("羁绊", "减伤")


from weiren_game.modifier_rules import register_modifier_provider as _rp
_rp("healthConsume", _health_protection_modifier)
_rp("healthDamage", _health_protection_modifier)

__all__ = [
    "PERSONALITY_MODULES", "PERSONALITY_LABELS", "PERSONALITIES",
    "BOND_TURN_START_HOOKS", "HEALTH_PROTECTION_HOOKS", "END_SANITY_COST_HOOKS",
    "BOND_END_HEALTH_HOOKS", "AWAKENING_MULTIPLIER_HOOKS", "EMOTION_CHANGE_HOOKS",
    "register_personality_module",
]

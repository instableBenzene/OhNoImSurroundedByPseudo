"""效果注册表 dump（只读）：核对 docs/ARCH.md 的「闸门 / 数值 / 触发」目录。

用法：``python tools/dump_effects.py``（不改任何状态；退出码 0）。

目的：`docs/ARCH.md` §5 的目录容易随内容增长而过时，用本脚本一键列出**所有注册方**，
迁移或评审时以它为准。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import weiren_game.data as D  # noqa: E402


def fname(fn: object) -> str:
    """函数 → ``模块.名`` 的短名。"""
    if fn is None:
        return "-"
    module = getattr(fn, "__module__", "?")
    return f"{module.rsplit('.', 1)[-1]}.{getattr(fn, '__name__', fn)}"


def main() -> int:
    """打印所有注册表；不做任何判定，只列事实。"""
    print("===== NODE_HOOKS（全局节点：角色 HOOKS / 物品 / 性格 / 伪人） =====")
    for node, hooks in sorted(D.NODE_HOOKS.items()):
        print(f"  {node} -> {[fname(h) for h in hooks]}")

    print("\n===== CHARACTER_NODE_HOOKS（按房客） =====")
    for cid, nodes in sorted(D.CHARACTER_NODE_HOOKS.items()):
        for node, fn in nodes.items():
            print(f"  {cid}: {node} -> {fname(fn)}")

    print("\n===== CHARACTER_VALUE_HOOKS（按房客的数值节点） =====")
    for cid, nodes in sorted(D.CHARACTER_VALUE_HOOKS.items()):
        for node, fn in nodes.items():
            print(f"  {cid}: {node} -> {fname(fn)}")

    print("\n===== ITEM_HOOKS（按物品的节点） =====")
    for iid, nodes in sorted(D.ITEM_HOOKS.items()):
        for node, sub in sorted(nodes.items()):
            for key, fn in sub.items():
                print(f"  {iid}: {node}/{key} -> {fname(fn)}")

    print("\n===== GATE_PROVIDERS / GATE_REGISTRY（布尔闸门） =====")
    from weiren_game.modifier_rules import GATE_PROVIDERS, GATE_REGISTRY

    for gate_type, providers in sorted(GATE_PROVIDERS.items()):
        print(f"  {gate_type} -> {[fname(p) for p in providers]}")
    for gate_type, gates in sorted(GATE_REGISTRY.items()):
        for g in gates:
            print(f"  {gate_type}: path={g.path} source={g.source} op={g.operation}={g.value}")

    print("\n===== 状态定义：blocked_emotions / suppresses_conditions =====")
    from weiren_game.condition import STATUS_DEFINITIONS

    for sid, sd in sorted(STATUS_DEFINITIONS.items()):
        blocked = getattr(sd, "blocked_emotions", ())
        suppresses = getattr(sd, "suppresses_conditions", ())
        if blocked or suppresses:
            print(f"  {sid}: blocked={blocked} suppresses={suppresses} hook={fname(getattr(sd,'hook',None))}")

    print("\n===== MODIFIER_PROVIDERS（条件式修饰器，按通道） =====")
    from weiren_game.modifier_rules import MODIFIER_PROVIDERS, MODIFIER_REGISTRY

    for effect, providers in sorted(MODIFIER_PROVIDERS.items()):
        print(f"  {effect} -> {[fname(p) for p in providers]}")

    print("\n===== MODIFIER_REGISTRY（静态修饰器，按通道） =====")
    for effect, modifiers in sorted(MODIFIER_REGISTRY.items()):
        for m in modifiers:
            print(f"  {effect}: path={m.path} source={m.source} op={m.operation}/{m.value_type}={m.value}")

    print("\n===== 伪人场景 HANDLERS =====")
    for pid, handlers in sorted(D.SCENARIO_HANDLERS.items()):
        print(f"  {pid}: {sorted(handlers.keys())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

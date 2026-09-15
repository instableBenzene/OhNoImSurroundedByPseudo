"""内容校验：检查内置内容包的完整性与自描述是否齐全。

用法：``python tools/validate_content.py``（退出码 0 = 无错误；仅警告时仍为 0）。

覆盖：角色（编号唯一 / 头像 / 性格 / 主动技能的派发）、物品（标签）、伪人（人类原型 / 必要处理器）、
信息（地点 / 奖励引用）、以及自描述注册表（TARGET_OPTIONS / CODEX_EXTRA）。
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from weiren_game.data import (  # noqa: E402
    ABILITY_TARGET_OPTIONS,
    CHARACTER_CODEX_EXTRA,
    CHARACTERS,
    CHARACTER_MODULES,
    DEFAULT_PSEUDO,
    INFORMATION_TEMPLATES,
    ITEMS,
    LOCATIONS,
    PERSONALITIES,
    PERSONALITY_LABELS,
    PSEUDOS,
)

errors: list[str] = []
warnings: list[str] = []


def check_characters() -> None:
    """检查角色编号唯一、头像与性格、主动技能派发。"""
    numbers = Counter(c.source_id for c in CHARACTERS.values())
    for number, count in numbers.items():
        if count > 1:
            errors.append(f"角色编号 {number} 重复 {count} 次")
    for cid, definition in sorted(CHARACTERS.items()):
        module = CHARACTER_MODULES.get(cid)
        if module is None:
            errors.append(f"{cid}: 缺少行为模块")
            continue
        if not getattr(module, "AVATAR", ""):
            warnings.append(f"{cid}: 未声明 AVATAR（将回退通用头像）")
        for slot, key in (("主", definition.primary), ("副", definition.secondary)):
            if key not in PERSONALITY_LABELS:
                errors.append(f"{cid}: {slot}性格 {key!r} 未登记")
            elif key not in PERSONALITIES:
                warnings.append(f"{cid}: {slot}性格 {key!r} 为特殊性格（非羁绊正式性格）")
        dispatch = getattr(module, "ACTIVE_DISPATCH", None) or {}
        for ability in definition.actives:
            if ability.id not in dispatch:
                errors.append(f"{cid}: 主动技能 {ability.id!r} 没有 ACTIVE_DISPATCH 处理函数")


def check_items() -> None:
    """检查物品标签与分类。"""
    for iid, item in sorted(ITEMS.items()):
        if not item.tags:
            errors.append(f"物品 {iid}: 没有标签")


def check_pseudos() -> None:
    """检查伪人的人类原型与必要处理器。"""
    for pid, definition in sorted(PSEUDOS.items()):
        if definition.human_character_id not in CHARACTERS:
            errors.append(f"伪人 {pid}: human_character_id {definition.human_character_id!r} 不存在")
    from weiren_game.data import PSEUDO_MODULES

    for pid, module in sorted(PSEUDO_MODULES.items()):
        handlers = getattr(module, "HANDLERS", None) or {}
        for required in ("observed_skills", "progress_text"):
            if required not in handlers:
                warnings.append(f"伪人 {pid}: 建议提供 HANDLERS[{required!r}]")
    if DEFAULT_PSEUDO not in PSEUDOS:
        errors.append(f"DEFAULT_PSEUDO {DEFAULT_PSEUDO!r} 不在 PSEUDOS 中")


def check_information() -> None:
    """检查信息模板的地点与奖励引用。"""
    for tid, template in sorted(INFORMATION_TEMPLATES.items()):
        if template.location_id and template.location_id not in LOCATIONS:
            errors.append(f"信息 {tid}: 地点 {template.location_id!r} 不存在")
        for reward in template.reward_ids:
            if reward not in ITEMS:
                errors.append(f"信息 {tid}: 奖励 {reward!r} 不是已知物品")


def check_registries() -> None:
    """检查自描述注册表是否可调用。"""
    for ability_id, provider in sorted(ABILITY_TARGET_OPTIONS.items()):
        if not callable(provider):
            errors.append(f"TARGET_OPTIONS[{ability_id!r}] 不是可调用对象")
    for cid, provider in sorted(CHARACTER_CODEX_EXTRA.items()):
        if not callable(provider):
            errors.append(f"CODEX_EXTRA[{cid!r}] 不是可调用对象")


def main() -> int:
    """运行全部检查并打印结果。"""
    check_characters()
    check_items()
    check_pseudos()
    check_information()
    check_registries()
    if warnings:
        print("警告：")
        for line in warnings:
            print("  -", line)
    if errors:
        print("错误：")
        for line in errors:
            print("  x", line)
        print(f"内容校验失败：{len(errors)} 个错误，{len(warnings)} 个警告。")
        return 1
    print(f"OK：内容校验通过（{len(CHARACTERS)} 角色 / {len(ITEMS)} 物品 / "
          f"{len(PSEUDOS)} 伪人 / {len(INFORMATION_TEMPLATES)} 信息，{len(warnings)} 个警告）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

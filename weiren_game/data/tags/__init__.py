"""Tag 行为模块：物品通用机制按 tag 存放。

主程序只做“读取物品 tag → 到本注册表找到同名 tag 模块 → 运行其中声明的
方法/修饰器”。标准 tag（food/medicine_kit/surgery_kit…）由原版内容自带，
将来 DLC 加同类物品可复用；DLC 也可用 :func:`register_tag_module` 注册新 tag
行为。
"""

from __future__ import annotations

from pathlib import Path

from .._discovery import discover_modules

# tag id -> 行为模块（模块内暴露 use/modifier 等方法名）。
TAG_BEHAVIORS: dict[str, object] = dict(discover_modules(__name__, Path(__file__).parent))


def register_tag_module(tag: str, module: object) -> None:
    """登记一个 tag 的行为模块（供 DLC 扩展；同 tag 覆盖为后注册者）。"""
    TAG_BEHAVIORS[tag] = module


__all__ = ["TAG_BEHAVIORS", "register_tag_module"]

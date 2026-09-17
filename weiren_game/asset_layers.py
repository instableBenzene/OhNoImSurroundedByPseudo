"""内容层资产的**装载顺序**（低 → 高优先级）：base → 资料包（位次）→ 资源包（位次）。

头像零件（``avatars.py``）与物品图标（``item_icons.py``）共用这一套顺序：
同 id 的文件，位次高的包赢；base 层（``weiren_game/data/``）永远垫底。
资源包总在资料包之后套用，所以资源包也总能盖过资料包自带的同 id 资产。
"""

from __future__ import annotations

from pathlib import Path


def layer_roots(*, dlc_root: str | Path | None = None,
                rp_root: str | Path | None = None) -> list[Path]:
    """按**低 → 高**优先级列出各资料包 / 资源包的根目录（不含 base 层）。"""
    from .config import CONFIG
    from .paths import app_base

    base = app_base()
    dlc_base = Path(dlc_root) if dlc_root else base / "dlc"
    rp_base = Path(rp_root) if rp_root else base / "resourcepacks"
    roots: list[Path] = []
    # 资料包：位次低者先（pack_order 是高 → 低）。
    for name in reversed([n for n in CONFIG.pack_order if n != "base"]):
        roots.append(dlc_base / name)
    # 资源包：位次低者先（`base` 是内置材质那一行，不是目录）。
    for name in reversed([n for n in (CONFIG.resourcepack_order or ()) if n != "base"]):
        roots.append(rp_base / name)
    return roots


__all__ = ["layer_roots"]

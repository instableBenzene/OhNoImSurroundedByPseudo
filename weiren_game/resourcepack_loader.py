"""独立资源包（resourcepacks/<name>/）：只改外观（色调 / 字体 / 贴图 / 素材位）。

与内容包（dlc/）分开、各自有序：**位次高者覆盖低者**；独立资源包始终在内容包之后套用，
所以它总能盖过 DLC 内嵌的 ``resourcepack/``。

目录规范::

    resourcepacks/<name>/
        pack.json         # 可选：{"name": "...", "label": "显示名", "min_game_version": "2.1.0"}
        theme.py          # THEME = {"tokens": {...}, "css": "..."}（只能改色调/字体）
        symbols*.py       # SYMBOLS = {"i-xxx": "<path .../>"}
        assets/           # 素材位文件（background.svg / title.svg ...）
        *.py              # ASSETS = {"background": "background.svg"}
"""

from __future__ import annotations

from pathlib import Path

from .content import CONTENT
from weiren_game.data.lang import TEXT

_LOADED_RP: set[str] = set()

# 资源包清单里的 ``base`` 行 = **内置材质**（``weiren_game/data/resourcepack/``）。
# 与内容包里的 ``base`` 同义：它的位次可调，排在它下方的资源包改不动内置材质。
BASE_MATERIAL = "base"


def _normalize_order(order: "list[str] | tuple[str, ...] | None", available: set[str]) -> list[str]:
    """规整资源包优先级序列：丢弃未知项、去重、保证 ``base`` 存在（缺失则垫底）。"""
    ordered: list[str] = []
    for name in order or ():
        name = str(name)
        if (name == BASE_MATERIAL or name in available) and name not in ordered:
            ordered.append(name)
    if BASE_MATERIAL not in ordered:
        ordered.append(BASE_MATERIAL)
    return ordered


def resourcepack_root(root: str | Path | None = None) -> Path:
    """资源包根目录（默认游戏根目录下的 resourcepacks/）。"""
    from .paths import app_base

    base = Path(root) if root else app_base() / "resourcepacks"
    base.mkdir(parents=True, exist_ok=True)
    return base


def available_resourcepacks(root: str | Path | None = None) -> list[Path]:
    """列出可用资源包目录（跳过 `_`/`.` 开头，以及保留名 `base`）。"""
    base = resourcepack_root(root)
    return sorted(
        path for path in base.iterdir()
        if path.is_dir() and path.name != BASE_MATERIAL
        and not path.name.startswith(("_", "__", "."))
    )


def resourcepack_label(name: str, root: str | Path | None = None) -> str:
    """资源包的显示名（pack.json 的 label > name > 目录名）。"""
    import json

    manifest_path = resourcepack_root(root) / name / "pack.json"
    if manifest_path.is_file():
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        if isinstance(raw, dict):
            return str(raw.get("label") or raw.get("name") or name)
    return name


def load_single_resourcepack(name: str, root: str | Path | None = None) -> None:
    """套用一个独立资源包（重复套用会被跳过）。"""
    from .dlc import import_file, _dlc_module_name, _version_tuple, read_manifest

    if name in _LOADED_RP:
        return
    directory = resourcepack_root(root) / name
    if not directory.is_dir():
        raise FileNotFoundError(f"no such resourcepack: {name}")
    manifest = read_manifest(directory)
    min_version = manifest.get("min_game_version")
    if min_version:
        from .data import GAME_VERSION

        if _version_tuple(min_version) > _version_tuple(GAME_VERSION):
            raise ValueError(
                TEXT["resourcepack_loader.load_single_resourcepack.1"].format(p1=name, p2=min_version, p3=GAME_VERSION)
            )
    for path in sorted(directory.glob("*.py")):
        module = import_file(path, _dlc_module_name(name, "resourcepack", path.stem))
        CONTENT.register_resource_pack(module, pack=name)
    _LOADED_RP.add(name)


def apply_resourcepack_order(order: "list[str] | tuple[str, ...]", root: str | Path | None = None) -> list[str]:
    """按位次（**高 → 低**）套用资源包；``base`` 行 = 内置材质，**位次可调**。

    与内容包同一套语义：从最低优先级套起，轮到 ``base`` 时把内置材质重新盖一遍，
    于是排 ``base`` 下方的资源包无法改写内置材质定义的 token/零件，
    排在 ``base`` 上方（更高优先级）的可以覆盖它们自己的同 id 项。
    只重置**资源包容器**（不动内容注册表），所以可以独立于内容包随时切换。
    """
    available = {path.name for path in available_resourcepacks(root)}
    # 只有用**默认根**时才认"已套用过的名字"；指定 root（测试/自定义目录）时只认该目录里的包，
    # 否则会把别的根下的包名带进来，装载时找不到目录而炸掉。
    if root is None:
        available |= set(_LOADED_RP)
    ordered = _normalize_order(order, available)
    # 起点 = 「内容包装载完之后」的外观（含 DLC 内嵌 resourcepack/），再按位次叠加。
    CONTENT.restore_resourcepack_baseline()
    _LOADED_RP.clear()
    applied_below_base = False
    for name in reversed(ordered):
        if name == BASE_MATERIAL:
            # 只有在确实有包排在 base 下方时才需要"把内置材质抬回来"；
            # base 垫底（常见情形）时什么都不做，于是与旧行为逐字节一致。
            if applied_below_base:
                CONTENT.overlay_resourcepack_base()
            continue
        load_single_resourcepack(name, root=root)
        applied_below_base = True
    return list(ordered)

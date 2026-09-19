"""DLC 内容装载器。

预留的扩展入口：游戏启动时可调用 :func:`load_dlc` 扫描 ``dlc/`` 下的每个
文件夹，把其中的新内容注册进既有注册表（不会改写核心代码）。

目录规范（文件夹名即 DLC 名）::

    dlc/<dlc_name>/
        dlc.json                  # 可选元数据（name/version/min_game_version）
        characters/<char_id>.py   # 每个文件暴露 CHARACTER 或 CHARACTERS，
                                  #   可选 ACTIVE_DISPATCH / requirements_*/costs_*
        personalities/<key>.py    # 每文件一类性格（TIERS/TIER_AT/HOOKS/BOND_* + LABEL）
        items/*.py                # 每个文件暴露 CATEGORY 与 ITEMS
        tags/*.json               # 文件名即 tag，内容为 item_id 或物品名列表（合并进物品）
        tags/<tag>.py             # 文件名即 tag 的行为模块（进 TAG_BEHAVIORS）
        statuses/*.py             # 暴露 STATUSES / EMOTIONS（状态与情绪定义）
        resourcepack/*.py         # 暴露 SYMBOLS（贴图零件）/ THEME（CSS 变量 + css）
        avatars/<section>/<id>.svg  # 头像零件/整张头像（shapes/features/characters，见 avatars.py）
        item/item/<id>.svg        # 自带物品的图标；item/tag/<tag>.svg 按标签兜底
        icon/<section>/<id>.<ext> # 地点/信息/伪人图标（locations/information/pseudos，见 icon_files.py）
        locations/*.py            # 暴露 LOCATIONS
                                  #   可选 MAP_GROUPS：新分组纳入开局抽取
        maps/<id>/map.py          # 自带一张地图（MAP = MapDefinition）
        information/*.py          # 暴露 INFORMATION_TEMPLATES，
                                  #   可选 LOCATION_INFORMATION_MODIFIERS
        pseudos/<pseudo_id>.py    # 每文件一类伪人（DEFINITION + 可选 State/HANDLERS/NODE_HOOKS）
        __init__.py               # 可选：暴露 register(ctx) 自定义入口
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Sequence

from .content import CONTENT
from .content import BASE_PACK
from weiren_game.data.lang import TEXT


_LOADED: set[str] = set()


def dlc_root(root: str | Path | None = None) -> Path:
    """返回 DLC 根目录（默认游戏根目录下的 dlc/）。"""
    from .paths import app_base

    base = Path(root) if root else app_base() / "dlc"
    base.mkdir(parents=True, exist_ok=True)
    return base


def available_dlcs(root: str | Path | None = None) -> list[Path]:
    """列出根目录下可作为 DLC 的文件夹（按名称排序）。"""
    base = dlc_root(root)
    return sorted(
        path
        for path in base.iterdir()
        if path.is_dir() and not path.name.startswith(("_", "__", "."))
    )


def read_manifest(dlc_dir: Path) -> dict[str, Any]:
    """读取 DLC 的 dlc.json 元数据；缺失或损坏返回空 dict。"""
    manifest_path = dlc_dir / "dlc.json"
    if not manifest_path.exists():
        return {}
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _version_tuple(version: str) -> tuple[int, ...]:
    """把版本字符串解析为可比较的整数元组。"""
    return tuple(int(part) if part.isdigit() else 0 for part in str(version).split("."))


def import_file(path: Path, module_name: str):
    """按文件路径导入一个 Python 模块。"""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _dlc_module_name(dlc_name: str, *parts: str) -> str:
    """为 DLC 文件生成唯一且可复现的模块名。"""
    safe = "".join(char if char.isalnum() else "_" for char in dlc_name)
    return ".".join(("_dlc", safe, *parts))


def load_character_file(path: Path, character_id: str, *, replace: bool = False) -> None:
    """注册一个 DLC 角色及其能力模块。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "characters", path.stem))
    definitions = getattr(module, "CHARACTERS", None) or [module.CHARACTER]
    for definition in definitions:
        CONTENT.register_character(definition, replace=replace)
    CONTENT.register_character_module(character_id, module)


def load_item_file(path: Path, *, replace: bool = False) -> None:
    """注册一个 DLC 物资文件（CATEGORY + ITEMS）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "items", path.stem))
    category = getattr(module, "CATEGORY", None)
    if category is None:
        raise ValueError(TEXT["dlc.load_item_file.1"].format(p1=path.name))
    for definition in module.ITEMS.values():
        CONTENT.register_item(definition, category=category, replace=replace)
    hooks = getattr(module, "ITEM_HOOKS", None)
    if hooks:
        for item_id, node_map in hooks.items():
            CONTENT.register_item_hook(item_id, node_map)
    effects = getattr(module, "ITEM_EFFECTS", None)
    if effects:
        for item_id, effect in effects.items():
            CONTENT.register_item_effect(item_id, effect)


def load_location_file(path: Path, *, replace: bool = False) -> None:
    """注册 DLC 地点；可选 ``MAP_GROUPS`` 把新分组纳入开局抽取。

    ``MAP_GROUPS = {"<group>": {"weight": 20, "label": "医疗", "icon": "i-cross",
    "required": False}}``；也允许直接写权重数字。
    """
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "locations", path.stem))
    for location in module.LOCATIONS.values():
        CONTENT.register_location(location, replace=replace)
    for group, spec in getattr(module, "MAP_GROUPS", {}).items():
        if isinstance(spec, dict):
            weight = int(spec.get("weight", 20))
            required = bool(spec.get("required", False))
            label = str(spec.get("label") or group)
            icon = str(spec.get("icon") or "i-gate")
        else:
            weight, required, label, icon = int(spec), False, group, "i-gate"
        CONTENT.register_map_group(group, weight, required=required)
        CONTENT.register_location_group(group, label, icon)


def load_information_file(path: Path, *, replace: bool = False) -> None:
    """注册 DLC 信息模板与可选地点修正。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "information", path.stem))
    for template in module.INFORMATION_TEMPLATES.values():
        CONTENT.register_information_template(template, replace=replace)
    for template_id, modifier in getattr(module, "LOCATION_INFORMATION_MODIFIERS", {}).items():
        CONTENT.register_location_modifier(template_id, modifier)


def load_pseudo_file(path: Path, *, replace: bool = False) -> None:
    """注册一个 DLC 伪人模块（需暴露 DEFINITION、State、HANDLERS）。

    新房客级伪人的运行时协调（PseudoRuntime 场景表）仍在注册化中；模块一旦
    注册成功便会进入 PSEUDOS/SCENARIO_HANDLERS。装载本身不再被保留位阻止。
    """
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "pseudos", path.stem))
    CONTENT.register_pseudo(module, replace=replace)


def load_codex_file(path: Path) -> None:
    """装载一个 DLC 图鉴模块：调用其 register(ctx)，或读取 SECTIONS。"""
    from .data import codex_pack

    module = import_file(path, _dlc_module_name(path.parent.parent.name, "codex", path.stem))
    register = getattr(module, "register", None)
    if callable(register):
        register(codex_pack)
    for section in getattr(module, "SECTIONS", ()) or ():
        codex_pack.register_section(section)


def _load_dir(dlc_dir: Path, subdir: str, loader, *, pattern: str = "*.py",
              replace: bool | None = None) -> list[str]:
    """装载 ``<包>/<subdir>/<pattern>``：逐文件交给 ``loader``，返回文件名（去扩展名）列表。

    ``replace=None`` 时按单参调用 loader，否则 ``loader(path, replace=replace)``。
    所有 ``load_*_dir`` 都是这一个循环，别再各写一份。
    """
    directory = dlc_dir / subdir
    if not directory.is_dir():
        return []
    loaded: list[str] = []
    for path in sorted(directory.glob(pattern)):
        if replace is None:
            loader(path)
        else:
            loader(path, replace=replace)
        loaded.append(path.stem)
    return loaded


def load_tag_file(path: Path) -> None:
    """把 DLC tags/*.json 合并进现有物品 tag。"""
    entries = json.loads(path.read_text(encoding="utf-8"))
    CONTENT.apply_item_tags(path.stem, entries or ())


def load_personality_file(path: Path) -> None:
    """注册一个 DLC 性格（羁绊）模块：文件名即性格键。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "personalities", path.stem))
    CONTENT.register_personality_module(path.stem, module)


def load_status_file(path: Path) -> None:
    """注册一个 DLC 状态/情绪文件（可选暴露 STATUSES、EMOTIONS）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "statuses", path.stem))
    for definition in getattr(module, "STATUSES", ()) or ():
        CONTENT.register_status_definition(definition)
    for definition in getattr(module, "EMOTIONS", ()) or ():
        CONTENT.register_emotion_definition(definition)


def load_resourcepack_file(path: Path) -> None:
    """注册一个资源包文件（贴图零件 ``SYMBOLS`` / 主题 ``THEME``）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "resourcepack", path.stem))
    CONTENT.register_resource_pack(module, pack=dlc_name)


def load_tag_behavior_file(path: Path) -> None:
    """注册一个 tag 行为模块（文件名即 tag）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "tags", path.stem))
    CONTENT.register_tag_module(path.stem, module)


def load_maps_dir(dlc_dir: Path) -> list[str]:
    """装载资料包自带的 maps/<id>/map.py（一张地图一个文件夹）。

    地图是**加**进来的（同 id 覆盖靠包优先级：高优先级后装载），
    所以这里不参与 §3.11 的快照回滚，卸载时由 `_BASE_CONTAINERS` 里的 `MAPS` 整体还原。
    """
    from .data.maps import load_map_dirs

    directory = dlc_dir / "maps"
    if not directory.is_dir():
        return []
    load_map_dirs(directory)
    return sorted(path.parent.name for path in directory.glob("*/map.py"))


def load_single_dlc(
    name: str, root: str | Path | None = None, *, replace: bool = True
) -> None:
    """装载名为 name 的单个 DLC；重复装载会被跳过。

    ``replace`` 默认 True：后装载的包可覆盖同 id 的角色/物品/地点/信息/伪人
    （内容包优先级由装载顺序决定，见 :func:`apply_pack_order`）。
    """
    if name in _LOADED:
        return
    # 首次装载任何包之前先抓 base 快照（幂等）；此后所有登记都能随包回滚。
    CONTENT.ensure_captured()
    dlc_dir = dlc_root(root) / name
    if not dlc_dir.is_dir():
        raise FileNotFoundError(f"no such dlc: {name}")
    manifest = read_manifest(dlc_dir)
    min_version = manifest.get("min_game_version")
    if min_version:
        from .data import GAME_VERSION

        if _version_tuple(min_version) > _version_tuple(GAME_VERSION):
            raise ValueError(
                TEXT["dlc.load_single_dlc.1"].format(p1=name, p2=min_version, p3=GAME_VERSION)
            )
    module_prefix = _dlc_module_name(name)
    init_path = dlc_dir / "__init__.py"
    if init_path.exists():
        package = import_file(init_path, f"{module_prefix}._init")
        register = getattr(package, "register", None)
        if register:
            register(CONTENT)
    # 顺序即注册顺序（同名覆盖靠包优先级，别打乱）。
    _load_dir(dlc_dir, "characters",
              lambda path, replace=False: load_character_file(path, path.stem, replace=replace),
              replace=replace)
    _load_dir(dlc_dir, "personalities", load_personality_file)
    _load_dir(dlc_dir, "statuses", load_status_file)
    _load_dir(dlc_dir, "items", load_item_file, replace=replace)
    _load_dir(dlc_dir, "tags", load_tag_file, pattern="*.json")
    _load_dir(dlc_dir, "tags", load_tag_behavior_file)
    _load_dir(dlc_dir, "codex", load_codex_file)
    _load_dir(dlc_dir, "resourcepack", load_resourcepack_file)
    _load_dir(dlc_dir, "locations", load_location_file, replace=replace)
    _load_dir(dlc_dir, "information", load_information_file, replace=replace)
    load_maps_dir(dlc_dir)

    pseudo_dir = dlc_dir / "pseudos"
    if pseudo_dir.is_dir():
        for path in sorted(pseudo_dir.glob("*.py")):
            load_pseudo_file(path, replace=replace)
    CONTENT.validate_catalogue()
    _LOADED.add(name)
    CONTENT.register_pack(name)


def _normalize_order(order: Sequence[str] | None, available: set[str]) -> list[str]:
    """规整包优先级序列：丢弃未知包名、去重、保证 base 存在（缺失则垫底）。"""
    ordered: list[str] = []
    for name in order or ():
        name = str(name)
        if (name == BASE_PACK or name in available) and name not in ordered:
            ordered.append(name)
    if BASE_PACK not in ordered:
        ordered.append(BASE_PACK)
    return ordered


def apply_pack_order(order: Sequence[str], root: str | Path | None = None) -> list[str]:
    """按**内容包优先级**重建注册表（免重启）。

    ``order`` 为**高 → 低优先级**的包名序列，可含 ``base``：装载从最低优先级开始，
    因此高位包覆盖低位包；轮到 ``base`` 时执行一次 base 覆盖，于是排在 base 下方的包
    无法改写内置内容，而排在 base 上方（更高优先级）的包可以覆盖它们自己的同 id 内容
    例：把「某角色的替换包」放到 base 上方，即可让包内同 id 的角色覆盖内置角色。

    未提供/不存在的名字会被忽略；``base`` 缺失时视为最低优先级。
    返回最终启用的包名（高 → 低）。
    """
    from .content import CONTENT

    available = {path.name for path in available_dlcs(root)}
    ordered = _normalize_order(order, available)
    CONTENT.ensure_captured()
    CONTENT.restore_base()
    _LOADED.clear()
    # 从最低优先级装到最高优先级；base 处让内置内容重新赢过它下方的包。
    for name in reversed(ordered):
        if name == BASE_PACK:
            CONTENT.overlay_base()
        else:
            load_single_dlc(name, root=root, replace=True)
    CONTENT.set_packs(ordered)
    CONTENT.ensure_base()
    # 外观层：独立资源包在内容包之后套用（低 → 高），因此总能盖过 DLC 内嵌的 resourcepack/。
    from .config import CONFIG
    from .resourcepack_loader import apply_resourcepack_order

    CONTENT.capture_resourcepack_baseline()
    # 规整后的清单回写（`base` 恒在；位次可调），供界面与下次启动复用。
    CONFIG.resourcepack_order = apply_resourcepack_order(CONFIG.resourcepack_order, root=root)
    return list(CONTENT.pack_order())


def loaded_dlcs() -> list[str]:
    """返回已装载成功的 DLC 名列表。"""
    return sorted(_LOADED)


def load_configured_dlc() -> list[str]:
    """按总配置 ``pack_order`` 装载启动 DLC（默认只有 base）。"""
    from .config import CONFIG
    from .content import CONTENT

    available = {path.name for path in available_dlcs()}
    # 已装载的包也算"可用"：自定义 root 装载（工具/测试）或目录被改动时，不因找不到而卸载。
    available |= set(_LOADED)
    CONTENT.ensure_captured()
    order = _normalize_order(CONFIG.pack_order or [BASE_PACK, *CONFIG.enabled_dlc], available)
    # 已是目标集合（且都装载完毕）就不重建，避免每次新开局都无谓回滚重装。
    current = list(CONTENT.pack_order())
    if current == order and all(name in _LOADED for name in order if name != BASE_PACK):
        from .resourcepack_loader import apply_resourcepack_order

        apply_resourcepack_order(CONFIG.resourcepack_order)
        return current
    return apply_pack_order(order)

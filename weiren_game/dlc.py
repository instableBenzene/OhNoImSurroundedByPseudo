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
        locations/*.py            # 暴露 LOCATIONS
                                  #   可选 MAP_GROUPS：新分组纳入开局抽取
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
        raise ValueError(f"{path.name} 缺少 CATEGORY")
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


def load_codex_dir(dlc_dir: Path, module_prefix: str) -> list[str]:
    """装载 codex/*.py（DLC 提供的图鉴分节）。"""
    codex_dir = dlc_dir / "codex"
    loaded: list[str] = []
    if not codex_dir.is_dir():
        return loaded
    for path in sorted(codex_dir.glob("*.py")):
        load_codex_file(path)
        loaded.append(path.stem)
    return loaded


def load_tag_file(path: Path) -> None:
    """把 DLC tags/*.json 合并进现有物品 tag。"""
    entries = json.loads(path.read_text(encoding="utf-8"))
    CONTENT.apply_item_tags(path.stem, entries or ())


def load_character_dir(dlc_dir: Path, module_prefix: str, *, replace: bool = False) -> list[str]:
    """装载 characters/*.py，返回角色 id 列表。"""
    character_dir = dlc_dir / "characters"
    ids: list[str] = []
    if not character_dir.is_dir():
        return ids
    for path in sorted(character_dir.glob("*.py")):
        load_character_file(path, path.stem, replace=replace)
        ids.append(path.stem)
    return ids


def load_personality_file(path: Path) -> None:
    """注册一个 DLC 性格（羁绊）模块：文件名即性格键。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "personalities", path.stem))
    CONTENT.register_personality_module(path.stem, module)


def load_personality_dir(dlc_dir: Path, module_prefix: str) -> list[str]:
    """装载 personalities/*.py，返回性格键列表。"""
    directory = dlc_dir / "personalities"
    loaded: list[str] = []
    if not directory.is_dir():
        return loaded
    for path in sorted(directory.glob("*.py")):
        load_personality_file(path)
        loaded.append(path.stem)
    return loaded


def load_status_file(path: Path) -> None:
    """注册一个 DLC 状态/情绪文件（可选暴露 STATUSES、EMOTIONS）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "statuses", path.stem))
    for definition in getattr(module, "STATUSES", ()) or ():
        CONTENT.register_status_definition(definition)
    for definition in getattr(module, "EMOTIONS", ()) or ():
        CONTENT.register_emotion_definition(definition)


def load_status_dir(dlc_dir: Path, module_prefix: str) -> list[str]:
    """装载 statuses/*.py（状态与情绪定义），返回文件列表。"""
    directory = dlc_dir / "statuses"
    loaded: list[str] = []
    if not directory.is_dir():
        return loaded
    for path in sorted(directory.glob("*.py")):
        load_status_file(path)
        loaded.append(path.stem)
    return loaded


def load_resourcepack_file(path: Path) -> None:
    """注册一个资源包文件（贴图零件 ``SYMBOLS`` / 主题 ``THEME``）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "resourcepack", path.stem))
    CONTENT.register_resource_pack(module, pack=dlc_name)


def load_resourcepack_dir(dlc_dir: Path, module_prefix: str) -> list[str]:
    """装载 resourcepack/*.py（材质 / 字体 / 贴图零件），返回文件列表。

    与其它资源包同一条注册路径：同名 token / 贴图 id **覆盖**内置
    （装载顺序 = 包优先级；base 覆盖它下方的包）。
    """
    directory = dlc_dir / "resourcepack"
    loaded: list[str] = []
    if not directory.is_dir():
        return loaded
    for path in sorted(directory.glob("*.py")):
        load_resourcepack_file(path)
        loaded.append(path.stem)
    return loaded


def load_items_dir(dlc_dir: Path, module_prefix: str, *, replace: bool = False) -> list[str]:
    """装载 items/*.py，返回文件列表。"""
    items_dir = dlc_dir / "items"
    loaded: list[str] = []
    if not items_dir.is_dir():
        return loaded
    for path in sorted(items_dir.glob("*.py")):
        load_item_file(path, replace=replace)
        loaded.append(path.stem)
    return loaded


def load_tags_dir(dlc_dir: Path, module_prefix: str) -> list[str]:
    """装载 tags/*.json（把条目合并进物品）。"""
    tag_dir = dlc_dir / "tags"
    loaded: list[str] = []
    if not tag_dir.is_dir():
        return loaded
    for path in sorted(tag_dir.glob("*.json")):
        load_tag_file(path)
        loaded.append(path.stem)
    return loaded


def load_tag_behavior_file(path: Path) -> None:
    """注册一个 tag 行为模块（文件名即 tag）。"""
    dlc_name = path.parent.parent.name
    module = import_file(path, _dlc_module_name(dlc_name, "tags", path.stem))
    CONTENT.register_tag_module(path.stem, module)


def load_tag_behaviors_dir(dlc_dir: Path, module_prefix: str) -> list[str]:
    """装载 tags/*.py（tag 行为模块），返回 tag 列表。"""
    tag_dir = dlc_dir / "tags"
    loaded: list[str] = []
    if not tag_dir.is_dir():
        return loaded
    for path in sorted(tag_dir.glob("*.py")):
        load_tag_behavior_file(path)
        loaded.append(path.stem)
    return loaded


def load_locations_dir(dlc_dir: Path, module_prefix: str, *, replace: bool = False) -> list[str]:
    """装载 locations/*.py（含可选 MAP_GROUPS 新分组）。"""
    locations_dir = dlc_dir / "locations"
    loaded: list[str] = []
    if not locations_dir.is_dir():
        return loaded
    for path in sorted(locations_dir.glob("*.py")):
        load_location_file(path, replace=replace)
        loaded.append(path.stem)
    return loaded


def load_information_dir(dlc_dir: Path, module_prefix: str, *, replace: bool = False) -> list[str]:
    """装载 information/*.py。"""
    info_dir = dlc_dir / "information"
    loaded: list[str] = []
    if not info_dir.is_dir():
        return loaded
    for path in sorted(info_dir.glob("*.py")):
        load_information_file(path, replace=replace)
        loaded.append(path.stem)
    return loaded


def load_single_dlc(
    name: str, root: str | Path | None = None, *, replace: bool = True
) -> None:
    """装载名为 name 的单个 DLC；重复装载会被跳过。

    ``replace`` 默认 True：后装载的包可覆盖同 id 的角色/物品/地点/信息/伪人
    （内容包优先级由装载顺序决定，见 :func:`apply_pack_order`）。
    """
    if name in _LOADED:
        return
    dlc_dir = dlc_root(root) / name
    if not dlc_dir.is_dir():
        raise FileNotFoundError(f"no such dlc: {name}")
    manifest = read_manifest(dlc_dir)
    min_version = manifest.get("min_game_version")
    if min_version:
        from .data import GAME_VERSION

        if _version_tuple(min_version) > _version_tuple(GAME_VERSION):
            raise ValueError(
                f"DLC {name} 要求游戏版本 ≥ {min_version}，"
                f"当前为 {GAME_VERSION}，无法装载。"
            )
    module_prefix = _dlc_module_name(name)
    init_path = dlc_dir / "__init__.py"
    if init_path.exists():
        package = import_file(init_path, f"{module_prefix}._init")
        register = getattr(package, "register", None)
        if register:
            register(CONTENT)
    load_character_dir(dlc_dir, module_prefix, replace=replace)
    load_personality_dir(dlc_dir, module_prefix)
    load_status_dir(dlc_dir, module_prefix)
    load_items_dir(dlc_dir, module_prefix, replace=replace)
    load_tags_dir(dlc_dir, module_prefix)
    load_tag_behaviors_dir(dlc_dir, module_prefix)
    load_codex_dir(dlc_dir, module_prefix)
    load_resourcepack_dir(dlc_dir, module_prefix)
    load_locations_dir(dlc_dir, module_prefix, replace=replace)
    load_information_dir(dlc_dir, module_prefix, replace=replace)

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


def reload_dlc(names: Sequence[str], root: str | Path | None = None) -> list[str]:
    """兼容入口：把 ``names`` 视为"base 之上的启用包"（默认 base 优先级最高）。

    需要让某个包覆盖内置内容时改用 :func:`apply_pack_order`，把它排在 ``base`` 之前。
    """
    return apply_pack_order([BASE_PACK, *[str(name) for name in names]], root=root)


def loaded_dlcs() -> list[str]:
    """返回已装载成功的 DLC 名列表。"""
    return sorted(_LOADED)


def load_dlcs(root: str | Path | None = None) -> list[str]:
    """按名称顺序装载全部 DLC（base 恒为最高优先级），返回本次新装载的名单。"""
    loaded: list[str] = []
    for dlc_dir in available_dlcs(root):
        if dlc_dir.name in _LOADED:
            continue
        load_single_dlc(dlc_dir.name, root=root)
        loaded.append(dlc_dir.name)
    from .content import CONTENT

    CONTENT.set_packs([BASE_PACK, *sorted(_LOADED)])
    return loaded


def load_dlc(root: str | Path | None = None) -> list[str]:
    """兼容入口：装载全部 DLC，返回本次新装载的名单（load_dlcs 别名）。"""
    return load_dlcs(root)


def load_configured_dlc() -> list[str]:
    """按总配置 ``pack_order`` 装载启动 DLC（默认只有 base）。"""
    from .config import CONFIG
    from .content import CONTENT

    available = {path.name for path in available_dlcs()}
    # 已装载的包也算"可用"：自定义 root 装载（工具/测试）或目录被改动时，不因找不到而卸载。
    available |= set(_LOADED)
    order = _normalize_order(CONFIG.pack_order or [BASE_PACK, *CONFIG.enabled_dlc], available)
    # 已是目标集合（且都装载完毕）就不重建，避免每次新开局都无谓回滚重装。
    current = list(CONTENT.pack_order())
    if current == order and all(name in _LOADED for name in order if name != BASE_PACK):
        from .resourcepack_loader import apply_resourcepack_order

        apply_resourcepack_order(CONFIG.resourcepack_order)
        return current
    return apply_pack_order(order)

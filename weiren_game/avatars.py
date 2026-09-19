"""头像「零件」：形状 / 专属特征 / 整张头像，都是**内容层文件**，资源包可覆盖。

目录约定（每件一个文件）::

    weiren_game/data/avatars/shapes/<id>.svg       # 基础形状（i-av1..）
    weiren_game/data/avatars/features/<id>.svg     # 专属特征（i-ft-*）
    weiren_game/data/avatars/characters/<id>.svg   # 兜底立绘（按角色 id；就是"整张头像"）
    dlc/<包>/avatars/<section>/<id>.svg            # 资料包同样可带
    resourcepacks/<包>/avatars/<section>/<id>.svg  # 资源包可覆盖（同 id 高者赢）

（没有第二个"外置美术目录"了：立绘与零件都住内容层。）

优先级（低 → 高）：**base → 资料包（按位次）→ 资源包（按位次）**。
头像只影响**显示**，不写进存档：移除资源包/资料包都不会影响存档可用性。
"""

from __future__ import annotations

import re
from pathlib import Path

SECTION_SHAPES = "shapes"
SECTION_FEATURES = "features"
SECTION_CHARACTERS = "characters"
SECTIONS = (SECTION_SHAPES, SECTION_FEATURES, SECTION_CHARACTERS)

# 与前端保持一致的顺序（哈希派生取模依赖顺序，别随意改）。
FEATURE_ORDER: tuple[str, ...] = (
    "i-ft-hat", "i-ft-cap", "i-ft-hood", "i-ft-glasses", "i-ft-mask", "i-ft-scarf",
    "i-ft-ponytail", "i-ft-headphones", "i-ft-flower", "i-ft-crown", "i-ft-eyepatch",
    "i-ft-bandage", "i-ft-antenna", "i-ft-earring",
)
DEFAULT_SHAPE = "i-av4"

# ---------------------------------------------------------------- 色槽（留给创作者）
# 零件文件里可以写 ``fill="var(--a)"`` / ``stroke="var(--b)"`` 这样的**色槽**，
# 由内容层给颜色（角色模块的 ``AVATAR_COLORS = {"a": "#c0333a", ...}``）。
# 没给就退回主题 token，于是"零件有默认颜色，但创作者可以输入颜色替换"。
# base 与血月包**不使用**色槽 —— 它们只有默认单色，靠主题染色。
SLOT_PATTERN = re.compile(r"var\(--([a-e])\)")
SLOT_TOKEN_DEFAULTS: dict[str, str] = {
    "a": "var(--ink)",
    "b": "var(--ink)",
    "c": "var(--ink2)",
    "d": "var(--ink3)",
    "e": "var(--ink3)",
}
# 允许的颜色写法：hex / rgb()·rgba() / var(--token) / 简单色名。其余（含引号、分号）一律忽略。
_COLOR_OK = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgba?\([0-9.,%\s]+\)|var\(--[a-z0-9-]+\)|[a-zA-Z]{3,20})$")
_LITERAL_COLOR = re.compile(r'(?:fill|stroke)\s*=\s*"(?:#[0-9a-fA-F]{3,8}|rgba?\()')
_SVG_HEAD = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_SVG_SIZE = re.compile(r'\s(width|height)\s*=\s*"[^"]*"', re.IGNORECASE)

# 本次索引里"整张头像来自 **base 层**"的角色 id（`avatar_index` 每次重建）。
# base 层 = `weiren_game/data/avatars/`（兜底立绘就在这里）；包自己放的算包提供。
BASE_PORTRAITS: set[str] = set()
# 零件内联标记的缓存（键含 mtime 与配色，改了文件/换了色自动失效）。
_PART_CACHE: dict[tuple, str] = {}


def avatar_hash(identifier: str) -> int:
    """与前端 ``avatarHash`` 同算法（x*31 + code，无符号 32 位）。"""
    value = 0
    for char in str(identifier):
        value = (value * 31 + ord(char)) & 0xFFFFFFFF
    return value


def _pack_dirs(*, dlc_root: str | Path | None = None,
                rp_root: str | Path | None = None) -> list[Path]:
    """按**低 → 高**优先级列出各内容包/资源包的根目录。"""
    from .asset_layers import layer_roots

    return layer_roots(dlc_root=dlc_root, rp_root=rp_root)


def avatar_index(*, dlc_root: str | Path | None = None,
                 rp_root: str | Path | None = None) -> dict[str, dict[str, Path]]:
    """三张表：section → {id: 文件路径}（按优先级覆盖，高者赢）。

    base 层提供的"整张头像"会被记进 ``BASE_PORTRAITS`` —— 那是兜底立绘；
    包声明 ``avatar_mode: parts`` 时它让位（改成零件组装），**包自己带的**仍优先。
    """
    index: dict[str, dict[str, Path]] = {section: {} for section in SECTIONS}
    BASE_PORTRAITS.clear()
    directories = [Path(__file__).parent / "data" / "avatars",
                   *_pack_dirs(dlc_root=dlc_root, rp_root=rp_root)]
    for root in directories:
        # base 的 weiren_game/data/avatars 本身就是 avatars 目录；包内布局是 <包>/avatars/<section>。
        avatars_root = root if root.name == "avatars" else root / "avatars"
        is_base_layer = avatars_root == Path(__file__).parent / "data" / "avatars"
        for section in SECTIONS:
            directory = avatars_root / section
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.svg")):
                index[section][path.stem] = path
                if section == SECTION_CHARACTERS:
                    # 谁提供的这张整图：base 层的算"兜底"，包提供的算"点名要用"。
                    (BASE_PORTRAITS.add if is_base_layer else BASE_PORTRAITS.discard)(path.stem)
    return index


def resolve_avatar_part(section: str, part_id: str, *, dlc_root: str | Path | None = None,
                        rp_root: str | Path | None = None) -> Path | None:
    """按 id 找零件文件（只接受裸 id / 裸文件名，防目录穿越）。"""
    name = Path(str(part_id)).name
    if not name or name != str(part_id) or section not in SECTIONS:
        return None
    return avatar_index(dlc_root=dlc_root, rp_root=rp_root)[section].get(name)


def avatar_mode(*, dlc_root: str | Path | None = None,
                rp_root: str | Path | None = None) -> str:
    """当前**最终生效**的头像模式：``art``（默认，立绘优先）或 ``parts``（一律零件组装）。

    由包声明（``pack.json`` 里 ``"avatar_mode": "parts"``）；优先级同零件：
    资料包（位次低）→ 资源包（位次高），高者说了算。用于"整套换掉所有配件、
    不要立绘"的外观包（血月就是）。
    """
    import json

    mode = "art"
    for root in _pack_dirs(dlc_root=dlc_root, rp_root=rp_root):
        manifest = root / "pack.json"
        if not manifest.is_file():
            continue
        try:
            raw = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        value = str((raw or {}).get("avatar_mode") or "").strip()
        if value in ("art", "parts"):
            mode = value
    return mode


def part_markup(path: Path, *, colors: dict | None = None) -> str:
    """读零件文件；若它用了色槽，就把 ``var(--a/b/c…)`` 换成具体颜色后返回**内联标记**。

    没用色槽（只有默认单色）的零件返回空串 —— 前端改用"蒙版 + 主题色"渲染，
    这样 base 的零件依旧跟着主题走，而创作者自定颜色的零件保留自己的配色。

    （**头像点缀色已废弃**：不再有"角色点缀色"这个默认值，色槽 a–e 没给就一律跟主题走。）
    """
    try:
        key = (str(path), path.stat().st_mtime_ns, tuple(sorted((colors or {}).items())))
    except OSError:
        return ""
    cached = _PART_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # 只有"声明过颜色"的零件才内联：色槽 var(--x) 或写死的 hex/rgb 都算；
    # 只用 currentColor 的零件（base 那批）交给前端"蒙版 + 主题色"，跟着主题走。
    if not SLOT_PATTERN.search(raw) and not _LITERAL_COLOR.search(raw):
        _PART_CACHE[key] = ""
        return ""
    resolved: dict[str, str] = {}
    for name, value in (colors or {}).items():
        value = str(value).strip()
        if _COLOR_OK.match(value):
            resolved[str(name)] = value

    def _sub(match: "re.Match[str]") -> str:
        name = match.group(1)
        value = resolved.get(name) or SLOT_TOKEN_DEFAULTS.get(name) or "currentColor"
        return value or "currentColor"

    markup = SLOT_PATTERN.sub(_sub, raw)
    # 内联进 HTML：尺寸交给 CSS，去掉固定 width/height，并确保能缩放。
    head = _SVG_HEAD.search(markup)
    if head and "<script" not in markup.lower():
        opening = head.group(0)
        cleaned = _SVG_SIZE.sub("", opening)
        markup = markup[:head.start()] + cleaned + markup[head.end():]
    else:
        markup = ""
    _PART_CACHE[key] = markup
    return markup


def avatar_view(character_id: str, module: object | None, *, dlc_root: str | Path | None = None,
                rp_root: str | Path | None = None) -> dict:
    """某个角色的头像视图：整张 → 形状/特征/点缀色（组装）。

    内容可声明 ``AVATAR``（形状 id）/``AVATAR_FEATURE``；缺省按 id 哈希派生。
    （``AVATAR_ACCENT``/``AVATAR_DECOR`` 与"点缀环"一起废弃了。）
    """
    index = avatar_index(dlc_root=dlc_root, rp_root=rp_root)
    full = index[SECTION_CHARACTERS].get(character_id)
    # `avatar_mode: parts`：跳过 **base 层的兜底立绘**，一律用零件组装
    # （包自己放的 characters/<id>.svg 仍优先——那是明说"这个角色就用这张整图"）。
    if full is not None and not (avatar_mode(dlc_root=dlc_root, rp_root=rp_root) == "parts"
                                 and character_id in BASE_PORTRAITS):
        return {"full": f"/api/avatar/{SECTION_CHARACTERS}/{character_id}"}

    get = (lambda name: getattr(module, name, "") or "") if module is not None else (lambda name: "")
    colors = get("AVATAR_COLORS") if module is not None else {}
    colors = dict(colors) if isinstance(colors, dict) else {}
    shape_id = str(get("AVATAR") or DEFAULT_SHAPE)
    if shape_id not in index[SECTION_SHAPES]:
        shape_id = DEFAULT_SHAPE
    shape = f"/api/avatar/{SECTION_SHAPES}/{shape_id}" if shape_id in index[SECTION_SHAPES] else ""

    hashed = avatar_hash(character_id)
    feature_id = str(get("AVATAR_FEATURE") or "")
    if not feature_id and FEATURE_ORDER:
        feature_id = FEATURE_ORDER[(hashed >> 3) % len(FEATURE_ORDER)]
    feature = (
        f"/api/avatar/{SECTION_FEATURES}/{feature_id}"
        if feature_id in index[SECTION_FEATURES] else ""
    )
    shape_path = index[SECTION_SHAPES].get(shape_id)
    feature_path = index[SECTION_FEATURES].get(feature_id)
    return {
        "full": "",
        # 明确告诉界面："这个角色用零件组装，别再用立绘"（包声明 avatar_mode=parts 时会走到这里）。
        "use_parts": True,
        "shape": shape,
        "feature": feature,
        # 用了色槽的零件给内联标记（创作者自定颜色）；没有则留空，前端走"蒙版 + 主题色"。
        "shape_svg": part_markup(shape_path, colors=colors) if shape_path else "",
        "feature_svg": part_markup(feature_path, colors=colors) if feature_path else "",
    }

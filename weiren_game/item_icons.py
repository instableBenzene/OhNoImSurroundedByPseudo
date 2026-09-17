"""物品图标（**内容层文件**）：专属图标 + 按标签兜底，资料包 / 资源包可覆盖。

目录约定（每件一个文件）::

    weiren_game/data/item/item/<item_id>.svg   # 专属图标
    weiren_game/data/item/tag/<tag>.svg        # 按标签兜底（没有专属图标时）
    dlc/<包>/item/item/<id>.svg                # 资料包同样可带（自带物品的材质）
    dlc/<包>/item/tag/<tag>.svg
    resourcepacks/<包>/item/item/<id>.svg      # 资源包可覆盖（同 id 高者赢）
    resourcepacks/<包>/item/tag/<tag>.svg

优先级（低 → 高）：**base → 资料包（位次）→ 资源包（位次）**；同 id 高者赢。

取图顺序：先找 ``item/item/<item_id>.svg``；没有就按物品标签顺序找 ``item/tag/<tag>.svg``
（顺序由内容层的 ``ITEM_TAG_ICON_PRIORITY`` 决定，"越具象越靠前"，避免被泛标签抢占）。
两者都没有时返回空串，界面回退到内置 ``i-*`` 贴图零件。

**两色渲染**（见 :func:`item_icon_markup`）：SVG 里 ``#d7ddd2`` / ``currentColor`` 是**底色**，
其余颜色是**特征色**；运行期把特征色换成该物品的**品质色**、底色交给主题 ``--ink``，
于是"大部分近白 + 少量品质色点缀"，同一张标签图标用在任何品质的物品上都不会串色。
图标只影响**显示**，不进存档：换/删资源包都不影响存档可用性。
"""

from __future__ import annotations

import re
from pathlib import Path

SECTION_ITEM = "item"
SECTION_TAG = "tag"
SECTIONS = (SECTION_ITEM, SECTION_TAG)

# 图标里的底色写法：写死的旧底色与 currentColor 都算"底色"。
BASE_COLOR = "#d7ddd2"
_HEX = re.compile(r"#[0-9a-fA-F]{3,8}")
_SVG_HEAD = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_SVG_SIZE = re.compile(r'\s(width|height)\s*=\s*"[^"]*"', re.IGNORECASE)

# 内联标记缓存（键含 mtime 与品质色；改文件 / 换包自动失效）。
_ICON_CACHE: dict[tuple, str] = {}


def quality_color(quality: int) -> str:
    """品质色（🔒 锁定 token，资源包改不动）。"""
    from .data.labels import QUALITY_COLORS

    try:
        index = int(quality)
    except (TypeError, ValueError):
        index = 0
    return QUALITY_COLORS[max(0, min(index, len(QUALITY_COLORS) - 1))]


def item_icon_index(*, dlc_root: str | Path | None = None,
                    rp_root: str | Path | None = None) -> dict[str, dict[str, Path]]:
    """两张表：``item`` → {item_id: 文件}、``tag`` → {tag: 文件}（高优先级覆盖低者）。"""
    from .asset_layers import layer_roots

    index: dict[str, dict[str, Path]] = {section: {} for section in SECTIONS}
    roots = [
        Path(__file__).parent / "data" / "item",   # base 层
        *layer_roots(dlc_root=dlc_root, rp_root=rp_root),
    ]
    for root in roots:
        # base 的 data/item 本身就是分区目录；包内布局是 <包>/item/<section>。
        section_root = root if root.name == "item" and (root / SECTION_ITEM).is_dir() else root / "item"
        for section in SECTIONS:
            directory = section_root / section
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.svg")):
                index[section][path.stem] = path
    return index


def tag_order(tags) -> list[str]:
    """物品标签的取图顺序：具象标签优先（内容层登记表），其余按原顺序补在后面。"""
    from .data.labels import ITEM_TAG_ICON_PRIORITY

    owned = [str(tag) for tag in (tags or ())]
    ordered = [tag for tag in ITEM_TAG_ICON_PRIORITY if tag in owned]
    ordered.extend(tag for tag in owned if tag not in ordered)
    return ordered


def resolve_item_icon(item_id: str, tags, *,
                      dlc_root: str | Path | None = None,
                      rp_root: str | Path | None = None) -> Path | None:
    """按"专属 → 标签兜底"找图标文件（只接受裸 id / 裸 tag，防目录穿越）。"""
    index = item_icon_index(dlc_root=dlc_root, rp_root=rp_root)
    name = Path(str(item_id)).name
    if name and name == str(item_id) and name in index[SECTION_ITEM]:
        return index[SECTION_ITEM][name]
    for tag in tag_order(tags):
        if Path(tag).name != tag:
            continue
        if tag in index[SECTION_TAG]:
            return index[SECTION_TAG][tag]
    return None


def item_icon_markup(item, *, dlc_root: str | Path | None = None,
                     rp_root: str | Path | None = None) -> str:
    """物品图标的内联标记：底色→``currentColor``（界面给 ``--ink``）、特征色→品质色。

    找不到图标文件、或标记里带脚本时返回空串（界面回退内置 ``i-*`` 零件）。
    """
    path = resolve_item_icon(getattr(item, "item_id", ""), getattr(item, "tags", ()),
                             dlc_root=dlc_root, rp_root=rp_root)
    if path is None:
        return ""
    accent = quality_color(getattr(item, "quality", 0))
    try:
        key = (str(path), path.stat().st_mtime_ns, accent)
    except OSError:
        return ""
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""

    def _sub(match: "re.Match[str]") -> str:
        return "currentColor" if match.group(0).lower() == BASE_COLOR else accent

    markup = _HEX.sub(_sub, raw)
    head = _SVG_HEAD.search(markup)
    if head is None or "<script" in markup.lower():
        markup = ""
    else:
        # 底色走主题：把 color 写在 <svg> 上（行内样式优先级最高，
        # 不会被 `.slot.q3 svg{color:var(--q3)}` 那类品质色规则带跑）。
        opening = _SVG_SIZE.sub("", head.group(0))
        if 'style="' in opening:
            opening = opening.replace('style="', 'style="color:var(--ink);', 1)
        else:
            opening = opening[:-1] + ' style="color:var(--ink)">'
        markup = markup[:head.start()] + opening + markup[head.end():]
    _ICON_CACHE[key] = markup
    return markup


__all__ = [
    "SECTION_ITEM", "SECTION_TAG", "SECTIONS", "BASE_COLOR",
    "item_icon_index", "item_icon_markup", "quality_color", "resolve_item_icon", "tag_order",
]

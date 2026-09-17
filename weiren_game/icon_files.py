"""地点 / 信息 / 伪人的图标（**彩色插画**）：内容层文件，资料包 / 资源包可覆盖。

目录约定（一件一个文件）::

    weiren_game/data/icon/locations/<location_id>.svg
    weiren_game/data/icon/information/<template_id>.svg
    weiren_game/data/icon/pseudos/<pseudo_id>.svg
    dlc/<包>/icon/<section>/<id>.<ext>          # 资料包可自带（同样能替换内置的）
    resourcepacks/<包>/icon/<section>/<id>.<ext>  # 资源包可覆盖（同 id 高者赢）

``section`` ∈ ``locations`` / ``information`` / ``pseudos``。
优先级（低 → 高）：**base → 资料包（位次）→ 资源包（位次）**。

这些图是**彩色插画**（医疗绿 / 类型色 / 污染红…），前端用 ``<img>`` 渲染，
**不参与配色 token**；所以这里只做"换文件"，不像物品图标那样内联两色。
图标只影响显示，不进存档。
"""

from __future__ import annotations

from pathlib import Path

SECTIONS = ("locations", "information", "pseudos")
EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg", ".webp")


def icon_index(section: str, *, dlc_root: str | Path | None = None,
               rp_root: str | Path | None = None) -> dict[str, Path]:
    """``{id: 文件}``（按优先级覆盖，同 id 高者赢）。"""
    from .asset_layers import layer_roots

    if section not in SECTIONS:
        return {}
    # 低 → 高：base 内容层 → 资料包（位次）→ 资源包（位次）。
    directories = [
        Path(__file__).parent / "data" / "icon" / section,
        *[root / "icon" / section for root in layer_roots(dlc_root=dlc_root, rp_root=rp_root)],
    ]
    index: dict[str, Path] = {}
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                index[path.stem] = path
    return index


def resolve_icon(section: str, icon_id: str, *, dlc_root: str | Path | None = None,
                 rp_root: str | Path | None = None) -> Path | None:
    """按 id 找图标文件（只接受裸 id，防目录穿越）。"""
    if section not in SECTIONS:
        return None
    name = Path(str(icon_id)).name
    if not name or name != str(icon_id):
        return None
    return icon_index(section, dlc_root=dlc_root, rp_root=rp_root).get(name)


def icon_url(section: str, icon_id: str, *, dlc_root: str | Path | None = None,
             rp_root: str | Path | None = None) -> str:
    """图标的 URL（找不到返回空串，界面回退内置单线图标）。"""
    if resolve_icon(section, icon_id, dlc_root=dlc_root, rp_root=rp_root) is None:
        return ""
    return f"/api/icon/{section}/{icon_id}"


__all__ = ["SECTIONS", "EXTENSIONS", "icon_index", "icon_url", "resolve_icon"]

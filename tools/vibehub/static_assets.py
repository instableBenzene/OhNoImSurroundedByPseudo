"""静态构建：把内容层文件资产内联成 data URL。

浏览器版本里没有本机后端，前端原本要请求的 ``/api/icon``、``/api/avatar``、
``/api/resourcepack/asset`` 全部改成这里直接读文件并内联。
只读文件，不参与任何游戏规则。

（本文件在构建时被复制到产物的 ``weiren_game/static_assets.py``，由
``tools/build_vibehub.py`` 完成，源码仓库本身不使用它。）
"""

from __future__ import annotations

import base64
from pathlib import Path

MIME = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def data_url_for(path: object) -> str:
    """把文件内联成 data URL；找不到文件返回空串（界面自己回退内置图标）。"""
    if path is None:
        return ""
    target = Path(path)
    try:
        raw = target.read_bytes()
    except OSError:
        return ""
    mime = MIME.get(target.suffix.lower(), "application/octet-stream")
    return "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii")


def pack_asset_data_url(pack: str, filename: str) -> str:
    """素材位文件（background / title …）：按包名解析后内联。

    解析顺序与 ``web_ui.resolve_pack_asset`` 一致：空包名 = 内置材质，
    否则先找独立资源包、再找资料包。
    """
    name = Path(str(filename)).name
    if not name or name != str(filename):
        return ""
    from .paths import app_base

    candidates: list[Path] = []
    if not pack:
        candidates.append(Path(__file__).parent / "data" / "resourcepack" / "assets" / name)
    else:
        candidates.append(app_base() / "resourcepacks" / Path(pack).name / "assets" / name)
        candidates.append(app_base() / "dlc" / Path(pack).name / "assets" / name)
    for path in candidates:
        if path.is_file():
            return data_url_for(path)
    return ""


__all__ = ["data_url_for", "pack_asset_data_url"]

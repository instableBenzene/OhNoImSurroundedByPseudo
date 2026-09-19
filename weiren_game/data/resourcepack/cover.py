"""内置封面（base 材质）：素材位 `background` + 它自己的动画样式。

素材文件：`data/resourcepack/assets/background.svg`（黄昏小镇）。
资源包只要给同名素材位（`ASSETS = {"background": "…"}`）就整张替换 —— 封面也是"跟着材质包走"的。
"""

from __future__ import annotations
from weiren_game.data.lang import TEXT

ASSETS = {
    "background": "background.svg",
}

THEME = {"tokens": {}, "css": TEXT["data.resourcepack.cover.module.1"]}

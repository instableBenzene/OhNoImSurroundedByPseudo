"""内置封面（base 材质）：素材位 `background` + 它自己的动画样式。

素材文件：`data/resourcepack/assets/background.svg`（黄昏小镇）。
资源包只要给同名素材位（`ASSETS = {"background": "…"}`）就整张替换 —— 封面也是"跟着材质包走"的。
"""

from __future__ import annotations

ASSETS = {
    "background": "background.svg",
}

THEME = {"tokens": {}, "css": """
/* ---- 内置封面（base 材质）：黄昏小镇 + 窗户闪动 / 雾流动 / 门缝的眼睛 ----
   素材本身在 `data/resourcepack/assets/background.svg`（`ASSETS = {"background": ...}`）；
   资源包给同名素材位就整张替换（那时封面按 `<img>` 渲染，这里的动画自然不参与）。 */
.dusk-bg{position:fixed;inset:0;z-index:0;pointer-events:none}
.dusk-bg svg{width:100%;height:100%;display:block}
.dusk-bg .win{fill:var(--amber);animation:flicker 5s ease-in-out infinite}
.dusk-bg .win.b{animation-delay:1.9s}
.dusk-bg .win.c{animation-delay:3.3s}
.dusk-bg .fog{animation:fogmove 30s ease-in-out infinite alternate}
.dusk-bg .fog.slow{animation-duration:44s}
.dusk-bg .eyes{animation:peer 11s ease-in-out infinite}
@keyframes flicker{0%,100%{opacity:.92}45%{opacity:.5}52%{opacity:.85}}
@keyframes fogmove{0%{transform:translateX(-4%)}100%{transform:translateX(5%)}}
@keyframes peer{0%,90%,100%{opacity:0}93%,97%{opacity:.85}}
"""}

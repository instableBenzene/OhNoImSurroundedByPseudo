"""夜班病区（冷青／医疗恐怖）外观包：只覆盖**色调 token**（语义色/品质色/尺寸由 base 锁定）。

取向：平光 + 硬边（荧光灯不投暖影）→ 把斜面配方压掉；强调色是"消毒水青绿"，
`--amber-rgb` 必须与 `--amber` 同步，否则 hover 的透明叠加会串色。
"""

from __future__ import annotations

THEME = {
    "tokens": {
        # 底 / 面板：近黑偏青
        "--bg": "#070a0b",
        "--panel": "#0f1516",
        "--panel2": "#141b1c",
        "--line": "#22302f",
        "--line2": "#1a2424",
        # 文字：冷白（像没校准的荧光屏）
        "--ink": "#dfe8e6",
        "--ink2": "#93a3a1",
        "--ink3": "#6b7877",
        "--ink-hi": "#f4fbfa",
        "--ink-btn": "#e2efec",
        "--ink-head": "#bfe6df",
        # 强调：消毒水青绿
        "--amber": "#3fb59a",
        "--amber-rgb": "63,181,154",
        "--amber-soft": "#17453c",
        "--jade-deep": "#0d2a26",
        "--edge": "#05090a",
        # 按钮
        "--btn-1": "#12201d",
        "--btn-2": "#0b1413",
        "--btn-hi-1": "#1c302c",
        "--btn-hi-2": "#12201d",
        "--pri-1": "#2f8d78",
        "--pri-2": "#1d5a4d",
        "--pri-hi-1": "#46b799",
        "--pri-hi-2": "#24705f",
        # 面板 / 悬浮层 / 启动器
        "--surface-1": "#101a19",
        "--surface-2": "#0b1312",
        "--surface-3": "#080f0e",
        "--surface-tip": "#0d1516",
        "--launcher-1": "#04080a",
        "--launcher-2": "#0a1415",
        "--launcher-3": "#10201f",
        # 平光：荧光灯没有暖斜面
        "--shadow-bevel": "none",
        "--shadow-bevel-lg": "none",
    },
    "css": (
        "/* 夜班病区：平光 + 冷光标题；走廊近处的灯在闪（class 写在背景 SVG 里） */\n"
        ".mc-title{filter:drop-shadow(0 0 14px rgba(63,181,154,.28))}\n"
        ".ward-flicker{animation:ward-flicker 7s steps(1,end) infinite}\n"
        "@keyframes ward-flicker{0%,92%{opacity:1}93%{opacity:.3}94%{opacity:.92}"
        "95%{opacity:.18}96%,100%{opacity:1}}\n"
    ),
}

ASSETS = {
    "background": "background.svg",
}

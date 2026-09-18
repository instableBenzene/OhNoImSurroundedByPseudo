"""夜班病区（惨白／医疗恐怖）外观包：只覆盖**色调 token**（语义色/品质色/尺寸由 base 锁定）。

取向：**平光 + 硬边**（荧光灯不投暖影）→ 压掉斜面配方；强调色是"惨白青"而不是饱和的青绿
——画面里最亮的东西应该是走廊，不是 UI。`--amber-rgb` 必须与 `--amber` 同步，
否则 hover 的透明叠加会串色。
"""

from __future__ import annotations

THEME = {
    "tokens": {
        # 底 / 面板：冷灰（暗场，衬托惨白的走廊；不带绿）
        "--bg": "#0f1314",
        "--panel": "#171d1e",
        "--panel2": "#1d2425",
        "--line": "#333c3c",
        "--line2": "#262e2e",
        # 文字：骨白
        "--ink": "#e6ebe8",
        "--ink2": "#a2acaa",
        "--ink3": "#7b8583",
        "--ink-hi": "#f8fcfa",
        "--ink-btn": "#e2efec",
        "--ink-head": "#dfe8e4",
        # 强调：惨白青（去饱和；不再是墨绿）
        "--amber": "#cbd6d1",
        "--amber-rgb": "203,214,209",
        "--amber-soft": "#4a5854",
        "--jade-deep": "#2c3a36",
        "--edge": "#080b0c",
        # 按钮
        "--btn-1": "#1a2122",
        "--btn-2": "#121819",
        "--btn-hi-1": "#28302f",
        "--btn-hi-2": "#1a2122",
        "--pri-1": "#8fa6a0",
        "--pri-2": "#5d726d",
        "--pri-hi-1": "#b3c4bf",
        "--pri-hi-2": "#748a84",
        # 面板 / 悬浮层 / 启动器
        "--surface-1": "#191f20",
        "--surface-2": "#121819",
        "--surface-3": "#0d1213",
        "--surface-tip": "#151b1c",
        "--launcher-1": "#070a0b",
        "--launcher-2": "#101617",
        "--launcher-3": "#1b2324",
        # 平光：荧光灯没有暖斜面
        "--shadow-bevel": "none",
        "--shadow-bevel-lg": "none",
    },
    "css": (
        "/* 夜班病区：平光 + 冷光标题；走廊近处的灯在闪（class 写在背景 SVG 里） */\n"
        ".mc-title{filter:drop-shadow(0 0 14px rgba(203,214,209,.30))}\n"
        ".ward-flicker{animation:ward-flicker 7s steps(1,end) infinite}\n"
        "@keyframes ward-flicker{0%,92%{opacity:1}93%{opacity:.3}94%{opacity:.92}"
        "95%{opacity:.18}96%,100%{opacity:1}}\n"
    ),
}

ASSETS = {
    "background": "background.svg",
}

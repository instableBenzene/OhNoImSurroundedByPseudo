"""血月（黑红）外观包：只覆盖**色调 token**（语义色/品质色/羁绊/尺寸由 base 锁定，改不动）。

另提供两个素材位：`background`（封面背景）与 `title`（大标题）。
"""

from __future__ import annotations

THEME = {
    "tokens": {
        # 底 / 面板：近黑偏褐红
        "--bg": "#07080a",
        "--panel": "#16100f",
        "--panel2": "#1d1413",
        "--line": "#3a2321",
        "--line2": "#2b1a19",
        # 文字
        "--ink": "#ecdcd8",
        "--ink2": "#a8948f",
        "--ink3": "#7a6663",
        "--ink-hi": "#fff5f4",
        "--ink-btn": "#f2e4e2",
        "--ink-head": "#f0c9c4",
        # 强调：血红
        "--amber": "#d9414a",
        "--amber-rgb": "217,65,74",
        "--amber-soft": "#5c1f24",
        "--jade-deep": "#3a1518",
        "--edge": "#0a0507",
        # 按钮面
        "--btn-1": "#241016",
        "--btn-2": "#150a0d",
        "--btn-hi-1": "#3a1a20",
        "--btn-hi-2": "#221014",
        "--pri-1": "#7a1f28",
        "--pri-2": "#4d1319",
        "--pri-hi-1": "#a12a35",
        "--pri-hi-2": "#66181f",
        # 面 / 悬浮层 / 启动器
        "--surface-1": "#1a0f10",
        "--surface-2": "#120a0b",
        "--surface-3": "#0e0708",
        "--surface-tip": "#150c0e",
        "--launcher-1": "#05070a",
        "--launcher-2": "#120a0d",
        "--launcher-3": "#1e0e12",
    },
    "css": "/* 血月：给主标题留一点血色辉光 */\n.mc-title{filter:drop-shadow(0 0 18px rgba(217,65,74,.35))}\n",
}

ASSETS = {
    "background": "background.svg",
    "title": "title.svg",
}

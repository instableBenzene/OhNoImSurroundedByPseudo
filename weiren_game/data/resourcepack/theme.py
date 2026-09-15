"""默认材质（base 资源包）：CSS 变量与字体栈。

- 本表是**默认材质**；前端 ``:root`` 里留了一份同值的兜底（有单测钉住两份一致），
  启动时经 ``/api/resourcepack`` 把资源包的值写回 ``:root``。
- **可覆盖**（换皮肤就改这些）：底色/面板/线/文字、琥珀强调、字体栈。
- **不可覆盖**（``resourcepack.LOCKED_TOKENS`` 强制）：语义提示色、品质色、羁绊位阶、
  以及尺寸（``--slot`` / ``--w``）——含义与布局不随皮肤变。
"""

from __future__ import annotations

THEME = {
    "tokens": {
        "--bg": '#0b0f10',
        "--panel": '#171e1e',
        "--panel2": '#1d2625',
        "--line": '#33403d',
        "--line2": '#27312f',
        "--ink": '#e6eadf',
        "--ink2": '#9aa79f',
        "--ink3": '#6f7d76',
        "--ok": '#68b998',
        "--danger": '#d46b63',
        "--warn": '#e2a84d',
        "--info": '#71a6c4',
        "--amber": '#e2a84d',
        "--amber-soft": '#6d4a21',
        "--jade-deep": '#274c3e',
        "--q0": '#c4c9c4',
        "--q1": '#66b875',
        "--q2": '#6b9fd1',
        "--q3": '#a77ad1',
        "--q4": '#d6aa45',
        "--q5": '#d86459',
        "--bronze": '#b07a4a',
        "--silver": '#c3ccd0',
        "--gold": '#f3d24e',
        "--prism": '#e3a6ee',
        "--prism-grad": 'linear-gradient(135deg,#7be0a8,#6bb8ff 30%,#c79bff 58%,#ffd76b 82%,#ff9ecb)',
        "--mono": 'Consolas,"Cascadia Mono","Courier New",monospace',
        "--sans": '"Microsoft YaHei UI","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif',
        "--serif": '"STKaiti","KaiTi",serif',
        "--px-font": '"Zpix","Fusion Pixel 12px","Minecraft","SimSun","Microsoft YaHei UI",monospace',
        "--hei": '"Microsoft YaHei UI","Microsoft YaHei","SimHei","PingFang SC","Noto Sans CJK SC",sans-serif',
        "--comic": '"Ink Free","Segoe Print","Comic Sans MS","Bradley Hand","Comic Sans",cursive',
        "--edge": '#0c0c0c',   # 描边黑（按钮/弹窗硬边框）
    "--ink-hi": '#fff',   # 最亮文字（悬停/强调）
    "--ink-btn": '#f2efe2',   # 按钮文字
    "--btn-hi-1": '#3c5247',   # 普通按钮·悬停渐变亮端
    "--btn-hi-2": '#25352c',   # 普通按钮·悬停渐变暗端
    "--btn-1": '#2c3b34',   # 普通按钮·渐变亮端
    "--btn-2": '#1b2620',   # 普通按钮·渐变暗端
    "--pri-2": '#274c3e',   # 主按钮·渐变暗端
    "--pri-1": '#3f6b4f',   # 主按钮·渐变亮端
    "--ink-head": '#f4e6c4',   # 标题文字（奶油）
    "--pri-hi-1": '#4f8663',   # 主按钮·悬停渐变亮端
    "--pri-hi-2": '#315e4c',   # 主按钮·悬停渐变暗端
    "--danger-1": '#8d3a30',   # 危险按钮·渐变亮端
    "--danger-2": '#5f241c',   # 危险按钮·渐变暗端
    "--danger-hi-1": '#b0463a',   # 危险按钮·悬停亮端
    "--danger-hi-2": '#7a2f24',   # 危险按钮·悬停暗端
    "--surface-tip": '#0f1416',   # 悬浮层底色
    "--surface-1": '#1b2622',   # 弹窗/面板渐变亮端
    "--surface-2": '#131b18',   # 弹窗/面板渐变暗端
    "--surface-3": '#0e1514',   # 次级面板底
    "--launcher-1": '#070d10',   # 启动器背景·上
    "--launcher-2": '#0b1416',   # 启动器背景·中
    "--launcher-3": '#101c1a',   # 启动器背景·下
    "--amber-rgb": '226,168,77',   # 强调色的 rgb 分量（透明叠加用）
    "--diff-hard": '#7a3d38',   # 难度标签·更难
    "--diff-easy": '#3d6a52',   # 难度标签·更易
    "--diff-neutral": '#4a4a4a',   # 难度标签·基准
    "--danger-ink": '#ffd9cf',   # 危险按钮/提示上的浅红文字（锁定）
    "--slot": '60px',
        "--w": '1.5px',
    },
    # 可选：额外 CSS（内容包写自己的规则；按装载顺序追加）。
    "css": "",
}

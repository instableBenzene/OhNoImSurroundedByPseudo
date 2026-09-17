"""默认材质（base 资源包）：CSS 变量与字体栈。

- 本表是**默认材质**；前端 ``:root`` 里留了一份同值的兜底（有单测钉住两份一致），
  启动时经 ``/api/resourcepack`` 把资源包的值写回 ``:root``。
- **可覆盖**（换皮肤就改这些）：底色/面板/线/文字、琥珀强调、字体栈、遮罩/面板底、
  棱彩五个色标（`--prism-1..5`，`--prism-grad` 由它们算出来）、
  **阴影/斜面配方**（`--shadow-*`，颜色由 `--edge`/`--ink-hi` 算出）、
  以及**内置剪字标题的整整齐齐一套**（`--title-paper-*` / `--title-ink-*` / `--title-wash`）—— 标题风格也归材质包管。
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
        "--prism-1": '#7be0a8',   # 棱彩渐变 1/5
        "--prism-2": '#6bb8ff',   # 棱彩渐变 2/5
        "--prism-3": '#c79bff',   # 棱彩渐变 3/5
        "--prism-4": '#ffd76b',   # 棱彩渐变 4/5
        "--prism-5": '#ff9ecb',   # 棱彩渐变 5/5
        # 棱彩渐变由上面 5 个色标算出来（改色标就整条变）。
        "--prism-grad": 'linear-gradient(135deg,var(--prism-1),var(--prism-2) 30%,var(--prism-3) 58%,var(--prism-4) 82%,var(--prism-5))',
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
        "--title-paper-1": '#e9e3cf',   # 剪字标题·纸色 1
        "--title-paper-2": '#e3dcc4',   # 剪字标题·纸色 2
        "--title-paper-3": '#ded6bd',   # 剪字标题·纸色 3
        "--title-paper-4": '#ece6d3',   # 剪字标题·纸色 4
        "--title-paper-5": '#e6dfc8',   # 剪字标题·纸色 5
        "--title-ink-1": '#241f18',   # 剪字标题·墨色 1
        "--title-ink-2": '#2b2419',   # 剪字标题·墨色 2
        "--title-ink-3": '#1d1913',   # 剪字标题·墨色 3
        "--title-ink-4": '#332a1c',   # 剪字标题·墨色 4
        "--title-ink-accent-1": '#6f2c25',   # 剪字标题·重音墨 1（「包围」二字备选）
        "--title-ink-accent-2": '#274a33',   # 剪字标题·重音墨 2
        "--flavor-ink": '#c8b48f',   # 图鉴「风味描述」的斜体墨色
        # ---- 遮罩 / 面板底：同一套暗色，数值不同只是为了层次 ----
        "--scrim-soft": 'rgba(6,10,10,.55)',   # 轻：发现浮层 / 档案头 / 提交池底
        "--scrim": 'rgba(6,10,10,.72)',   # 常规：弹窗遮罩 / 清单底
        "--scrim-deep": 'rgba(6,10,10,.88)',   # 更实：Esc 菜单 / 小面板进度条槽
        "--glass": 'rgba(9,15,15,.82)',   # 面板玻璃：启动器面板 / Esc 面板
        "--card-glass": 'rgba(20,28,26,.90)',   # 卡片玻璃：浮起来的卡片（比遮罩亮一档）
        "--moss": 'rgba(6,18,15,.55)',   # 提交区（偏绿）：提交槽 / 提交池
        # ---- 阴影配方：颜色从 --edge/--ink-hi 算出来；整条配方可被材质包替换 ----
        "--shadow-bevel": 'inset 1px 1px 0 color-mix(in srgb,var(--ink-hi) 10%,transparent),inset -1px -1px 0 color-mix(in srgb,var(--edge) 50%,transparent)',   # 小按钮斜面（凸起）
        "--shadow-bevel-lg": 'inset 2px 2px 0 color-mix(in srgb,var(--ink-hi) 10%,transparent),inset -2px -2px 0 color-mix(in srgb,var(--edge) 50%,transparent),0 7px 16px color-mix(in srgb,var(--edge) 45%,transparent)',   # 大按钮斜面 + 投影
        "--shadow-bevel-plus": 'inset 1px 1px 0 color-mix(in srgb,var(--ink-hi) 15%,transparent),0 8px 20px color-mix(in srgb,var(--edge) 50%,transparent)',   # 带投影的小斜面
        "--shadow-press": 'inset -1px -1px 0 color-mix(in srgb,var(--ink-hi) 5%,transparent),inset 2px 2px 3px color-mix(in srgb,var(--edge) 58%,transparent)',   # 按下态（凹进）
        "--shadow-inset": 'inset 0 2px 4px color-mix(in srgb,var(--edge) 55%,transparent),inset 0 -1px 0 color-mix(in srgb,var(--ink-hi) 4.5%,transparent)',   # 槽位内凹
        "--shadow-inset-deep": 'inset 2px 2px 4px color-mix(in srgb,var(--edge) 65%,transparent),inset -1px -1px 0 color-mix(in srgb,var(--ink-hi) 3.5%,transparent)',   # 锁定/更深的内凹
        "--shadow-inset-hover": 'inset 0 2px 5px color-mix(in srgb,var(--edge) 65%,transparent)',   # 槽位悬停内凹
        "--shadow-panel": 'inset 0 0 0 2px rgba(var(--amber-rgb),.17),0 15px 38px color-mix(in srgb,var(--edge) 57%,transparent)',   # 面板：琥珀内描边 + 大投影
        "--shadow-bar": '0 8px 22px color-mix(in srgb,var(--edge) 35%,transparent)',   # 顶栏投影
        "--shadow-tip": '0 15px 32px color-mix(in srgb,var(--edge) 57%,transparent)',   # 提示/悬浮层投影
        "--shadow-float-up": '0 -12px 30px color-mix(in srgb,var(--edge) 53%,transparent)',   # 贴底悬浮窗（向上投影）
        "--shadow-drawer": '8px 0 26px color-mix(in srgb,var(--edge) 45%,transparent)',   # 侧抽屉（向右投影）
        "--shadow-chip": '0 1px 3px color-mix(in srgb,var(--edge) 50%,transparent)',   # 小徽章投影
        "--shadow-title": '0 2px 0 color-mix(in srgb,var(--edge) 45%,transparent),0 0 0 1px color-mix(in srgb,var(--edge) 32%,transparent),inset 0 0 7px var(--title-wash)',   # 剪字标题·纸条
        "--shadow-title-tag": '0 3px 0 color-mix(in srgb,var(--edge) 45%,transparent),0 0 0 1px color-mix(in srgb,var(--edge) 32%,transparent)',   # 剪字标题·「？！」块
        "--text-shadow-bevel": '1px 1px 0 color-mix(in srgb,var(--edge) 60%,transparent)',   # 按钮文字投影
        # 羁绊「金」徽记的渐变（和 --prism-grad 同一路线）
        "--gold-grad": 'linear-gradient(160deg,#fff0b8,#f0c53d 55%,#d9a52e)',
        "--title-wash": 'rgba(120,100,60,.28)',   # 剪字标题纸条的内晕
        "--ok-rgb": '104,185,152',   # --ok 的分量，供 rgba(var(--ok-rgb),α) 用
        "--danger-rgb": '212,107,99',   # --danger 的分量（同上）
    },
    # 可选：额外 CSS（内容包写自己的规则；按装载顺序追加）。
    "css": "",
}

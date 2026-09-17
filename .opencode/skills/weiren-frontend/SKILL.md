---
name: weiren-frontend
description: Use when changing the OhNoImSurroundedByPseudo local web UI ("完蛋，我被伪人包围了！？", weiren_game/webui/index.html) or its material layer — page layout and interaction (launcher / create / saves / settings / codex / in-game boards / dialogs / Esc menu), resource packs, base 材质 tokens, colors and fonts, shadows and cut-out title, icon sets (generic symbols / item icons / location & information icons), avatars and their parts, cover & title assets, or adding a new "material knob" or asset kind. Also covers how to verify a frontend change (node --check + headless CDP probe) and the frontend-specific pitfalls.
---

# weiren-frontend —— 前端与材质

纯 Python 引擎 + 本地 Web UI。**前端只描述结构**（谁在哪、多大、什么层次），
**内容层描述长相**（颜色 / 字体 / 贴图 / 封面标题 / 阴影配方）。

**一条不变量**：前端不得出现具体内容 id/名称，也不得写死颜色。

## 0. 先读

- `AGENTS.md §3`（硬性不变量、注册表清单指向 `content.py::_BASE_CONTAINERS`）
- `docs/PRINCIPLES.md`（"前端只展示 / 机制进后端"）
- `docs/STYLE.md`（风格 + §9 可直接抄的参数表）

## 1. 三层材质（低 → 高，**同名覆盖**）

| 层 | 位置 | 内容 |
| --- | --- | --- |
| **base**（内置材质） | `weiren_game/data/resourcepack/` | `theme.py`（token / 字体栈 / 标题纸墨 / 遮罩 / 阴影配方）、`symbols_base.py`（59 个贴图零件）、`cover.py`（封面素材位 + 封面动画样式） |
| **资料包** | `dlc/<包>/resourcepack/` | 内容包自带外观 |
| **独立资源包** | `resourcepacks/<包>/`（`pack.json` + `theme.py` / `symbols*.py` / `avatars/` / `assets/`） | 只改外观的一层 |

装载顺序 `CONFIG.resourcepack_order`（**恒含 `base` 行且位次可调**，排在 `base` 下方就改不动内置材质）。
前端启动时 `GET /api/resourcepack` 取回，**首帧前**注入 `:root` 的 token 与 `<defs>` 的零件。

## 2. 材质由四样东西组成

1. **token**（`theme.py::THEME["tokens"]`）—— 颜色 / 字体栈 / 遮罩 / 阴影配方，**改颜色只改 token**：
   - 写值的三条合法姿势：`var(--x)`、`rgba(var(--x-rgb),α)`（分量 token，如 `--amber-rgb`）、
     `color-mix(in srgb, var(--edge|--ink-hi) N%, transparent)`（从主题色算出来的阴影/高光）。
     **不要**在 CSS 里出现裸色值。
   - 阴影一律 `box-shadow:var(--shadow-*)` / `text-shadow:var(--text-shadow-*)`（配方也是材质，见 `theme.py` 的 `--shadow-*`）。
   - `LOCKED_TOKENS`：语义提示色 / 品质色 / 尺寸（`--slot`/`--w`）——资源包改不动；羁绊位阶、遮罩、阴影、标题纸墨、棱彩五色标**都可以改**。
     **锁什么 / 放什么会随内容长出来而变**：现状以 `LOCKED_TOKENS` 为准，理由记在 `docs/DECISIONS.md`，判断手法见 `docs/PRINCIPLES.md` §11/§12。
   - **新增一个颜色前先问**：这是「风格」（→ 归一成一条基色 + 一维差异）、「语义」（→ 锁住）、还是「结构」（→ 留在前端的尺寸/布局里）？
2. **贴图零件 `SYMBOLS`**：`{"i-xxx": "<path …/>"}`，`viewBox` 固定 `0 0 24 24`；前端 `ic("i-xxx")` 用 `<use>` 引用。
3. **素材位 `ASSETS`**：`{"background": "x.svg", "title": "y.svg"}` → 前端取 `/api/resourcepack/asset?pack=&file=`；
   **SVG 会内联注入**（这样素材自带的 CSS 动画仍然生效），位图才退回 `<img>`。
4. **文件资产**（按 id 命名，**不需要清单**）：
   头像 `data/avatars/{shapes,features,characters}/<id>.svg`、物品图标 `data/item/{item,tag}/<id>.svg`、
   地点/信息/伪人图标 `data/icon/<section>/<id>.<ext>`、地图 `data/maps/<id>/map.py`。
   资料包/资源包放同名路径即按位次覆盖（顺序见 `weiren_game/asset_layers.py`）。

## 3. 渲染规则（照抄，别自创）

- **物品图标 = 两色**：图标里底色（`#d7ddd2` / `currentColor`）→ 主题 `--ink`，其余颜色 → 该物品的**品质色**；
  后端替换后**内联**下发，前端 `itemIcon(markup, iconId, qualityCls)` 渲染，尺寸走 `.art-inline`。
- **头像**：有整张（`avatars/characters/<id>.svg`）就用整张；否则「形状 × 特征」组装。
  **只能走 `avatarIcon(id, av, cls, art, parts)`** —— `ic("i-av*")` / `ic("i-ft-*")` 渲染出来是**空白**。
- **地点图标**：白底 + 档位特征色的**定制**插画（`<img>`，`LocationDefinition.tier` 只影响配色，界面不写档位文字）。
- **选择页**：`.choice-grid` 是公共卡片语言；`.cv-badge` 是机制分节色徽章；`.art-mask` 只给头像零件用。
- **发现界面**：`#mask.bare` + `.dialog.bare`（无背景板），`.disc-row` 用 `--gap` 控制间距。

## 4. 改前端前记住

- **文案/选项/提示/候选全部由后端下发**；前端只渲染，不做判定与排序。
- 待选时 `hasPending()` 会吞掉除 `#dialog / #pendingBtn / #toastWrap` 外的**所有**点击 ——
  新加菜单/浮层（如 `#pauseMenu`/`#menuBtn`）必须加进放行名单，且它在**启动器里要直接返回 false**。
- `GET /api/codex` 是**一次性**取的（含按当前包解析好的图标标记）：装卸包或换资源包后必须 `CODEX=null`。
- 前端文本统一 `mdText()` / `fmt()`（`·`/换行、`*斜体*`、对话 `“…”`、只有 `【标签】` 解析为悬浮）。
- 新增注册表 → 登记进 `content.py::_BASE_CONTAINERS`，否则卸载 DLC 会残留。
- **`:root` 兜底块必须与 base 的 token 逐一相同**（有单测钉住）：改 `theme.py` 的 token，必须同步改前端 `:root`。

## 5. 常见动作

| 想做的事 | 怎么做 |
| --- | --- |
| 加一个材质旋钮 | `theme.py` 加 token → 前端 `:root` 加同值 → CSS 用 `var(--x)`（别写死） |
| 加一种资产 | base `cover.py` 那样的模块暴露 `ASSETS` → `/api/resourcepack` 自动带出 → 前端在 `applyResourceAssets` 消费 |
| 换/加图标 | 放文件到 `data/icon/<section>/`（或 `data/item/…`、`data/avatars/…`）即生效，无需登记 |
| 让某个资源包生效 | 界面「设置 → 资源包」启用 / ▲▼ 调序 / 应用（`POST /api/dlc`） |

## 6. 验证（前端改动必做）

```powershell
# 1) 语法：把 <script> 抽出来再校验
node --check <抽出的 js>

# 2) 起服务（看 traceback；探针期间给 saves 换临时目录）
$env:WEIREN_SAVES_DIR = Join-Path $env:TEMP ("weiren-ui-" + (Get-Random))
python game_ui.py --no-browser --port 8899

# 3) 发布前压测
node tools/browser_playtest.mjs url=http://127.0.0.1:8730/ games=30 turns=12 budget=420
```

**无头 CDP 探针要点**（本仓库的常规做法）：
`Page.enable / Runtime.enable / Log.enable`；收 `Runtime.exceptionThrown` 与 `Log.entryAdded(level=error)`；
用 `Runtime.evaluate` 驱动 `document.querySelector(...).click()` 与量 `getComputedStyle().getPropertyValue()`；
跑完把 **`game_config.json` 备份/还原**（探针会触发 `/api/dlc` 落盘），临时脚本放 `%TEMP%`。

## 7. 坑（前端专属）

- **`ic("i-av*")` / `ic("i-ft-*")` 是空白**：形状/特征的 `<symbol>` 已搬去内容层 `data/avatars/`。
- **`.qN svg{color:var(--qN)}` 会盖掉内联图标底色**：物品图标把 `color:var(--ink)` 写在 `<svg>` 的**行内 style** 上，别删。
- **`color-mix()` 的环境要求**：Chrome / Edge 111+、Safari 16.2+、Firefox 113+（退路是分量 token）。
- **层叠顺序**：`#mask` 20 → `#pauseMenu` 40 → `.launcher` 60；新浮层别随手给 z-index。
- **改 `:root` 或 `theme.py` 时两边都要动**，否则 `test_resource_pack_defaults_match_frontend_fallback` 挂。
- **`ERR_EMPTY_RESPONSE` 多半是后端异常**：去读服务端 traceback，别在前端猜。

## 8. 相关文件地图

```text
weiren_game/webui/index.html          前端全部（HTML + CSS + JS 单文件）
weiren_game/web_ui.py                 /api/* 后端：state / codex / resourcepack / dlc / saves / quit / abort_start
weiren_game/data/resourcepack/        base 材质（theme / symbols_base / cover + assets/）
weiren_game/avatars.py                头像零件索引（按当前包现算）
weiren_game/item_icons.py             物品图标（专属 + 标签兜底 + 两色替换）
weiren_game/icon_files.py             地点/信息/伪人图标索引
weiren_game/asset_layers.py           三层资产的装载顺序
weiren_game/resourcepack_loader.py    独立资源包装载
resourcepacks/README.md               资源包作者文档（能改什么 / 怎么覆盖）
docs/STYLE.md                         风格与参数表
```

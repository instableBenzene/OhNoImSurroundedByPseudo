# 美术与 UI 风格

> 冻结的设计稿基准在 `design/svc-mock.html` + `design/README.md`（静态假数据）；
> **实际参数以本文件 §9 为准**（从 `weiren_game/webui/index.html` 的 `<style>` 提取）。

## 1. 色调（SVC：暖深绿 + 琥珀）
- 背景 `#0b0f10`；面板 `#171e1e` → `#1d2625`；线 `#33403d` / `#27312f`。
- 文字 `#e6eadf`（次 `#9aa79f` / `#6f7d76`）；主强调**琥珀 `#e2a84d`**。
- 次强调：翠绿 `#68b998`、砖红 `#d46b63`、雾蓝 `#71a6c4`。
- 品质六色：白 `#c4c9c4`、绿 `#66b875`、蓝 `#6b9fd1`、紫 `#a77ad1`、金 `#d6aa45`、红 `#d86459`（**直接映射到图标颜色**）。
- 字体：正文/标题用**黑体**（雅黑/思源黑栈）；数字/代号等宽。

## 2. 启动器（Minecraft 风，全屏多页）
- 全屏覆盖、保持独立页面观感；哈希路由 `#/main`、`#/saves`、`#/settings`、`#/dlc`、`#/create`、`#/codex`。
- 顶部中上标题：**报纸剪字拼贴**——每字有泛黄纸片底、字号/位移/旋转微扰；「完蛋」更大，「包围」用暗红或暗绿；结尾「？！」并排在右、带旋转。
- 按钮：MC 风立体（渐变 + 2px 黑边 + 内高光/内阴影）；主按钮翠绿。
- 若字体缺失，用 canvas 低分辨率+整数倍放大的像素化方案也可（历史实现）。

## 3. 游戏内
- 顶栏：左 `Esc 退出 | 保存 | 回溯`，右信息（状态 + 回合/难度/种子/屋内/门口）；按钮与面板同 MC 风。
- 对话/弹窗：深绿底 + 2px 黑边 + 琥珀内描边；退出弹窗只留「退出游戏 / 返回游戏」。
- 提示：**底部上滑吐司**（3s 自动消失、点击即消），不用阻断式 `alert`。

## 4. 图鉴
- 左列表（可滚动）+ 右详情；分页：房客 / 物资 / 地点 / 信息 / 伪人 / 羁绊 / 机制（+ DLC 分节）。
- 详情用"档案"式头部（大头像/图标 + 名称 + 副信息 + 标签 chip）。
- 标签用 `.cd-chip` 小 chip；品质色上图标；命运牌用无竖线表格（正/逆同列）。
- 文本标记：`·`/换行 → 换行；`*斜体*` 淡色；`**加粗**`；正文中出现的 tag 词自动悬浮出该 tag 物品列表；物资对话 `“…”` 自动换行。

## 5. 图标与头像
- 图标：单线 SVG（`stroke:currentColor`），线条简洁；地点图标体现**类型与规模差异**（大/小医疗点、餐车、货箱、夜市…）。
- 头像：**基础形状（12）× 专属特征（14：帽/兜帽/眼镜/耳机/口罩/发饰…）× 点缀色（低饱和，环/点/弧）**；主色仍为琥珀，点缀色只作装饰、不喧宾夺主。
- **外置美术**（`assets/art/` + `manifest.json`）：已有图时用 `<img class="art-img">` 覆盖内置图标，缺图回退。
  - 尺寸：`.cd-av .art-img` 72px、`.td-left .av .art-img` 56px、`.av .art-img` 42px、`.cv .art-img` 19px（图鉴列表/信息行）、`.loc-name .art-img` 19px。
  - 现状：24 房客 + 3 伪人 + 57 物资 + 25 地点 + 22 信息，共 131 张；**物资的品质色直接烧在 SVG 里**（`img` 不继承 `currentColor`）。
  - 上色约定：物资=品质色；地点=功能色（医疗绿/食物琥珀/工具雾蓝/混合灰）；信息=类型色（物资线索琥珀/地点修正雾蓝/房客状态紫/伪人红）。
  - 详见 `assets/art/README.md` 与 `docs/DECISIONS.md` 顶部条目。

## 6. 原则
- 内容相关文案一律走内容层；系统/前端只渲染。
- 动效克制（悬停变色、吐司上滑、启动器轻微渐变），整体统一、不花哨。
- **交互靠常理**：拖进去的能拖回来（如厄瑞玻斯上交槽，拖走即取回，不设"取回"按钮）；
  一个动作能解决就别堆按钮；某个操作放进去的，玩家应能用同样直觉拿回来。
- **不擅自加限制**：没声明的机制不要默认加上（如"每回合 1 次"必须由内容显式声明）。
- **查看放行、决定才阻断**：点空气/开卡/看日志等查看类点击不拦截；
  阻断只用于必须做的选择，且提供"隐藏 / 显示"而非"取消"（收起后仍可看场面）。
- **状态如实**：证伪就显示已证伪；没生效就显示未生效；不拿近似值冒充真相。
- **表现层要稳**：同流程不同步骤同宽；行高/宽度固定；长文本 `nowrap + ellipsis`，字体差异不导致错乱。
- 新按钮参数复用既有 `.btn` / `.btn.p`，不另起一套。

## 7. 图鉴细节（实现约定）

- **详情图标**：左上角图标 `.cd-dossier .cd-av svg.ic` = **72×72**（注意用高优先级选择器，避免被全局 `svg.ic.lg` 覆盖）。
- **品质上色**：物资图标与列表行按品质着色（`.cd-av.qN svg` / `.cv.qN svg`）。
- **tag 解析**：正文中**只有 `【标签】`** 才渲染为可悬浮的标签链接（普通"食物"等词不解析）；物资下方标签 chip 也可悬浮。
- **文本标记**：`·`/换行→换行（保留 `·` 项目符号）；`*斜体*` 淡色；`**加粗**`；对话 `“…”` 自动换行。
- **书籍**：正文正常显示，**仅把"获得的能力"放进高亮「获得能力」框**（`.cd-book`）。
- **筛选/排序**（物资页）：品质多选、标签多选（并集）、排序（默认/品质/名称）；全不选＝全部。
- **头像**：基础形状（12）× 专属特征（14：帽/兜帽/眼镜/耳机/口罩/发饰…）× 低饱和点缀色（环/点/弧）；主色仍为琥珀。
- **命运牌**：无竖线表格（正位/逆位同列）。
- **交互**：底部上滑吐司（3s 自动消失）；ESC 弹窗只留「退出游戏 / 返回游戏」。

## 8. 响应式（游戏内布局，防中间被挤没）
- 三栏列宽**流式**：`clamp(240px,20vw,340px) | minmax(0,1fr) | clamp(232px,17vw,320px)`；房客卡与网格也随之流式（`minmax(176px,1fr)`）。
- 断点：
  - `>1360`：三栏；
  - `1120~1360`：进一步收窄侧栏 + 卡片 `minmax(162px,1fr)`；
  - `≤1120`：改为**纵向堆叠**（board → 仓库 → 日志 → 详情），中间占满整宽；
  - `≤720`：顶栏/统计与卡片进一步紧凑。
- 原则：**中间内容优先**；侧栏可被压缩/下移，绝不让房客席位失去空间。

补充（**纵向**也会"吞席位"）：短屏（如 1366×768、1280×720）时，避难所上方的门口区会挤扁"房客席位"。
- 已给席位保底高度：`.roster{min-height:230px;flex:1 1 auto}`、`.roster .tenant-grid{min-height:170px;overflow-y:auto}`。
  **注意**：席位必须**可压缩**（`flex:1 1 auto`，只靠 `min-height` 兜底），否则内部网格不溢出、**席位自己的滚轮会消失**；矮屏时由 `.board` 一并滚动。
- `@media (max-height:840px)` 自动压缩门口区（`.door-zone`/`.door-button`）。
- 结论：**横向**（窄屏堆叠）与**纵向**（矮屏保底）都要防护，房客席位永远有空间。

补充：**耐久条**。带耐久的物资（手术包/医药箱/工具等）在仓库/背包槽位**底部显示一条耐久条**：
- 满→绿（`--ok`）、≤55%→黄（`--warn`）、≤25%→红（`--danger`）；悬浮物品显示`耐久 当前/上限`。
- 数据侧：物品条目第 10/11 项为当前/上限耐久；**耐久品按实例下发**（不按 item_id 聚合，避免耐久被合并丢失）。

## 9. 参数表（从实现提取，改样式以这里为准）

> **颜色 token / 字体由资源包定义、前端保留默认材质兜底**：前端 `:root` 里那份是**默认材质**
> （值与 base 资源包 `weiren_game/data/resourcepack/theme.py` 的 `THEME["tokens"]` **逐一相同**，
> 由单测钉住）；资源包（内容层，DLC 的 `resourcepack/` 同名覆盖）只做**覆盖/追加**，
> 启动时写回 `:root`。所以"资源包不可用"时界面**保持默认观感**。
> **尺寸与结构**始终在前端 `<style>` 里。
>
> **哪些 token 可以被材质包改**（其余一律锁定，见 `data/resourcepack/__init__.py` 的 `LOCKED_TOKENS`）：
> - ✅ 色调/材质：`--bg/--panel/--panel2/--line/--line2/--ink/--ink2/--ink3`、`--amber/--amber-soft/--jade-deep`、
>   `--amber-rgb`（强调色的 rgb 分量，供 `rgba(var(--amber-rgb),α)` 的 hover/选中叠加用——**与 `--amber` 必须同步**）、
>   `--ink-hi/--ink-btn/--ink-head`、`--edge`、按钮面 `--btn-*/--pri-*/--surface-*`、
>   启动器背景 `--launcher-1/2/3`、字体栈（`--mono/--sans/--serif/--hei/--comic/--px-font`）
> - ❌ 锁定（含义/尺寸）：语义 `--ok/--danger/--warn/--info`、危险红 `--danger-*` 与 `--danger-ink`、
>   难度标签 `--diff-hard/--diff-easy/--diff-neutral`、品质 `--q0..--q5`、
>   羁绊位阶 `--bronze/--silver/--gold/--prism/--prism-grad`、尺寸 `--slot/--w`
>
> **只剩 5 处字面量**（刻意不收编）：报纸剪字标题的纸/墨色（`.mc-title` / `.title-bangs b`）
> 与金牌徽记的金属渐变三色（`.tier-badge.t-gold`）。

### 颜色 token（`:root`）
- 底 `--bg:#0b0f10`；面板 `--panel:#171e1e` / `--panel2:#1d2625`；线 `--line:#33403d` / `--line2:#27312f`
- 文字 `--ink:#e6eadf` / `--ink2:#9aa79f` / `--ink3:#6f7d76`
- 语义 `--ok:#68b998` / `--danger:#d46b63` / `--warn:#e2a84d` / `--info:#71a6c4`
- 强调 `--amber:#e2a84d`、`--amber-soft:#6d4a21`、`--jade-deep:#274c3e`
- 品质 `--q0..--q5 = #c4c9c4 / #66b875 / #6b9fd1 / #a77ad1 / #d6aa45 / #d86459`
- 羁绊位阶 `--bronze:#b07a4a` / `--silver:#c3ccd0` / `--gold:#f3d24e` / `--prism:#e3a6ee`；
  棱彩另有多色渐变 `--prism-grad`（档名渐变文字、图标描边 `#prismGrad`、徽记渐变底）

### 字体栈
- 正文 `--sans:"Microsoft YaHei UI","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif`
- 标题/按钮 `--hei:"Microsoft YaHei UI","Microsoft YaHei","SimHei","PingFang SC","Noto Sans CJK SC",sans-serif`
- 数字/代号 `--mono:Consolas,"Cascadia Mono","Courier New",monospace`
- 楷体 `--serif:"STKaiti","KaiTi",serif`；另有 `--comic`（启动器偶用）

### 按钮
- 常规 `.btn`：`font 13px(--hei)`；底 `linear-gradient(#2c3b34,#1b2620)`；`border:2px solid #0c0c0c`；`radius:3px`；
  `box-shadow:inset 1px 1px 0 rgba(255,255,255,.10), inset -1px -1px 0 rgba(0,0,0,.5)`；`padding:7px 14px`；`transition .14s`
  - hover：`linear-gradient(#3c5247,#25352c)` + 琥珀边
  - 主按钮 `.btn.p`：`linear-gradient(#3f6b4f,#274c3e)`，hover `#4f8663,#315e4c`
- 启动器 `.mc-btn`：`font 17px(--sans) / padding:14px 22px`；双层内阴影 `inset ±2px` + `0 7px 16px rgba(0,0,0,.45)`；
  `text-shadow:1px 1px 0 rgba(0,0,0,.6)`；按下 `translateY(2px)`；`.wide` 全宽 `20px/19px 26px`

### 弹窗
- `.dialog`：`width:min(560px,92vw)`；底 `linear-gradient(180deg,#1b2622,#131b18)`；`border:2px solid #0c0c0c`；`radius:3px`；
  `box-shadow:inset 0 0 0 2px rgba(226,168,77,.18), 0 18px 40px rgba(0,0,0,.6)`；`.dialog.wide = min(880px,94vw)`
- 头 `.dhead` `padding:12px 16px`（底 `rgba(0,0,0,.22)`）；体 `.dbody` `padding:16px`；脚 `.dfoot` `padding:12px 16px`（底 `rgba(0,0,0,.18)`）

### chip / badge / 槽位
- `.chip`：`inline-flex; gap:4px; border:1px solid var(--line); padding:1px 6px; font 11px(--mono)`；`danger/warn/info` 变色
- `.badge`：`font 10.5px(--mono); padding:0 6px`；`pending`=琥珀、`true`=绿、`false`=红、`seal`=红
- `.slot`：`--slot:60px`（宽高）；品质用**左边框 2px**着色（`.slot.qN`）；`.drop` 琥珀边 + `rgba(226,168,77,.12)`
- 耐久条在槽位底部：满→绿 / ≤55%→黄 / ≤25%→红

### 房客卡 / 网格
- `.tenant`：`min-height:190px`、`padding:10px`、`gap:5px`、底 `linear-gradient(180deg,--panel,--panel2)`、`transition .15s`；
  hover `translateY(-1px)`；`.searching` 琥珀虚线边 + 头像 `.6`
- `.tenant-grid`：`repeat(auto-fill,minmax(176px,1fr))`（≤1360 → 162px；≤720 → 142px）

### 技能条（房客详情）
- `.ability`：两行（`.ab-head` 徽记/名称/chip/状态 → `.ab-text` 描述），`flex column`、`gap:5px`、`padding:8px 10px`
- `.ability.usable` / `.ability.locked`：复用 `.btn` 视觉——`border:2px solid #0c0c0c`、`radius:3px`、
  底 `linear-gradient(#2c3b34,#1b2620)`、`box-shadow:inset 1px 1px 0 rgba(255,255,255,.10),inset -1px -1px 0 rgba(0,0,0,.5)`
  - `.usable`：`cursor:pointer`；hover `#3c5247→#25352c` + 琥珀边 + 白字；`:active` `translateY(2px)` + 内凹
  - `.locked`（本回合不可用）：常驻 `translateY(2px)` + `inset 2px 2px 4px rgba(0,0,0,.65)`、`opacity:.72`（`.disabled` 再降到 `.5`）
- 被动技能＝普通条目，不加 `usable/locked`

### 信息条（现有信息）
- `.acc-head.head2`：纵向两行；第一行 `.acc-line` = 信息简称（`flex:1` + `nowrap/ellipsis`）+ 折叠箭头；
  第二行 `.acc-line` = 失效 chip 贴左 + 状态徽记 `margin-left:auto` 贴右

### 布局与层级
- 三栏 `.shell`：`clamp(240px,20vw,340px) | minmax(0,1fr) | clamp(232px,17vw,320px)`
  （≤1360 收窄、≤1120 纵向堆叠、≤720 紧凑、`max-height:840` 压缩门口区）
- 搜索两栏 `.search-layout`：`1fr 1fr`，`height:40vh; min-height:210px`
- 图鉴 `.codex-split`：`310px | 1fr`，`height:64vh`
- `z-index`：dusk-bg `0` < lpane `1` < mask `20` < bond-drawer `45` < launcher/tip `60` <
  pending-btn `70` < peek-toggle `71` < lc-dialog `80` < toast-wrap `95` < tip-layer `300`

### 动效
- 过渡 `.14s`（按钮）/ `.15s`（卡片）；吐司 `toastIn .18s`；启动器背景 `flicker`/`fogmove`；
  `@keyframes`：`flicker, fogmove, peer, toastIn`
- 悬停详情：普通 chip 即显；伪人技能 **1s** 后弹出（`.door-zone` 整块触发）

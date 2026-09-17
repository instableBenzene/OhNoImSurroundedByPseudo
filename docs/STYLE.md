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
- **内容层资产**（`weiren_game/data/` 下，资料包/资源包可同 id 覆盖）：
  - **物品图标** `data/item/{item,tag}/<id>.svg`：**两色** —— 底色（`#d7ddd2` / `currentColor`，前端给 `--ink`）
    + 特征色（运行期换成该物品的**品质色**）。后端内联下发，尺寸走 `.art-inline`（槽 20px / 图鉴行 19px / 详章 72px）。
  - **头像零件** `data/avatars/{shapes,features,characters}/`：形状吃 `--ink`（蒙版）、特征吃点缀色；见 `resourcepacks/README.md`。
- **封面 / 大标题**：base 材质自带（封面 = `data/resourcepack/assets/background.svg` + base 的动画样式；
  标题 = 剪字渲染器 + `--title-paper-*`/`--title-ink-*` token）。素材位 `background`/`title` 一给就整块替换。
- **地点 / 信息 / 伪人图标**：内容层 `data/icon/<section>/<id>.<ext>`（资料包/资源包同 id 覆盖，经 `GET /api/icon/<section>/<id>` 提供）→ 有图用 `<img class="art-img">` 覆盖内置单线图标，缺图回退。
  - 尺寸：`.cd-av .art-img` 72px、`.td-left .av .art-img` 56px、`.av .art-img` 42px、`.cv .art-img` 19px（图鉴列表/信息行）、`.loc-name .art-img` 19px。
  - 现状：3 伪人 + 25 地点 + 22 信息，共 50 张（房客立绘 24、物品图标 57+21 已搬进内容层）。
  - 上色约定：地点=功能色（医疗绿/食物琥珀/工具雾蓝/混合灰）；信息=类型色（物资线索琥珀/地点修正雾蓝/房客状态紫/伪人红）。
  - 详见 `resourcepacks/README.md` 与 `docs/DECISIONS.md` 顶部条目。

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

## 9. 参数表（改样式的入口；**具体色值不在这里复制**）

> **颜色的唯一来源**：`weiren_game/data/resourcepack/theme.py`（token / 字体栈 / 遮罩 / 阴影配方 / 标题纸墨 / 棱彩色标）。
> 前端 `:root` 里有一份**同值的默认材质兜底**（单测钉住逐一相同）；启动时 `GET /api/resourcepack`
> 把资源包的 token 写回 `:root`、把贴图零件注入 `<defs>`。**尺寸与结构**始终在前端 `<style>` 里。
> 外观那摊的完整说明见 `.opencode/skills/weiren-frontend/SKILL.md`。
>
> - ✅ **资源包可改**：色调与字体栈、**遮罩/面板底**（`--scrim*`/`--mask*`/`--glass`/`--card-glass`/`--moss`）、
>   **阴影配方**（`--shadow-*`，整套 UI 的斜面/投影都引用它们，写 `none` 就是扁平风）、
>   **标题整套**（`--title-paper-*`/`--title-ink-*`/`--title-wash`）、
>   **羁绊四档**（`--bronze/--silver/--gold/--gold-grad/--prism/--prism-grad`）、棱彩五色标（`--prism-1..5`）。
> - ❌ **锁定**（含义/尺寸，见 `data/resourcepack/__init__.py::LOCKED_TOKENS`）：语义 `--ok/--danger/--warn/--info`
>   与 `--danger-*`、难度 `--diff-*`、品质 `--q0..--q5`、尺寸 `--slot`/`--w`。
> - **CSS 里不许出现裸色值**，只有三条合法姿势：`var(--x)`、`rgba(var(--x-rgb),α)`、
>   `color-mix(in srgb, var(--edge|--ink-hi) N%, transparent)`（阴影/高光从主题色算出；需要 Chrome/Edge 111+）。

### 颜色与阴影
- 分组：底 / 面板 / 线 / 文字、琥珀强调（`--amber` + `--amber-rgb` 分量）、语义、品质六档、羁绊四档、
  **遮罩 / 面板底**、**阴影配方**（`--shadow-*` 一族 —— 整套 UI 的斜面与投影都引用它们，
  写 `none` 就是扁平风）。**token 名与值一律去 `theme.py` 看**（这里不复制清单，会漂）。

### 字体栈
- 正文 `--sans`、标题/按钮 `--hei`、数字/代号 `--mono`、楷体 `--serif`，另有 `--comic`/`--px-font`（值在 `theme.py`）。

### 按钮
- 常规 `.btn`：`font 13px(--hei)`；面 `linear-gradient(var(--btn-1),var(--btn-2))`；`border:2px solid var(--edge)`；
  `radius:3px`；`box-shadow:var(--shadow-bevel)`；`padding:7px 14px`；hover 换 `--btn-hi-*` + 琥珀边。
- 主按钮 `.btn.p`：`linear-gradient(var(--pri-1),var(--pri-2))`，hover `--pri-hi-*`。
- 启动器 `.mc-btn`：`font 17px(--sans)`；`box-shadow:var(--shadow-bevel-lg)`；`text-shadow:var(--text-shadow-bevel)`；
  按下 `translateY(2px)`；`.wide` 全宽 `20px/19px 26px`。

### 弹窗
- `.dialog`：`width:min(560px,92vw)`；底 `linear-gradient(180deg,var(--surface-1),var(--surface-2))`；
  `border:2px solid var(--edge)`；`radius:3px`；`box-shadow:var(--shadow-panel)`；`.dialog.wide = min(880px,94vw)`。
- **面板高度**：`.lpane-inner.tall`（创建对局 / 存档 / 资料包 / 资源包）`min-height:90vh`，其 `.mc-panel`
  `min-height:68vh` + `max-height:86vh` + `overflow-y:auto`；列表 `.dlc-list`/`.save-list` 随列拉伸。
- 头 `.dhead` `padding:12px 16px`（底 `color-mix(in srgb,var(--edge) 22%,transparent)`）；
  体 `.dbody` `padding:16px`；脚 `.dfoot` `padding:12px 16px`（底同色 18%）。

### 发现（无背景板的选择浮层）
- `.mask.bare`：`rgba(5,7,9,.66)`、**无模糊** —— 只把外面的场面调暗；`.dialog.bare`：透明、无边框、无投影、隐藏 `.dhead`
- 一行卡片 `.disc-opts`：**总宽固定** `min(1180px,94vw)`；`.disc-row` 的 `gap` = `--gap`（JS 给：`max(8, 48-6×张数)`，**张数越多越紧**，实测 3 张 30px / 5 张 18px / 2 张 36px）
- 卡片 `.card`（bare）：`flex:1 1 0`、`max-width:240px`、`padding:18px 12px`、深底 `rgba(20,28,26,.88)`；头像 56px；选中/悬停用琥珀描边 + 底色加重
- 翻页箭头 `.pg-arrow`：`44×72` 命中区（三角用 `::before`）；**只在一页以上时出现**，到端点置灰（`.off`）而不隐藏 —— 行宽不跳
- 分页粒度 `PER_PAGE = 5`；页码状态 `PAGER={key,page}`（key 变了自动回第 1 页）

### 选择类弹窗（技能目标 / 效果 / 数量 / 搜索房客与地点）
- `.choice-grid`：`repeat(auto-fit,minmax(186px,1fr))`、`gap:12px`、`max-height:56vh` 可滚；
  卡片沿用 `.card`（`.sel` 琥珀描边 + 加底、悬停同款），`.card.wide` 是"图标 + 文字"横条（读效果文本用）
- 房客卡（`tenantChoiceCard`）：`.cn` 编号 + `.dc-av` 头像 40px + `.dc-name` + `.ch-vitals`（生命/理智两条 `.bar`）+ `.ch-persona`
- 效果卡（`optChoiceCard`）：`.dc-av` 取内容声明的 `i-*`、`.dc-name` 标签、`.dc-desc` 说明（第 4 项）
- 数量（`amountBox`）：`.amt-btn` 46×46 步进 + `.amt-num` 88×46 + `.amt-range` 滑杆 + `.amt-bar > i.on` 格数条；端点按钮 `disabled`
- 搜索地点行：`.loc-ico` 26px（图标已是「白底 + 档位特征色」）+ `.loc-main > b` + `.loc-sub > .chip`（**档位** `#8fa6b8/#c9a86a/#b06a5c` / 分组 / 固定）
- 搜索地点详情：`.cd-title` + `.chips` + `.cd-block` + `.loc-drop`（`标签 → 百分比`）+ `.loc-mech`（`▸` 逐条）+ `.loc-raw`（`<details>` 原始长句）

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
- `z-index`（低 → 高）：dusk-bg `0` < lpane `1` < 羁绊条 `15` < mask `20` < 专属面板 `26` <
  pause（ESC）`40` < launcher / tip `60` < pending-btn `70` < peek-toggle `71` < lc-dialog `80` <
  bond-drawer `85` < toast-wrap `95` < tip-layer `300` < quit-screen `999`
- **羁绊条只需要高过页内普通内容**（抬高它是为了让 chip 自己的悬浮窗不掉到可视日志之下），
  **不要给到覆盖层之上**——它曾经是 `80`，结果把遮罩 / ESC / 专属面板全压住了。

### 动效
- 过渡 `.14s`（按钮）/ `.15s`（卡片）；吐司 `toastIn .18s`；启动器背景 `flicker`/`fogmove`；
  `@keyframes`：`flicker, fogmove, peer, toastIn`
- 悬停详情：普通 chip 即显；伪人技能 **1s** 后弹出（`.door-zone` 整块触发）

---

## 10. UI 范式（**照着用，别另造**）

> 做新界面时的第一步：从下面挑现成的范式。挑不出来，才轮到"扩范式 / 扩词表"——
> 而那是**核心改动**，一次为全体服务（与卡片的 `svg` 图标位、面板的 `backdrop` 同一条规矩）。
> 只有一句话要守：**形归范式，值归内容**——内容给 id / 数量 / 值，图标、品质色、尺寸、间距由范式决定；
> 文案一律由内容随视图下发。

### 10.1 选人（房客）

- 组件：`tenantChoiceCard(t, extra)` + 容器 `.choice-grid`；点选 `pickUnit(this)`、读取 `pickedEl()`、
  取 id `Number(el.dataset.id)`。卡片自带头像（**必须走 `avatarIcon()`**）、`#id`、名字、**生命/理智条**、性格，
  以及可选的"搜索中"标签。
- 现有用例：**指派搜索选房客**（`showSearch()`，这就是最初的好样例）、**技能目标选择**、
  **命运抽牌的「指定房客」那一步**。
- 别自己拼"一行名字 + 确定按钮"的选人界面。

### 10.2 物品（一个格子）

- 组件：`.slot` + `slotInner(item)`（只画"格子里有什么"）；图标走 `itemIcon(entry[12], entry[0], "q"+品质)`。
- 一个**物品条目**的形状由后端 `web_ui._item_entry()` 决定（图标标记 / 名字 / 品质 / 数量 / 是否堆叠 / `item_id` /
  中文标签 / 描述 / 风味 / 是否装备 / 耐久 / 上限）。**前端不去别处查物品**：仓库、背包、专属面板、上交池
  吃的是同一种条目。
- 现有用例：屋主仓库、房客背包、**专属面板的格子**、上交 / 提交池。

### 10.3 卡片选项（选一个）

**两种行，按语义选——这不是风格之争：**

| 语义 | 形状 | 现有用例 |
| --- | --- | --- |
| **抽出来的少数**（三选一 / 五选一） | `.disc-row` + `pagedOptions(key, cards)`：**居中、总宽固定、卡片等宽、间距随张数变**（越少空隙越大）；每页 5 张、多于一页才出箭头（端点置灰、不隐藏） | 发现（开局抽 3）、命运牌的选牌与选方向、待处理通用选项 |
| **罗列全体候补**（有几张就摆几张） | `.choice-grid`：自适应网格、能塞几列塞几列、间距固定；条目多时容器内滚动 | 指派搜索选房客、技能选人 / 选效果、使用 / 装备选目标、指认、移除状态 |

- 判据一句话：**"这些是从一堆里抽出来的几个"→ 第一行；"这就是全部候选"→ 第二行。**
- 两种都合理，**别为了"统一"把一种改成另一种**（把"罗列"改成等宽居中，张数一多卡片就细成条）。
- 边界：**带说明文字的选项**（每个候补各自一坨描述）走第二行——等宽会把描述挤断；
  **光有名字 / 图标的少数选项**走第一行。
- 选中/确认两种共用：`.card` + `pickUnit(this)`（网格）/ `tglSelect(i)` + `selectedIndex()`（卡片行）、
  **双击 = 选中并确认**（`optDbl(i)`）。
- **并排的两个选项也等宽**：`.disc-row` 里 `.card` 已有 `flex:1 1 0`，`.pick-card` 也有（不然"是/否"
  "结算/反悔"会按内容宽排，一眼不等宽）。
- `.dc-av` 图标位可以放：头像（`avatarIcon`）、物品图（`itemIcon`）、或**内容自带的内联 svg**
  （24×24 内坐标、不写颜色与线宽，见 `docs/GUIDE.md` §14.11）。

### 10.4 行式信息（描述一块状态）

- 组件：`slotHtml(rows)`。词表只有五种：`mark`（引用印记）/ `bar`（可带档位刻度）/ `text` / `tags` /
  `glyph`（可旋转、悬停给文案）。
- 现有用例：房客详情页的**小面板**（`DETAIL_SLOT`）、**专属面板的 `rows`**。

### 10.5 按钮与反馈

- 按钮只有三种：`.btn`（普通）/ `.btn.p`（主要）/ `.pick-card`（大块选择）。**新按钮一律复用，不另起一套参数。**
- 反馈用 `toast(msg, kind)`；查看类信息走悬浮层（`tipLayer`），不要挤进正文。

### 10.6 浮层放哪

- 弹窗：`openDialog(title, sub, html, wide, cb, hideFoot, bare)`。
  **`bare=true` ＝「发现」那套无背景板浮层**（只把场面调暗，不出面板底与标题栏）——
  所有"选一个"的流程都用它。
- 贴底浮窗：`.bp-float`（背包）/ `.mission-float`（外出搜索）；可拖动浮窗：`.panel-float`（专属面板，
  位置记进 `game_config.json`）。
- 阻断只留给**必须做的决定**；一切"查看"类操作都放行。

### 10.7 清单 + 详情（候补多、每个候补都有一大坨详情）

卡片放不下详情时用**左清单 + 右详情**，不要硬塞进卡片行：

| 用例 | 结构 |
| --- | --- |
| 选地点（指派搜索） | `.search-layout`：`.loc-list` + `.loc-detail` |
| 图鉴 | `.codex-split`（`310px | 1fr`） |
| 启动器的存档 / 资料包 / 资源包页 | 左列表 + 右详情 / 右侧有序清单 |

> 门口事件目前是**第四种**（一排 `.btn` 的按钮行），已定将来大改 —— 在那之前**不要照它写新界面**。

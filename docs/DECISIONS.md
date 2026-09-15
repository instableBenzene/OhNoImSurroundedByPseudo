# 决策与修正记录

> `AGENTS.md` 只保留"现状速览"；**具体到某次为何这么改、当时踩了什么坑**记在这里。
> 目的：不把入口文档撑成流水账，又不丢上下文。要加新条目就追加在顶部。

## 资源包清单里的 base 可调位次 + 全员和风头像 + 零件色槽

- **`base` 行与资料包同义、位次可调**：资源包页右侧现在恒有一行 `base（内置材质）`
  （= `weiren_game/data/resourcepack/`），**不可卸载、可上下移动**。装载从最低优先级开始，
  轮到 `base` 时把内置材质**重新盖一遍**（`CONTENT.overlay_resourcepack_base()` →
  `data.resourcepack.apply_base_material`），于是：
  - 排在 `base` 上方 → 覆盖内置材质（血月就是这么用的）；
  - 排在 `base` 下方 → 改不动内置材质已定义的东西，但**它新增的** token / 零件 / 素材位仍在。
  踩坑：只有在"确实有包排在 base 下方"时才重盖 base，`base` 垫底（常态）时什么都不做 ——
  与旧行为逐字节一致，不会把 DLC 内嵌 `resourcepack/` 的外观冲掉。
  另一个坑：`apply_resourcepack_order(root=...)` 曾把"已套用过的包名"并进候选集，
  测试里给自定义 root 时会带着默认根下的包名去装载 → `FileNotFoundError`；现在只有默认根才认。
- **血月包：全员和风头像**。`pack.json` 声明 `"avatar_mode": "parts"` → 该包生效时，
  立绘兜底（`assets/art/characters/`）被**跳过**，所有角色改用零件组装，于是"全套配件换掉"成立；
  包自己放的 `avatars/characters/<id>.svg` 仍优先（明说要那张整图）。
  血月自带 12 个和风形状（単髪／姫カット／ツインテール／お団子／坊主／縦ロール／みずら／侍髷…）
  与 14 个和风特征（菅笠／鉢巻き／頭巾／丸眼鏡／狐面／半纏襟／簪／提灯／桜／鬼角／眼帯／血痕／御币／勾玉）。
  `avatar_view` 多回一个 `use_parts: True`，界面据此**让立绘让位**（踩坑：不加这个标记时，
  房客卡的 `art` 依旧优先，和风那套永远看不到 —— 已由无头浏览器实测钉住）。
- **零件色槽（留给创作者）**：零件文件里可以写 `fill="var(--a)"` / `stroke="var(--b)"`
  （槽名 a–e），颜色由内容层角色模块的 `AVATAR_COLORS = {"a": "#c0333a", ...}` 给定；
  没给的槽退回主题 token（`a`→该角色点缀色、`b/c/d`→`--ink/--ink2/--ink3`）。
  实现：后端把槽替换成具体颜色后**内联**下发（`shape_svg`/`feature_svg`），尺寸交给 CSS。
  判定规则：零件**声明过颜色**（色槽或写死的 hex/rgb）才内联；只用 `currentColor` 的零件
  继续走"蒙版 + 主题色"，所以 base 那批跟着主题变色。**base 与血月自带的零件都不写色槽**
  （只有默认单色），色槽是给创作者的 —— 这也是单测里钉住的约定。
  安全：颜色值只接受 hex/rgb()/var(--token)/简单色名，含引号或尖括号一律忽略；
  内联前还会拒掉带 `<script` 的标记。
- **验证**：61 单测（新增 `test_resourcepack_base_row_and_wafu_style`）/ 审计 / 内容校验 / 冒烟 /
  `node --check`；无头 CDP：资源包页出现 `base（内置材质）基底` 行且"卸载 base"被拒；
  启用血月后房客卡头像 = 2 个内联 SVG（形状＋特征）+ 点缀环、不再出现立绘；控制台零报错；
  `browser_playtest` 跑满 6 回合无 JS 错误。

## 头像零件文件化（内容层）+ 物品「底色 + 品质色」+ 血月标题重塑

- **头像不再写死在贴图里**：`data/avatars/{shapes,features,characters}/<id>.svg`，**一件一个文件**；
  资料包 `dlc/<包>/avatars/...`、资源包 `resourcepacks/<包>/avatars/...` 同 id 覆盖，优先级
  **base → 资料包（位次）→ 资源包（位次）**。索引在 `weiren_game/avatars.py` 按"当前配置 + 文件系统"
  现算（不是注册表快照），所以资源包增删/改位次**立即生效、无需回滚登记**。
  既有外置美术 `assets/art/characters/`（24 张立绘）作为**最低优先级**并入 `characters` 分区 →
  老观感不变，而资源包放一张 `avatars/characters/hkw.svg` 就能盖掉某个角色（人/伪人都适用）。
- **零件也走内容层声明**：角色 `.py` 里 `AVATAR`（形状 id）/`AVATAR_FEATURE`/`AVATAR_ACCENT`/`AVATAR_DECOR`
  仍有效；缺省按 id 哈希派生（**顺序表搬进后端** `FEATURE_ORDER`/`ACCENTS`/`DECOR` 并保持原顺序，
  所以既有头像一个都没变——`hkw` 仍是 `i-ft-hat` + `#6fb3a6`）。前端只拿后端解析好的
  `avatar_parts = {full, shape, feature, accent, decor}` 去渲染，不再自己算哈希。
- **渲染方式**：组装件用 CSS **mask + currentColor**——形状吃 `--ink`、特征吃点缀色；整张头像仍是 `<img>`。
  这样材质包换主题色能带动头像，同时零件文件本身只需单色线条。
- **物品「底色 + 品质色」**：物资图标改成 `itemIcon()` → 外置图当**蒙版（底色）**，
  颜色由所在 `.qN` 品质类给（`--q0..--q5` 是锁定 token，材质包改不动）。于是"同图不同品质"自动分色，
  原先烘在 SVG 里的品质色不再起作用（要改色改 token 即可）。地点/信息/角色等**彩色插画仍走 `<img>`**，
  只有物资图标用蒙版——避免把整张彩图压成剪影。
- **存档无关**：单测递归扫描存档 JSON 的**字段名**，断言不含 `art/theme/avatar/resourcepack*`
  （`0:start.discover.0` 这类计数键不算——"art" 只是子串）。→ 资源包可随时移除，不影响存档。
- **血月标题重塑**：中文主标题保留（楷体 + 血色渐变 + 描边 + 血滴 + 円相 + 飞墨 + 朱印「偽」），
  「伪人」二字单独走**浅红→暗红**横向渐变（`tspan`），整行**微微透明**（.93/.95），
  并叠了**血污/墨韵**（`washSoft`/`washMid` 晕染大块 + 斜向飞白 + 溅点）；副标题为日语那一行。
- **验证**：60 单测（新增 `test_avatar_parts_follow_content_and_pack_priority`）/ 审计 / 内容校验 /
  冒烟 / `node --check`；无头 CDP 实测：头像零件三条 URL 均 200、路径穿越 404、组装件 2 个蒙版
  （形状= `--ink`、特征= 点缀色）+ 点缀环、整张头像优先 `<img>`；品质色取 `--q0/#c4c9c4`、
  `--q3/#a77ad1`、`--q5/#d86459` 逐一命中；血月标题素材含日语副标题与墨韵、封面 200、控制台零业务报错。
- **待办**：资源包页也想有一行可调位次的 `base`（表示"内置材质在覆盖链里的位置"）；
  目前 base 恒为最底层（资源包永远盖过它），要做"某一包位于 base 之下"需要复用资料包那套
  `overlay_base()` 的位置化套用，留作下一轮。

## 退出游戏对齐 bat / 标题整块可换 + 不遮挡 / 血月标题改日语

- **退出游戏 ≠ 只是"停服"**：`停止游戏UI.bat` 其实是按命令行**强杀** `*game_ui.py*`
  （多开也能全杀）。为对齐它的效果，`/api/quit` 改成三步：
  **① 先 `session.flush_pending_save()` 把未落盘的存档写掉**（比强杀更安全）；
  ② `server.shutdown()` 优雅停服；③ 0.8s 后 `os._exit(0)` **确保进程退出**
  （即使有卡住的请求线程也不会留下"僵尸服务"）。实测：`200 {"ok":true}` → 端口停止监听、进程退出码 0。
  旧进程没有这个接口时，仍然用 `停止游戏UI.bat` 兜底。
- **标题两端不再被遮挡**：随机位移/旋转会把标题顶出容器两侧。现在渲染完**量一次宽度**，
  超宽就整体等比缩小（`transform: scale(可用宽/实际宽)`）——随机排版保留，但永远落在容器内。
  实测内置剪字标题 `minLeft/maxRight = 219/893`（视口 1410）、素材标题 256/1139，左右都有余量。
- **`title` 素材 = 一整块**：新增 `.title-block` 包住「大标题 + 副标题」两行，高度固定；
  资源包的 `title` 素材替换**整块**（`.has-title-art` 把两行都隐藏），所以副标题也能被包改写。
  实测两种模式（内置剪字 / 素材）下按钮位置都固定在 `menuTop=478`——切主题不会让菜单跳。
- **血月标题重做**：中文主标题保留（楷体笔意 + 血色渐变 + 深色描边 + **血滴** + 円相 + 飞墨 +
  朱印「偽」），**副标题由英文改为日语**「しまった、偽人に囲まれた？！」——和风恐怖主题下更统一。
- **资源包能力边界（澄清）**：`SYMBOLS` 是**通用**的（任意 icon id，内容引用即可生效，
  可做头像零件/小面板图形/物品图标零件）；`ASSETS` 目前前端消费 `background` 与 `title` 两个 kind。
  "整张物品/角色图替换"仍属 `assets/art/` 外置美术接口，那是另一档改动（本次不做）。
- **验证**：59 单测 / `audit_separation` / `validate_content` / 冒烟 / `node --check`；
  无头 CDP 实测：退出接口关服、标题两种模式都不越界、`menuTop` 一致、副标题随素材隐藏、控制台零报错。

## 外观层独立成"资源包" + 一批 UI 修正（血月主题）

- **血条配色（实现失误）**：设计稿没规定血条颜色；实现里 `.bar i.h`（理智·正）与 `.bar i.neg-san`
  （理智·负）**都写成了 `--q3`** → 正负看不出差别。按"负=紫"的语义改为
  **生命 正=绿(`--ok`) / 负=红(`--danger`)；理智 正=蓝(`--q2`) / 负=紫(`--q3`)**，
  负值文字仍用 `.purple`。
- **主页面标题抖动**：`renderScrapTitle` 每次加载随机字号/位移 → `.mc-title` 高度随排版变，
  下方"开始游戏/设置"跟着上下漂。修法：按 `base`（随窗口宽度）**固定标题占位高度**
  （`base*2.95`，英文副标题 `base*0.75`），随机只影响视觉溢出，不影响布局。
- **资源包（独立一层，与资料包并列）**：新增一级目录 `resourcepacks/<name>/`
  （`pack.json` + `theme.py` / `symbols*.py` / `assets/*`），**各自有序**：`CONFIG.resourcepack_order`
  （高→低），高者覆盖低者。加载顺序：内容包（含 DLC 内嵌 `resourcepack/`）→ 独立资源包，
  所以独立资源包总能盖过资料包自带的外观。
  **两层基线**（踩坑）：`apply_pack_order` 会先 `restore_base()`；如果随后直接
  `restore_resourcepack_*` 回退，就会把"资料包自带的外观"一起抹掉。改为：
  内容包装完后 `capture_resourcepack_baseline()` 记一份基线，独立资源包以**基线**为起点叠加。
- **素材位 `ASSETS`**：资源包用 `ASSETS = {"background": "background.svg", "title": "title.svg"}`
  声明文件（放 `<包目录>/assets/`），后端经 `/api/resourcepack/asset?pack=&file=` 提供（**只接受裸文件名**，
  防目录穿越）；前端 `applyResourcePack()` 把它们应用为**封面背景**与**大标题**（给了图就覆盖内置画面）。
  资源包切换时前端**幂等重套**（先摘掉上次注入的 symbols/背景/标题）。
- **命名与入口**：`DLC` 在界面上一律改叫**资料包**（`dlc/` 目录名与代码标识不动）；
  设置菜单里并列「资料包 / 资源包」两个子页（都可 ▲▼ 调位次、可启停）；
  主页原来放 DLC 按钮的位置改为**退出游戏**——调 `POST /api/quit` 关停本地服务，
  等价于原来的「停止游戏UI.bat」，省掉再点一次停止脚本。
- **内置示例包**：`resourcepacks/blood_moon/`（血月·黑红）——只覆盖色调 token（近黑底 + 血红强调），
  并自带 `background.svg`（血月夜空）与 `title.svg`（血红剪字标题）。
- **验证**：59 单测（新增独立资源包的套用/回滚/锁定/素材解析断言）/ `audit_separation` /
  `validate_content` / 冒烟 / `node --check`；无头 CDP 9/9：素材位生效、色调生效且品质与尺寸锁定、
  **刷新三次按钮位置完全一致**（标题抖动已修）、设置里出现「资料包/资源包」、资源包页可卸载装回、
  生命正绿负红、理智正蓝(`rgb(107,159,209)`)负紫(`rgb(167,122,209)`)。

## 换肤二：把一次性点缀色按功能收编（只剩 5 处刻意保留）

- **来由**：第一轮只收编了 20 个"反复出现"的色，剩下 60 来种一次性点缀色还是字面量 ——
  换皮肤时那些细节不变，观感会"花"。用户要求**按相近功能归并**（早期没有严格规则留下的发散）。
- **做法**（值允许向相近色收敛，这是有意的）：
  - **区域角色 token**：启动器背景三段 `--launcher-1/2/3`（原 `#070d10/#0b1416/#101c1a`）。
  - **琥珀透明叠加**：`rgba(226,168,77,α)` **29 处**（hover/选中/边框/阴影）改为
    `rgba(var(--amber-rgb),α)`，新增 `--amber-rgb` 分量 token —— 于是**所有 hover 与选中态
    都跟着材质包的强调色走**（单测断言 `--amber-rgb` 与 `--amber` 同步）。
  - **相近语义归并 22 处**：顶栏渐变/羁绊条/悬浮层/启动器卡片/存档图标 → `--panel2`/`--surface-*`；
    不可用技能按下态 → `--surface-3`；次要标签字 → `--ink3`；标题暗影 → `--amber-soft`；
    已失效羁绊描边、危险按钮描边 → `--danger-2`；淡红文字三处合并为新锁定 token `--danger-ink`；
    难度说明字 → `--ink2`、副标题/夕阳 → `--amber`、图鉴 chip 字 → `--ink-head`、日志强调 → `--ink`。
  - **难度标签**（更难/更易/基准）收编为 `--diff-hard/--diff-easy/--diff-neutral` 并**锁定**
    （它们是"难度含义"，不随皮肤变）。
- **刻意保留的 5 处字面量**：报纸剪字标题的纸色/墨色（`.mc-title`、`.title-bangs b`）与
  金牌徽记的金属渐变三色（`.tier-badge.t-gold`）——都属"画面里的具体物件"，不是 UI 材质。
- **结果**：`<style>` 里 `:root` 之外的写死颜色从 **166 处降到 5 处**；换肤现在能覆盖
  背景/面板/顶栏/按钮/弹窗/悬浮层/启动器/文字/强调色及其全部透明叠加态。
- **踩坑（工具侧）**：我用来演示换肤的临时脚本按逗号切 `"--amber-rgb": '226,168,77'`
  把 theme.py 写坏了（含逗号的值），导致服务器起不来；**不是仓库问题**，但也顺带印证了
  "base 内容模块坏了 = 起不来"（DLC 包坏了会被 `run_server` 忽略并打印）。
- **验证**：58 单测（新增 `--amber-rgb` 与 `--amber` 同步断言）/ `audit_separation` /
  `validate_content` / 冒烟 / `node --check`；无头 CDP 对照：默认材质下
  `选中态底 = rgba(226,168,77,.08)`，换青色皮后变成 `rgba(79,209,197,.08)`，
  而 `--q4`（品质金）与 `--slot`（60px）不变。

## 换肤：把"这套 UI 的配色"收编成 token（尺寸与语义色锁死）

- **需求澄清**：用户要的是"**配色**能被材质包加载"（墨绿背景、琥珀强调那一套），
  而**尺寸/布局不能变**；品质色、羁绊位阶、红色之类**提示色**也不该随皮肤变。
- **真问题**：之前那套 token 只覆盖了底色/面板/线/文字/琥珀，而**按钮、弹窗、气泡的渐变
  是写死的十六进制**（`#2c3b34`/`#1b2620`/`#3f6b4f`/`#0c0c0c`…）——所以"换材质包"时
  chrome 根本不变（第一次演示只看到 `--amber` 生效）。统计：`<style>` 里 **166 处写死颜色、
  81 种**。
- **做法**：把**反复出现、定义观感**的 20 种收编成 token（值逐字不变 → 零视觉变化）：
  `--edge`（描边黑）、`--ink-hi`/`--ink-btn`/`--ink-head`（亮字/按钮字/标题字）、
  普通按钮面 `--btn-1/--btn-2/--btn-hi-1/--btn-hi-2`、主按钮面 `--pri-1/--pri-2/--pri-hi-1/--pri-hi-2`、
  危险按钮面 `--danger-1/--danger-2/--danger-hi-1/--danger-hi-2`、
  面 `--surface-1/--surface-2/--surface-3/--surface-tip`；共替换 **105 处**字面量。
  值同时写进前端 `:root` 与 base 资源包（两份一致由单测钉住）。
- **锁定规则（系统级强制，不靠自觉）**：`resourcepack.LOCKED_TOKENS` = 语义
  (`--ok/--danger/--warn/--info`)、危险红、品质 `--q0..--q5`、羁绊 `--bronze/--silver/--gold/--prism/--prism-grad`、
  尺寸 `--slot`/`--w`。一般资源包/DLC 想改这些会被**忽略并打一行提示**（base 资源包
  `allow_locked=True`，因为默认值由它给出）。→ 换皮肤**改不动颜色含义、也改不动布局**。
- **端到端演示**：临时把 base 的 13 个色调 token 换成青色皮 → 按钮/主按钮/描边/标题整屏跟随
  （`btnBg` 从 `rgb(44,59,52)→rgb(27,38,32)` 变成 `rgb(34,56,58)→rgb(19,31,33)`），
  而 `--q4`（品质金）与 `--slot`（60px）不变；演示后还原（单测确认两份仍一致）。
- **未收编**：剩下约 60 种**一次性点缀色**（某些面板的专用深绿、少见高亮等）仍是字面量，
  换皮肤时这些细节不变；要全覆盖可按同一套路继续收编（若需要，单独一批做）。
- **验证**：58 单测（`test_resource_pack_channels_and_rollback` 增加"锁定 token 改不动 /
  自定义 token 允许"断言；`test_resource_pack_defaults_match_frontend_fallback` 钉住
  CSS↔资源包一致）、`audit_separation`、`validate_content`、冒烟；无头 CDP 截图对照
  （默认材质与收编前观感一致；青色皮整屏生效）。

## 资源包：材质 / 字体 / 贴图零件从前端独立到内容层

- **来由**：前端 `index.html` 里同时压着「结构样式」与「材质」——`:root` 的 34 个 token、字体栈、
  以及头像零件（12 形状 + 14 特征）等 SVG symbol。用户提出按 `assets/art` 的既有思路，
  把**材质与贴图**也做成内容层资源包，DLC 可自带。
- **做法**：新增内容层 `weiren_game/data/resourcepack/`（**base 资源包 = 默认材质**），
  自动发现 `*.py`，每个文件可暴露：
  - `THEME = {"tokens": {...}, "css": "..."}` —— CSS 变量（含字体栈）+ 追加样式（可写 `@font-face`）；
  - `SYMBOLS = {"i-xxx": "<path …/>"}` —— 贴图零件（viewBox 统一 24×24）。
  注册表（`RESOURCE_SYMBOLS` / `RESOURCE_THEME`）纳入 `_BASE_CONTAINERS` 快照 →
  **装载/卸载随包回滚**；同 id 覆盖 = 走既有**包优先级**（高优先级赢、base 覆盖它下方的包）。
  新增 `GET /api/resourcepack`；前端 `boot()` 在**首次渲染前**取回：注入 `<defs>`、把 token
  写到 `:root`、追加 CSS。DLC 新增目录 `dlc/<包>/resourcepack/`。
- **搬了什么 / 留了什么**：搬走**贴图零件**（头像 12 形状 + 14 特征 + `i-moon`/`i-taiji`，共 28 个
  symbol，前端只剩 59 个通用控件图标）；材质 token **不搬走**——见下条「事故」的结论：
  前端 `:root` 保留**默认材质**（兜底），资源包提供**覆盖/追加**。
  `docs/STYLE.md` §9 仍是参数速查；材质改法：改资源包（要连带同步前端兜底，有测试钉住）。
- **头像「零件组合」落地**：角色可声明 `AVATAR_FEATURE` / `AVATAR_ACCENT` / `AVATAR_DECOR`
  （后端下发，前端优先用、缺省仍按 id 哈希），于是"形状 × 专属特征 × 点缀色"完全由内容决定，
  而特征/形状可以由资源包提供**新零件**——这就是用户说的"资源包放各种零件进行组合"。
  优先级：`assets/art` 立绘 > 声明零件 > 哈希兜底（注意：内置 24 位角色**都有立绘**，
  所以哈希组合其实只在没有立绘的角色/DLC 上才会用到）。
- **事故与修正（"UI 风格全变了"）**：第一版把 token 表整份**从前端删掉**、只靠
  `GET /api/resourcepack` 运行时注入；结果**后端还是旧进程**（没有该接口）时返回 404 →
  前端只剩 9 个变量的兜底色 → 整屏配色/字体走样，**连布局 token 都没了**
  （`--slot` 一丢，仓库网格 `repeat(6,var(--slot))` 整条声明失效 → 变成一格一排）。教训：
  ① 把"默认外观"放到运行时依赖上，等于让一次刷新就能毁掉界面；
  ② 兜底不能是"缩水版"，必须是**完整默认材质**。
  **修法**：前端 `:root` 写回完整的 34 个 token（默认材质，值与 base 资源包逐一相同），
  资源包只做**覆盖/追加**；资源包不可用时只 `console.warn` 一句、界面**零变化**。
  另加单测 `test_resource_pack_defaults_match_frontend_fallback` 钉住"两份必须一致"，
  避免以后改一处忘另一处。
- **验证**：57 单测（新增 `test_resource_pack_channels_and_rollback`：覆盖 token / 新增零件 /
  覆盖同 id 零件 / 追加 css，卸载后逐项回滚）；`audit_separation` / `validate_content` / 冒烟全过；
  无头 CDP 7/7（接口字段、前端 HTML 确实已无零件与 token 表、启动注入 87 个 symbol、
  token/字体生效、声明零件覆盖哈希、资源包零件能被内容引用并渲染、控制台零报错）。

## 彩蛋两枚：厄瑞玻斯的明月 / 混的太极图（附一处显示修正）

- **需求**：小面板要能承载"定制化的小设计"。第一版就试两枚彩蛋——
  ① 厄瑞玻斯在**伟大的封印**（`great_seal`）期间，面板里多一轮明月，悬停显示
  「厄瑞玻斯-正在杀出月球」；② 混的面板画一张**太极图**：平时不定向、随机速度旋转，
  固定**纯真的自我**（`pure_self`）后稳定顺时针。
- **做法**：小面板新增第 5 种条目 **`glyph`**（装饰性图形）：`icon` + 可选 `label`/`hint`
  （悬停走游戏内气泡 `showChipTip`）+ `spin`。`spin="random"` 由**前端**在每次渲染随机
  方向与速度（2.4~4.8s，`animation-direction: normal|reverse`）；`spin="cw"` 固定 6s 正向；
  不写则不转。旋转只是 CSS 动画，**不改任何机制**。图标 `i-moon` / `i-taiji` 加在内联
  symbol 表里（与其它 85 个图标同源）。
  两处的判定都写在角色自己的文件里（`tenant.condition(...)`），系统层不知道任何具体内容。
- **`random` 是"持续乱"而不是"每次渲染随机一次"**：只在渲染时掷一次的话，两次状态更新之间
  数值是恒定的，看着像稳定旋转。改为 `chaosTick()`：页面上只要存在 `.glyph[data-spin="random"]`
  就每 300ms 扫一次，**每个图形按自己的节奏**（0.45~1.75s）换时长（0.85~3.2s）、方向与缓动
  （linear / ease-in-out / 自定义贝塞尔 / `steps(6)`）；没有这种图形时**自动停表**
  （不留后台定时器）。实测 4 秒内出现 4 组不同的参数组合。
- **踩坑**：旋转模式名一开始叫 `chaos`，撞上了角色 id「混」→ 被 `audit_separation` 抓出
  "系统/前端出现内容 id"。改名 **`random`** 后干净（教训：给机制枚举取名时要避开内容 id）。
- **踩坑 2（转不起来）**：`animation-duration` 写在 `.glyph` 的**行内样式**上，而
  `animation-name` 挂在**子元素 `svg`** 上——`animation-duration` **不会继承**，于是动画时长为
  0s，看着就是静止。修法：动画整体挂到 `.glyph` 本身（行内时长/方向与它同元素）。
- **踩坑 3（没居中/条不齐）**：小面板原本是**收缩到内容宽度**的（只有图标时仅 34px），
  于是图形偏在左、各角色的进度条长度还各不相同。修法：`flex:1 1 auto` 让它吃满头像右侧的
  剩余宽度（左栏固定 220px → 面板 154px），居中与"等长进度条"都自然成立。
- **顺带修正**：厄瑞玻斯的「命运牌」印记实例存的是**牌号**（0..21），而 `MarkPool.count`
  求和 → 旧详情页显示成 `231 / 22`。既然它现在自己声明小面板，改为按**张数**
  （`len(marks.instances_of("fate"))`）画一条 `bar`，显示 `22 / 22`。
- **验证**：56 单测（新增 `test_slot_easter_eggs`：明月只在封印期出现、太极图随 `pure_self`
  从 `random` 变 `cw`）/ audit / validate / 冒烟；无头 CDP 7/7（两种图形渲染、明月静态且悬停出文案、
  太极图 6 次渲染得到 6 组不同的时长/方向、固定后 6s+normal+无限循环、标签随之变化、控制台零报错）。

## 小面板：头像右侧 / 伪人袖珍卡改成内容声明的公共区域

- **想法来源**：详情页头像右侧原本是"印记专用"的一列，伪人门口的袖珍卡也是固定结构。
  改成**内容声明的小面板**后，每个角色/伪人在**自己的 py 里**决定这里放什么；
  系统只提供几种通用条目，排版（整行占满、等高等宽）由框架保证，不需要每个内容各自调样式。
- **条目种类（最小集）**：`mark`（引用自己的印记，含进度条）/ `bar`（自定义进度条，可带档位刻度）/
  `text`（一段说明）/ `tags`（一排小标签）。声明方式是模块级 `DETAIL_SLOT(engine, tenant)`
  （伪人是 `CARD_SLOT(engine)`），聚合进 `CHARACTER_DETAIL_SLOTS` / `PSEUDO_CARD_SLOTS`
  并纳入 `_BASE_CONTAINERS` 快照（DLC 卸载同样回滚）。
  **不声明 `DETAIL_SLOT` 的角色**回退为"列出自己的印记"——现有 24 位房客零改动。
- **档位刻度**：`bar_tiers` 每档从 `at` 升级为可写 `(at, 标注, 刻度配色)`；
  后端把它投影成 `{at, ratio, label, css}`，前端在进度条上画一条刻度线（`danger`=红线、
  `warn`=黄线、`ok`=绿线），悬停显示标注。颜色映射仍走羁绊那套位阶 token（纯展示）。
  已声明的例子：罗兹 `(3 临界)(4 可驱逐，红)(6 转化)`、澪叁贰玖 `(1 可发动，红)(3 满)`、
  洋葱 `(1 可平静，红)(3 大招)`、比格小星 `(10 满档)`。
- **状态栏 opt-out**：`StatusDefinition.chip_hidden`（默认 False）——声明后该状态不进房客卡状态栏，
  适合"改用面板展示"的状态。首个使用者是薯条的 `persona_*`：人设从状态栏搬到 `DETAIL_SLOT`
  里连同风味一起显示（`fries.detail_slot`）。
- **不做的事**：不引入通用"插槽语言/布局引擎"（按用户要求"不需要过于公式化"）——
  条目就这 4 种，位置固定为那两块区域；要更多表现力时再按需加种类。
- **验证**：55 单测（新增 `test_detail_slot_and_chip_hidden`，并把 `test_mark_bar_projection`
  升级为"档位标注 + 刻度比例"断言）/ audit / validate / 冒烟；无头 CDP 8/8（4 种条目渲染、
  刻度按 css 上色且带悬停说明、多条进度条等宽、印记逐条含 0 值、档位换色、伪人卡同款容器、
  人设落在面板、控制台零报错）。

## 印记进度条：内容层声明阈值，无上限也能画

- **背景**：详情页的印记原来只有数字。像**星之印记**这种 `maximum=None`（理论上无上限）的印记
  根本没有分母，既没有条、也看不出"攒到多少算够"。
- **做法**：`MarkDefinition` 新增 **`bar_tiers: tuple[int, ...]`**（升序，最多 4 档）——由角色在
  **自己的文件里**声明"达到多少换档"：
  - 有 `maximum` → 进度条按 `maximum` 铺满；
  - `maximum=None` 但有阈值 → 用**最后一个阈值当"满槽"参照**（星之印记 `(10,)`：10 就是
    代码里"每回合最多消耗"的上限；攒满即满格，数字继续照实显示更多）；
  - 两者都没有 → 不画条，只显示数字。
- **后端只算，前端只画**：`build_state` 下发 `bar = {scale, fill, tier, tiers}`（`tier` = 已达档位数）；
  换档配色在前端映射为羁绊同一套 token（2 档=银/金、3 档=铜/银/金、4 档=+棱彩，复用
  `bondTierClasses`），与羁绊"颜色/档名映射留前端（纯展示）"的既有约定一致。
- **顺带**：印记徽记补 `hint`（= `acquisition` + `special`，悬停可见），玩家不用翻图鉴就知道怎么攒。
- **已声明的阈值**（只取代码里**真实存在**的分档，不凭空编）：比格小星 10（每回合消耗上限）、
  罗兹恶魔 3/6（≤3 与满档转魔化）、洋葱共情 1/3（够付一次 / 大招代价）、澪叁贰玖警觉 1/3；
  厄瑞玻斯命运牌只有 `maximum=22`（整副牌），不加阈值。
- **验证**：`tests/test_status_flow.test_mark_bar_projection` 钉住投影规则（有上限 / 无上限超出 /
  不声明即 None）；54 单测 + audit + validate 全过；无头 CDP 8/8（三种印记各画各的条、
  达标换色、按比例填充、悬停提示、控制台零报错）。

## 前端六项：详情页印记 / 技能点击与悬浮 / 情绪显现改事件 / 羁绊层级 / 全局事件分页

- **① 详情页印记**：原来是 11px 灰字一行（`名称 3 / 22`，数字 `--ink3` 比名称还暗），看着像没做完。
  改为**徽记**：复用 `.mark-chip`（琥珀描边）+ `i-mark` 图标 + `名称 当前/上限`（上限 `None` 只显示当前），
  数字用 `--ink` 提亮。`build_state` 同时改为**声明过的印记一律下发（含 0）**——否则玩家攒到第 1 枚
  才知道这套机制存在。
- **② 技能栏点击**：整条技能栏本来就是按钮，但**不可用时没有 `onclick`**，点击会冒泡到详情页的
  「点空白返回缩略」→ 点冷却/被动技能莫名退回席位。改为恒带 `event.stopPropagation()`，
  只在可用时调 `useAbility`。顺带修悬浮层漂移：紧凑模式下先 `mouseenter`（起 0.5s 定时器）再点技能，
  会重绘并摘掉宿主，定时器到点时 `_tipPlace` 拿到**零尺寸矩形** → 悬浮层贴左上角。
  现在 `abilityHoverStart` 检查 `el.isConnected`，`_tipPlace` 对"已摘掉/零尺寸"的宿主直接隐藏
  （所有共用它的悬浮层都吃到这条兜底）。
- **③ 情绪显现改为全局事件**：原实现是信息被证实后给**目标房客** `set_status("reveal_<情绪>")`——
  一个黏在房客身上的 condition（还会作为 chip 出现在房客卡上）。现改为**世界级事件**
  `emotion.reveal.<情绪>`（键由 `global_event.emotion_reveal_event()` 唯一生成）：
  `information_system` 证实后写事件、`engine.emotion_visible` 读事件、`condition.py` 为每种情绪
  登记事件定义（label「情绪显现（X）」+ 图标 + 说明），于是它会出现在新的「全局事件」页里。
  **语义变化**：该情绪对**所有房客**可见（与洋葱「情绪显现-烦躁」既有做法一致；原稿的逐人揭示未保留）。
  `reveal_*` 状态与自动生成逻辑一并删除。
- **④ 羁绊概况被缩略条压住**：`.bonds-strip` 的 `z-index:80`（当初为了让它的悬浮窗压过日志）高于
  `.bond-drawer` 的 `45` → 抽屉被盖。抽屉提到 `85`（高于缩略条，仍低于吐司 95 与悬浮层 300）。
- **⑤⑥ 现有信息 ↔ 全局事件**：面板标题改为可点击的切换键（带 `⇄`），在两页之间来回切；
  切到事件页时隐藏「隐藏已失效」（不适用）。事件行沿用信息条目的折叠结构：**图标 + 名称 + 剩余回合**，
  点开看内容。数据由 `build_state().events` 下发：`label/icon/description` 取自内容层
  `GlobalEventDefinition`（**新增 `icon` / `description` 字段**，16 张命运牌事件已全部补齐），
  剩余回合按既有约定渲染：≥99 显示「长期」，否则「还能持续 N 回合」。
- **验证**：53 单测（新增 `test_status_flow.test_emotion_reveal_is_global_event`）/ `audit_separation` /
  `validate_content` / 冒烟；无头 CDP 12/12 通过（印记徽记、冷却与被动技能点击后仍停留详情页、
  宿主消失后悬浮层不再贴左上角、抽屉 85 > 缩略条 80、标题切换与事件行展开、控制台零报错）。

## 内容包优先级：可调序 + 覆盖内置内容（"角色更新包"）

- **需求**：将来会有"替换某个角色"的更新包（而不是纯扩展包）。希望在 UI 里右侧启用清单
  可选、可 ▲▼ 调序，`base` 也在这份清单里；越靠上优先级越高，把包调到 `base` 之上即覆盖内置同 id 内容。
- **模型**：启用包是一份**有序**清单（高 → 低，含 `base`），持久化到
  `game_config.json::pack_order`（老配置无此字段时迁移为 `["base", *enabled_dlc]`，
  `enabled_dlc` 退化为派生视图）。`dlc.apply_pack_order()` 从**最低优先级**开始装载，
  **轮到 `base` 时调用 `CONTENT.overlay_base()`**，让内置内容重新赢过它下方的包；
  排在 base 上方的包最后装载，因此可以覆盖内置。`reload_dlc(names)` 保留为兼容入口
  （= `["base", *names]`，即 base 最高）。
- **覆盖语义**：只在**按 id 索引的定义**上生效——`register_character/item/location/
  information_template/pseudo` 增加 `replace=` 参数（DLC 装载恒为 True）；钩子序列
  （`NODE_HOOKS` 等）保持"只增不换"，卸载时整体回滚。物品覆盖会把它从原分类摘掉，
  地点覆盖会从原分组摘掉。伪人的通用节点钩子只增不删（已在文档注明）。
- **`overlay_base()` 的细节**：逐容器取 base 快照里**已有的键**覆盖回当前注册表；
  嵌套注册表（如 `CATEGORY_ITEMS[类别][id]`）只合并一层，避免把低位包在同一层里
  新增的条目一起抹掉；list 型容器（hook 序列、`BASE_MAP_GROUPS` 等）不参与覆盖。
- **顺带修**：`load_configured_dlc()` 改成"**已是目标集合就不重建**"（此前每次
  `GameEngine.new_game` 都会重跑一遍回滚+装载），并把**已装载**的包也算作可用，
  免得自定义 root 装载（工具/测试）的包在开局时被"找不到目录"顺手卸掉。
- **UI**：DLC 页右侧改为有序清单（`base` 带「基底」标注、拒绝卸载），底下加 ▲▼；
  左→右安装时**追加到末尾**（= 最低优先级），要覆盖内置就再往上调。
- **已知限制**：存档记录的是**包清单**（`meta.packs`，排序后比较），不含顺序——
  对局中途改序不会被存档校验拦下。覆盖是"按 id"的，跨包引用（DLC 引用被替换 id）
  仍需自行保证成组一致。
- **验证**：`tests/test_architecture.py::test_dlc_content_channels_and_rollback` 增加
  "包在 base 上→覆盖内置角色；base 调到上方→内置角色复原"断言；52 单测 / audit /
  validate / 冒烟全过（冒烟输出与改前一致）；无头 CDP 实测 DLC 页 9/9（base 常驻、
  ▲ 调序、应用后 `pack_order` 持久化、base 拒绝卸载、控制台零报错）。

## DLC 投放补齐：性格 / 状态·情绪 / tag 行为 / 地点分组 + 回滚闭环

- **来由**：一份探针报告列出「加 DLC 前须知」的缺口。逐条核实后（结论：①–④ 基本属实、
  ⑤ 的"除 ② 外全部还原"偏乐观），目标不是只堵两个漏，而是让**内容少改核心**。
- **回滚闭环**：`_BASE_CONTAINERS` 的键由"data 子模块名"改为**模块全路径**，于是
  `weiren_game.condition`、`weiren_game.data`（包根派生表）、`data.labels`、`data.personalities`
  都能纳入快照；`_clone` / `restore_base` 补 set 支持。补登的漏项：`ABILITY_TARGET_OPTIONS`、
  `CHARACTER_CODEX_EXTRA`、`PROTECTED_STARTERS`、状态·情绪键集合、`codex_pack` 静态表、
  标签表、地图分组权重。
- **登记缺口**：`register_character_module` 补 `SEARCH_REWARD` 与 `PROTECTED_STARTER`——
  此前 DLC 角色的搜索保底钩子不生效，`PROTECTED_STARTERS` 也不含它。
- **新目录投放**（`dlc.py`）：`personalities/*.py`、`statuses/*.py`、`tags/*.py`（行为模块，
  与既有 `tags/*.json` 并存）、`locations/*.py` 的 `MAP_GROUPS`（新分组纳入开局抽取）。
- **性格**：注册表搬进 `data/personalities/__init__.py`（`PERSONALITY_MODULES` /
  `PERSONALITY_LABELS` / `PERSONALITIES`），base 发现与 DLC 装载**共用**
  `register_personality_module` 一条路径；`PERSONALITIES` 改 list——DLC 追加后既有模块级绑定
  同样可见（若改成"重绑定"就会踩 `from ... import` 的旧绑定坑），顺序仍是 base 后追加，
  **不动随机确定性**。DLC 性格用 `LABEL` 给中文名，缺省回退键名（否则界面按中文名取值会 KeyError）。
- **情绪**：`ALL_EMOTIONS` / `EROSION_EMOTIONS` / `AWAKENING_EMOTIONS` 改 list；新增
  `register_emotion_definition` 统一登记「情绪显现」事件定义并同步 data 层中文名表
  （当时补的是 `reveal_<id>` 状态，后改为全局事件 `emotion.reveal.<情绪>`，见顶部条目）
  （系统与界面按那张表取 label）。
- **地点分组**：`BASE_MAP_GROUPS` / `MAP_DRAW_WEIGHTS` 改 list + `register_map_group`；
  `_generate_locations` 对空/缺失分组容错（`.get`）。无 DLC 时随机流不变（冒烟输出与改前一致）。
- **验证**：新增 `tests/test_architecture.py::test_dlc_content_channels_and_rollback`
  （装载生效 + 卸载逐项还原）；52 单测 / `audit_separation` / `validate_content` / 冒烟全过；
  另用临时探针包实测"装载→卸载"零残留、新分组地点 60/60 进开局池、`validate_content`
  接受 DLC 性格键。

## 屋主直接驱逐按钮 + 「隐藏」按钮残留

- **直接驱逐**：两条链（1 条已证实 / 3 条待验证指认）本来只有终端 `accuse` 命令，UI 没有入口。
  新增**纯查询** `engine.accusation_evidence(tenant_id)`（`pseudo_system.py`）：把"能否指认"的判定
  从 `accuse()` 里抽出来共用，阈值收敛为类常量 `ACCUSE_PENDING_NEED = 3`——不掷骰、不写状态。
  `build_state` 只对**在场且存活**的房客下发 `expellable` 与 `expel_risk`（risk = 有证据但尚无已证实）；
  前端 `expelBtn / askExpel / doExpel` 通用渲染：达标者**头像右上角**出「驱逐」，点击弹「否 / 是」
  确认框（`openDialog(..., hideFoot=true)`，按钮放在正文）。真伪判定仍留在 `accuse()` 里
  （真伪 → 驱逐替身 / 误逐房客），**前端只消费后端状态，不重算规则**。
- **「隐藏」按钮残留（修复）**：`#pendingBtn` 的显隐与文案完全由 `syncPeek()` 决定，但
  `mergeState()` 末尾只有 `renderAll(); maybePending();`——而 `maybePending()` 在"无待处理"时直接
  `return`，于是**状态已经清空、浮动按钮却留在屏幕上**（`confirmDialog()` 关弹窗同样不同步，
  双击选项确认后最容易复现）。点一下才会消失，正是因为那一下才走到 `syncPeek()`。
  修法：`mergeState()` 末尾补 `syncPeek()`；`maybePending()` 的空选项分支也补 `syncPeek()`。
- 顺带清掉 `.btn.danger` 的重复样式块。
- **回归**：`test_pseudo_fate.test_fries_accusation_clone_fortune_and_hermit` 增加 `expellable_of()`
  断言——无证据 `(False, False)` / 3 条待验证 `(True, True)` / 指认后证据失效 `(False, False)`；
  另用无头 CDP 实测 11 项（按钮位置与文案、确认框、点"否/是"后弹窗与浮动按钮状态、无 JS 报错）。

## DLC 做伪人的三个障碍：图鉴技能 / chip 重复 / 人形校验

- **⑦ DLC 伪人技能进不了图鉴「伪人」页（属实）**：`codex_pack.PSEUDO_SKILLS` 是内置静态表，也不在
  快照清单里。修法：图鉴页改为 `PSEUDO_SKILLS.get(pid)`，**取不到就回退读该伪人模块的 `CODEX_SKILLS`**
  （`((名称, 文案), ...)`）；突破/解放来自 `DEFINITION`，无需处理。
- **⑧ `ABILITY_CHIPS` 重复（属实，且有死键）**：键 `info_collect` 与真实 id `information_collect` 不符（死键）；
  `deep_thought`/`rose_recover` 与 `A(..., chips=...)` 重复。修法：把仅存在于表里的 chip
  （`call_friends`/`emotion_strip`/`group_counselling`/`encourage`/`ordinary`）**移进各自 `A(..., chips=...)`**，
  然后**删除 `ABILITY_CHIPS` 与 web_ui 的两处回退**——chip 从此完全由技能自声明，DLC 天然生效。
- **伪人人类形态（原报告称 engine.py:229 未修）**：经核实该行**已经**是 `key != pseudo_def.human_character_id`，
  实测人类形态不在访客池。但 `PSEUDO_HUMAN_CHARACTERS` 是**导入时**算的常量，DLC 加载后不刷新 →
  "禁用人形"的校验对 DLC 会漏。修法：engine 改为**运行时**从 `PSEUDOS` 计算；删除已失效的
  `PSEUDO_HUMAN_CHARACTERS` 常量（含测试里的未使用导入）。
- **Skill / 文档**：`.opencode/skills/weiren-dev`（必读加入 `docs/ARCH.md`、闸门措辞、dump 工具、测试数 51）、
  `weiren-new-dlc`（DLC 伪人 `CODEX_SKILLS`、chip 自声明、人形互斥）、`docs/ADD_CONTENT.md` 同步；
  `AGENTS.md` 测试数 50 → 51。

## 图鉴：伪人·薯条条目重写（暴露值可读性 + 对齐现实现）

- **问题**：`暴露值` 同时出现在伪人卡顶栏、`card_info.breakthrough`、以及「潜伏」长文里，读起来"混在一起"；
  且 `codex_pack.PSEUDO_SKILLS` 的薯条文案是旧稿（例如仍写"识破 +15 会再产线索"，与已修的
  **回敬不产新线索** 不符）。
- **改法**：重写薯条条目——「潜伏」拆开讲遭遇/绑架/替身；新增**独立**的「【暴露值】来源」一条，
  集中列出各来源与 5/10 里程碑；`card_info.breakthrough` 去掉暴露值数字，只由**印记（顶栏）**与
  「潜伏」技能行显示，避免同值多处堆叠。
- 纯内容文案改动，自检全过。

## 修复：薯条替身"还在外"就被「正义」驱逐

- **症状**：伪人薯条绑架搜索者后（人还在外），用命运牌「正义（正位）」竟能"驱逐屋内伪人"，
  等于白送一次驱逐、提前放回被绑架者。
- **根因**：`infiltrator_id` 在 `capture_searcher`（**绑架发生**时）就写入，而替身要到
  `captured_return`（返程）才真正回屋；`_card_11` 只判了 `infiltrator_id` 非空。
- **修法**：新增纯查询 `engine.pseudo_in_house()`——`infiltrator_id` 指向的房客必须
  **在屋 + 存活 + `is_pseudo`**。凡"驱逐/指认/处理**屋内**伪人"的判定统一走它：
  `erebus._card_11`（正义）、`information_system`（伪人在屋信息的生成与真伪）、
  `round_effects`（伪装表演的触发）、`zero329`（直觉概率 .65/.25）。
  （`settle_end` / `performance` 原本已查 `at_home`，保持一致。）
- **回归**：实测"人在外"时正义不生效（`infiltrator_id` 与进度不变）；替身回屋后才能驱逐。
## 效果内核 P3-1：`emotion.apply.block` 迁移（三层拆分）

- `condition_system._emotion_application_blocked` 改为**三层**：
  1. **通用基础谓词**：状态自带 `blocked_emotions` + hook（`calm_onion`「平静-洋葱」仍走这里）；
  2. **纯闸门** `emotion.apply.block`（`path=("施加", 情绪键)`）：`zero329._erosion_block_gate`、
     `information_carriers._legend_erosion_block_gate`、`onion._irritation_block_gate`；
  3. **结算点**：可能掷骰/带副作用者保留为节点 hook——`onion.calm_irritation`（30% + 得共情印记）
     迁到新节点 `condition.irritation.settle`。
- 废弃 `condition.erosion.block` / `condition.irritation.block` 两个节点（无残留注册）。
- **注意**：`irritation` 本身属于**侵蚀情绪**，因此"侵蚀免疫"同时挡烦躁——这是既有语义，迁移后不变。
- 结果：51 单测 / `audit_separation` / `validate_content` / 冒烟 全过。
- **其余目录项的评估结论（保留）**：`status.apply.block` 的两个注册方都**带消耗/掷骰**
  （高生命免疫扣充能；护甲 25%×4 且扣 5 耐久）→ 属结算点，不做纯闸门；`status.extra_effect.allowed`
  是 `suppresses_conditions` + hook，**与 `blocked_emotions` 同型的通用状态字段** → 不另设 gate；
  `pseudo.capability` / `action.allowed` / `information.verify.allowed` / `pseudo.in_house` 已是
  **全局事件/字段**形态；`target.lock` / `search.resist` 受保护（§7）。→ **可干净迁移的声明式闸门已迁完**。

## 效果内核 P1/P2：闸门内核 + `emotion.visible` 迁移

- **P1（内核）**：`modifier_rules` 新增 `Gate` / `gate()` / `GATE_REGISTRY` / `GATE_PROVIDERS` /
  `collect_gates` / `evaluate_gate`，与修饰器**共用** `_source_tokens` / `_matches` / `path·source·match`；
  聚合为逻辑（`any`=OR、`veto`=NOT，**veto 最终生效、与顺序无关**）。
  `marks_system` 新增 `engine._eval_gate(gate_type, source, context, base=False)`——**纯查询**（不掷骰、不写状态）。
- **P2（首迁 `emotion.visible`）**：`engine.emotion_visible` 只保留**基础谓词**（强度>5 / `reveal_*` 状态），
  其余改走 `_eval_gate("emotion.visible", source=("显示情绪", 情绪键))`；`chaos`（理智/癫狂）、
  `onion`（烦躁）、`pseudo_onion`（初访后烦躁，读全局事件 `emotion.reveal.irritation`）改为注册
  **gate provider**，删除各自的 `EMOTION_VISIBLE`。行为等价（含初访后才接纳的房客）。
- **工具/文档**：`tools/dump_effects.py` 增加闸门清单输出；方案、令牌词表、闸门目录与迁移进度见
  `docs/ARCH.md`（P1/P2 已标 ✅）。后续按 P3 逐个迁移（`emotion.apply.block` → `status.apply.block` → …）。

## 洋葱「情绪显现」漏新客 + 详情页显示印记

- **bug：伪人洋葱不给新接纳的房客揭示烦躁**。原实现是"给当时在场的房客逐人挂 `reveal_irritation`
  状态"（`on_first_reveal` / `on_emotion_increase`），初访之后才被接纳的房客没有状态 → 看不到烦躁。
  现改为**全局事件**（通用键）：`engine.emotion_visible` 通用地读 `emotion.reveal.<情绪>`；
  `pseudo_onion.on_first_reveal` 初访时 `_set_global_event("emotion.reveal.irritation", 1, 99)`，
  洋葱解放时 `_consume_global_event` 结束它。`emotion_end_extra`（烦躁追加恶化/延长）也改读该事件。
  逐人 `reveal_*` 状态机制保留（信息/技能等单点揭示仍在用）。
- **房客详情页显示印记**：`build_state` 的租客 `marks` 由 `[icon,label,""]` 改为
  `{label,current,max}`（`max=None` 表示无上限）；前端在**头像右侧**（`.td-avid`）按
  「名称 当前 / 上限」显示，无上限只显示当前——纯文本，不做条条。

## 上供界面重排 + 混的选项文案

- **上供槽**：`.submit-slot` 从"一整条黄框（70px 高、全宽）"改成**墨绿面板 + 中间一个小格子
  （`var(--slot)` = 60px）**，槽位下方显示物资名与品质；放入物资的图标限 22px
  （此前 `.art-img` 在该处没有尺寸 → 按 SVG 固有尺寸渲染，所以"超级大"）。
- **总物资栏**：改 `grid-template-columns:repeat(auto-fill, var(--slot))` + `justify-content:center`，
  固定格宽、居中对齐，间隔均匀（原来是 `repeat(6,1fr)` 配固定宽格子，间隔忽大忽小）。
- **混的权限转让文案**：选项改为不直白的「代我出手 / 收走那道伤 / 收走那点乱」，描述去掉「（外）/（内）」
  的机械标注（`nested_option="imitate"` 等机制字段不变）。

## `discover` 支持权重池（朝"统一选择原语"走）

- **统一方向**：「发现」的本质就是**从池子里选**——玩家选择（`discover`）与加权随机
  （`_weighted_choice`）本来是两套。约定：`discover(pool, count)` 在 `count < len(pool)` 时抽样、
  否则全给；池子可带权重。
- **本次落地**：`discover` 的池子现在支持混入 `(值, 权重)` 项（权重为数字）→ 走**加权不放回**抽样；
  **纯值池的路径与随机流保持不变**（避免改动既有对局的可复现性）。新增 `_weighted_sample` /
  `_weighted_pick`。实测：权重 100:1:1 的池子 200 次里 199 次抽到高权重项；纯值池仍近似均匀。
- **尚未做（做的话要单独评审）**：把能力的 `options` / `TARGET_OPTIONS` / `PENDING_VIEWS` 也表达成
  "池 + 选择视图"，让前端只认这一种"选择池"渲染。目前能力选项是**固定列表**（玩家选择、不随机），
  与 `discover` 的抽样语义不同，合并要明确"池/数量/权重/是否随机"这几个字段。

## 混的性格改为随机 + 房客卡显示"运行时性格" + 派搜索的结算顺序

- **混可以自选性格（bug）**：`roll_personality_and_carry` 原本用 `engine.discover(...)`，
  而 `discover` 会挂起 `_pending_choice`，于是玩家每到回合开始就被弹一次"选性格"。
  改为**按种子随机取两个不同性格**（`_rng(...).sample`），不再产生待选。
- **房客卡显示静态 `混沌-混沌`**：`build_state` 的 `persona` 与 `providers` 之前读角色**静态定义**
  （`info.primary/secondary`）。改为读**运行时** `engine._tenant_personalities(tenant)`，
  于是混经过随机切换、以及性格改写类效果（如某些物品）之后，卡片与羁绊名单都会显示真实性格。
  但**混未固定自我（`pure_self`）时对外仍显示「混沌」**——按原稿「性格：？」：内容层用
  `PERSONA_LABEL` 钩子覆写（`chaos.persona_label`），`build_state` 统一走 `persona_display`；
  固定后显示真实性格。（图鉴仍是静态预览，显示「混沌」。）
- **权限转让改为"启动一次、之后免费"**：原稿是"混消耗1层理智并获得1层癫狂"每次发动都付。
  按澄清改为：**首次**发动支付一次「1理智→1癫狂」作为启动代价（状态 `permission_shift`），
  此后（外）模仿 /（内）治疗两个分支都**不再消耗理智**，只受**每回合 1 次**（`per_turn=True`）约束。
- **权限转让"选完目标没反应"（bug）**：技能声明了 `options`（治疗创伤/治疗紊乱/模仿）与
  `nested_option="imitate"`，但前端 `useAbility` 的 `tenant` 分支选完目标就直接发送、忽略 options；
  且 `web_ui` 的 ability 动作**没有透传 `copied_ability_id`**。改为：
  `build_state` 下发 `nested_option`；前端新增 `afterTarget`（目标→效果）与 `pickCopiedAbility`
  （选中的是 `nested_option` 时列出目标主动能力）；`sendAbility`/后端动作透传 `copied_ability_id`
  （及 `secondary_*`）。实测：目标 → 治疗创伤/治疗紊乱/模仿 → 模仿 → 目标的主动能力列表。
- **顺带修一处结算顺序 bug**：`start_search` 先在"搜索者尚算在屋"的状态下 `_recalculate_search`，
  之后才把 `at_home=False`；导致首次掉落与之后任何一次重算不一致（测试 `test_recompute_…` 抓到）。
  改为**先离屋再结算**，搜索者的性格/羁绊不再计入屋内加权。

## 发现页/悬停/羁绊层级/命运抽牌流程

- **悬停延迟**：简约模式的技能悬浮 1s→**0.5s**；伪人卡技能悬浮 1s→**0.5s**；发现页选项 **0.25s**。
- **发现页泛化**：`web_ui` 的待选项不再只下发名字字符串，而是视图 `{kind,id,name,avatar/art/icon,desc,...}`：
  房客→头像/立绘，性格→大图标 + 中文名 + **当前激活加权总和**，物资→图标与品质。前端 `discoverCardHtml`
  通用渲染 + 0.25s 悬浮说明。**修掉**混的「混沌的性格」发现里选项显示英文性格键的问题。
- **羁绊悬浮层级**：未激活 chip 用了 `opacity<1`，会**新建层叠上下文**，导致其悬浮窗掉到可视日志之下。
  改法：给 `.bonds-strip` 加 `position:relative;z-index:80`，整条栏抬到内容之上（不再依赖逐个 chip）。
- **命运抽牌重排为四步**：① 选牌（**只给牌面，不揭示方向**；悬浮 0.25s 列正/逆效果）→
  ② 是否上供（「命运之轮」类**跳过**此步）→ ③ 选方向（上供时同时选一件物资）→
  ④ 宣布方向 + 结算/反悔。视图 `options` 改为结构化（number/name/display/upright/reversed/
  orientation/requires_orientation），文案全部由内容层下发。**踩坑**：前端不得出现 `正位/逆位/抽牌/
  牌面/命运牌` 等词（`audit_separation.FRONTEND_FORBIDDEN`），故文案与「未知牌」等一律经视图下发。

## 修复：随机伪人失效（Web 端新建对局恒为苯环）

- **症状**：从创建页随便开一局，伪人几乎总是苯环。
- **根因**：`web_ui.Session.new_game` 只透传了 `pseudo_id`、**没传 `random_pseudo`** → 引擎回落
  `CONFIG.random_pseudo`（默认 False）；而 `engine.new_game` 在 `pseudo_id is None` 时取
  `CONFIG.default_pseudo or DEFAULT_PSEUDO`，其中 `DEFAULT_PSEUDO = pseudo_benzene`。
  前端 `confirmCreate` 也只发 `pseudo: null`、**没发 `random_pseudo`**——所以"随机"从未真正生效。
- **修法**：前端在「勾选随机」或「下拉选到（随机）」时发 `random_pseudo:true`；
  `Session.new_game` 透传 `random_pseudo`（缺省 `None`，引擎仍回落 CONFIG，向后兼容）。
- **验证**：24 个随机种子 → 苯环 9 / 洋葱 8 / 薯条 7；不带该字段仍为苯环；指定伪人不受影响。

## 平衡待办（讨论中，暂不实施）：退化公式的构成

> 按用户要求：先只做诊断、**不改内部**，等整轮平衡讨论结束后一起开刀。以下为已定位项。

- **柳七鱼「不行，我要受不了了」产出 = 10 份**（设计稿为 **2 份**；驱逐后屋内 ≤3 人额外 +1）。
  单次驱逐白拿 10 件 ≈ 每接纳一名访客 = 10 件；`cannot_stand` 又未声明 `per_turn`（不限次数），
  一回合即可清空整屋；叠加驱逐近乎零代价、遗物（含购物袋）全额归还 → `招人→枪毙` 成为无条件最优。
- **待一起评估的候选**：产出改回 2(+1)；是否加 `per_turn`/冷却；产出是否与目标携带物资挂钩；
  购物袋回收是否应更易损；以及其它角色的同类"净赚"点（用户指出不止柳七鱼一人）。

## 细节：背包标题按钮固定、羁绊窗口收窄

- 背包悬浮窗标题行：三角按钮改为**相对窗口绝对定位**（右缘固定），标题 / 名字 / 容量在剩余空间里
  省略——字数再多也不会把按钮挤出窗口。
- 羁绊概况抽屉宽度 **400 → 340px**，减少对房客席位的遮挡。

## 设置分层 + 显示设置（紧凑技能）+ 背包悬浮窗 + 日志分隔行

- **设置页改为菜单**：`设置` 进入后是「显示设置 / 难度 / 图鉴」的菜单，难度拆进独立子页
  （`lpaneDifficulty`），新增显示设置子页（`lpaneDisplay`）。PANE_IDS 相应扩展。
- **显示偏好 `show_full_skills`**（默认开，持久化到 `game_config.json`，随 `/api/menu` 下发）：
  关 → 房客详情页技能只显示一行（名称 + chip），**悬浮 1 秒**用悬浮层显示完整效果；
  开 → 现状（直接展开 `a.text`）。实现：`tenantDetailHtml` 分支 + `abilityHoverStart/End`。
- **房客背包**：与仓库**同宽对齐**的贴底悬浮窗（绝对定位在 `.warehouse-col` 内、`bottom:0`，
  覆盖其上、不改变仓库布局）；**6 格/行、最多两排**，超过两排则内部纵向滚动；点击房客默认展开
  （`setBpCollapsed(false)`），可用三角折叠。
- **可视日志**：字号调小、标题单行容纳「清空显示」；`==== 第 N 回合：回合开始 ====` 这类分隔行
  改由 **CSS 画满宽横线**（`.log-sep`），长度不再随原文等号数量变化，换行不再难看。
- **启动器内 Esc 逐级外退**：`display/difficulty/codex → settings`，其余子页 `→ main`，
  且**不弹**「退出对局」（退出弹窗只在游戏中、启动器关闭时才出现）。

## 悬浮窗化（背包 / 外出搜索 / 羁绊概况）+ 格子凹陷 + 指派按钮失效态

- **房客背包**：不再嵌在展开卡里，改为仓库列底部冒出的**贴底悬浮窗**（`.bp-float` 绝对定位在
  `.warehouse-col` 内），只占一排，超出的格子在该区域**横向滚动**；只占自身区域、不拦截外部操作。
  仓库平时占满右半，悬浮窗轻微遮挡其底部。
- **外出搜索**：同样改为贴右栏底部的悬浮窗（`.mission-float` 绝对定位在 `.detail-panel` 内），
  右上角三角切换展开/收起（收起只留标题条）；无人工干预时**有任务自动冒上来**，玩家手动收起后
  尊重其选择（`MISSIONS_MANUAL`）。现有信息因此可以占满右栏。
- **羁绊概况**：去掉遮罩（`.drawer-backdrop{display:none}`）不再阻塞外界点击；「拥有此羁绊的人」
  改为「**本局可提供此羁绊**」，由后端下发本局名单（排除本局禁用角色与伪人的人类形态）。
- **格子质感**：仓库/背包格子加暗底 + 内阴影，做出"凹陷"实体感。
- **指派搜索按钮**：新增 `.pressed` 失效态，状态由后端 `searchBlocked` 下发（当前=本回合已指派）；
  **前端不写死搜索次数规则**，将来若一回合可多次搜索，只改后端这个字段。
- **可视日志**：去掉导出按钮（导出只在存档页），隐藏滚动条、文本自动换行；新消息用平滑滚动到底。
- **文案/标签**：信息条数 chip 显示「N 条」并加 tooltip；保存/读档的可见文案改为
  「保存游戏。」/「进入游戏。」，自动存档静默（`save(quiet=True)`，只在完整日志留痕）。

## 修复薯条暴露值的自我放大（信息暴增的真凶）

- **现象**：薯条对局的信息条数异常膨胀（实测 32 回合堆到 **237** 条，其余伪人只有 7~19 条）。
- **根因（正反馈环）**：`on_information_verified` 对「由暴露值产生的虚假信息」回敬 **+15 暴露**；
  而 `add_exposure` 按**每累计 5 层**产 1 条假指认、每 10 层产 1 条真指认。于是
  「识破 1 条 → +15 → 再生 3 条假指认 → 又被识破 → …」增益 ≈ 3，指数级放大。
  多疑羁绊的「每回合识破 1 条虚假信息」让它**每回合自动发生**，所以只在薯条 + 多疑同场时炸开。
- **修法**：给 `FriesState` 增加独立的 `milestone_pool`，只有**自然来源**（回合结束 +1、
  玩弄人心 +3、模仿能力 +3/+7、理智溢出转化）才累计进该池并触发里程碑；
  「虚假信息被识破 +15」改用 `add_exposure(..., spawn=False)`——**仍计入暴露总量（照常推进
  炼狱扳机/心机判定），但不再产新指认**。指数环被切断，实测同种子回落到 17 条。
- **偏离一处设计稿**：原稿「每累计获得 5 层暴露值产指认」字面上包含这 15 层回敬，正是环的成因；
  这里按「回敬只推进炼狱扳机、不产线索」处理，已在设计稿附录 A 记差异。回归见
  `test_pseudo_fate.FriesExposureTest`。

## 伪人解耦 / 信息可读性 / 席位与仓库左右重排

- **伪人不再直连具体角色**：`pseudo_fries.captured_return` 原本 `from ...characters import zero329`
  再调 `on_fries_capture`，等于伪人技能硬编码某个角色。改为广播通用节点
  `pseudo.tenant_replaced`（在 `pseudo.instance.created` 之外单独发一次，避免重复触发），
  澪叁贰玖在自身模块里以 `HOOKS` 订阅并响应。伪人侧现在不知道任何角色存在。
  （`character_items.py` 里「仅比格小星可用」属内容→内容的描述文案，保留；限制由 `bigstar.py` 判定。）
- **伪人技能信息不再露内部 id**：`observed_skills` 由 `("trigger", …)` 改为返回
  `(("trigger", "炼狱扳机"), …)`；`information_system` 用展示名写文本、用 id 存 `data` 供核验。
  此前信息里会出现 `[trigger]` 这类裸 id（本次一并修）。
- **信息来源可读 + 可收纳**：`web_ui` 的 `intel` 条目补 `source` 与 `kind_label`；信息面板每条显示
  「来源：X · 类型」，并加「隐藏已失效」开关（`INTEL_HIDE_EXPIRED`）。生成频率（如多疑每回合
  1~3 条）仍与设计稿一致，**未改数值平衡**。
- **日志随对局重置 + 可导出**：完整日志改为持久化（`SessionLogState.entries`，随存档保存/读档恢复；
  回溯保留日志）。前端新增 `seedLog()`——开新局/读档时用它重建可视日志，不再把上一局的内容留下。
  新增 `GET /api/export[?file=]`（复用 `engine.export_full_log()`），可视日志「导出流程」与
  存档页「导出所选流程」都会下载 txt。
- **对局界面重排**：中间改为一行满高（去掉上下两层的 dock），内部左右分栏——左「房客席位」、右
  「屋主仓库」。仓库 6 格宽、席位固定 3 列；原「房客背包」面板移除，改为选中房客时出现在其展开卡
  正下方。选中房客不再用详情页替换整个网格，而是**完整卡置顶、其余缩略卡在下方**，再点（或点空白/
  「返回席位」）回到原排布；缩略卡名字过长按字数自动缩小并省略。拖拽到房客/仓库/背包等交互沿用原处理器。
  **踩坑**：`.cd-av` 之外的 `.panel>.head` 在窄栏里 `nowrap` 会顶出面板、`wrap` 又显乱，
  最终用「容器 wrap + `.btn` 自身 nowrap」，标题不竖排、按钮不裁切。

## 图鉴「机制」教程重做 + 羁绊图标分档位循环

- **教程正文移出 `codex_pack.py`**：新建内容层 `data/codex_mechanics.py`（`MECHANICS`），
  `codex_pack` 改为 `from .codex_mechanics import MECHANICS`。旧教程内容陈旧且过简
  （难度仍写 `a1~a6`、苯环解放写 2/3 次），单独成文件便于继续维护。正文只讲**通用规则**、
  不列具体内容，数值一律以 `systems/` 实现为准（已核对：难度 `a-10~a10`、房客上限 10、
  休克强度上限 4、每回合一次搜索、苯环解放 5/7 等）。现为 **17 节 / 95 条**。
- **羁绊页图标循环预览（纯展示）**：`index.html` 新增 `start/stopBondTierCycle`——详情页
  `#bondTierIcon` 每 **1.4s** 在 `t-bronze/silver/gold/prism` 间轮换，并同步 `#bondTierPreview`
  文案；离开图鉴（`lpane` 切页 / `enterGame`）停表，切分页 / 切条目由 `renderCodexDetail`
  顶部重入停表。颜色覆盖写成 `.cd-av.t-*`：`.cd-av` 的默认琥珀色虽同权重但定义更靠后，
  不提高特异性就盖不掉、看不出变化。
- **顺带修 `mdText` 加粗失效**：行首 `·` 的临时哨兵原本复用 `\u0001`（与加粗占位 `\u0001b` 撞车），
  导致 `**加粗**` 渲染成「·b…」。改为独立哨兵 `\u0003`。新教程大量使用加粗，才暴露这个老 bug
  （此前内容几乎不用 `**`）。
- **文档同步**：`AGENTS.md` 难度范围 `a-6~a0~a6` → `a-10~a0~a10`；`GUIDE.md` 苯环突破补
  `max(0, …)`、解放 2/3 → 5/7。

## 屋内死亡与驱逐统一为一条移除路径

- **设计澄清**：**屋内死亡与驱逐本质是同一件事**（房客都离屋且不再回来），唯一区别是播报文本；
  对伪装中的伪人（in-house pseudo）两者也都是"离屋"——都走 `expel_infiltrator`。
- **之前的问题**：`_expel_tenant` 把房客置 `alive=False`，却不走 `_notify_tenant_death()`。
  于是驱逐不算死亡：苯环突破的「两次来访之间死亡数」不增加、也不打断「早交班」的连续无死亡进度；
  角色的 `TENANT_DEATH` 被动同样被跳过。（`alive=False` 与"未通知死亡"语义混用。）
- **修法**：抽出公共收尾 `engine._remove_tenant_from_house(tenant)`（归还遗物 → 清任务 →
  `_notify_tenant_death()` → `_after_health_changed()`），`_kill_tenant` / `_expel_tenant` 共用。
  两者只剩调用方的**播报文本**不同，以及驱逐附带、且由基础设定声明的「其余房客理智 −5」
  （`sanity_exempt_ids` 供柳七鱼自身豁免）。
- **顺带修**：旧驱逐按实例逐件 `_return_item` 归还、忽略 `count`，**堆叠物只会还 1 个**；
  改用 `_return_tenant_items` 后按堆叠完整归还。
- **回归**：`test_benzene_marks_breakthrough_and_liberation` 增加「驱逐推进死亡计数、打断早交班」断言。

## 使用 / 装备精确到玩家选中的那一件（槽位）

- **症状**：同名的耐久品 / 堆叠物，使用或装备时总作用到"最靠前"的那件，而不是玩家点 / 拖的那件。
- **根因**：后端 `use_item` / `equip_item` 早已支持 `slot`（`_take_item` / `_consume_durability`
  用 `spot` 精确定位，`equip_item` 用 `inventory.at_plot`），但前端只在**背包来源**时带 `slot`；
  **仓库来源**的点击与拖拽都漏了（`slot:fromBp?index:null`、`use_item/equip` 干脆不带槽位）→
  后端回退 `earliest / remove_first`，即"最靠前的一件"。
- **修法**：所有物品动作统一带 `slot`（仓库 = `plot`，背包 = `plot`）——`showItemUse`、
  `dropOnTenant`、`dropOnBackpack` 三处补齐。顺带修槽位悬浮提示的耐久：`showItemTip` 改为接收
  该格自身的 `dur/dmax`，不再用 `itemEntry(name)`（首个同名，和鼠标所指无关）。
- **回归**：单测 `test_use_exact_slot_bag_and_warehouse` 覆盖仓库精确槽位；
  无头浏览器实测四种入口（点击使用 / 点击装备 / 拖给房客 / 拖进背包）的动作体都带正确 `slot`。

## 羁绊图标重绘 + 位阶配色（金 / 棱彩）

- **羁绊图标换成"签名物"**：原 8 个过于抽象、小尺寸下难以区分。改为一件可辨识的物象：
  太阳（开朗）/ 侧身人像+隔离线（孤僻）/ 四角星芒（机敏）/ 挂锁（固执）/ 山脉（稳重）/
  闪电（急躁）/ 心（温和）/ 眼睛+斜杠（多疑）。仍为单线 SVG（`stroke:currentColor`），
  保证 19px 列表与 72px 图鉴都清楚。
- **金色更黄**：`--gold` 由 `#e2a84d`（与 `--bronze` 太近）改为 `#f3d24e`；徽记另加金色渐变底。
- **棱彩要"华丽"而不是纯紫**：新增 `--prism-grad`（青绿→蓝→紫→金→粉）。棱彩档名用
  `background-clip:text` 走渐变字；图标描边用 SVG 渐变 `stroke:url(#prismGrad)`（在 defs 里定义），
  徽记走同一渐变底。**注意**：渐变文字只能加在纯文本元素（`.t-prism.nm/.name`），
  不能给承载 SVG 的 `<span class="t-prism">` 设 `color:transparent`，否则 `stroke:currentColor` 的图标会消失。
- **缓存**：`/api/*` JSON 响应补 `Cache-Control: no-store`，避免后端已更新但浏览器仍用旧状态。
  （**后端改动必须重启 UI 进程**才生效；只刷新页面只能拿到新的前端 HTML。）

## 羁绊激活显示 + 游戏内物资图标同步外置图

- **羁绊"是否激活"看 `reached`，不看 `tier_value`**：非"达到即激活"的性格（`TIER_AT` 返回 0）在
  任意等级下 `tier_value` 恒为 0，前端 `tierFor` 曾用它 `indexOf` 判档 → 明明已激活却显示成"未激活"
  （孤僻/固执）。后端早已下发 `reached`（当前激活档位的序号，由内容 `ACTIVE_TIERS` 决定），
  前端改为只按 `reached` 映射位阶色；达到即激活的普通羁绊结果不变。**颜色/档名映射仍是纯展示。**
- **物资图标统一走外置图**：`assets/art/` 的接口约定是"有图就覆盖内置图标"（见 `docs/STYLE.md` §5、
  `assets/art/README.md`），品质色也已烧进物资 SVG。但游戏内槽位一直用标签内置图标（午餐肉/蒜瓣同为
  `i-snack`），只有图鉴吃 `art` → 同一件物品两处图标不一致。修法：`_item_entry` 多下发一项 `art`
  （数组末位，缺图空串），槽位 / 提交池 / 上交槽一律用 `iconOrArt`，并补 `.slot .art-img` 尺寸
  （与 `svg.ic` 同 20/22px）。品质仍由 `.slot.qN` 负责左边框与名称。
- **顺带修**：`codex_state()` 漏下发 `qualityNames`，图鉴物资页品质筛选只剩"全部"；已补。

## 技能条 / 信息条排版 + 外置美术接口启用

- **房客技能条改两行**：`.ability` 由「名称 | 描述 | 按钮」三列改为上下两行——第一行
  `徽记 + 名称 + chip + 状态徽记`，第二行是技能描述。**可用的主动技能不再单独放「使用」按钮**：
  整条技能栏本身就是按钮，复用 `.btn` 观感并整条可点（`useAbility`）；本回合不可用（冷却/已用/已封印）
  加 `.locked`，用 `translateY(2px)` + 内凹阴影表现**按下未回弹**；被动技能保持普通条目（不可点）。
  旧的「已封印/冷却/本回合已用」从按钮列移到第一行 chip。
- **信息条改两行**：新增 `.acc-head.head2`——第一行信息简称（尾随折叠箭头），第二行 chip 贴左、
  状态徽记（待验证/已证实/已证伪/已失效 四态之一）贴右；正文里重复的失效信息已删。
- **外置美术接口启用（已铺满 131 张）**：`assets/art/` 新增 **24 房客 + 3 伪人 + 57 物资 +
  25 地点 + 22 信息** SVG 并登记 `manifest.json`（缺图仍回退内置图标）。头像由多模态模型按角色特征
  （发型/配件/强调色）产出，伪人是同一底的"污染版"（红调 + 螺旋眼 + 错位线条）；地点按功能分组上色
  （医疗绿/食物琥珀/工具雾蓝/混合灰），信息按类型上色（物资线索琥珀/地点修正雾蓝/房客状态紫）。
- **地点 / 信息的接入点**：地点图鉴本就吃 `o.art`，只需补 `build_state` 的 `locations[].art` 与前端
  "选择地点"弹窗改用 `iconOrArt`；信息的 `codex_state().information[]` 原先没有 `art` 字段（前端恒用
  `i-note`），补 `art_url("information", _iid)`；游戏内「现有信息」按 `Information.template_id` 下发
  `art`，行首加 19px 小图标（动态生成、无模板的信息回退 `i-note`）。
- **物资品质色写进 SVG**：`<img>` 不继承 `currentColor`，所以**逐件把该物品的品质色烧进 SVG 的强调部分**
  （`--q0..--q5`），保住"部分颜色代表品质"的观感；槽位左边框与名称仍走 `.slot.qN`。
  **局限**：同一张图无法随品质动态改色；若品质将来会变，需改成 mask/inline SVG 渲染。
- **图鉴列表行的坑**：`.codex-row .cv` 只靠 `svg.ic` 的 19px 定尺寸，换成 `<img>` 后按 SVG 固有尺寸
  （≈300×150）撑破行、看起来"崩了"。补 `.cv .art-img{width:19px;height:19px}` 对齐内置图标尺寸。

## 背包槽位 / 拖拽 / 搜索容量（一次系统整理）

- **携带容量统一入口**：新增 `engine.tenant_carry_capacity(tenant)`（角色基础容量经
  `search`·`携带` 修饰器管线演算）。界面格数、装备/转移上限、搜索容量全部走它，修掉"背包显示
  2 格、搜索却按 7 格结算"与"ED + 购物袋看不到 7 格"的错位。
  **修饰器以基础容量为 `base` 参与全阶段**（flat/percent/mul/limit/final），而不是"先按 0.0 算
  增量再相加"——后者会让乘算/百分比被 0 基值吃掉，任何非 fixed 的携带修饰都会失效。
  正则回归：`test_multiplicative_carry_modifier_is_honored`（模拟未来 `携带` 乘算修饰）。
- **搜索回合改用最终容量**：`start_search` **先在演算前**求出容量，再摇
  `[容量×0.75]+1 ~ [容量×1.5]`（原稿公式），不再"用基础容量摇完再补 +5"。只挪动了修饰器的
  **作用节点**，没有另起一套数值系统。`固执`的容量 +1/+2/+4 从 `search.start.bond`（演算之后、
  且带 RNG 与保底副作用的 hook）移到无副作用的 `携带` 修饰器，才能既被搜索、也被界面/装备上限
  共用；否则同一个"基础容量 + 修正"会出现两套口径。
- **真实槽位下发**：`build_state` 的 `warehouse` 与房客 `inventory` 改为**定长数组**（空格 `null`，
  带 `warehouseSize`），前端按槽位渲染；`ItemInstance.plot` 是唯一权威。
- **自由摆放**：新增 `engine.move_item(container, from_slot, to_slot)`；仓库与背包内拖拽即移动，
  目标格被占用则与原占用者**交换**（`Inventory.move_to`）。
- **来源感知的使用/装备**：`use_item / equip_item / unequip_item / transfer_item` 增加
  `source_tenant / slot / target_slot`。可直接使用房客背包里的物资（此前只认仓库，故"背包物品
  不能拖拽使用"）；耐久品精确扣到被拖的那一格（`spot`），用后留在原格。
- **容量缩小即溢出**：卸下/转移购物袋等容量来源后调用 `_spill_tenant_overflow`，超出格数的物资
  回到屋主仓库，不再"看不见 = 消失"；搜索返程损坏购物袋后同样结算。
- **死亡/驱逐归还的范围**：**只有屋内死亡与屋内驱逐**才把背包物资归还仓库（`_kill_tenant` 判
  `tenant.at_home`；驱逐走 `_expel_tenant`）。屋外死亡（搜索途中）、理智过低自行离开、连续被拒
  两次后离场，均**不返还**——遗物随人走失。
- **装备标志由内容规则派生**：`_item_entry` 的 equip 标志改为 `item_requires_equip` /
  `item_is_carried_only` / 是否可 `use` 推导，而非旧 `EQUIP_TAGS` 一刀切——修正
  "星之玩偶/智能手机被当成装备"、"弹药被当成可使用物"。
- **前端**：新增 `bpTenant`（退出房客详情不清空背包对应房客）；`webui` 的拖拽统一携带
  `itemId/kind/slot`；房客技能行改为两列（名称+chip / 描述 / 尾部按钮）；羁绊抽屉恢复完整
  逐档文案（`PERSONALITY_TIER_TEXT`）并只高亮"恰好激活"的一档；伪人悬浮窗锚定伪人卡；
  未揭示时印记显示 `? / ?`；信息条改为「名称 + 失效 chip 贴左，状态徽记靠右」。

- **修饰器 base 语义（值型 vs 增量型）**：`calculate_modified_amount` 是一个大公式且恒等
  ——缺加算 = 0、缺乘算 = 1、未出现的阶段不参与计算；唯一的坑是调用方传 `base=0.0`：通道里
  一旦有 `percent`/纯 `mul`，这一步就会被 0 吃掉。**凡该通道可能含乘算/百分比（值型）就必须传
  真实数值**。已修 `search`·`携带`（容量）、`search`·`回合`、`search`·`时运`（改为以真实
  回合/时运为 base 演算再换算回增量）。`抵御` 概率累加器（撬棍/运动鞋/燧发枪/堤谧特/久孤/错潮）
  是**纯加算点数**，以 0 为基值即其定义，保持不动。回归：`tests/test_modifier_pipeline.py`。

## 难度扩展 a7 / a-7 与开局补给

- **正向=更难、负向=更易**：新增的两级沿用该约定，所以 `a7`（更难）开局补给更差、
  `a-7`（更易）开局补给更好（此前一度把符号写反，已按难度方向对调）。
- **新增两条难度词条**（`data/__init__.py`）：`start_fortune_delta`（本池时运）与
  `start_loot_draws`（多抽/少抽几次池子）。
- **时运走修饰器、用 source 区分**：不开新概念。`_difficulty_search_modifier` 为
  `start_fortune_delta` 产出一条 `path("开局")` 的 `search`·时运修饰器；开局补给调用点用
  `_apply_modifiers("search", 0.0, ("开局","时运"), ...)` 收集，于是全局 `fortune_delta`
  （a4/a-4）与本池时运一起叠加（`a7 = -1 + -3 = -4`），而搜索调用点的 source 不含「开局」，
  不会被污染。为支持这个无 tenant 的调用点，各 `search` provider 统一对 `tenant is None` 提前返回。
- **开局抽取改为品质加权**：新增 `engine._start_loot_draw()`，权重 = `品质权重 ×
  max(.01, 1+时运×0.1×(品质+2))`，与搜索公式一致。代价是 **a0 及所有难度的开局抽取不再是
  池内等概率**，现有种子的开局物资会变化（属于预期）。
- **次数词条 = 多抽/少抽几次池子**：`_start_loot_schedule()` 在基础「食物2/医疗1/工具1/载体1」
  上整体增减；多抽时按种子随机类别加一次，少抽时按种子随机去掉一次（不绑定某个类别）。
- **词条生成数据驱动**：取 `_POSITIVE/_NEGATIVE_TOKENS` 的最大等级生成档位与顺序表（目前共
  21 档：a-10…a0…a10）。
- **a8 / a-8（开局生命与理智）**：新增两条词条轴 `start_vital_pct`（当前值百分比）与
  `start_vital_max_pct`（最大值百分比）。`a8`：开局房客当前生命/理智 −20%（普通 100→80，
  沙白理智 50→40）；`a-8`：最大生命/理智 +20% **且当前值同样 ×1.2**（100→120）。仅在
  `_finish_start` 对**开局房客**结算一次。
- **a9 / a-9（开局消沉值）**：`start_depression_delta` = ±100，写入开局房客的隐藏消沉值。
- **a10 / a-10（开局异常状态 / 免疫）**：`start_condition_trauma_disorder` 在
  `_on_tenant_accepted`（含开局房客与后来被接纳的访客）附带 1/99 的创伤或紊乱；
  `trauma_disorder_immunity` 复用「高生命免疫」状态——入住时**一次性给 99 点充能**即可常驻，
  不做每回合刷新。
- **高生命免疫改为「充能强度」**：`high_health_immunity.intensity` = 可抵挡次数（隐藏，
  `shown` 不含 intensity），规则按**原稿 + 完整生命周期**：
  回合开始若 `生命 ≥95 且无创伤/紊乱` → 给 **1 强度 1 层**；
  抵挡时消耗 1 点强度（归零即消失）；
  若整回合没用掉 → 回合末 **层数 −1** 归零消失。为此给状态挂了 `turn_end.status_effects`
  节点（**非创伤状态没有通用层数衰减**，`auto_decay` 字段目前没有任何代码读取）。
  `a-10` 在入住时一次性给 99 强度 99 层并跳过回合末衰减，即常驻。
  顺带修 `TenantState.set_status`：原先把值交给 `Condition(...)` 构造，会先被
  `__post_init__` 的默认上限 10 夹一次，导致强度上限 >10 的状态（本状态 99）设不上去；
  现在改为 0/0 构造后再按 `status_caps` 钳制。
  顺带修掉 `value_system._restore_sanity` 里写死的 `min(100.0, …)` 上限，改用
  `tenant.max_sanity`，否则"最大理智 +20%"无法真正生效；前端血条/理智条也改为使用后端下发的
  `hp_max` / `san_max`，不再写死 100。

## 状态层数归一化（layers = 剩余回合数）

**规则一句话：`condition` 在回合末统一走公共函数 `round_effects._decay_conditions()` 做
`layers - 1`，归零即消失。**

- 任何状态都不再各自 `-1`；各自的"可能 +1"（创伤/紊乱恶化、情绪强化、休克回层）留在原地。
- 永续效果 `permanent=True`（回合末回满），自管状态 `auto_decay=False`（跳过）——都写在定义上，
  不在公共函数里写特例。
- 顺带由此产生的既有修正：`layers` 一律是"剩余回合数"（镇痛、食物余味、平静、青桃保护、
  澪叁贰玖情报/警觉、`reveal_*` 全部从"绝对回合号"改回持续回合数）；原稿「宽慰」改用已有觉醒
  情绪「满足」承载。
- **`high_health_immunity`**：自管（自己的回合末衰减 hook），标 `auto_decay=False`，避免双重衰减。

## 特例清理（普适规则就删特例）

- **状态 chip 数据驱动**：`web_ui._condition_chips` 原本写死"创伤/紊乱/休克 + 排除名单
  `{trauma,disorder,shock,*情绪}`"。现在改为遍历全部状态、情绪按 `EmotionDefinition` 类型跳过；
  图标/配色由 `StatusDefinition.chip_icon/chip_css` 声明（创伤 warn、紊乱 info、休克 danger）。
  将来任何新状态自动获得 chip，无需改这里。
- **"可直接使用"规则只写一处**：新增内容层 `items.item_is_directly_usable(id)`，`web_ui._item_entry`
  与 `cli.use_item/equip_item` 统一复用它，删掉 CLI 里那两张写死的 id 清单。
- **统计文本不再写死**：`engine.codex_lines()` 的 `/24`、"本局10个"、以及"16号为白板补位"改为
  按注册表动态计算（内容细节留给内容层）。
- **性格表不再反选**：`PERSONALITIES` 直接等于八类常规性格表，`dynamic/unknown` 作为展示专用键
  在之后追加，而不是"全部键减去两个"。

## 交互 / UI

- **发现界面（通用，不可反悔）**：一切「发现/待处理」弹窗无取消键；描述居中置顶，
  选项居中、每页最多 5，超过 5 时两侧为等边三角形翻页箭头；界面正下方居中悬浮
  「隐藏/显示」（藏起后仍可看场面）。前端在 `openDialog` 统一注入（`syncPeek`）。
  悬浮按钮复用其它按钮参数（`.btn`/`.btn.p`），底部居中、`bottom:46px`、16px。
  **选择期间**点击弹窗以外的操作 → toast「请先完成当前选择」（capture 兜底）；
  **双击选项 = 选择并确认**（`optDbl`）。守卫**只拦操作**（`button/.btn/.slot/[data-act]`），
  放行查看类点击（空气/房客卡/日志/吐司本身）。
- **厄瑞玻斯命运抽牌（三步）**：①选牌 → ②上交紫色物资或「命运之轮」定向 → ③两选项「结算/反悔」；
  `build_fate_view` 下发 `title/settle/cancel_prompt`（前端不写死）。
- **上交物资可反悔**：交紫色改定牌面的槽——把槽内物资**拖走**即取回（或再点同一物资 toggle），
  池内高亮 `.slot.sel`；**不设取回按钮**。物资只在最终结算时扣除。
- **搜索选地点**：左滚轮列表 + 右详情（`.search-layout`/`.loc-list`/`.loc-detail`，高 42vh）。
  两步弹窗同宽（`wide`），行内文本 `nowrap + ellipsis`，行高固定。

## 机制 / 数值

- **主动能力限制由内容显式声明**：`AbilityDefinition.per_turn`（默认 False）；
  引擎只在 `per_turn` 为真时才 `_mark_ability_used`，**未声明的技能就是不限次**。
  更长的冷却仍由内容 `_set_ability_cooldown` 设置。后端仅在 `per_turn` 且无 chip 时补
  `ACTIVE_USES_CHIP`；游戏内房客详情技能行会渲染 `a.chips`。
- **柳七鱼「不行，我要受不了了」**：当前实现产出 **10 份**随机物资；按目标已损失生命给时运修正
  （基础 +5，每损失 10 点 −1，最低 −5）；`_random_item` 有 `fortune` 参数
  （与搜索时运同公式 `1 + fortune*0.1*(品质+2)`）。
  **注意**：设计稿原值为 **2 份**（驱逐后屋内 ≤3 人额外 +1），10 份是当前强度崩坏的主因之一；
  暂不改，待平衡批次统一处理（见文首「平衡待办」）。
- **苯环「早交班」**：连续无休克 **5** 次 / 连续无死亡 **7** 次即解放（同步改日志、`card_info`、图鉴文本）。

## 状态如实下发（曾经的错）

- **情绪可见性**：统一走 `engine.emotion_visible(tenant, key)`（强度 >5 / `reveal_<key>` 未过期 /
  角色模块 `EMOTION_VISIBLE`）；`status_lines` 与 `web_ui` 都用它，**默认不显示情绪**。
- **情绪 chip 传参**：后端条目是 `[icon,label,extra]`，前端要 `chip(e[1],e[0],e[2])`，
  曾把 icon 当 label → 界面出现 "i-emotion" 文本。
- **信息状态**：后端按真实状态下发 `pending/confirmed/refuted/expired`
  （前端显示 待验证/已证实/已证伪/已失效），曾把非 pending 一律当 `true` → 证伪也显示已证实。
- **信息不可主动验证**：已移除前端「验证」按钮与 `verify_info` 动作。
- **普通状态下发**：如「伟大的封印」随 `statuses` 下发；能力运行态
  `disabled/used/cooldown/learned` 真实下发（封印时详情显示「已封印」并隐藏「使用」）。
- **访客顺序**：开局用 `EVENT_IDS["visitor.queue"]` 洗牌 `visitor_pool`（按种子确定），
  不再按角色注册顺序 `pop(0)`。

## 分离度加固（前端不许做机制）

- 后端算好：访客序列、羁绊档位、目标合法性（含 `tenant_condition` 的 `condition_targets`）、信息顺序。
- `web_ui` 只下发数据；羁绊档位用 `engine._bond_tier`，下发 `tier_value`/`reached`，
  颜色/档名映射留前端（纯展示）。
- 护栏：`tools/audit_separation.py` 的 `FRONTEND_FORBIDDEN_PATTERNS`
  （禁止前端 `tiers.filter` 算档位、重排 `STATE.intel`）。
- 系统层不再硬编码 `PERSONALITY_ICONS`/`PERSONALITY_TIERS`（改 `i-b-{key}` + 内容模块档位）。
- **性格划线语义**：只有 `persona_off`（=`passives_disabled`）才划线；
  羁绊等级为 0（副性格权重取整 / 外出 / 消沉）**不得划线**，只显示暗色 `p-idle`。
- 已知小尾巴：`engine.codex_lines()` 房客计数写死 `/24`；状态/情绪/全局事件需**注册函数**（非"放文件即生效"）。

## 工程事故与教训

- `ACTIVE_USES_CHIP` 导入被放进函数内部，导致 `build_state` 与**图鉴** `codex_state` 各自
  `NameError`（前者让开局动作返回空响应、后者让图鉴整页空）。教训：**导入放对作用域**，
  改完对相关入口都验证。UI 提示文件见 `docs/PRINCIPLES.md` §二。
- 早前清理误删过用户存档 `小汪的存档.json`（`Remove-Item` 不进回收站）→ 之后一律
  `WEIREN_SAVES_DIR` 隔离。

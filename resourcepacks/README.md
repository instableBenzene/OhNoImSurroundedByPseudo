# 资源包（resourcepacks/）

> 只改**外观**的包：配色 / 字体 / 贴图零件 / 素材位（封面背景、大标题）。
> 与资料包（`dlc/`）并列，**各自有序**；越靠上越优先，低者被高者覆盖。
> 资源包总在资料包之后套用，所以**能盖过资料包自带的外观**。

## 目录

```text
resourcepacks/<名字>/
  pack.json        # 可选：{"name": "...", "label": "显示名", "min_game_version": "2.1.0"}
  theme.py         # THEME = {"tokens": {...}, "css": "..."}（**只能改色调/字体**）
  symbols*.py      # SYMBOLS = {"i-xxx": "<path .../>"}（贴图零件，viewBox 24×24）
                   #   内置的 59 个零件在 base 里：weiren_game/data/resourcepack/symbols_base.py
  assets/          # 素材位文件
  *.py             # ASSETS = {"background": "background.svg", "title": "title.svg"}
```

## 能改 / 不能改

- ✅ **色调**：`--bg/--panel/--panel2/--line/--line2/--ink/--ink2/--ink3`、
  **遮罩/面板底**（`--scrim*`/`--mask*`/`--menu-scrim-*`/`--glass-*`/`--card-glass-*`/`--drop-glass`/`--pool-glass-*`）、
  **标题整套**（`--title-paper-*`/`--title-ink-*`/`--title-wash`）、**羁绊四档**（`--bronze/--silver/--gold/--gold-grad/--prism/--prism-grad`）、
  `--amber`（以及
  **`--amber-rgb`**：强调色的 rgb 分量，hover/选中态用它做透明叠加，必须与 `--amber` 同步）、
  `--amber-soft/--jade-deep`、`--ink-hi/--ink-btn/--ink-head`、`--edge`、
  `--btn-*/--pri-*/--surface-*/--launcher-*`、字体栈（`--mono/--sans/--serif/--hei/--comic/--px-font`）
- ✅ **贴图零件 `SYMBOLS`**：任意图标 id（`i-xxx`）都能覆盖/新增；内容按 id 引用它们，
  所以资源包能改**头像零件、小面板图形、以及任何由内容声明 icon id 的地方**。
  （要替换**整张**物品图标是 `item/item/<物品id>.svg`；**整张头像**是
  `avatars/characters/<角色id>.svg` —— 都走内容层，见下。）
- ✅ **素材位 `ASSETS`**：`background`（启动器封面背景；base 自带黄昏小镇那张，SVG 会**内联注入**
  所以封面的动画样式还有效）、`title`（大标题**整块**，
  含副标题那行——例如把原本的英文换成日文）。前端目前消费这两个 kind。
- ✅ **阴影/斜面是材质的一部分**：所有 `box-shadow` / `text-shadow` 都只引用**配方 token**
  （`--shadow-bevel` / `--shadow-bevel-lg` / `--shadow-press` / `--shadow-inset*` / `--shadow-panel` /
  `--shadow-bar` / `--shadow-tip` / `--shadow-float-up` / `--shadow-drawer` / `--shadow-chip` /
  `--shadow-title` / `--text-shadow-bevel`…）。配方里的颜色是**算出来的**：
  `color-mix(in srgb, var(--edge) N%, transparent)`（阴影）与 `var(--ink-hi) N%`（高光）。
  所以：改 `--edge`/`--ink-hi` → 全部阴影跟着变色；直接覆盖某条配方（例如 `--shadow-bevel:none`）
  → 立刻变成无斜面的扁平风格。
  （`color-mix()` 需要 Chrome/Edge 111+ / Safari 16.2+ / Firefox 113+。）
- ✅ **棱彩渐变也是算出来的**：`--prism-grad` 由 `--prism-1..5` 五个色标拼出，
  SVG 里的 `#prismGrad` 同样引用这 5 个色标（`stop-color="var(--prism-N)"`）—— 改色标整条渐变跟着变。
- ❌ **锁定**（含义与尺寸，不随皮肤变）：语义色 `--ok/--danger/--warn/--info`、危险红 `--danger-*`、
  难度标签 `--diff-*`、品质 `--q0..--q5`、尺寸 `--slot/--w`。写了会被忽略并在服务端打印一行提示。
- ✅ **羁绊位阶已解锁**（`--bronze/--silver/--gold/--prism/--prism-grad`）：羁绊是内容可自定义的，
  所以它的颜色也交给材质包管；羁绊/性格的**图标**同样是 base 材质里的普通零件（`i-b-*`，可覆盖）。
- 完整默认值见 `weiren_game/data/resourcepack/theme.py`；参数速查见 `docs/STYLE.md` §9。

## 现成示例

- `blood_moon/` —— 血月・和风恐怖：只覆盖色调 token（近黑底 + 血红强调），并自带
  `assets/background.svg`（和风恐怖封面：血月 / 鸟居 / 竹林 / 红灯笼 / 烛火）与
  `assets/title.svg`（血红剪字标题）。

启用方式：启动器「设置 → 资源包」里 ▶ 启用、▲▼ 调位次、点「应用」（即时生效，无需重启）。
### 人物（头像）——`avatars/`

**资源包清单里的 `base` 行**：和资料包页一样，右侧恒有一行 `base（内置材质）`，位次可调、不可卸载。
排在它上方 = 覆盖内置材质；排在它下方 = 改不动内置材质定义的东西（但自己新增的仍在）。

头像零件是**内容层文件**（一件一个文件），不再是写死的贴图：

```text
weiren_game/data/avatars/shapes/<id>.svg        # 基础形状（i-av1..）
weiren_game/data/avatars/features/<id>.svg      # 专属特征（i-ft-*）
weiren_game/data/avatars/characters/<角色id>.svg # 整张头像（直接替换这个角色的头像）
```

资料包（`dlc/<包>/avatars/...`）与资源包（`resourcepacks/<包>/avatars/...`）**同 id 覆盖**，
优先级：**base → 资料包（位次）→ 资源包（位次）**，高者赢。于是：

- 覆盖一个**零件**：把同名文件放进 `avatars/shapes/i-av5.svg` → 全屋同形状的角色一起变。
- 替换**某个角色的头像**：放 `avatars/characters/hkw.svg` → 只改这一个（人类与伪人都适用；
  连 base 层 `data/avatars/characters/` 里的 24 张立绘也能这样盖掉）。
- 内容侧还能在角色 `.py` 里声明 `AVATAR`（形状 id）/`AVATAR_FEATURE`（点缀色/点缀环已废弃）。

零件按「形状（`--ink` 上色，走蒙版）× 专属特征」组装（特征自己带色，或跟主题走）；
**与存档无关**：头像只是显示，存档里不含任何头像字段，所以资源包可随时移除。

#### 让全员都用零件（不要立绘）：`avatar_mode`

`pack.json` 里写 `"avatar_mode": "parts"`，该包生效时**跳过 base 层的立绘兜底**
（`data/avatars/characters/`），所有角色改用「形状 × 特征」组装 —— 想"整套换掉所有配件"就靠它（血月就是）。
包里自己放的 `avatars/characters/<id>.svg` 仍然优先（那是明说"这个角色就用这张整图"）。

#### 零件色槽（留给创作者）

零件文件里可以写**色槽**，颜色由内容层给（角色模块 `AVATAR_COLORS = {"a": "#c0333a", "b": "#1b1418"}`）：

```svg
<path d="M4 4h16" stroke="var(--a)"/>   <!-- a–e 缺省 = --ink / --ink / --ink2 / --ink3 / --ink3 -->
<path d="M4 9h16" stroke="var(--b)"/>   <!-- b/c/d 缺省 = --ink / --ink2 / --ink3 -->
```

没写色槽（只用默认单色）的零件继续走"蒙版 + 主题色"，跟着配色 token 变。
**base 与血月自带的零件默认都不写色槽** —— 色槽是留给创作者按角色微调的。

### 物品图标 ——`item/`

物资图标的**内容层文件**（一件一个文件），和头像零件同一套优先级与路径规则：

```text
weiren_game/data/item/item/<item_id>.svg   # 专属图标（有就用这张）
weiren_game/data/item/tag/<tag>.svg        # 按标签兜底（没有专属图标时）
```

资料包（`dlc/<包>/item/...`）与资源包（`resourcepacks/<包>/item/...`）**同 id 覆盖**，
优先级同样是 **base → 资料包（位次）→ 资源包（位次）**。于是资源包能：

- 覆盖**某个物品**：放 `item/item/flintlock.svg` → 只改这一件；
- 覆盖**某类物品**：放 `item/tag/food.svg` → 所有只带 `food` 标签、
  且没有专属图标的物品一起变（自带物品大多有专属图标，所以这条主要给 DLC 新物品兜底）；
- 资料包自带物品时也能顺手带自己的图标（`item/item/<新物品id>.svg`）。

**两色规则**（决定图标怎么上色）：SVG 里 `#d7ddd2`（或 `currentColor`）是**底色**，
其余颜色是**特征色**；运行期特征色会被换成该物品的**品质色**、底色交给主题 `--ink`
（所以同一张标签图用在蓝/紫/金物品上不会串色）。写多个特征色也没关系，它们都会被换成同一个品质色。
没有图标文件的物品自动回退内置 `i-*` 贴图零件，不会报错。**纯显示，不进存档。**

### 地点 / 信息 / 伪人图标 ——`icon/`

这三类图是**彩色插画**（不参与配色 token，用 `<img>` 渲染），同样走内容层 + 包覆盖：

```text
weiren_game/data/icon/locations/<location_id>.svg
weiren_game/data/icon/information/<template_id>.svg
weiren_game/data/icon/pseudos/<pseudo_id>.svg
```

资料包 `dlc/<包>/icon/<section>/<id>.<ext>`、资源包 `resourcepacks/<包>/icon/<section>/<id>.<ext>`
同 id 覆盖，优先级同样是 **base → 资料包（位次）→ 资源包（位次）**；支持 `.svg/.png/.jpg/.jpeg/.webp`。
注意：这些图**不会**跟着主题变色 —— 换肤只影响配色 token。

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
  assets/          # 素材位文件
  *.py             # ASSETS = {"background": "background.svg", "title": "title.svg"}
```

## 能改 / 不能改

- ✅ **色调**：`--bg/--panel/--panel2/--line/--line2/--ink/--ink2/--ink3`、`--amber`（以及
  **`--amber-rgb`**：强调色的 rgb 分量，hover/选中态用它做透明叠加，必须与 `--amber` 同步）、
  `--amber-soft/--jade-deep`、`--ink-hi/--ink-btn/--ink-head`、`--edge`、
  `--btn-*/--pri-*/--surface-*/--launcher-*`、字体栈（`--mono/--sans/--serif/--hei/--comic/--px-font`）
- ✅ **贴图零件 `SYMBOLS`**：任意图标 id（`i-xxx`）都能覆盖/新增；内容按 id 引用它们，
  所以资源包能改**头像零件、小面板图形、以及任何由内容声明 icon id 的地方**。
  （若要替换**整张**物品/角色图，那是 `assets/art/` 那套外置美术接口，另一档改动。）
- ✅ **素材位 `ASSETS`**：`background`（启动器封面背景）、`title`（大标题**整块**，
  含副标题那行——例如把原本的英文换成日文）。前端目前消费这两个 kind。
- ❌ **锁定**（含义与尺寸，不随皮肤变）：语义色 `--ok/--danger/--warn/--info`、危险红 `--danger-*`、
  难度标签 `--diff-*`、品质 `--q0..--q5`、羁绊位阶 `--bronze/--silver/--gold/--prism/--prism-grad`、
  尺寸 `--slot/--w`。写了会被忽略并在服务端打印一行提示。
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
  连 `assets/art/characters/` 里的 24 张立绘也能这样盖掉）。
- 内容侧还能在角色 `.py` 里声明 `AVATAR`（形状 id）/`AVATAR_FEATURE`/`AVATAR_ACCENT`/`AVATAR_DECOR`。

零件按「形状（`--ink` 上色，走蒙版）× 专属特征（点缀色上色）× 点缀环」组装；
**与存档无关**：头像只是显示，存档里不含任何头像字段，所以资源包可随时移除。

#### 让全员都用零件（不要立绘）：`avatar_mode`

`pack.json` 里写 `"avatar_mode": "parts"`，该包生效时**跳过立绘兜底**（`assets/art/characters/`），
所有角色改用「形状 × 特征」组装 —— 想"整套换掉所有配件"就靠它（血月就是）。
包里自己放的 `avatars/characters/<id>.svg` 仍然优先（那是明说"这个角色就用这张整图"）。

#### 零件色槽（留给创作者）

零件文件里可以写**色槽**，颜色由内容层给（角色模块 `AVATAR_COLORS = {"a": "#c0333a", "b": "#1b1418"}`）：

```svg
<path d="M4 4h16" stroke="var(--a)"/>   <!-- a 缺省 = 该角色的点缀色 -->
<path d="M4 9h16" stroke="var(--b)"/>   <!-- b/c/d 缺省 = --ink / --ink2 / --ink3 -->
```

没写色槽（只用默认单色）的零件继续走"蒙版 + 主题色"，跟着配色 token 变。
**base 与血月自带的零件默认都不写色槽** —— 色槽是留给创作者按角色微调的。

# AGENTS.md

> 给在本仓库工作的 AI / 开发者：**开工前先读本文件**；本文件是「入口 + 硬性约束 + 现状」，
> **唯一权威架构文档是 `docs/GUIDE.md`**。记忆地图见 §8。
>
> ⚠️ **开工第一步：先读 `docs/PRINCIPLES.md`（品味与手法 / 灵魂篇）**。重置后最容易一起丢掉的
> 不是机制，而是"为什么这样做才对"的判断取向 —— 它写在那一篇里。

## 0. 一句话

《完蛋，我被伪人包围了！？》的**纯 Python 标准库**实现：核心系统与内容严格分离，内置内容即
「基础内容包」（`weiren_game/data/`），可用 `dlc/` 声明式扩展，并提供本地 Web UI。

## 1. 环境与常用命令

- Python **3.10+**，仅标准库，无第三方依赖。
- 终端：`python game.py`
  `--pseudo/--difficulty/--seed/--max-turns/--disable/--save/--load/--list-content`（目标回合 **≥12**）。
- 图形（**本地 Web UI**）：`python game_ui.py` → `weiren_game/web_ui.py`，默认 `http://127.0.0.1:8730`；
  入口 `game_ui.py`；双击启动用 `启动游戏UI.vbs`（**无窗口**，走 pythonw）/ `启动游戏UI.bat`，
  排错用 `启动游戏UI(调试窗口).bat`。无窗口时输出写入 `logs/web_ui.log`。前端在 `weiren_game/webui/index.html`。
- 测试（**提交前必跑**）：`python -m unittest discover -s tests -p "test_*.py"`（**必须全绿**；刻意精简，勿再堆冗余用例。
  这里**不写用例数**——它每加一条就要同步一堆文档，而且和「文档只写规则、不复制清单」相冲）。
- 冒烟：`python tools/smoke_simulation.py --seeds 3 --log-dir <dir>`
- 分离度自检：`python tools/audit_separation.py`
- 内容校验：`python tools/validate_content.py`
- 日志文案自检：`python tools/audit_text.py`（规则见 `docs/STYLE.md` §11；有 error 退出码 1）
- 角色脚手架：`python tools/new_character.py <ascii_id> <中文名> [--carry N]`
- 浏览器对局压测：`node tools/browser_playtest.mjs url=http://127.0.0.1:8730/ games=30 turns=12 budget=420`
- 版本：`GAME_VERSION="2.1.0"`（`weiren_game/data/__init__.py`）；存档 `meta.packs` 与当前启用包不一致会拒读。

## 2. 文档地图

| 文档 | 作用 |
| --- | --- |
| `docs/GUIDE.md` | **唯一权威**：数据模型、生命周期、系统、通道+修饰器、全局事件、伪人机制、扩展 checklist；**§14 架构分层**、**§15 原稿覆盖清单**（已并入） |
| `docs/PRINCIPLES.md` | **品味与手法（灵魂篇）**：产品取向、工程手法、判断样例、用户期待 —— **先读** |
| `docs/STYLE.md` | 美术与 UI 风格；**§9 是可直接抄用的参数表**（颜色 token / 字体栈 / 按钮 / 弹窗 / chip / 槽位 / 断点 / z-index / 动效） |
| `docs/DECISIONS.md` | 近期交互/机制/状态的具体决策与踩坑记录（AGENTS.md 现状速览的展开） |
| `docs/BALANCE.md` | **平衡改动记录**：每个技能被增强/削弱过几轮的账（只记"改了什么"；为什么改在 DECISIONS） |
| `docs/ARCH.md` | **效果内核**：数值通道 × 布尔闸门（共用 path/source、分用算术/逻辑）、令牌词表、闸门目录、迁移策略 |
| `docs/ADD_CONTENT.md` | **内容创作**（合并原 CONTENT_TYPES / ADD_CHARACTER / ADD_DLC）：内容类型全景、加房客步骤、写 DLC 步骤、检查清单、已知限制 |
| `docs/COOKBOOK.md` | **创作样例集（给人读）**：需求模板 + 可抄改的最小样例（物品/技能/被动/伪人/信息/事件/DLC）与常见坑 |
| `docs/PACKAGING.md` | 免安装分发（便携 `runtime/` + VBS；可选 PyInstaller exe） |
| `docs/archive/` | **归档**（旧任务书、被替换的实现与数值快照）：**非现行参考、不要主动读**，只在追溯或回滚时看。约定见 `docs/archive/README.md` |
| `dlc/README.md` / `dlc/_template/` | 内容包（含 `codex/`）编写规范与模板 |
| `design/README.md` + `design/svc-mock.html` | **冻结的界面设计稿基准**（静态假数据，SVC 风）；参数以实现为准，见 `docs/STYLE.md` §9 |
| `../完蛋，我被伪人包围了？！/` | **设计原稿（项目外）**：`*.docx` 与 `md/*.md`（附录 A 记差异） |

> 设计文档与代码冲突时，**永远以代码为准**。

## 3. 硬性不变量（不要破坏）

1. **核心/内容分离（含 UI）**：系统层与前端不得出现具体内容 id/名称，也不得 import 具体内容模块（扫描范围以 `tools/audit_separation.py` 的 `SYSTEM_GLOBS` 为准）；需要交互/渲染内容时经通用机制（注册表全集见下方 §3）。
   **内容文案（提示语/标题/标签/选项名）同样不得写死在前端或系统里，必须由内容层随视图/状态下发。**新内容只放 `data/` 或 `dlc/`。
   **验收**：删任一内容文件（角色/性格/伪人/物品/标签）项目仍能开局；系统/前端内容名残留为 0。
   **反向**：`data/` 不得 import `weiren_game.systems`（只可用协议 `weiren_game.types.EngineProtocol`）。
2. **注册表自描述 + 自动发现**：`data/_discovery.py` 扫描目录；放/删 `.py` 即生效，无需登记。
   - 顺序（影响随机确定性，勿随意改）：`CHARACTER_MODULES` 按文件名、`CHARACTERS` 按 `source_id`、`personalities/pseudos/tags` 按文件名、`items` 按 `CATEGORY_ORDER`。
   - 可登记的东西（**完整、权威的清单是 `content.py::_BASE_CONTAINERS`**，新增注册表必须登记进去，见 §3.11）：
     - 角色/能力：`ACTIVE_DISPATCH`、`INTERACTIONS`、`PENDING_VIEW`、`TARGET_OPTIONS`、`MARKS`、`DETAIL_SLOT`、`CONTAINERS`、`PANEL`、
       `CODEX_EXTRA/SECTION/SUMMARY`、`SEARCH_REWARD`、`TURN_START`、`VALUE_HOOKS`、`NODE_HOOKS`、`HOOKS`、`ON_*`、`CAN_LOCK_PERSONALITY`、`PROTECTED_STARTER`；
     - 伪人：`DEFINITION`/`HANDLERS`、`CARD_SLOT`、`DEFAULT_PSEUDO`；
     - 物品/地点/信息/性格/标签：`ITEMS`+`ITEM_HOOKS`、`LOCATIONS`+`MAP_GROUPS`、`MAPS`、`INFORMATION_TEMPLATES`、`PERSONALITIES`、`TAG_BEHAVIORS`、`ABILITY_CHIPS`、`MODIFIERS`；
     - 外观（资源包）：`THEME`、`SYMBOLS`、`ASSETS`；头像/图标/地图是**文件**（见 §6「外观与材质」）。
3. **数值/概率走通道 + 修饰器**：`engine._apply_modifiers(...)` / `_apply_chance(...)`；实现见 `modifier_rules.py`/`probability.py`。**旧 `ModifierPool` 已删，勿复活**。
4. **概率统一**：必定 0/100；非必定收敛 **5%~95%**；`random() < p`。
5. **`path` vs `source`**：`path`=响应哪些功能；`source`=调用点事件构成；命中取交（`match="all"` 取子集）。
6. **布尔闸门 vs 数值通道**：两者**共用 `path`/`source` 匹配**（同一套注册与命中），但**分用聚合**——
   通道是算术（`flat/percent/mul/final/max/min`），闸门是逻辑（`any`=OR、`veto`=NOT）。
   **闸门是纯查询**（不掷骰、不写状态）；掷骰与消耗只发生在**结算点**。
   免疫、目标锁定、行为位压制、能否来访/搜索、回溯、扳机门控等属闸门。细则与目录见 `docs/ARCH.md`。
7. **id 分层**：静态内容 id 是 `str`；运行时实例 id 是 `int`（每类独立 `InstancePool`）。
8. **全局事件用通用键**；持续回合：下回合初兑现 ≥2 / 本回合内 1 / 长期 99 / 限时具体数。
9. **派生项用 `source` 区分**，不新增通道。
10. **声明式能力规格**：`AbilityDefinition(target/prompt/options/amount_label/amount_mark/chips/nested_option)`；前端与 CLI **一律据此渲染，禁止按能力 id 特判**。
11. **新增注册表必须登记进 `_BASE_CONTAINERS`**（`weiren_game/content.py`）：DLC 装载/卸载的热回滚以那张表为准；漏登记就会在卸载后残留、与后续内容串味（历史踩坑：目标候选、图鉴补充、状态·情绪、图鉴静态表、效果内核的修饰器·闸门表）。
    base 快照是**懒抓**的（`dlc.py` 在装载任何包之前调 `CONTENT.ensure_captured()`），**不要**挪回 `content` 模块级：效果内核的 provider 由 `systems/*` 在导入时登记，早抓会漏。

## 4. 目录速览

```text
game.py                       终端入口
game_ui.py                    Web UI 入口
weiren_game/web_ui.py         Web 后端（JSON 状态 + 动作；含 codex/DLC/存档接口）
weiren_game/webui/index.html  前端（只认状态 JSON + 动作 JSON）
weiren_game/ui.py             UI 适配层（CLI 交互）
weiren_game/text.py           风味文本标记：**加粗** / *斜体* / 换行
weiren_game/engine.py         薄引擎：回合流程与系统调度
weiren_game/systems/          核心系统（不含具体内容）
weiren_game/modifier_rules.py 通道 + path/source + 九阶段数值计算
weiren_game/probability.py    概率收敛
weiren_game/content.py        ContentManager（注册表边界 / 热切换快照）
weiren_game/data/             基础内容包：characters/items/locations/information/
                              personalities/pseudos/tags + avatars/（头像零件）+ item/（物品图标）
                              + icon/{locations,information,pseudos}/（地点·信息·伪人图标）
                              + maps/<地图id>/map.py（地图/区域包：显式地点名单 + 屋子名）
weiren_game/data/resourcepack/ 资源包（默认材质）：theme.py（CSS 变量/字体/标题纸墨色）
                              + symbols_base.py（59 个内置贴图零件）+ cover.py（封面素材位 + 封面动画样式）
weiren_game/data/codex_pack.py       图鉴包（羁绊档位/伪人技能/地点图标与文案/关联）
weiren_game/data/codex_mechanics.py  图鉴「机制」教程正文（通用规则，与代码一致）
weiren_game/data/labels.py           内容展示标签（分类/tag/品质段位/组图标 + EQUIP_TAGS）
weiren_game/data/information_text.py 信息图鉴完整描述（自设计稿）
weiren_game/data/items/codex_text.py 物资图鉴完整文本（自设计稿）
weiren_game/config.py / dlc.py / models.py / lifecycle.py / cli.py
weiren_game/resourcepack_loader.py  独立资源包装载（resourcepacks/，外观层）
weiren_game/asset_layers.py         内容层资产的装载顺序（base → 资料包 → 资源包）
weiren_game/item_icons.py           物品图标（data/item/{item,tag}，两色渲染 + 标签兜底）
weiren_game/icon_files.py           地点/信息/伪人图标（data/icon/<section>，彩色插画，包可覆盖）
docs/*.md                     GUIDE/PRINCIPLES/STYLE/ADD_CONTENT/DECISIONS/PACKAGING（archive/ 为归档）
dlc/                          外部内容包 + _template（含 codex/）
resourcepacks/                独立资源包（只改外观：色调/字体/贴图/素材位），与 dlc/ 并列、各自有序
tests/                        单元 / 回归测试（命令与约束见 §1）
tools/smoke_simulation.py     批量对局冒烟
tools/audit_separation.py     分离度自检（系统/前端无内容泄漏；data 不依赖 systems）
tools/browser_playtest.mjs    浏览器对局压测（CDP 驱动）
tools/validate_content.py     内容校验（编号/头像/性格/技能派发/引用完整性）
tools/audit_text.py           日志文案自检（句式/长度/标点/标记；规则见 docs/STYLE.md §11）
tools/dump_effects.py         效果注册表 dump（只读；核对 docs/ARCH.md 的闸门/数值目录）
tools/new_character.py        房客脚手架（自动分配 source_id 与 AVATAR）
tools/prepare_portable.py     准备便携运行时（embeddable Python → runtime/）
tools/extract_source_catalog.py / summarize_source_catalog.py
runtime/                       便携 Python 运行时（免安装用；非源码）
```

## 5. 工作流

0. **先读 `docs/PRINCIPLES.md`**（品味与手法）；改前再读 `docs/GUIDE.md` 对应小节；不确定以**代码实际行为**为准。
1. 加内容优先复用现有节点/通道/修饰器，目标是**零改核心系统**。
2. 按 PRINCIPLES 的工程手法：**先复现 → 找根因 → 在正确的层修**；机制用**后端既有方法**（别把前端算法抄进后端）；前端只做展示。
3. 改后跑：`compileall` → 单测 → `validate_content` → `audit_separation` → `audit_text`（动了文案才跑）；前端另做 `node --check` 与无头浏览器实测；发布前 `browser_playtest`。**起服务看 traceback**，别凭猜。
4. 若行为与设计稿不符，更新 `../完蛋，我被伪人包围了？！/md/` 的「附录 A」。
5. **"为什么这么改"记进 `docs/DECISIONS.md`**，别堆进本文件；**动了平衡**（某个技能/数值的强度变化）先照格式记一条进 `docs/BALANCE.md`，再改代码。

## 6. 当前状态（交接）

> 只写"**现在是什么样**"。为什么这么改、当时踩了什么坑 → `docs/DECISIONS.md`。
> 外观/材质那一摊的完整说明在 `.opencode/skills/weiren-frontend/SKILL.md`。

**架构与内容**

- 核心无内容引用；DLC 可热切换；三伪人可玩；测试全绿（刻意精简，见 §1）。
- **自定义 UI（内容自有的专属界面）**：内容可声明专属状态容器 `CONTAINERS = {"<key>": <类>}`（进存档、随包回滚）
  与专属面板 `PANEL = (build_view, resolve_action)`（核心只"下发视图 + 转发动作"）。
  第一个真实调用者是花尔维纳的「田」（`data/characters/flowey.py`）。面板**不参与回合流程**，
  开合由前端记；格子条目词表与 `DETAIL_SLOT` 同一套。
- 全部内置内容**自动发现**（放/删文件即生效），已逐个删除验证（角色 24 / 性格 8 / 伪人 3 / 物品分类 7 / 标签 3）。
- **DLC 可投放**：角色、性格（`LABEL`）、状态·情绪（`statuses/`）、物品与分类、tag（`tags/*.json` + `*.py`）、
  地点与开局分组（`LOCATIONS` + `MAP_GROUPS`）、**地图**（`maps/<id>/map.py`）、信息模板、伪人、图鉴分节，
  以及外观（`resourcepack/`、`avatars/`、`item/`、`icon/`）。**全局事件**仍需 `register(ctx)`／模块导入时注册。
  装载 → 卸载**完整回滚**（§3.11）。
- **地图（区域包）**：`MapDefinition(id, name, shelter, locations, draw_count)`；默认地图 id 是 `base`
  （显示名 **城郊小镇**，屋子叫 **城郊小屋**）。`locations` 是**显式名单** —— DLC 自带的地点默认不进图，
  要 `ctx.register_map_location(map_id, location_id)` 或自带一张 `maps/<id>/map.py`。开局按本图名单 +
  分组权重抽 `draw_count` 个；地图记在存档 `meta.map_id`（老存档缺字段 → 回落默认图），创建对局页有「地图」下拉。
- **内容包优先级**：资料包页右侧是**有序**清单（上 = 高，含 `base`），▲▼ 调序、「应用」即时生效；
  移到 `base` 之上就是**替换内置内容**。顺序存 `game_config.json::pack_order`。

**界面**（`weiren_game/webui/index.html`，只消费状态 JSON + 动作 JSON）

- 启动器（MC 风、哈希路由、报纸剪字标题）、游戏内顶栏、吐司、图鉴（7 分页 + 搜索/品质标签筛选/排序）。
- 对局界面「席位 / 仓库」左右分栏（仓库 6 格、席位 3 列）；选中房客展开置顶；**背包**是仓库下方贴底悬浮窗，
  **外出搜索**是右栏贴底悬浮窗，**羁绊概况**是不阻塞点击的悬浮窗；信息条目标注来源/类型并可隐藏已失效；
  可视日志随对局重置、导出在存档页（`GET /api/export`）；达标的房客头像右上角出「驱逐」。
- **选择页统一卡片语言**：技能目标/效果/数量、指派搜索的房客与地点（房客卡带头像 + 生命理智条，
  数量用步进 + 滑杆，地点详情把掉落与机制分行）。
- **「发现」= 无背景板浮层**：只把场面调暗；卡片一行从左往右、**总宽固定**、间距随张数收紧、
  多于一页才出箭头（端点置灰不隐藏）；支持隐藏 / 分页 / 双击。
- **游戏内 Esc = MC 风「桌面」**：长条「退出游戏」/ 并排「设置」「图鉴」/「返回游戏」。
  开局「发现」还没选完就退出 → `POST /api/abort_start` 丢掉这场没真正开始的局（等价回退到发现之前）。
- **设置**：启动器「设置」是菜单（显示设置 / 难度 / 图鉴 / 资料包 / 资源包）；`CONFIG.show_full_skills`
  控制房客详情页是否直接展开完整技能；启动器内 Esc 逐级外退。
- **退出游戏**：`POST /api/quit` = 先落盘 → 停服 → 确保进程退出（等价 `停止游戏UI.bat`，但多了落盘、更安全）。

**外观与材质**（三层，低 → 高：base → 资料包 → 独立资源包）

- **base** 住在 `data/resourcepack/`：`theme.py`（配色 token / 字体栈 / 标题纸墨 / 遮罩 / 阴影配方）、
  `symbols_base.py`（59 个贴图零件）、`cover.py` + `assets/background.svg`（封面素材位与封面动画）。
  资料包写 `resourcepack/`、独立资源包写 `resourcepacks/<包>/`，**同名覆盖**；
  `CONFIG.resourcepack_order` 恒含 `base` 行且**位次可调**（排在 base 下方就改不动内置材质）。
  前端 `:root` 保留一份**同值兜底**（有单测钉住逐一相同），`GET /api/resourcepack` 在首帧前注入 `:root` 与 `<defs>`。
- **锁定 token**（现状以 `LOCKED_TOKENS` 为准）：语义提示色 / 品质色 / 尺寸（`--slot`/`--w`）；
  **羁绊位阶已解锁**，遮罩、阴影配方、标题纸墨、棱彩五色标都可改。
  判断与手法（归一化 + 一维差异、命名空间代替清单）见 `docs/PRINCIPLES.md` §11/§12。
- **前端零写死色值**：CSS 里要么引用 token、要么 `color-mix()` 从 `--edge`/`--ink-hi` 算、要么
  `rgba(var(--x-rgb),α)`；所有阴影都只引用 `--shadow-*` 配方 token（所以改 `--shadow-bevel:none` 就是扁平 UI）。
- **头像**：`data/avatars/{shapes,features,characters}/<id>.svg` **一件一个文件**，包可同名覆盖；
  `characters/<角色id>.svg` 是"整张头像"，直接替换该角色（人/伪人都适用）；
  包声明 `pack.json::avatar_mode="parts"` 时 **base 层立绘让位**、全员改用零件组装（包自己放的整图仍优先）。
  **前端画头像只能走 `avatarIcon()`**。零件可声明色槽 `var(--a…)`（创作者填色），否则走"蒙版 + 主题色"。
- **物品图标**：`data/item/item/<id>.svg` 专属、`data/item/tag/<tag>.svg` 按标签兜底；
  底色 → 主题 `--ink`、其余颜色 → 该物品的**品质色**（后端内联下发，尺寸走 `.art-inline`）。
- **地点/信息/伪人图标**：`data/icon/<section>/<id>.<ext>`（彩色插画，走 `GET /api/icon/...`）；
  地点图是"白底 + 档位特征色"的**定制**插画，`LocationDefinition.tier` 只影响配色（界面不再写档位文字）。
- **图鉴缓存**：`GET /api/codex` 是一次性取的（含按当前包解析好的图标标记），
  **装/卸资料包或换资源包后必须 `CODEX=null`**，否则新内容与新图标看不到。

**机制与界面契约**

- **声明式能力**：目标选择（房客/情报/资源/数量/状态/提交物资）与限定 chip 全由内容声明，
  前端与 CLI **一律据此渲染**，禁止按能力 id 特判。
- **待处理 / 提交交互**：`PENDING_VIEWS` 支持多步与 `submit`（厄瑞玻斯：选牌 → 交紫色物资或命运之轮定向 → 结算/反悔）。
- **全局事件**：世界级"条件"（`GlobalEventDefinition` + 实例，含 `value`/剩余回合）；右栏「现有信息」标题可点，
  与「全局事件」页来回切换；**情绪显现也是事件**（`emotion.reveal.<情绪>`），不再挂在房客身上。
- **堆叠（模型 B）**：按 `stack_size` 合并；`obtain_range` 默认 `stack_size/4 ± 1`；消耗走 `Inventory.consume`。
- **已知差异（以代码为准，非 bug）**：难度 `a-10~a0~a10`（共 21 级）；《星云传说》回合末理智 = 最终固定加算 −10；
  智能手机消沉 −50%；燧发枪消耗弹药 95%。

## 7. 已知坑

- 设计原稿在**项目文件夹之外**（`../完蛋，我被伪人包围了？！/`）。
- `discern` 不是独立命令，只是「意图感知」等交互里的选项（现在也是内容声明的 `options`）。
- `logs/`、`__pycache__`、`runtime/`、`saves/` 是运行期目录，不是源码。
  （外置美术目录 `assets/art/` 已删干净：立绘/图标/物品图全部住内容层 `weiren_game/data/`。）
- **严禁批量删除 `saves/` 下的用户存档**：脚本/测试一律设环境变量 `WEIREN_SAVES_DIR` 到临时目录
  （`weiren_game/paths.py::saves_dir()` 已支持），只清理自己产生的文件。
- 改动 `weiren_game/systems/` 时务必检查内容耦合（不变量 1）。
- **改完必须复核**（本项目最容易翻车的三件事）：
  ① 批量替换**一律用脚本做条件替换并 `assert` 命中数**（`str.replace` 找不到会静默"成功"；中文锚点尽量少用）；
  ② `apply_patch` 改完 **grep 复核**（相对路径/空白易错）；③ 前端改动 **`node --check` + 无头浏览器/CDP 实操双验证**
  （`ERR_EMPTY_RESPONSE` 多半是后端未捕获异常 —— 去读服务端 traceback，别猜）。
- **JS `>>` 会按有符号 32 位溢出**：哈希取模用 `>>>`。
- **全局点击守卫要记得放行新菜单**：`hasPending()` 为真时会吞掉除 `#dialog/#pendingBtn/#toastWrap` 外的**所有**点击；
  新加的菜单/浮层必须加进放行名单，否则待选时按钮全点不动；它在**启动器里必须直接返回 false**。
- **头像只能走 `avatarIcon()`**：形状/特征的 `<symbol>` 已搬去内容层，前端 `ic("i-av*")` / `ic("i-ft-*")` 一律**空白**。
- **`.qN svg{color:var(--qN)}` 会盖掉内联图标的底色**：物品图标把 `color:var(--ink)` 写在 `<svg>` 的**行内 style** 上，别删。
- **导入作用域**：`ACTIVE_USES_CHIP` 曾误放进函数内 → `build_state` 与 `codex_state` 双双 `NameError`；改完要对**所有使用入口**验证。
- 前端文本统一走 `mdText()/fmt()`（`·`/换行、`*斜体*`、对话 `“…”` 换行、`【】` 内 tag 才解析为悬浮）。
- 测试用 `tests/_baseline.py` 钉住基准，避免受玩家 `game_config.json` 影响。
- 创建/设置的"目标回合数"下限为 **12**（与后端一致）。

## 8. 记忆地图（skill / agent / 文档 / 自检）

> 面向"以后再加角色 / 写 DLC"的固化经验。**新会话请先读这里。**

- **Skill**（按任务选）：
  - `.opencode/skills/weiren-dev/SKILL.md` —— 通用开工入口（两条分离、声明式规格、验证、坑、风格）。
  - `.opencode/skills/weiren-new-character/SKILL.md` —— 新增房客（用脚手架 + 校验）。
  - `.opencode/skills/weiren-new-item/SKILL.md` —— 新增物资（`I(...)` 字段 / tag / `on_use` / hook / 图鉴与贴图）。
  - `.opencode/skills/weiren-new-pseudo/SKILL.md` —— 新增伪人（`DEFINITION` / `HANDLERS` / 印记 / 图鉴技能）。
  - `.opencode/skills/weiren-new-information/SKILL.md` —— 新增信息模板与全局事件（kind / 占位符 / 地点修正 / 事件键）。
  - `.opencode/skills/weiren-new-dlc/SKILL.md` —— 编写 DLC 内容包（含 `codex/`）。
  - `.opencode/skills/weiren-release/SKILL.md` —— 发布前自检（审计 + 单测 + 冒烟 + 压测 + 人工抽查）。
  - `.opencode/skills/weiren-frontend/SKILL.md` —— **前端与材质**（三层材质、token/素材位/图标/头像/阴影、验证手法）。
  - 各"新增内容"skill 都带**需求描述清单**（要提供哪些字段/数值/文案）与**真实内容拆解**
    （如 `weiren-new-character` 拆呼朋引伴、`weiren-new-item` 拆麦当当、`weiren-new-pseudo` 拆展示三件套、
    `weiren-new-information` 拆 `good_talk` / 地点修正 / 全局事件）；通用模板见
    `docs/ADD_CONTENT.md`「内容需求描述模板」，效果字段以 `docs/ARCH.md` 为准。
- **Agent**：`.opencode/agent/weiren-steward.md`（架构守门人 + 内容作者）。
- **Config**：`.opencode/opencode.json` 把 `docs/PRINCIPLES.md`、`AGENTS.md`、`docs/STYLE.md` 作为常驻 instructions。
- **必读顺序**：`docs/PRINCIPLES.md`（灵魂篇）→ `AGENTS.md` → `docs/GUIDE.md` + `docs/STYLE.md` → 按需 `docs/ADD_CONTENT.md`。
- **决策记录 / 归档**：`docs/DECISIONS.md`（**为什么这么改 + 踩坑**）；`docs/archive/QA_TASK.md`（旧任务书）。文档地图见 §2。
- **内容全景 / 样例 / 美术**：`docs/ADD_CONTENT.md`（base vs DLC 全类型）、`docs/COOKBOOK.md`
  （给人读的样例集：照着改就能用）。
- **自检/压测/脚手架/分发**：`tools/audit_separation.py`、`tools/audit_text.py`（日志文案，规则见 `docs/STYLE.md` §11）、`tools/validate_content.py`、`tools/dump_effects.py`（核对 `docs/ARCH.md` 的闸门目录）、`tools/new_character.py`、`tools/browser_playtest.mjs`、`tools/smoke_simulation.py`、`tools/prepare_portable.py`、`docs/PACKAGING.md`。

**每次改完的固定动作**：
```
python -m compileall -q weiren_game
python -m unittest discover -s tests -p "test_*.py"
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
python tools/audit_separation.py
python tools/audit_text.py
```

> 修改 `.opencode/` 下的 skill/agent/config 后，**需重启 opencode** 才会加载。

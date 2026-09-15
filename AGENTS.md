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
- 测试（**提交前必跑**）：`python -m unittest discover -s tests -p "test_*.py"`（当前 **52 全绿 / 10 模块**；刻意精简，勿再堆冗余用例）。
- 冒烟：`python tools/smoke_simulation.py --seeds 3 --log-dir <dir>`
- 分离度自检：`python tools/audit_separation.py`
- 内容校验：`python tools/validate_content.py`
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
| `docs/ARCH.md` | **效果内核**：数值通道 × 布尔闸门（共用 path/source、分用算术/逻辑）、令牌词表、闸门目录、迁移策略 |
| `docs/ADD_CONTENT.md` | **内容创作**（合并原 CONTENT_TYPES / ADD_CHARACTER / ADD_DLC）：内容类型全景、加房客步骤、写 DLC 步骤、检查清单、已知限制 |
| `docs/COOKBOOK.md` | **创作样例集（给人读）**：需求模板 + 可抄改的最小样例（物品/技能/被动/伪人/信息/事件/DLC）与常见坑 |
| `docs/PACKAGING.md` | 免安装分发（便携 `runtime/` + VBS；可选 PyInstaller exe） |
| `docs/archive/QA_TASK.md` | 归档：早期"系统性 QA + 视觉升级"任务书（给 Agent）；**非现行参考**，只在追溯时看 |
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
   - 注册表：`INTERACTIONS`、`PENDING_VIEW`、`TARGET_OPTIONS`、`CODEX_EXTRA/SECTION/SUMMARY`、`ABILITY_CHIPS`、`MODIFIERS`、`HOOKS`、`NODE_HOOKS`、`MARKS`、`VALUE_HOOKS`、`ON_*`、`CAN_LOCK_PERSONALITY`、`AVATAR`、`ACTIVE_DISPATCH`、`DEFAULT_PSEUDO`、`PROTECTED_STARTER`。
   - 注册表：`INTERACTIONS`、`PENDING_VIEW`、`TARGET_OPTIONS`、`CODEX_EXTRA/SECTION/SUMMARY`、`ABILITY_CHIPS`、`MODIFIERS`、`HOOKS`、`NODE_HOOKS`、`MARKS`、`DETAIL_SLOT`、`VALUE_HOOKS`、`ON_*`、`CAN_LOCK_PERSONALITY`、`AVATAR`（+ 可选的 `AVATAR_FEATURE/ACCENT/DECOR`）、`ACTIVE_DISPATCH`、`DEFAULT_PSEUDO`、`PROTECTED_STARTER`；伪人另有 `CARD_SLOT`；资源包用 `THEME`/`SYMBOLS`（`data/resourcepack/`）。
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
11. **新增注册表必须登记进 `_BASE_CONTAINERS`**（`weiren_game/content.py`）：DLC 装载/卸载的热回滚以那张表为准；漏登记就会在卸载后残留、与后续内容串味（历史踩坑：目标候选、图鉴补充、状态·情绪、图鉴静态表）。

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
                              personalities/pseudos/tags + types.py
weiren_game/data/resourcepack/ 资源包（默认材质）：theme.py（CSS 变量/字体）+ symbols_*.py（贴图零件）
weiren_game/data/codex_pack.py       图鉴包（羁绊档位/伪人技能/地点图标与文案/关联）
weiren_game/data/codex_mechanics.py  图鉴「机制」教程正文（通用规则，与代码一致）
weiren_game/data/labels.py           内容展示标签（分类/tag/品质段位/组图标 + EQUIP_TAGS）
weiren_game/data/information_text.py 信息图鉴完整描述（自设计稿）
weiren_game/data/items/codex_text.py 物资图鉴完整文本（自设计稿）
weiren_game/config.py / dlc.py / models.py / lifecycle.py / cli.py
weiren_game/resourcepack_loader.py  独立资源包装载（resourcepacks/，外观层）
docs/*.md                     GUIDE/PRINCIPLES/STYLE/ADD_CONTENT/DECISIONS/PACKAGING（archive/ 为归档）
dlc/                          外部内容包 + _template（含 codex/）
resourcepacks/                独立资源包（只改外观：色调/字体/贴图/素材位），与 dlc/ 并列、各自有序
tests/                        10 个模块 / 52 项（刻意精简）
tools/smoke_simulation.py     批量对局冒烟
tools/audit_separation.py     分离度自检（系统/前端无内容泄漏；data 不依赖 systems）
tools/browser_playtest.mjs    浏览器对局压测（CDP 驱动）
tools/validate_content.py     内容校验（编号/头像/性格/技能派发/引用完整性）
tools/dump_effects.py         效果注册表 dump（只读；核对 docs/ARCH.md 的闸门/数值目录）
tools/new_character.py        房客脚手架（自动分配 source_id 与 AVATAR）
tools/prepare_portable.py     准备便携运行时（embeddable Python → runtime/）
tools/extract_source_catalog.py / summarize_source_catalog.py
assets/art/                    外置美术资源（manifest.json + 图片；不改代码）
runtime/                       便携 Python 运行时（免安装用；非源码）
```

## 5. 工作流

0. **先读 `docs/PRINCIPLES.md`**（品味与手法）；改前再读 `docs/GUIDE.md` 对应小节；不确定以**代码实际行为**为准。
1. 加内容优先复用现有节点/通道/修饰器，目标是**零改核心系统**。
2. 按 PRINCIPLES 的工程手法：**先复现 → 找根因 → 在正确的层修**；机制用**后端既有方法**（别把前端算法抄进后端）；前端只做展示。
3. 改后跑：`compileall` → 单测 → `validate_content` → `audit_separation`；前端另做 `node --check` 与无头浏览器实测；发布前 `browser_playtest`。**起服务看 traceback**，别凭猜。
4. 若行为与设计稿不符，更新 `../完蛋，我被伪人包围了？！/md/` 的「附录 A」。
5. **"为什么这么改"记进 `docs/DECISIONS.md`**，别堆进本文件。

## 6. 当前状态（交接）

- 架构：核心无内容引用、DLC 可热切换、三伪人可玩；测试 **52 全绿**。
- 内容可插拔：全部内置内容**自动发现**；已逐个删除验证（角色 24 / 性格 8 / 伪人 3 / 物品分类 7 / 标签 3）均不破坏开局。
  **DLC 可投放**：角色、性格（`personalities/`，带 `LABEL`）、状态·情绪（`statuses/`）、物品与分类、
  tag 条目与行为（`tags/*.json` + `tags/*.py`）、地点与开局分组（`LOCATIONS` + `MAP_GROUPS`）、信息模板、
  伪人、图鉴分节；全局事件仍需在 `register(ctx)`／模块导入时注册。装载→卸载可完整回滚（见 §3.11）。
- **图鉴**：7 个分页（房客/物资/地点/信息/伪人/羁绊/机制，+DLC 追加分节）；内容层 `codex_pack.py`、`codex_mechanics.py`（机制教程正文）、`labels.py`、`information_text.py`、`items/codex_text.py` 提供完整文案与图标；支持搜索、品质/标签筛选、排序；羁绊页图标按档位 1.4s 循环预览。
- **声明式能力**：目标选择（房客/情报/资源/数量/状态/提交物资）与限定 chip 由内容声明，前端/CLI 通用渲染。
- **待处理 / 提交交互**：`PENDING_VIEWS` 支持多步与 `submit`（厄瑞玻斯：选牌 → 交紫色物资或命运之轮定向 → 结算/反悔）；提示与选项文案由内容下发。
- **全局事件**：世界级"条件"（`GlobalEventDefinition` + 实例，含 `value`/剩余回合）；右栏「现有信息」标题可点，与「全局事件」页来回切换；事件行 = 图标 + 名称 + 剩余回合（≥99 显示「长期」），点开看内容（`description` 来自内容层）。**情绪显现也是事件**（`emotion.reveal.<情绪>`），不再挂在房客身上。
- **堆叠（模型 B）**：按 `stack_size` 合并；`obtain_range` 默认 `stack_size/4 ± 1`；消耗走 `Inventory.consume`。
- Web UI：启动器（MC 风、哈希路由、报纸剪字标题）、游戏内顶栏、吐司提示、图鉴筛选、搜索两栏、发现界面（隐藏/分页/双击）；对局界面为「席位/仓库」左右分栏（仓库 6 格、席位 3 列），选中房客展开置顶、**背包为仓库下方贴底悬浮窗**；**外出搜索为右栏贴底悬浮窗**（三角收起/展开）；**羁绊概况为不阻塞点击的悬浮窗**；信息条目标注来源/类型并可隐藏已失效；可视日志随对局重置，导出在存档页（`GET /api/export`）；达标（1 条已证实 / 3 条待验证指认）的房客**头像右上角出「驱逐」按钮**，弹「否 / 是」确认后指认，判定与风险由后端 `accusation_evidence` 下发。
- **设置**：启动器「设置」是菜单（显示设置/难度/图鉴）；显示设置里可切换「房客卡详情页显示完整技能」（`CONFIG.show_full_skills`，关=一行+悬浮 1s 看效果）；启动器内 Esc 逐级外退、不弹退出对局。
- **内容包优先级**：DLC 页右侧是**有序**启用清单（上 = 优先级高，含 `base`），选中后用 ▲▼ 调序、`应用` 即时生效；高位包覆盖低位包的同 id 内容，把包移到 `base` 之上即可**替换内置内容**。顺序持久化在 `game_config.json::pack_order`（缺省 = `["base", ...enabled_dlc]`）。
- **资源包（色调/字体/贴图）**：**配色**token、字体栈与 SVG 贴图零件由内容层 `data/resourcepack/` 提供（默认材质），前端启动时经 `GET /api/resourcepack` 取回并注入 `<defs>`/`:root`；DLC 的 `resourcepack/` 同名覆盖。**只能改色调**——语义色、品质色、羁绊位阶与尺寸（`--slot`/`--w`）由 `LOCKED_TOKENS` 锁死；前端 `:root` 自带同值默认材质兜底（有单测钉住一致），资源包缺失时观感不变。
- **头像（人物零件）**：`data/avatars/{shapes,features,characters}/<id>.svg` **一件一个文件**；资料包/资源包可带同名 `avatars/` 覆盖，优先级 **base → 资料包（位次）→ 资源包（位次）**（`weiren_game/avatars.py` 现算索引）。整张头像（`characters/<角色id>.svg`）直接替换该角色头像，人/伪人都适用；`assets/art/characters/` 的 24 张立绘是**最低优先级**来源，包可声明 `pack.json::avatar_mode="parts"` 让它让位、全员改用零件组装（血月）。零件按「形状 × 特征 × 点缀环」组装：声明过颜色（`var(--a…)` 色槽或写死颜色）的零件由后端替换颜色后**内联**，只用 `currentColor` 的走**蒙版 + 主题色**；可被 `AVATAR/AVATAR_FEATURE/AVATAR_ACCENT/AVATAR_DECOR/AVATAR_COLORS` 声明覆盖，缺省按 id 哈希（顺序表在后端）。**纯显示、不进存档**。
- **物资图标 = 底色 + 品质色**：`itemIcon()` 把外置图当蒙版（底色），颜色由所在 `.qN` 给（`--q0..--q5` 锁定）；彩色插画（地点/信息/角色）仍走 `<img>`。
- **资源包（色调/字体/贴图/头像零件/素材位）**：`data/resourcepack/` 是默认材质；另有**独立一层** `resourcepacks/<name>/`（`pack.json` + `theme.py`/`symbols*.py`/`avatars/*`/`assets/*`，见 `weiren_game/resourcepack_loader.py`），与资料包并列、**各自有序**（`CONFIG.resourcepack_order`，**恒含 `base` 行且位次可调**：排它上方覆盖内置材质，排它下方改不动内置材质），高者覆盖低者，且总在资料包之后套用。设置菜单：**资料包 / 资源包**两个子页；界面文案统称 **资料包**（代码标识仍是 `dlc`）。资源包可改**色调/字体/贴图零件/头像零件/素材位**（`ASSETS`：`background` 封面、`title` 大标题）；**语义色、品质色、羁绊位阶、尺寸锁定**（`LOCKED_TOKENS`）。
- **退出游戏**：主页「退出游戏」→ `POST /api/quit`：**先落盘 → 停服 → 确保进程退出**（与 `停止游戏UI.bat` 的强杀等效且更安全）；旧进程没有该接口时仍用 bat 兜底。
- **已知差异（以代码为准，非 bug）**：难度 `a-10~a0~a10`（共 21 级）；《星云传说》回合末理智 = 最终固定加算 −10；智能手机消沉 −50%；燧发枪消耗弹药 95%。
- **交互 / 机制 / 状态的具体决策与踩坑 → `docs/DECISIONS.md`**（状态如实下发、前端不许做机制、性格划线语义、`per_turn` 限制、情绪可见性、访客顺序等）。

## 7. 已知坑

- 设计原稿在**项目文件夹之外**（`../完蛋，我被伪人包围了？！/`）。
- `discern` 不是独立命令，只是「意图感知」等交互里的选项（现在也是内容声明的 `options`）。
- `logs/`、`__pycache__`、`runtime/`、`saves/`、`assets/art/` 是运行期/资源目录，不是源码。
- **严禁批量删除 `saves/` 下的用户存档**：脚本/测试一律设环境变量 `WEIREN_SAVES_DIR` 到临时目录
  （`weiren_game/paths.py::saves_dir()` 已支持），只清理自己产生的文件。
- 改动 `weiren_game/systems/` 时务必检查内容耦合（不变量 1）。
- **本环境 `apply_patch` 相对路径易错**：改完必须 grep 复核；批量改动用脚本做条件替换后统一写盘。
- **JS `>>` 会按有符号 32 位溢出**：哈希取模用 `>>>`。
- **导入作用域**：`ACTIVE_USES_CHIP` 曾误放进函数内 → `build_state` 与图鉴 `codex_state` 双双 `NameError`（前者开局返回空响应、后者图鉴整页空）。改完要对**所有使用入口**验证。
- **脚本化替换必须 `assert` 替换次数**：`str.replace` 找不到会静默"成功"；中文锚点尽量少用。
- **前端改动双验证**：`node --check`（抽出 `<script>` 再校验）+ 无头浏览器/CDP 实操；`ERR_EMPTY_RESPONSE` 多为后端未捕获异常，去读服务端 traceback。
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
  - 各"新增内容"skill 都带**需求描述清单**（要提供哪些字段/数值/文案）与**真实内容拆解**
    （如 `weiren-new-character` 拆呼朋引伴、`weiren-new-item` 拆麦当当、`weiren-new-pseudo` 拆展示三件套、
    `weiren-new-information` 拆 `good_talk` / 地点修正 / 全局事件）；通用模板见
    `docs/ADD_CONTENT.md`「内容需求描述模板」，效果字段以 `docs/ARCH.md` 为准。
- **Agent**：`.opencode/agent/weiren-steward.md`（架构守门人 + 内容作者）。
- **Config**：`.opencode/opencode.json` 把 `docs/PRINCIPLES.md`、`AGENTS.md`、`docs/STYLE.md` 作为常驻 instructions。
- **必读顺序**：`docs/PRINCIPLES.md`（灵魂篇）→ `AGENTS.md` → `docs/GUIDE.md` + `docs/STYLE.md` → 按需 `docs/ADD_CONTENT.md`。
- **文档**：`docs/PRINCIPLES.md`、`AGENTS.md`、`docs/STYLE.md`、`docs/GUIDE.md`（含 §14 架构 / §15 原稿覆盖）、`docs/ARCH.md`（效果内核：通道 × 闸门）、`docs/ADD_CONTENT.md`、`docs/DECISIONS.md`、`docs/PACKAGING.md`。
- **决策记录 / 归档**：`docs/DECISIONS.md`（交互/机制/状态的具体修正）；`docs/archive/QA_TASK.md`（旧任务书）。
- **内容全景 / 样例 / 美术**：`docs/ADD_CONTENT.md`（base vs DLC 全类型）、`docs/COOKBOOK.md`
  （给人读的样例集：照着改就能用）、`assets/art/README.md`（外置美术接口）。
- **自检/压测/脚手架/分发**：`tools/audit_separation.py`、`tools/validate_content.py`、`tools/dump_effects.py`（核对 `docs/ARCH.md` 的闸门目录）、`tools/new_character.py`、`tools/browser_playtest.mjs`、`tools/smoke_simulation.py`、`tools/prepare_portable.py`、`docs/PACKAGING.md`。

**每次改完的固定动作**：
```
python -m compileall -q weiren_game
python -m unittest discover -s tests -p "test_*.py"
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
python tools/audit_separation.py
```

> 修改 `.opencode/` 下的 skill/agent/config 后，**需重启 opencode** 才会加载。

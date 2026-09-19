---
name: weiren-dev
description: Use when working in the OhNoImSurroundedByPseudo repository ("完蛋，我被伪人包围了！？") — adding or editing characters / items / pseudos / locations / information / bonds, writing or loading DLC packs, touching the web UI or codex, refactoring, or preparing a release. Covers data/system separation, frontend/backend separation, pluggable content, verification, audits, and the project art style.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# weiren-dev —— 本仓库开发规范

纯 Python 标准库的生存策略游戏（核心 + 基础内容包 + DLC + 本地 Web UI）。
本 skill 是"开工入口"；**细节以 `docs/GUIDE.md` 为准**，风格见 `docs/STYLE.md`。

## 0. 必读顺序
0. **`docs/PRINCIPLES.md`（品味与手法 / 灵魂篇）—— 最重要，先读**：产品取向、工程手法、判断样例、用户期待。
1. `AGENTS.md`（入口 + 硬性约束 + 现状 + 记忆地图）
2. `docs/GUIDE.md`（**唯一权威**：数据模型/生命周期/系统；§14 分层、§15 原稿覆盖）
3. `docs/ARCH.md`（**效果内核**：数值通道 × 布尔闸门；令牌词表、闸门目录、迁移策略）
4. `docs/STYLE.md`（美术与 UI 风格 + §9 参数表）
5. 加内容：`docs/ADD_CONTENT.md`；具体修正：`docs/DECISIONS.md`

**按内容类型选 skill**：`weiren-new-character`（房客）/ `weiren-new-item`（物资）/
`weiren-new-pseudo`（伪人）/ `weiren-new-information`（信息与全局事件）/ `weiren-new-dlc`（打包）；
它们各自带一份"需求描述清单"，需求描述模板总表见 `docs/ADD_CONTENT.md`。

## 1. 两条分离（最重要）
- **内容 / 系统分离（含 UI）**：`weiren_game/data/`（内容）不得被系统层/前端**按具体内容引用**。
  "系统层/前端"的文件范围以 `tools/audit_separation.py` 的 `SYSTEM_GLOBS` 为准；需要内容时经
  注册表/协议泛化访问（注册表全集见 `AGENTS.md §3`）。
- **前端 / 后端分离**：前端只认"状态 JSON + 动作 JSON"，**不写死任何内容文案/名称**；提示、选项、限定、候选、图鉴文案全部由后端/内容层下发。
- **反向也禁止**：`data/` 不得 import `weiren_game.systems`（只可用协议 `weiren_game.types.EngineProtocol`）。

**验收**：`tools/audit_separation.py` 全过——删除任一内容文件仍能开局；系统/前端内容名与内容 id 残留为 0；`data/` 不依赖 `systems/`。

## 2. 内容自描述（新增内容零改系统）
- 自动发现：`weiren_game/data/_discovery.py` 扫描目录；放入 `.py` 即生效，无需登记。顺序影响随机确定性，勿随意改。
- **能力声明式规格**：字段以 `AbilityDefinition`（`weiren_game/types.py`）为准；前端与 CLI 据此渲染，**不写死内容**。
  **限定 chip 一律由技能自己声明**（`A(..., chips=...)`）；不要再往 `codex_pack` 加静态 chip 表（DLC 读不到）。
- 选择/候选/图鉴补充一律由内容自描述（`TARGET_OPTIONS`、`CODEX_EXTRA/SECTION/SUMMARY`、`PENDING_VIEW` 等；注册表全集见 `AGENTS.md §3`），DLC 也可经 `codex/` 贡献分节。
- **DLC 伪人的图鉴技能**：`codex_pack.PSEUDO_SKILLS` 是内置静态表；DLC 伪人应由其模块声明 `CODEX_SKILLS`
  （`((名称, 文案), ...)`），图鉴页会自动回退读它。
- **面向玩家的文字一律先写进 lang 表**（见下条），不散落在定义里；图鉴正文仍在 `data/` 的图鉴包与 `*_text.py`
  （**以代码为准**），但它们同样只从 lang 取字。

### 2.1 文本（lang）：加一条就能用，没有注册动作

- **表在哪**：base 是 `weiren_game/data/lang.py::TEXT`；每个 DLC 自带 `dlc/<包>/lang.py`
  （模块顶部 `TEXT = pack_text_from_file(__file__)`）。
- **键名用既有 id 拼**：`ability.<id>.name` / `ability.<id>.description` / `character.<id>.name|description|tag.N` /
  `item.<id>.name|description|flavor` / `pseudo.<id>.*` / `info.<id>.*` / `mark.<id>.*`；
  系统层与前端的键按位置生成（`<模块>.<函数>.<n>`、`ui.js.<n>`、`ui.markup.<n>`）。
- **用法**：
  ```python
  # 1) lang.py 加一条（顺序随意）
  "ability.call_friends.name": "呼朋引伴",
  # 2) 使用点按 key 取
  A("call_friends", TEXT["ability.call_friends.name"],
    TEXT["ability.call_friends.description"], chips=(TEXT["ability.call_friends.chip.0"],))
  ```
  带占位符的模板写 `{名字}`，调用点 `.format(名字=…)`；前端 chrome 用 `TXT("ui.x")` 或槽位 `data-t="ui.x"`。
- **加文本 = 只加一条**。没有注册步骤；打错 key 在 Python 侧当场 `KeyError`，
  前端则原样显示 key（肉眼可见）。核对/盘点：`python tools/dump_text.py --out <目录>`。
- **数据键不进 lang**：`path` / `source` / tag / 性别 / 年龄 / 兴趣参与规则命中，**禁止翻译**（见 `docs/ROADMAP.md` §7）。
- **外观/材质也是内容**（三层：base → 资料包 → 独立资源包）。要动前端或材质，
  先读 **`.opencode/skills/weiren-frontend/SKILL.md`**（token/零件/素材位/文件资产、渲染规则、验证手法、坑）。

## 3. 验证（每次改完必跑）
```
python -m compileall -q weiren_game
python -m unittest discover -s tests -p "test_*.py"        # 必须全绿（刻意精简，勿堆冗余用例）
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
python tools/audit_separation.py                            # 分离度自检
python tools/audit_text.py                                  # 动了文案就跑（规则见 docs/STYLE.md §11）
python tools/dump_effects.py                                # 效果注册表 dump（核对 docs/ARCH.md 的闸门/数值目录）
```
前端改动：抽出脚本 `node --check`；发布前跑浏览器压测：
```
python game_ui.py --no-browser --port 8775
node tools/browser_playtest.mjs url=http://127.0.0.1:8775/ games=30 turns=12 budget=420
```

## 4. 常见坑
- `apply_patch` 在本环境相对路径解析易错——**改完必须 grep 复核**；批量改动优先用脚本条件替换后统一写盘。
- JS `>>` 按有符号 32 位溢出；哈希取模用 `>>>`。
- 前端文本统一走 `mdText()`（`·`/换行→换行、`*斜体*`、`**加粗**`、对话 `“…”` 换行）与 `fmt()`（再叠加标签悬浮）；**只有 `【标签】` 才会被解析为 tag**。
- 新增注册表必须纳入 `content.py` 的热切换快照（`_BASE_CONTAINERS`），否则 DLC 卸载回滚会漏。
  快照是**懒抓**的（`dlc.py` 在装载任何包之前调 `CONTENT.ensure_captured()`）：抓取时机**不能**挪回
  `content` 模块级 —— 效果内核的 provider 由 `systems/*` 导入时登记，早抓会把 base 自己抹掉。
- 概率统一 5%~95%（**必定**用 `.certain(0/1)`）；**闸门与通道共用 `path/source`、分用聚合**
  （通道算术、闸门 `any`/`veto`），**闸门是纯查询**（不掷骰/不写状态，掷骰在结算点）；目标回合数下限 12。详见 `docs/ARCH.md`。
- 测试基准由 `tests/_baseline.py` 钉住，勿依赖玩家 `game_config.json`。
- **要专属界面 / 专属状态**（面板、可拖拽浮窗、进存档的专属数据）→ 先读 `weiren-custom-ui`；
  界面验收走 `weiren-ui-probe`。这两件事**别写进当前 skill**，引用就够了。
- **文档只写规则，不复制清单**：清单指向唯一来源（代码或单一文档）；
  同一件事在两处各说一遍 = 下次改动必然打架。也**不要写"多此一举的强调"**——
  例："塔罗牌不是系统，而是厄瑞玻斯的技能"这种句子不承载任何信息，删掉。

## 5. 美术风格（详见 docs/STYLE.md）
暗绿底 + 琥珀主色；启动器 Minecraft 风、哈希路由；标题"报纸剪字"拼贴；单线 SVG 图标、品质映射到颜色；头像 = 基础形状 × 专属特征；吐司代替弹窗。改 UI 前先读 `docs/STYLE.md`。

## 6. 品味与手法（摘要，全文见 `docs/PRINCIPLES.md`）
- **交互靠常理**：拖进去的能拖回来；别为已有动作再加冗余按钮（如"取回"）。
- **不擅自加限制**：没声明的机制不要默认加上；限制必须由内容显式声明（如 `per_turn`）。
- **信息要能看**：查看类点击一律放行；阻断只用于必做的决定，且是"隐藏/显示"而非"取消"。
- **状态如实**：证伪就是已证伪；没生效就是没生效；不要用近似值冒充。
- **机制进后端且调用后端既有方法**：别把前端算法抄进后端覆盖它；前端只渲染。
- **前端只展示**：只渲染后端下发的字段；任何机制/判断都留在后端（排序、档位、合法性、概率、顺序等）。
- **先复现→根因→正确层修**；每次改完按固定动作验证，**起服务看 traceback**；平衡改动要顺手更新写死旧值的测试。
- **普适规则就删特例**：一条规则若对全体成立，就删掉所有 `if 特例`，用唯一公共函数/入口表达；
  不要用"排除名单"反着描述普适规则（例：所有 `condition` 回合末走同一个 `layers-1` 公共函数）。
- **规则文档只写规则，不复制清单**：注册表、字段名、文件名、性格键、目录树这类清单一律指向唯一来源
  （代码 / `AGENTS.md` / `docs/*.md`），避免双维护漂移。
- **测试保持精简**：合并同类断言、能用 `subTest` 就别开一堆方法；不写"镜像实现 / 重复基本行为"的用例。
  **别在文档里写用例数**（`AGENTS.md` §1 同规矩），更不要为一次性改动堆冗余测试。
- **术语与文案属于内容层**；只清自己产生的文件（`WEIREN_SAVES_DIR` 隔离）。

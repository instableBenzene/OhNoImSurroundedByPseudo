# 项目指南（唯一权威文档）

> 目的：即使读者（人或 AI）对本项目**毫无记忆**，读完本文也能理解游戏的运行原理、
> 代码结构与扩展方式。旧的日志/蓝图已全部并入本文件。
> 原稿内容覆盖清单与“未给出数值时的统一约定”见本文件 **§15**；分层与边界见 **§14**（原 `ARCHITECTURE.md`）。

---

## 0. 这是什么游戏

你（屋主）管理一栋房子与其中的房客。某一天，一个**伪人**混了进来——它可能敲门、可能
顶替外出的房客。你要在第 N 回合内活下去、收集物资、识破并驱逐伪人；伪人则要潜伏完成
“突破”。核心循环：

1. **回合开始**：结算上回合的搜索返程、生成门口事件（人类访客 / 补给 / 伪人到访）、
   羁绊与实例的回合初效果。
2. **行动阶段**：处理门口事件（接纳/拒绝）、指派房客搜索、使用物资、发动房客技能。
   门口事件未清完不能结束回合。
3. **回合结束**：基础生命/理智消耗、状态演化、信息核验、背包/书籍结算、伪人回合末。
4. 重复，直到胜利/失败（伪人突破=失败；满足解放或生存到终局=胜利）。

三位内置伪人：**无眠怪医-苯环**（来访）、**深潜者祭司-洋葱**（来访）、
**藏于人群之中的黑手-薯条**（绑架搜索者、顶替回屋）。

---

## 1. 运行时数据模型

核心状态是一棵可序列化的对象树（`weiren_game/models.py`、`tenant.py`、`marks.py`、
`global_event.py`、`pseudo.py`）：

- `GameState`
  - `flow`：回合数、阶段（turn_start/action/turn_end）、max_turns、game_over/victory。
  - `meta`：难度、seed、启用内容包清单等。
  - `round`：本回合的临时计数（是否已搜索、物资使用次数）。
  - `ids`：`InstancePool`，为每类运行时对象发放**唯一 int 实例 id**
    （tenant / item / information / search / pseudo / mark）。
  - `house`：`tenants: {int_id: TenantState}`、`inventory`（屋主仓库）、`information`。
  - `world`：`visitors`、`locations`、`events`（门口事件队列）、`global_events`、
    `disabled_characters`、`missions`（外出的搜索任务）。
  - `pseudo_state`：`PseudoRuntime`（见第 7 节）。
- `TenantState`（房客/伪人替身）：`id`(int)、`character_id`(str)、`health/sanity`、
  `conditions`（状态/情绪）、`personalities`（性格权重）、`inventory`、
  `abilities`（主动/被动状态）、`marks`（`MarkPool`）、`depression`（消沉）、
  `is_pseudo` / `pseudo_source`、`at_home`、`home_turns` 等。
- `Condition`：`intensity` / `layers` / `active`，用于创伤、紊乱、休克、情绪、临时增益等。
- `MarkPool`：`MarkInstance`（`mark_instance_id` + `mark_id` + `value`）列表；
  默认按实例 id 最小优先消耗。
- `GlobalEventState`：世界级条件 `event_id -> (value, layers)`，回合末 `layers −1`。
- `PseudoRuntime`：`scenario_id`(str) + `pseudo_instance_id`(int) + 共享字段
  （`revealed` / `visit_count` / `liberated` …）+ `states{场景后缀: State}`（**每个伪人
  自己的运行时状态放在自己的 `State` 里**）。

静态内容 id（`character_id` / `item_id` / `scenario_id`）是**字符串**；运行时实例 id 是
**int**，二者分离。

---

## 2. 回合循环（生命周期）

阶段顺序由 `weiren_game/lifecycle.py` 的 `START_TURN_PHASES` / `END_TURN_PHASES` 表声明，
引擎按表调用对应方法（`engine.start_turn` / `end_turn`）：

**turn_start**
1. 消沉/生命/理智的“提供效果”；
2. 搜索推进/返程（外出的房客结算返回、掉落、损耗）；
3. 人类访客生成（含温和羁绊/火龙派对焦点）；
4. 伪人到访（日历驱动）；
5. 羁绊统计/等级/激活/权重；
6. 实例回合初：房客 → 背包 → 屋主仓库 → 全局事件 → 伪人；
7. 状态效果、信息核验。

**action**：玩家动作（门口接纳/拒绝、使用物资、装备、发起搜索、房客技能）。

**turn_end**（单根有序）：
基础消耗 → 状态效果 → 状态自演化 → 信息 → 背包/书籍 → 实例收口（含伪人）→ 胜负结算；
最后 `end_turn` 统一衰减全局事件。

**门口事件队列**（`world.events.door_events`）类型：`human`（接纳/拒绝）、`supply`（补给）、
`pseudo`（伪人到访）。必须清空才能结束回合。

---

## 3. 核心系统职责（`weiren_game/systems/`）

| 系统 | 职责 |
| --- | --- |
| `round_effects` | 回合开始/结束各阶段调度（消沉结算、基础消耗、实例收口、伪人回合初/末） |
| `value_system` | 生命/理智的消耗/回复/流失/伤害管线；护甲、减伤、溢出 |
| `condition_system` | 状态/情绪的施加、恶化、恢复、免疫判定、回合触发 |
| `search_system` | 发起搜索、推进、返程结算、掉落抽取与加权 |
| `visitor_system` | 门口事件生成与处理、访客排队、额外访客 |
| `pseudo_system` | 伪人到访、突破、场景 handler 分发、搜索遭遇/抵御 |
| `item_system` | 物资使用/装备/耐久/易损、背包与仓库 |
| `ability_system` | 主动能力门槛/成本/结算（`ability.used/failed`） |
| `cost_system` | 成本结算（理智/生命/印记/物资/次数） |
| `marks_system` | 印记获得/消耗/触达、全局事件与修饰器入口、节点派发 |
| `personality_system` | 性格权重、羁绊等级、被动可用性 |
| `information_system` | 信息生成/核验/效果 |
| `random_system` | 确定性随机（按回合 + 事件 id + 后缀） |

判定口诀：**在 `systems/` 里、做数值/概率变动、被多方复用的“出口”才是通道**；
其余在 `data/` 里只“调用通道 + 发 tag”的都是内容函数/节点。

---

## 4. 数值管线：通道 + 修饰器

### 4.1 通道（系统固定出口）

| 域 | 通道 |
| --- | --- |
| 生命 | `healthConsume` / `healthRestore` / `healthLoss` / `healthDamage` |
| 理智 | `sanityConsume` / `sanityRestore` / `sanityLoss` / `sanityDamage` |
| 消沉 | `depressionChange` |
| 状态 | `condition.intensity.add` / `condition.intensity.reduce` / `condition.layer.add` / `condition.layer.reduce` |
| 概率 | `chance`（单一；子类 tag：搜索/遭遇/易损/抵御/医疗/休克/离屋/恶化/技能失败/物品浪费/濒死） |
| 搜索 | `search`（单一；tag：回合/时运/携带） |
| 物品 | `item.durability` |
| 掉落 | `loot.weight` |
| 印记 | `markGain` |
| 情绪 | `emotionValue` / `awakeningGain` |

- **能由 `source` 区分的派生项不新增通道**：回合末理智 = `sanityConsume` + source `回合末消耗`；
  难度伤害 = `healthDamage`/`sanityDamage` 的最终百分比乘算。
- **布尔闸门不是通道**：免疫、目标锁定、行为位压制、能否来访/搜索、回溯、扳机门控。
- **效果本体（固定伤害/回复/转换/写值）向通道发 base**，因此同样会被修饰器影响。

### 4.2 path 与 source

- `path`：修饰器声明“响应哪些功能”；
- `source`：调用点携带的 tag 集合（含调用链累积）；
- 命中：`modifier.path ∩ event.source ≠ ∅`；`match="all"` 要求 `path ⊆ source`；
  不写 `path` = 全命中。

### 4.3 修饰器与计算

`Modifier`（对象、**无实例**）字段：`modifier_id / effect_type / path / source /
value_type / operation / stage / value / limit / match`。

链式声明：
```python
from weiren_game.modifier_rules import spec
MODIFIERS = (
    spec("healthDamage").final().mul(1.1),                       # 难度：最终无限制乘算
    spec("search").path("回合").flat(-1),                        # 普通固定加算
    spec("chance").path("遭遇").percent(-0.75),                  # 普通百分比加算
    spec("sanityConsume").path("回合末消耗").final().max(0),      # 最终范围限制
    spec("healthConsume").mul(3.0, limit=20),                    # 普通有限制乘算
    spec("chance").certain(1.0).match("all").path("抵御","伪人使用主动能力"),
)
```

**计算顺序**（`calculate_modified_amount(base, modifiers)`）：
```
基础值
→ 普通固定加算
→ 普通百分比加算
→ 普通无限制固定乘算
→ 普通有限制固定乘算
→ 最终固定加算
→ 最终百分比加算
→ 最终无限制固定乘算
→ 最终有限制固定乘算
→ 最终范围限制（max/min）
```
- 有限制乘算：只算自身变化量 `pre × (乘算值 − 1)`，`|变化量| ≤ |limit|` 才乘，否则转为
  **同号 limit 的特殊加算**（普通阶段在其乘算位之后、最终固定加算之前；最终阶段在最终
  无限制乘算之后）；
- `certain`（0/100）：只有单一方向时直接输出，冲突则回落计算；
- 最终范围限制：对全部算完的结果收敛。

**挂载与入口**
- 静态：内容模块声明 `MODIFIERS = (...)`（聚合层按 `effect_type` 收表）；
- 条件式：`register_modifier_provider(channel, provider)`，`provider(context)` 返回 `Modifier`/可迭代/None；
  静态项与 provider 都住在 `modifier_rules` 的四张表里，已纳入 base 快照（随包装卸回滚，
  装载器每次「应用」先还原 base 再重装，所以重复装载不会累积）；
- 调用点：`engine._apply_modifiers(channel, base, source, context)`；
  `engine._apply_chance(base, source, context)`（再收敛 5%~95%）。

### 4.4 概率规则（`probability.resolve`）

1. 先看“必定”（0/100）：有且不冲突 → 直接采用；
2. 必定冲突 → 忽略必定，进入计算；
3. 计算中不设限；最终结果落在 **5%~95%**（必定的 0/100 除外）；
4. 掷骰统一半开区间 `random() < p`。

---

## 5. 状态 / 情绪 / 印记 / 信息

- **状态/情绪**：`Condition(intensity, layers)`；`StatusDefinition`（`condition.py`）声明
  上限、显示、`nodes`、`hook`、`blocked_emotions`、`suppresses_conditions`，以及**风味描述**
  `description`（面向屋主、与机制无关）。`MarkDefinition` 同样带 `description`。核心对状态做
  **通用遍历**（如按 `blocked_emotions` 判免疫、按 `suppresses_conditions` 判压制）。
- **情绪**：归侵蚀/觉醒族，参与消沉结算（`depressionChange` 通道）。
- **印记**：`MarkDefinition`（`minimum` / `maximum` / `externally_locked`）；实例存
  `TenantState.marks`，默认按实例 id 最小优先消耗；节点 `mark.gained/consumed/reached`。
  `externally_locked=True` 表示“内部牌库”（如厄瑞玻斯的 `fate`），禁止被外界改写。
- **信息**：`Information`（模板 + 目标 + 真伪 + 状态）；`register_state_effect` 登记核验/
  待验证效果；节点 `information.created` / `information.verified`。
- **风味文本**：`ItemDefinition.flavor`（+`flavor_shown`）与 `StatusDefinition.description`
  （受 `shown` 控制）承载面向屋主的描写/台词，与机制字段分离；设计稿 `游戏资源.docx` 的
  整段风味（含对话）即迁入此处。支持轻量标记 `**加粗**` 与换行，终端显示经
  `weiren_game/text.py` 的 `render_markup`（`ansi=False` 时退化为 `strip_markup`）。

### 5.0 堆叠系统（模型 B：真堆叠）

- **可堆叠品**（`ItemDefinition.stack_size > 1`、无耐久）在入库时按 `item_id` **合并**为一个
  `ItemInstance`，`count` 累加，**上限 = `stack_size`**，超出开新实例。
- **不可堆叠品**（耐久品 / 装备，`stack_size = 1`）每件独立实例，各存各的耐久，永不合并。
- **获得数量**：战利品授予（搜索 / 必然获得）时，可堆叠品按 `ItemDefinition.obtain_range`
  掷出 `[下限, 上限]` 内的数量（默认 **`stack_size/4 ± 1`**，下限 ≥1、上限 ≤`stack_size`）；不可堆叠品固定 1。角色/信息等
  **明确数量**的给予按给定数量入账（不走随机）。
- **消耗**：`Inventory.consume(item_id, n)` 按“单位”扣减 —— 可堆叠只减 `count`，归零才移除
  实例；`_take_item` / `_decrement_inventory` 均走此路径。
- **携带位**：一个实例（≤ `stack_size`）占 1 组；同种多实例占多组。

## 5.1 表现层（前端）

引擎保持无头；**命令行**（`weiren_game/cli.py`）与**图形界面**（`weiren_game/gui.py`，tkinter）
是同一引擎的两套前端。内容/引擎需要向用户询问（选项/确认/整数/选目标/选牌）时，一律调用
`engine.ui`（`weiren_game/ui.py` 的 `UserInterface`），由前端注入实现——内容里**不得**直接
调用 `input()` 或导入 `cli`。风味标记的统一渲染见 `weiren_game/text.py`
（`segments` / `render_markup` / `strip_markup`）。

---

## 6. 全局事件键与持续回合约定

- 全局事件 = 世界级条件（`WorldState.global_events`），回合末 `layers −1`。
- **一次性事件用通用键**，不出现内容名：`guard.rewind`、`visitor.extra`、
  `visitor.extra_pseudo`、`visitor.suppress`、`visitor.supply`、`information.false_lock`、
  `item.fragile.multiplier`、`item.durability.multiplier`、`encounter.rate.multiplier`、
  `search.turn_delta`、`search.fortune_delta`、`breakthrough.adjust`、
  `sanity_end.multiplier`、`conversion.health_to_sanity` 等。
- **持续回合约定**：
  - 下回合初/跨回合兑现：**≥2**（撑过回合末一次衰减）；
  - 本回合内兑现：**1**；
  - 长期/一次性未定：**99**；
  - 限时若干回合：具体回合数。
- 例：恋人正位写 `visitor.extra`（2 回合）→ 下回合开始阶段由访客调度消费并 `_queue_human_visitor`。

---

## 7. 伪人机制（含三位内置实例）

**通用**
- `PseudoDefinition`：`id` / `name` / `human_character_id` / `description` / `breakthrough`
  / `liberation` / `enters_house`（是否亲自到访） / `mark_field` / `mark_label`
  / `mark_externally_locked`。
- 流程：初访揭示（初访不突破）→ 后续来访按场景 handler 结算 → 突破=失败 / 解放=胜利。
- 场景 handler 由 `SCENARIO_HANDLERS[scenario_id]` 查表（`visit` / `cast_*` / `start_passive`
  / `encounter_chance` / `attack_searcher` / `end_sanity_multiplier` …）。
- 行为位（“压制”）：禁用 `visit` / `cast` / `breakthrough` / `auto_expel`。
- 运行时状态放各自 `State`（`pseudo_state.scenario()` 读取）。

**苯环（来访型）**
- `mark_field=fear_marks`（恐惧印记）：访客来访 +1、被接纳再 +1；满阈值自动释放诅咒。
- 突破：两次来访间死亡数 + 当前休克数 > `max(0, min(5, 9 − 来访次数))`；
- 诅咒：对屋内伤害 + `(10−印记)×人数` 次随机选人加创伤/紊乱；
- 解放：连续 5 次无人休克 或 连续 7 次无人死亡；
- 袭击：`精湛刀艺`（创伤 +2/+2、15 伤害）。

**洋葱（来访型）**
- `mark_field=whisper_marks`（低语印记）：房客理智下降 +1；满阈值自动释放低语。
- 突破：来访时烦躁占比 ≥ `15% × 来访次数`（上限 75%）；
- 低语：目标数 `ceil(印记/4)`，烦躁 +2 强度 / +5 层数；强度≥5 造成 10 伤害；
- 解放：连续 2 次无人获得烦躁 或 连续 4 次无人因低语损失生命；
- 袭击：`潮汐的诱惑`；被动：`先兆低语`、`情绪显现-烦躁`、`旧日的回声`。

**薯条（屋内型，`enters_house=False`）**
- `mark_field=exposure`（暴露值，`mark_externally_locked=True`）：潜伏回合、理智溢出、模仿能力、
  虚假信息被验证等累计；达 25 触发 `炼狱扳机` 后自逐。
- 突破：屋内累计 ≥10 回合 或 单次潜伏 ≥5 回合 或 释放炼狱扳机时屋内 <3 人；
- 解放：累计驱逐替身 3 次；
- 主动：`潜伏`（绑架搜索者、替身顶替）、`玩弄人心`、`表演`、`炼狱扳机`；
- 人类薯条（角色）另有：`莫名带点东西`（燧发枪+弹药）、`莫名的幸运 B`、`深度思考`（人设系统）。

---

## 8. 内容模型与注册表

**注册表**（聚合层 import 阶段并入，运行时只查表）：
| 注册表 | 键 → 值 |
| --- | --- |
| `CHARACTERS` / `CHARACTER_MODULES` | character_id → 定义 / 模块 |
| `ITEMS` / `CATEGORIES` | item_id → 定义 |
| `PSEUDOS` / `PSEUDO_MODULES` / `SCENARIO_HANDLERS` | pseudo_id → 定义 / 模块 / {handler: fn} |
| `PERSONALITY_MODULES` | personality_id → 模块 |
| `LOCATIONS` | location_id → 定义 |
| `NODE_HOOKS` | 节点名 → hook 列表 |
| `CHARACTER_NODE_HOOKS` / `CHARACTER_VALUE_HOOKS` | character_id → {节点: fn} |
| `ITEM_HOOKS` | item_id → {节点: {标签: fn}} |
| `MARK_*_HOOKS`、`HEALTH_CHANGED_HOOKS` 等 | hook 列表 |
| `ABILITY_INTERACTIONS` | ability_id → 交互结算 UI（内容自描述，如命运抽牌的选牌流程） |
| `CODEX_SUMMARY_HOOKS` / `CODEX_SECTIONS` | 图鉴的统计行 / 详细展示段（内容自描述） |

**自动发现**：`characters/`、`personalities/`、`pseudos/`、`items/`、`tags/` 的聚合由
`weiren_game/data/_discovery.py` 扫描目录并导入——**放入或删除 `.py` 文件即生效，无需登记**。
顺序固定以保随机确定性：`CHARACTER_MODULES` 按文件名、`CHARACTERS` 按 `source_id`、
`items` 按 `CATEGORY_ORDER`（新分类追加）。

**内容模块可声明**：`CHARACTER`、`ITEMS`、`DEFINITION`、`State`、`ACTIVE_DISPATCH`、
`SEARCH_REWARD`、`VALUE_HOOKS`、`NODE_HOOKS`、`HOOKS`、`MARKS`、`TURN_START`、
`HEALTH_CHANGED`、`TENANT_DEATH`、`ON_ABILITY_USED/FAILED`、`HANDLERS`、`MODIFIERS`。

**分发**：事件节点 `engine._emit_node(node, **ctx)`；伪人 `SCENARIO_HANDLERS`；
数值/概率 走通道（第 4 节）。

---

## 9. 内容组织规范

- **一人一文件**：`data/characters/<id>.py`（“定义 / 修饰器 / 技能函数”三节），注册到 `CHARACTERS`。
- **物品按大类**：`data/items/{surgery_kits, medicine_kits, analgesics, food, tools_armor,
  information_carriers, character_items}.py`；tag 行为放 `data/tags/*.py`。
- **伪人**：`data/pseudos/pseudo_<id>.py`（`DEFINITION` + `State` + `HANDLERS`）。
- **性格/羁绊**：`data/personalities/<id>.py`（`HOOKS` / `*_HOOKS` / provider）。
- **印记**：`MARKS`（`MarkDefinition`）。
- **信息**：`data/information.py`（模板 + `register_state_effect`）。

**source 词表（多维 tag）**
- 行为：使用物品 / 装备 / 持有 / 研读 / 消耗 / 触发 / 搜索 / 搜索中 / 搜索返程 /
  回合初 / 回合末 / 伪人技能 / 主动技能 / 被动 / 治疗 / 调味
- 类别：医疗物资 / 食物 / 工具 / 防具 / 信息载体 / 工艺品
- 类型：手术包 / 药箱 / 镇痛剂 / 燧发枪 / 弹药 / 沃尔玛购物袋 / 护甲 / 手电筒 / …
- 具体：物品名 / 技能名 / 状态名
- 目标：创伤 / 紊乱 / 生命 / 理智 / 消沉 / 易损 / 抵御 / 遭遇 / 搜索 / 时运 / 回合 /
  携带 / 状态 / 恶化 / 状态避免 / 医疗 / 保底 / 护甲
- 归属：房客 / 携带者 / character_id / pseudo_id / personality_id

---

## 10. 内容包 / 存档 / 配置

- 内容包集合**启动即定、对局不变**：`SaveMetadata.packs` 记录启用清单，读档不一致即拒绝；
  `base` 恒启用、缺失即启动失败；DLC 由 `game_config.json::enabled_dlc` 启用；
  `dlc.json` 支持 `min_game_version` 前置校验。
- 外部内容包放 `dlc/<pack>/`，暴露 `register(manager)`（或模块级注册表），与内置包同一接口。
- `game_config.json`：默认难度、回合、随机伪人、默认伪人、enabled_dlc。
- 示例 DLC：`dlc/likai_test`（角色 likai + 物品印象派名画）。

---

## 11. 如何新增内容（checklist）

**新角色**：加 `data/characters/<id>.py`（`CHARACTER` + 需要的 `VALUE_HOOKS/HOOKS/MARKS`），
在 `data/characters/__init__.py` 登记；数值效果写成 `MODIFIERS` 或 provider。

**新物品**：加进对应大类 `ITEMS`；效果用 `on_use` + `ITEM_EFFECTS`；
数值修正用 provider / `MODIFIERS`；机制点用 `ITEM_HOOKS`。

**新伪人**：加 `data/pseudos/pseudo_<id>.py`（`DEFINITION` + `State` + `HANDLERS`），
在 `data/pseudos/__init__.py` 登记；事件/印记用通用事件键 / provider / 通道。

**DLC**：`dlc/<pack>/` + `register(manager)`；`dlc.json` 可带 `min_game_version`。

**禁止**：在 `systems/` 出现具体内容 id 或模块 import；新增派生通道（优先用 source 区分）。

---

## 12. 验证

- 单元测试：`python -m unittest discover -s tests -p "test_*.py"`（必须全绿，刻意精简；见 `AGENTS.md` §1）；
- 冒烟：`python tools/smoke_simulation.py --seeds 3 --log-dir <dir>`（三伪人可跑通）。
- 修改后先跑测试再冒烟；行为不变才继续。

---

## 13. 术语表与常见误区

- **通道 vs 内容函数**：通道在 `systems/`，是数值/概率出口；内容函数在 `data/`，只发 tag。
- **path vs source**：`path`=修饰器响应什么；`source`=事件由什么构成；命中看交集（或子集）。
- **扳机 vs 通道**：扳机决定“何时”；通道决定“改什么”。吉利服的“避免返程恶化”是**扳机门控**，
  不是 `chance` 修饰器。
- **标记 / 印记**：`mark` 是角色或伪人的数值积累；`_mark_*_hooks` 是节点钩子，别混。
- **溢出**：走“回复后扳机”，直接取溢出量（比格小星转星之印记；薯条转暴露）。
- **实例 id**：运行时是 int（每类独立池）；静态内容 id 是 str。
- **全局事件持续**：下回合初兑现必须 ≥2；本回合内用 1。

---

## 14. 架构：分层、边界与可插拔（原 `ARCHITECTURE.md`，内容保留）

> 细节以 `docs/GUIDE.md` 为准；本文件是"为什么这样分层 + 怎么遵守"。

### 1. 分层

```
weiren_game/
  data/            内容层：角色、物品、地点、信息、性格、伪人、标签、图鉴文案
  systems/         系统层：能力/条件/物品/印记/性格/伪人/搜索/访客/回合末/数值…
  engine.py        薄引擎：编排 systems、维护状态与生命周期
  cli.py           终端前端（仅认状态与通用交互）
  web_ui.py        本地 Web 后端（JSON 状态 + 动作）
  webui/index.html 前端（仅认状态 JSON + 动作 JSON）
  content.py       ContentManager：内容注册/查询边界 + 热切换快照
dlc/<name>/        外部内容包（同 data 的结构）
```

### 2. 内容 / 系统 边界
- 系统层**不得**出现具体内容名或内容 id；需要内容时经注册表/`CONTENT` 泛化访问。
- 内容层可以依赖系统层的**协议**（`EngineProtocol`）与 `Engine` 的通用方法，但不得反向要求系统认识它。
- 新增内容只改 `data/` 或 `dlc/`，**零改核心**（自动发现生效）。

### 3. 前端 / 后端 边界
- 前端只消费 `build_state()` 产出的 JSON 与 `/api/action` 的动作；不引用游戏规则。
- 特殊提示、选项、限定条件、候选目标、图鉴文案……**全部由后端/内容层下发**；前端只做通用渲染。
- 交互统一经通用机制：`ABILITY_TARGET_OPTIONS`（目标候选）、`PENDING_VIEWS`（待处理视图）、`CODEX_EXTRA`（图鉴补充）、`AVATAR`（头像）、`chips`（限定条件）。

### 4. 声明式能力规格
`AbilityDefinition`：`target / prompt / options / amount_label / amount_mark / chips / nested_option`。
- `target`：`none / tenant / other_tenant / tenant_condition / resource / amount / information / fate`。
- 前端与 CLI 都据此渲染，禁止按能力 id 特判。

### 5. 可插拔内容
- 自动发现：`data/_discovery.py`；顺序（影响随机确定性）见 `AGENTS.md`。
- 热切换：`content.py` 的 `ensure_captured()/restore_base()` + `dlc.reload_dlc()`；新增注册表须加入 `_BASE_CONTAINERS` 快照。
  base 快照是**懒抓**的（`dlc.py` 在装载任何包之前调用 `ensure_captured()`），不能挪回 `content` 模块级：
  效果内核的 provider 由 `systems/*` 在导入时登记，早抓会漏掉它们，回滚时反而把 base 抹掉。
  内容包**有序**（`pack_order`，高→低，含 base）：`dlc.apply_pack_order()` 从最低优先级装载，
  轮到 base 时 `overlay_base()` 让内置内容赢过它下方的包；把包排在 base 之前即可替换内置同 id 内容。
- DLC：`dlc/<name>/`（`dlc.json` + 各内容目录：`characters/ personalities/ items/ tags/ statuses/
  locations/ information/ pseudos/` + 可选 `codex/`）；启动/界面应用时装载，卸载即热回滚。

### 6. 配置与存档隔离
- `game_config.json` 只放"对局外设置"（难度/回合/默认伪人/启用包）；测试用 `tests/_baseline.py` 钉住基准，避免受玩家设置影响。
- 存档记录 `meta.packs`；与当前启用包不一致时拒绝读档。

### 7. 验收与审计（每次改动后）
```
python -m compileall -q weiren_game
python -m unittest discover -s tests -p "test_*.py"
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
python tools/audit_separation.py
```

### 8. 图鉴内容层（可插拔）

- `data/codex_pack.py`：**基础图鉴包**——羁绊档位/基础效果/激活条件、伪人技能、基础机制、地点图标与完整文案、物品关联；并提供 `register_section()`（DLC 用）。
- `data/labels.py`：内容展示标签（物品分类/tag/品质段位/地点分组图标 + `EQUIP_TAGS`）。
- `data/information_text.py` / `data/items/codex_text.py`：信息与物资的**设计稿全文**（图鉴展示用；未收录回退到定义内描述）。
- 角色可自声明图鉴补充：`CODEX_EXTRA()`（如厄瑞玻斯的命运牌表格、薯条的人设）。
- DLC 贡献图鉴：`dlc/<名>/codex/*.py`，暴露 `register(ctx)` 或 `SECTIONS`；`dlc.py` 的 `load_codex_dir` 装载。
- **热切换**：`codex_pack` 的各静态表（`EXTRA_SECTIONS` / `PSEUDO_SKILLS` / `LOCATION_ICONS` / `LOCATION_TEXT` /
  `PERSONALITY_*`）与 `labels` 的各标签表都已纳入 `content.py` 的 `_BASE_CONTAINERS` 快照；卸载 DLC 时自动回滚。

### 9. 声明式交互（前端/CLI 通用）

- **能力规格**：`AbilityDefinition.target` ∈ `none / tenant / other_tenant / tenant_condition / resource / amount / information / fate`；
  配套 `prompt / options / amount_label / amount_mark / chips / nested_option`。前端与 CLI 只按规格渲染，**不得按能力 id 特判**。
- **目标候选**：`TARGET_OPTIONS = {ability_id: fn(engine, actor) -> [{value,label,desc}]}`（如「情报收集」）。
- **待处理视图**：`PENDING_VIEW = (build, resolve)`；`build` 返回 `{prompt, options, cancel, submit?}`。
  - `submit` 规格支持"提交物资"交互（如厄瑞玻斯上交紫色物资改定牌面）；`resolve` 接受结构化值 `{index, item_id, orientation}`。
- 后端 `build_state` 把这些规格与图鉴数据一并下发；`web_ui` 不做内容判断。
- **界面照现有范式拼**：选人＝房客卡、物品＝格子、选一个＝卡片行、描述＝行式信息条目——
  完整清单与各自用例见 `docs/STYLE.md` **§10 UI 范式（照着用，别另造）**。

### 10. 边界自检

`tools/audit_separation.py` 同时检查：
1. 系统层 + 前端**不含**内容名/内容 id；
2. `data/` **不 import** `weiren_game.systems`（仅允许协议）。

### 11. 自定义 UI（内容自有的专属界面）

- 内容可以给自己开一块**专属状态**和**一个专属界面**，核心只当宿主：
  - `CONTAINERS = {"<key>": <类>}`：房客专属状态，存进 `TenantState.containers` 随存档走；
    类自己实现 `to_dict` / `from_dict`（契约同 `PseudoRuntime`）；引擎入口 `engine.container(tenant, key)`。
    存档里没声明过的 key、坏数据一律丢弃（对玩家宽容）。
  - `PANEL = (build_view, resolve_action)`：专属面板。`build_view(engine, tenant)` 返回
    `{title, prompt, slots, rows, actions, backdrop?}` —— `rows` 与 `DETAIL_SLOT` **同一套词表**；
    `slots` 里放物品（内容只给 `item_id` / 数量，图标与品质由前端按目录补）。
    `resolve_action(engine, tenant, action, *, slot, item_id, source)` 收下玩家的动作，**动作名由内容定**。
  - 入口：`AbilityDefinition.opens_panel = True` 的技能行渲染成开 / 关，点击**不走能力结算**
    （引擎也会拒绝该技能被当普通主动技能调用）。
- **面板不是待处理交互**：随时能开、看完能关，"开着没有"是纯展示状态；它**不参与回合流程**
  （不阻塞保存 / 开始回合 / 结束回合）。浮窗可以拖，位置按视口比例记进 `game_config.json`
  （`panel_draggable` 默认开）。
- 登记：`CHARACTER_CONTAINERS` / `CHARACTER_PANELS` 与类型表 `tenant.CONTAINER_TYPES` 都在
  `_BASE_CONTAINERS` 里，随内容包装卸一起回滚。
- 第一个真实调用者：花尔维纳「园艺达人」的田（`data/characters/flowey.py`）。


---

## 15. 原稿内容覆盖与实现约定（原 `docs/CONTENT.md`，内容保留）

> 本文由 README 拆出，记录“原稿内容覆盖清单”与“原稿未给出数值时的统一实现约定”。
> 与代码冲突时一律以代码为准；架构与扩展见 `docs/GUIDE.md`。

### 原稿内容覆盖

#### 房客与性格

- 原稿编号 1～24 全部建档；其中 23 名可用房客会正常生成、来访和结算能力。
- 原稿从 15 号直接跳到 17 号，没有第 16 号角色定义；程序用 `stone` 占住第 16 号
  （显示名 **古雕塑**，`available=False`）维持编号完整，不进对局（见 `data/characters/stone.py`）。
- 已实现原稿八类常规性格：开朗、孤僻、机敏、固执、稳重、急躁、温和、多疑。
- 性格主/副权重会随消沉值变化；达到阈值后激活相应羁绊。孤僻和固执的非连续阈值也按原稿处理。
- 休克、创伤、紊乱和高消沉会按对应规则令性格、主动或被动能力失效；被动并非在高消沉时永久关闭，而是按原稿进行 50% 失效判定。
- 火龙、比格小星、ED Tear、苯环、葱头、错潮、厄瑞玻斯、柳七鱼、久孤、薯条、澪叁贰玖、青桃、罗兹、罗丁、混、堤谧特、花尔维纳和沙白的专属机制均已接入。
- 没有专属能力文本的 HKW、白龙、端、斜阳、小五和古雕塑（16 号，不可用）仍完整参与性格、状态、搜索、信息、装备和来访系统。

#### 数值、状态与情绪

- 生命、理智、生命上限、休克、离屋次数和隐藏消沉值。
- 创伤与紊乱 1～10 级的各档生命/理智流失、自我恶化、延长、行动限制、搜索惩罚、主动/被动失效概率。
- 侵蚀情绪：无聊、烦躁、焦虑、忧郁、恐慌。
- 觉醒情绪：满足、专注、信任、兴奋、快乐。
- 稀有情绪：混的理智与癫狂，以及其他由专属机制生成的状态。
- 情绪集加权选择、强化断点、延长、减少、回合末自我变化，以及回合开始的消沉/昂扬合成结算。
- 高生命状态的自然恢复、低生命休克、休克死亡与消退、消沉导致的自行离屋和返回。
- 镇痛只免疫状态的“额外效果”，不会跳过基础回合末流失或状态自身变化。

#### 搜索与战利品

- 25 个原稿地点全部定义；每局生成 10 个，其中县级综合医院、便利店、大型工农商超市、县快递驿站固定出现。
- 搜索回合、搜索行为次数、成功率和携带容量是分离的状态轴；开始搜索后，改变某一轴不会错误反算其他轴。
- 按 `游戏种子 + 搜索开始回合 + 搜索序号 + 事件 ID + 执行序号` 固定随机结果；改变成功率会重新判断同一序列，不会重抽结果。
- 必然获得先于普通搜索结算，并占用携带容量；普通成功只提供战利品抽取机会，背包满时不会多拿。
- 完整品质、标签、地点权重、时运修正、机敏羁绊、角色追加、信息修饰和物品池二次筛选。
- 可堆叠物资按原稿每组上限计算临时携带占位；常驻装备也占用搜索容量。
- 搜索返回自动受到 10 生命伤害和 10 理智伤害；既有创伤、紊乱与侵蚀情绪会恶化/延长。
- 外出期间生命低于 0 时，通常死亡；5% 概率以 0 生命、休克 1/2 返家，并失去所有临时与常驻携带物。
- 武器、防具、吉利服、燧发枪及弹药、沃尔玛购物袋和角色抗性会参与伪人搜索袭击。

#### 物资、装备与研读

- 57 种物资全部建档并进入对应使用、装备、掉落或专属获取流程。
- 包含六档创伤手术包、六档紊乱药箱、三种镇痛剂、强心剂、完整食物/零食、搜索工具、四种防具、随身听、留声机、四类书籍、报刊录像与手机，以及角色专属物资。
- 消耗品、易损品、耐久消耗品和可堆叠物资分别处理；耐久按每一件物品独立保存。
- 同一房客可携带多件装备，但一次生命伤害只由最早装备的一件装甲响应。
- 书籍在持有后的每个回合结束推进研读：《基础生命支持》《植被图鉴》《避险手册》在第 5 次结算习得永久被动，《星云传说》在第 7 次结算习得永久被动。
- 永久研读能力习得后，即使卸下或失去书籍仍然保留，但触发时仍遵循被动能力失效规则。
- 留声机是屋内工艺品，只要在屋主物资栏中就于回合开始为全员回复理智，不需要也不能装备。

#### 信息与指认

- 22 类静态信息模板全部实现，包括物资奖励、地点修饰和房客状态事件。
- 另外会按上下文动态生成普通来访、伪人来访、返家、搜索返回、伪人技能、情绪显现和薯条替身信息。
- 信息拥有真假、待验证/证实/证伪/失效状态、目标、地点、有效期和一次性结算标记。
- 搜索、来访、返家和伪人技能会用真实事件自动核验相关信息；厄瑞玻斯、澪叁贰玖、多疑羁绊、太阳牌和主动识别也能改变核验流程。
- 已证实的地点/物资信息会加入实际搜索奖励或临时战利品修饰；房客离开、死亡或休克时，依赖其作为目标的信息会失效。
- 薯条替身会通过表演制造信息和暴露值；一条已证实实锤或三条待验证疑点可以发起指认。错误指认会驱逐真人。

#### 厄瑞玻斯的命运抽牌

- 命运抽牌是厄瑞玻斯的专属主动能力：0～21 共 22 张牌全部实现正位与逆位，包括愚者回溯、命运之轮定向/隐藏、正义驱逐、倒吊人转换、死神净化/休克、太阳信息规则、审判加入人类对应形态和世界长期压制。
- 抽牌为抽三选一。**界面流程**（全部由内容声明、前端只渲染）：
  ① 选牌（「发现」那套无背景板卡片，悬浮看正/逆位效果）→
  ② 上供：给一个紫格，把紫色及以上物资**拖进去**＝上供，空着直接「继续」＝不上供 →
  ③ 选正位／逆位（上供买到的那一步；「命运之轮」这类需要定向的牌直接从这里开始）→
  ④ **先揭晓**（牌面 + 方向 + 效果），再问「结算 / 反悔」。
- 22 张牌面与两个方向各有符号（`data/characters/erebus_fate_symbols.py`，内容自带的**内联 svg**，
  跟着主题色走）；图鉴「房客 → 厄瑞玻斯 → 牌面符号」是一面可直接核对的符号墙。
- **需要指定房客的牌**（目前只有死神·正位）在第 ③ 步之后多一步选人：由内容声明 `target`
  （牌号 + 方向 + 候选），前端复用「指派搜索」那套房客卡，选中的 `target_id` 交给结算。
- 审判在伪人初访后才进入可抽范围。
- 已被永久移出牌堆的愚者不会再次抽到；世界生效后，本局命运抽牌关闭。

#### 存档、迁移与回溯

- JSON 存档包含完整世界状态、随机上下文所需字段、房客、搜索、装备逐件耐久、信息、命运牌堆、伪人进度和回合历史。
- 存档版本为 `2.1.0`；若存档版本或启用内容包与当前不符，读取时会明确拒绝。
- 每个回合开始前保存快照，默认保留最近 20 个；玩家可回到当前回合开始前重新决策。
- 查询状态不会消耗随机数，被动是否失效只在具体触发点判定，因而查看菜单不会改变结果。

### 原稿未给出数值时的统一实现约定

原稿包含少量明确的占位、问号、缺失数值或互相冲突的草案文本。为了让整局可运行，程序只在这些位置补充稳定默认值；其余有明确数字的规则均直接采用原稿。以下约定也写入了代码注释与测试，便于日后替换：

| 原稿空缺或冲突 | 终端版约定 |
| --- | --- |
| 没有规定开局人数、初值和初始库存 | 随机 2 名真实房客（两次 Discover(3)，每次至少含一位“御三家”）；常规房客生命/理智各 80；开局物资从战利品池按种子抽取（食物×2、医疗×1、工具×1、信息载体×1） |
| 没有规定普通访客与门外伪人的基础频率 | 每回合安排 1 个基础门口事件；苯环/洋葱的基础伪人来访间隔为 3 回合；羁绊、能力和命运抽牌可增加、取消或替换来访 |
| 流程只说“视具体胜负条件”，没有统一最长回合 | 默认第 32 回合日出，可用 `--max-turns` 修改，且不覆盖各伪人的专属解放/突破条件 |
| 普通随机情报没有给出真假基础概率；太阳逆位只写“假情报概率增加” | 常态采用 70% 真情报；太阳逆位期间采用 45% 真情报；所有固定真假来源仍严格服从原稿 |
| 待验证状态信息没有自动识破概率 | 每次回合末触发后以稳定 20% 尝试自动核验 |
| 温和基础效果写“回复生命”但没有数值 | 采用 5 生命，与其最低羁绊档的明确治疗量保持一致 |
| 普通驱逐没有写理智代价 | 被驱逐者以外的在场房客各消耗 5 理智；柳七鱼按能力文字豁免自身 |
| 医疗越级公式带有多余百分号 | 按概率 `2 / (强度差 + 2)` 解释，并保留原稿的最低 5% 与 BLS 最高 95%；医疗等级范围内仍为明确的 100% 成功 |
| 殒痛去、帕瑞昔布、吗啡没有品质 | 依次采用绿色、紫色、红色，不改变其明确功能 |
| 汇总表写“星尘手术包”，正文写“星云手术包” | 采用正文名称“星云手术包” |
| 极地冲锋衣“失败后重复，最多 4 次”存在触发解释歧义 | 一次状态施加最多进行 4 次独立的 25% 避免判定，统一消耗一次触发耐久 |
| “片刻的宁静”写入“宽慰 2/3”，但原稿没有定义宽慰效果 | 保存 `宽慰强度=2、层数=3` 标记，不擅自附加未写明的数值效果 |
| 魔术师逆位文本与正位相同且带问号 | 按字面与正位相同处理：下一位访客替换为神秘补给 |
| 稳重 8 档对非稳重者的“减少并分担”措辞可有两种理解 | 同阶段减伤加算：非稳重者先按原稿获得 60% 减免，再把原伤害的 50 个百分点作为不可修饰流失分配给稳重房客 |
| 愚者逆位要求“伪人来访两次”，但薯条没有门外形态 | 薯条场景映射为下一回合对外部搜索者进行两次强制绑架判定 |
| 解放条件文字写“下一次来访获得解放”，但没有额外来访结算定义 | 达成所需连续次数或累计次数时立即结算解放，避免已经完成条件后仍被无定义的等待回合杀死 |
| 原稿第 16 号房客缺失 | 只保留不可生成占位；没有杜撰人物和能力 |
| “全局事件”原稿标注暂不实装 | 已实装为通用机制（`global_event.py` 的 `GlobalEventState`）：事件键与层数/回合数解耦，供命运抽牌、物资、信息与伪人技能共用 |

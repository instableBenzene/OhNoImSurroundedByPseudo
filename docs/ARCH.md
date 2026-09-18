# ARCH.md — 统一效果内核：通道（channel）× 闸门（gate）

> 面向"以后再加内容"的架构约定。**本文是方案与目录，不代表已实现**；落地按 §8 分阶段、增量、每步过自检。
> 唯一权威架构文档仍是 `docs/GUIDE.md`；本文只展开"效果计算"这一层。

## 0. 一句话

**数值/概率**与**布尔闸门**共用同一套「声明 + 收集」（registry + `path` + `source` + `match`），
只在**聚合器**上分叉：数值走算术九阶段，布尔走逻辑（OR/AND/NOT）。

## 1. 两轴模型

| | 通道 channel | 闸门 gate |
| --- | --- | --- |
| 语义 | 幅度 / 概率「多少」 | 许可 / 存在「能不能」 |
| 聚合 | 算术：`flat / percent / mul / final / max / min` | 逻辑：`any`(OR) / `all`(AND) / `veto`(NOT) |
| 时机 | **结算点**算一次（有 base） | **纯查询**（随时重算、无副作用） |
| 入口 | `engine._apply_modifiers` / `_apply_chance` | `engine._eval_gate`（拟） |
| 注册 | `MODIFIER_REGISTRY` / `MODIFIER_PROVIDERS` | `GATE_REGISTRY` / `GATE_PROVIDERS`（拟） |
| 值域 | 数值 | 0 / 1 |

**共用**：`path`（响应哪些功能）、`source`（调用点令牌）、`match="any"|"all"`、`_matches` / `_source_tokens`。
即：**同一套 path·source，换一个聚合函数**。

## 2. 三条硬规则

1. **精确定位用 `match="all"`**：`path=("功能","对象")`，调用点 `source=("功能","对象", …)`。
   `any` 只用于宽泛订阅；"功能+对象"一起写并用 `all`，才不会被相邻事件误触发。
2. **两个 `source` 不是一回事**：
   - 调用点 `source`：本次查询携带的**匹配令牌**；
   - `spec(...).source(...)`：这个效果的**出身标注**（只做追溯/展示，**不参与匹配**）。
3. **闸门是纯查询**：`_eval_gate` 里**禁止掷骰 / 写状态**；**掷骰与消耗只能发生在结算点**。
   否则"反复查询"会烧掉随机数、破坏可复现性。

## 3. 必定 / 95% / 组合型效果

| 意图 | 表达 | 结果 |
| --- | --- | --- |
| **必定** | `.certain(0/1)` | 字面 0 / 100，`resolve()` 不动 |
| **几乎必定（会失手）** | 通道数值 + `resolve()` | 收束到 **5%~95%** |

组合骨架：

```
gate(是否进入判定)  ×  chance(基础 + 修正 → resolve)  ×  roll(结算点)
```

**反例警示**：像"消耗弹药→100% 抵御"这种，是 **`chance` 通道里的数值**（`flat(+1.5)` → 夹到 95%），
**不要**写成 `.certain(1.0)` 或 gate。

## 4. 令牌词表（`path` / `source` 的共享词汇）

> 新增效果时**只从这里取词**；缺词先补词表，再写声明。避免以后出现"各自造词"导致不完整。

### 4.1 功能词（`path` 的首令牌）

`显示情绪`、`施加`、`额外效果`、`抵御`、`锁定`、`验证`、`行动`、`伪人行为`、`到访`、
`搜索`、`易损`、`回合末消耗`、`战时`、`开局`。

### 4.2 对象词

- 情绪键：`烦躁`、`无聊`、`忧郁`、`恐慌`、`焦虑`、`满足`、`专注`、`信任`、`兴奋`、`快乐`…
- 生理状态：`创伤`、`紊乱`、`休克`
- 资源：`生命`、`理智`
- 行动位：`visit`、`cast`、`breakthrough`、`auto_expel`
- 其它：品质段（`白/绿/蓝/紫/金/红`）、印记名。

### 4.3 出身词（`source` / `spec().source()`）

`角色`、`性格`、`性格羁绊`、`伪人场景`、`物品`、`物品 tag`、`状态`、`全局事件`、`难度`、`技能名`、`地点`。

### 4.4 物品 tag 表（`ITEM_TAG_LABELS`，可直接作 source 令牌）

| tag | 标签 | tag | 标签 | tag | 标签 |
| --- | --- | --- | --- | --- | --- |
| `ammo` | 弹药 | `anodyne` | 镇痛剂 | `armor` | 装甲 |
| `book` | 书籍 | `can` | 罐头 | `consultation_carrier` | 资讯刊物 |
| `consumable` | 消耗品 | `craft` | 工艺品 | `drink` | 饮料 |
| `durability_consumable` | 耐久度消耗品 | `entertainment` | 消遣物 | `flintlock` | 燧发枪 |
| `food` | 食物 | `fragile` | 易损品 | `information_carrier` | 信息载体 |
| `medical_supply` | 医疗物资 | `medicine_kit` | 医药箱 | `placeholder` | 占位符 |
| `seasoning` | 调味品 | `shoes` | 鞋类 | `snack` | 零食 |
| `star_doll` | 星形玩偶 | `surgery_kit` | 手术包 | `tool` | 工具 |
| `walmart_bag` | 购物袋 | | | | |

> 例：`source=("物品","护甲", "armor")`、`source=("物品","工具","flintlock")`、`source=("物品","镇痛剂","anodyne")`。

## 5. 闸门目录（Gate Catalog）

> **本表是闸门的唯一目录**：新增闸门必须先登记在这里。聚合默认「任一为真即真」（OR）。
> 每个闸门**现有谁在注册**见 §5.4（迁移核对表）。

### 5.1 状态施加 / 可见

| gate 键 | path（功能 · 对象） | source 举例 | 查询点 / 函数 | 现行机制 |
| --- | --- | --- | --- | --- |
| `emotion.visible` ✅已迁 | `显示情绪` · 情绪键 | `("角色","混","情绪显现")`、`("角色","葱头","情绪显现-烦躁")`、`("伪人场景","洋葱","情绪显现")` | `engine.emotion_visible` → `_eval_gate` | **基础谓词**（强度>5 / 「情绪显现」全局事件 `emotion.reveal.<情绪>`）+ 闸门 provider（`chaos` / `onion` / `pseudo_onion`） |
| `emotion.apply.block` ✅已迁 | `施加` · 情绪键 | `("角色","…","敏锐直觉")`、`("物品","古老传说")`、`("角色","…","情绪显现-烦躁")` | `condition_system._emotion_application_blocked` → `_eval_gate` | **三层**：状态 `blocked_emotions`（通用基础）+ 闸门 provider + 结算点节点 `condition.irritation.settle`（概率/副作用型） |
| `status.apply.block` ⛔保留 | `施加` · `创伤`/`紊乱` | `("物品","护甲", tag)`、`("道具","高生命免疫")` | `condition_system._status_avoidance` | **非纯闸门**：`high_health_status_immunity` 扣充能、`armour.allows_status` 掷 25%×4 并扣 5 耐久 → 属**结算点**，见 §6 |
| `status.extra_effect.allowed` ⛔保留 | `额外效果` · `创伤`/`紊乱` | `("物品","镇痛剂","anodyne")` | `condition_system._condition_extra_effect_active` | **通用状态字段**（`suppresses_conditions` + hook，判定纯），与 `blocked_emotions` 同型 → 见 §6 |

### 5.2 伪人 / 目标 / 行动 / 信息（评估结论：**全部保留**）

> 这些查询点要么是**字段/全局事件**（本身就是闸门式状态，无需再包一层），要么**明确受保护**
> （见 §7）。即：**它们不是"待迁移项"，评估后维持现状。**

| gate 键 | path | source 举例 | 查询点 / 函数 | 现行机制 |
| --- | --- | --- | --- | --- |
| `pseudo.capability` | `伪人行为` · `visit/cast/breakthrough/auto_expel` | `("世界","世界牌")`、`("角色","白桃","正义执行")` | `_pseudo_capability(name)` / `_pseudo_actions_suppressed()` | 全局事件 `suppress.pseudo.<cap>` |
| `pseudo.in_house` ✅已实现 | `伪人` · `屋内` | `("伪人场景","薯条")` | `engine.pseudo_in_house()` | 纯查询：`infiltrator_id` 指向的房客须**在屋 + 存活 + `is_pseudo`**（`infiltrator_id` 在绑架时就写入，不能只判非空）。消费点：正义正位、信息生成/真伪、伪装表演、零三二九直觉概率 |
| `target.lock` | `抵御`/`锁定` · 技能事件 | `("角色","久孤","忍术")`、`("角色","堤谧特","默默无声")` | `_target_lock_responder` | `CHARACTER_NODE_HOOKS[char]["target_lock"]`（**只增量，见 §7**） |
| `search.resist` | `抵御` · `搜索` | `("物品","工具","flintlock")`、`("物品","工具", tag)` | `_search_resist_responder` | `ITEM_HOOKS[item]["search_resist"]`；**数值走 chance** |
| `action.allowed` | `行动` · `all`/`search` | `("状态",… )` | `tenant.action_lock(kind)` | `action_locks` 字段 |
| `information.verify.allowed` | `验证` · `信息` | `("全局事件","information.false_lock")` | `information_system._verify_information_object` | 全局事件直读（**锁定=反向**） |

### 5.3 待定闸门

| gate 键 | path | source 举例 | 现状 | 备注 |
| --- | --- | --- | --- | --- |
| `madness.active` | `癫狂` · `生效` | `("角色","混","情绪显现-清醒／癫狂")` | `NODE_HOOKS["madness.available"]`（`chaos.reason_madness_available`） | 即"混的『情绪显现-清醒/癫狂』被动是否生效"（癫狂的额外效果与超量转化为创伤/紊乱是否运行）。**是否 gate 化待定** |

### 5.4 现有注册方核对表（迁移时逐个照抄，一个不漏）

> 迁移某个 gate 之前，先把下面这些注册方**全部**改写（或先双读过渡），确认无遗漏。
> 完整机器可读版本见 §5.5 的 `tools/dump_effects.py`；下表是它对到目录后的归纳。

- **`emotion.visible`**
  - 内建（基础谓词）：`强度 > 5`
  - 「情绪显现」全局事件 `emotion.reveal.<情绪>`：`information_system` 的 `emotion_reveal` 信息被证实后写入
    （`emotion_reveal_event(info.subtype)`，世界级：该情绪对所有房客可见）
  - 全局事件 `emotion.reveal.<情绪>`：`伪人·洋葱`（`irritation`）
  - 角色 `EMOTION_VISIBLE`：`混`（理智/癫狂）、`葱头`（烦躁）
- **`emotion.apply.block`** ✅已迁
  - 纯闸门 provider：`澪叁贰玖`（`zero329._erosion_block_gate`）、`古老传说`（`information_carriers._legend_erosion_block_gate`）、
    `葱头·情绪显现-烦躁`（`onion._irritation_block_gate`）
  - 通用基础谓词：状态 `blocked_emotions` + hook（`calm_onion`「平静-洋葱」，blocked=`irritation`）
  - **结算点**（不迁，闸门是纯查询）：`葱头·平静` 的 30% + 获得共情印记 → 节点 `condition.irritation.settle`
    （原 `condition.erosion.block` / `condition.irritation.block` 两个节点已废弃）
- **`status.apply.block`** ⛔保留（结算点）
  - 高生命免疫：`effects.health_sanity.high_health_status_immunity`（生命≥95 每回合首次；a-10 常驻 99）——**扣充能**
  - 护甲：`tools_armor.armour_allows_status`——**掷 25%×4 且扣 5 耐久**
  - 二者都写状态 → 不属纯闸门，留在 `_status_avoidance`。
- **`status.extra_effect.allowed`** ⛔保留（通用状态字段）
  - `analgesia_trauma` / `analgesia_disorder`（`suppresses_conditions` + `analgesics._suppress`）；判定纯，
    但与 `blocked_emotions` 同型 → 当作**通用状态机制**，不另设 gate。
- **`pseudo.capability`**
  - `厄瑞玻斯`（世界牌：`_suppress_pseudo(5)`，`visit/cast/breakthrough/auto_expel` 全禁）
  - `青桃·正义执行`（`_suppress_pseudo(2, ("visit",))`）
- **`pseudo.in_house`**
  - `伪人·薯条`：`pseudo_state.infiltrator_id`（替身在屋）
- **`target.lock`**（抵御伪人主动能力；数值在 `chance` 通道）
  - `堤谧特·默默无声`：gate `demit.resists_pseudo_active` + 数值 `demit._demit_resist_modifier`
  - `久孤·忍术`：gate `jiugu.resists_pseudo_active` + 数值 `jiugu._jiugu_resist_modifier`（45%）
- **`search.resist`**（搜索遇袭抵御；数值在 `chance` 通道）
  - 物品（`ITEM_HOOKS["search_resist"]`）：`撬棍._resist_crowbar`(25%)、`运动鞋._resist_sports_shoes`(20%)、
    `燧发枪._resist_flintlock`(25%；弹药 `flat(+1.5)` → 95%)
  - 角色（`pseudo_search_resist`）：**`错潮·走你！`**`wrongwave.try_resist`
    —— 触发需消耗一个【饮料】或【罐头】；成功概率 70% 由 `chance` 提供（`wrongwave._wrongwave_resist_modifier`），
    成功还会顺延伪人到访。
- **`action.allowed`**
  - `path=("行动","search")`：`沙白`（`search_locked_until += 2`）
  - `path=("行动","all")`：`罗兹`（`skip_until_turn`）、`cost_system`（外部施加）
  - 另注：`tenant.shock` 也会挡搜索，属**状态闸门**，不在 `action_locks`。
- **`information.verify.allowed`**
  - `厄瑞玻斯` 太阳逆位（`information.false_lock` 3 回合）
- **`madness.active`**（待定）
  - `混`（`chaos.reason_madness_available`，「情绪显现-清醒／癫狂」）

### 5.5 全量注册表（自动生成，避免遗漏）

上表只归纳"会迁移的闸门"；**所有**注册方（含保留项与数值通道）以脚本为准：

```
python tools/dump_effects.py
```

它会列出：`NODE_HOOKS` / `CHARACTER_NODE_HOOKS` / `CHARACTER_VALUE_HOOKS` / `ITEM_HOOKS` /
角色 `EMOTION_VISIBLE` / 带 `blocked_emotions`·`suppresses_conditions` 的状态定义 /
`MODIFIER_PROVIDERS`·`MODIFIER_REGISTRY` / 伪人场景 `HANDLERS`。**只读、不改状态。**

内容增长后跑一遍，逐项对到 §5 的闸门或下面 §6 的保留项；对不上的就是新增项，必须归类。

## 6. 明确**不做** gate（保留为技能/物品独有效果）

> 目标：`tools/dump_effects.py` 里的每一项，要么在 §5 有归属，要么在这里有归属。**不留未归类项。**

### 6.1 数值型保护 / 转换（与技能强绑定，抽 gate 无意义）

- `_health_protection_multiplier`（性格「分担」）、`_apply_armour`（护甲减伤，`armour.apply`）
- `NODE_HOOKS["sanity.floor"]`（青桃·持之以缓）、`health.transfer_receivers`（稳重·分担）
- `value.health_consume.convert` / `value.sanity_consume.convert`（厄瑞玻斯·倒吊人）
- `value.health_consume.multiplier`（厄瑞玻斯·高塔）

### 6.2 布尔但按裁定**保留现状**（不迁移）

- `breakthrough.guard`（青桃·正义执行，阻止突破）
- `item.use_wasted`（多疑 10% 浪费）
- **`status.apply.block`**（`high_health_status_immunity` 扣充能、`armour.allows_status` 掷骰并扣耐久）
  —— 结算点副作用，非纯查询
- **`status.extra_effect.allowed`**（`suppresses_conditions` + hook）—— 与 `blocked_emotions` 同型的
  **通用状态字段机制**
- **`pseudo.capability`** / **`action.allowed`** / **`information.verify.allowed`** / **`pseudo.in_house`**
  —— 已是**全局事件 / 字段**形态的闸门式机制，无需再包一层（见 §5.2）
- **`target.lock`** / **`search.resist`** —— 现有 hook 即闸门，且**受保护**（见 §7）
- `personality.lock`（混·纯真的自我）、`madness.convert_excess`（混·癫狂超量转化）
- `visitor.accept_healing` / `visitor.extra_interval` / `visitor.supply`（温和羁绊）
- `item.fragility_delta`（机敏）、`loot.quality_weights`（机敏）——数值
- `personality.weights`（混·锁定权重）、`end_turn.sanity_modifier`（混）——数值

### 6.3 内容映射（本就不是闸门）

- `analgesic.duration` / `analgesic.status_id`（镇痛剂 → 持续时间 / 对应状态 id）

### 6.4 触发 / 通知型（事件，不是"调整布尔"）

- `on_arrival`（薯条/罗丁/ED Tear 入住）、`legend.turn_start`（古老传说）
- `information.verified`（薯条）、`sanity.lost`（伪人·洋葱）、`sanity.after_decrease`（混）
- `pseudo.tenant_replaced`（澪叁贰玖对替身顶替的响应）、`pseudo_visit`（澪叁贰玖）
- `search.reward`（信息载体/角色保底）、`search.return.rest`（沙白）、`search.parameters.reset`（急躁）、
  `search.carry_override`（混）、`search.pool_weight`（比格小星）、`search.start.bond`（固执）
- 物品回合钩子：`bls_book/plants_book/disaster_book/nebula_legend` 的 `turn_end.held`、
  `walkman` `turn_start.backpack`/`turn_end.held`、`gramophone`/`smartphone` `turn_start.house`、
  `mcdangdang` `turn_start.status_effects`、食材调味 `after_food` 等

## 7. 目标选择流程：保持不动

`pseudo_system` 的"技能选择目标 / 锁定 / 抵御"（`_target_lock_responder`、`_search_resist_responder`、
`_skill_respond_skill`）流程设计良好，**不重构**。闸门化只做**增量**：

- 保留现有函数签名与调用顺序；
- 新增一个 gate 查询作为**附加判定**，现有 hook 仍可注册（双读过渡）；
- 数值（25% / 45% 等）继续留在 `chance` 通道。

## 8. 落地阶段与自检

- **P1 内核 ✅ 已完成**：`modifier_rules` 增加 gate 支持（`GATE_REGISTRY`/`GATE_PROVIDERS`、
  `collect_gates`、`evaluate_gate`），`marks_system` 加 `engine._eval_gate`。**不碰内容**。
- **P2 首迁 ✅ 已完成**：`emotion.visible` 迁移——引擎只留**基础谓词**（强度>5 / 「情绪显现」全局事件）
  + `_eval_gate`；`chaos` / `onion` / `pseudo_onion` 改为注册 **gate provider**（`EMOTION_VISIBLE`
  已删除）。全测试通过，行为等价。
- **P3 首轮迁移 ✅ 已完成**：`emotion.apply.block` 迁移（三层拆分，见 §5.4）。
  其余原目录项经**纯度/对称性评估**后判定为**保留**（§5.2 / §6.2）：
  `status.apply.block`（结算点副作用）、`status.extra_effect.allowed`（通用状态字段）、
  `pseudo.capability`/`action.allowed`/`information.verify.allowed`（已是状态/事件闸门）、
  `target.lock`/`search.resist`（受保护）。
  → **可干净迁移的声明式闸门已迁完**；后续若新增"内容声明的纯查询免疫/许可"，按 §5 登记即可。
- **P4 文档**：更新 `AGENTS.md §3.6`（"闸门不是通道" → "**闸门与通道共用 path/source；分用逻辑/算术**"），
  并把 `GUIDE.md` 的注册表清单补上 gate。

**每一步都要跑**：`compileall` → 单测 → `audit_separation` → `validate_content` → 冒烟。

## 9. 待定 / 开放问题

1. ~~`pseudo.in_house` 的用途~~ **已落地**：作为纯查询 `engine.pseudo_in_house()`，用于"驱逐/指认/处理**屋内**伪人"的判定（正义、信息生成、伪装表演、零三二九）。
2. `madness.active` 是否真的做成 gate，还是保留 `NODE_HOOKS`。
3. ~~闸门的 veto 语义~~ **已实现**：`gate(...).veto()` 提供"强制假（NOT）"，聚合为「先 OR 后否决」，
   与顺序无关。是否需要更细的**优先级 / 强制开启**（over-override）待定。
4. 令牌词表是否需要"层级"（父对象/子对象），例如 `情绪` vs 具体情绪键。

# 决策与修正记录

> `AGENTS.md` 只保留"现状速览"；**具体到某次为何这么改、当时踩了什么坑**记在这里。
> 目的：不把入口文档撑成流水账，又不丢上下文。要加新条目就追加在顶部。

## 「纯真的自我」补完：玩家发动 + 自选性格（顺带暴露"入口缺失"这一类 bug）

**玩家报告**：存档里混已经 13 层清醒，纯真的自我仍然触发不了。

**根因（不是机制写错，是够不着）**：旧实现把它做成**只有终端 CLI 有的指令**
（`system.lock_personality` + `cli.py` 的 `lock`），`web_ui.py` 与 `index.html` **零入口**；
而且**零测试**。上一轮已把它改成内容层私有机制，但这轮按作者要求补完语义：

**语义（作者定）**：稿写「清醒 ≥10 层时可以**固定**主副性格」，实际要的是**自选**，而且——
    1. **回合初自动弹**（不是玩家点技能），够 10 层就问；
    2. **复用 discover 那套待选卡片**：第一次 **8 选 1** 选主性格、第二次 **7 选 1** 选副性格
       （`engine.discover(keys, count=len(keys))` 挂 `_pending_choice`，`_pending_resume` 接回内容）；
    3. **一旦确定不可逆**：`pure_self` 是 `permanent` 状态，清醒掉回 0 也不退回混沌。
    中间步骤记在内容状态 `pure_self_picking.layers`（1/2），主性格暂存在 `tenant.personalities`；
    **自选期间随机切换暂停**。

   > 我第一次做成了「主动技 + `PENDING_VIEW` 两步选择」——**方向错了**：作者记得的界面就是
   > discover 那套（后端 `web_ui` 里本来就有 `kind:"personality"` 的选项投影与 `i-b-*` 图标），
   > 且应该是**回合初自动**而不是玩家点技能。

**顺带修掉的入口缺口**：`cli.py` **从来没有处理过 `_pending_choice`**（连开局的 discover 选人都走不下去，
只有冒烟脚本自己 `choose_discover`）。已补一个通用的 `_resolve_pending_choice`，两条前端从此同槽。

**这一类 bug 的共性与对策（值得记住）**：

- **"机制存在 ≠ 玩家够得着"**：能力/门控/实现都对，缺的是入口。同类隐患还有
  `ABILITY_INTERACTIONS`（注册了但**没有任何消费方**）与厄瑞玻斯的终端路径。
- **判据**：新增机制先问「**触发点在哪**」；若答案只能是"某个前端点一下"，先怀疑它该由
  **节点/事件**触发。这次是"玩家主动技 + 声明式视图"，所以两端都要接。
- **便宜的自检**：`tools/dump_core.py --refs` 已经能给"只被 `cli.*` 引用 / 只被 `web_ui.*` 引用"
  的差集——把它当信号读，这类 bug 会自己浮出来。

**验证**：探针走通——回合初（`_settle_tenant_instance_start`）自动挂待选 8 项
（`build_state` 里是 `kind:"personality"` 的性格卡片）→ 选 1 → 再挂 7 项 → 选 1 →
`personalities` 落定、`pure_self` 99、`chaos_carry` 99、待选清空；把清醒打回 0 再跑回合初，
**不再问、也不回退**。回归用例钉住"<10 层不问 / 8→7 两步 / 不可逆"；单测 75 项、四个审计、
冒烟全绿；设计稿「附录 A」已同步（含删掉 `_apply_chance` 那条）。记账见 `docs/BALANCE.md`。

## 引用面盘点（第四轮）：`EngineProtocol` 从 24 条补齐到 81 条，并做成机检

**做法**：给 `tools/dump_core.py` 加了 `--refs`：**AST 扫描**运行时（`weiren_game/` + `dlc/`），
把每个核心符号的引用**按调用者方法名**列出（`模块.类.方法`，不含行号），并区分同文件/跨文件；
>5 个调用者只记数。`tests/` 与 `tools/` **不算引用**（不参与游戏运行），只被它们引用的单独标注。

**为什么换掉正则**：原来逐行扫，**注释、docstring、`lang.py` 的点分键**（`"…_decrement_inventory.1"`）
都会被当成"有人用"。换成 AST 后这些天然排除，于是又掉出 7 个真死：
`information_system.verify_information`、`item_system._decrement_inventory`、`random_system._loot_draw`、
`search_system.apply_search_modifier`、`dlc.reload_dlc`/`load_dlc`/`load_dlcs`（测试同步改）。
**还修了一个真 bug**：`from x import 名字 as 别名` 只记了别名、漏了原名（`register_container_type` 被误判为 0 引用）。

**最大的一块**：`EngineProtocol`（"内容能碰什么引擎 API"的权威）只声明了 **24** 个方法，
而实测内容面有 **81** 个。已按实测重写（签名由 AST 生成），并删掉内容从未调用的 3 个
（`_mark_ability_used` / `_record_log` / `_show_message`）。**协议与实测面双向差集现在为 0**，
且 `--refs` 每次都会重算这个差集（`## EngineProtocol vs 实测内容面`），协议再漂移会立刻看见。

**我上一条判断错的地方（记下来以免再犯）**：我曾把 `_clear_pending_choice` / `_record_action` /
`_collect_start|flush` 列为"内容越界"。细看后**都不该收敛**：
前者是命运牌取消待选的**合法逃生口**（引擎不可能认识命运牌），后两者就是内容层该用的日志 API。
所以处理方式是**写进协议并说明用途**，而不是把内容的手脚捆住。

**未做（留档）**：`_Spec` / `_GateSpec` 的链式方法名（`path`/`id`/`match`/`flat`/`max`/`min`/`any`/`certain`）
与字段名到处撞，是这张表噪声的主要来源；改名（`path`→`where`、`id`→`key`、`match`→`mode`…）是一次性
机械替换，能让后续盘点不用再人工剔除噪声——**尚未做**。

**验证**：`compileall` / 74 单测 / 四个审计 / `validate_content` / 冒烟 3 seeds 全绿；
`docs/CORE_REFS.md` 重生成（627 项；1–5 个调用者 411、>5 个 201、0 个 15）。

## 第二轮核心瘦身：四处「专属 / 兼容」逻辑搬出核心

作者逐个核对了 `docs/CORE.md` 的方法清单，指出若干方法泛用性不足。本轮按
「公共路径只该为多处共用而建」改掉：

| 之前（在核心） | 现在（在内容层 / 通用机制） |
| --- | --- |
| `item_system._use_analgesic` + `use_item` 里的 `"anodyne" in item.tags` 分支 | `data/tags/anodyne.py::use`；核心只写 `_item_tag_fn(item, "use")` |
| `item_system._item_tag_use` / `_item_tag_after_food` | 合并为一个 `_item_tag_fn(item, 钩子名)`——核心不再枚举钩子名 |
| `ability_system._ability_has_local_cost` | 删掉；`chaos` 自己用 `engine._local_skill_module(...)` 查 `costs_<id>` |
| `SCENARIO_HANDLERS["ability_fail_modifier"]`（只为薯条存在） | 通用通道 `abilityFail`（内容写 `spec("abilityFail").path("ability_fail")`） |
| `SCENARIO_HANDLERS["ability_fail_resolved"]`（只为薯条存在） | 通用节点 `ability.resolved` |
| `round_effects._settle_books_and_equipment`（名字像内容） | 改名 `_settle_held_items`；派发本来就按 `ITEM_HOOKS[item_id]`（内容登记） |
| `personality_system.lock_personality`（玩家指令，只为混存在） | 删掉；改名 `chaos.pure_ego_personality`，走**回合初·实例·房客**路径（`TURN_START`）自动判定 |

**没动的一处**：`item_system._durability_multiplier` 看着像专属，其实只是读**全局事件**
`item.durability.multiplier` 的通用访问器——任何内容都能设置那个事件，保留。

### 这次新立的两条命名 / 合并判据（作者提出）

1. **"看起来泛用"是陷阱**：过往只把**明显私有**的方法搬了出去，但长期创作里，私有方法常因疏忽
   起了个通用名字（`lock_personality` 就是——它只服务混）。判据：**这个方法除了某一个角色/场景，
   还有谁会调？** 没有 → 名字要写成它自己的（`pure_ego_personality` 这种），并走既有的
   `lifecycle` 节点路径（本例走回合初·实例·房客），**不要留在核心当公共动作**。
2. **合并要看"容纳关系"**：公共方法之间若有"甲 ⊂ 乙"的关系，就该只留乙、让甲退回内容层。
   典型例：使用镇痛剂 ⊂ 使用物品（已改成 tag 的 `use`）、食用食物后 ⊂ 食物 tag 自己的方法。
   **判断入口就是 `weiren_game/lifecycle.py`**：属于既有节点的一律走节点，别新造公共方法。

**副作用**：`use_item` 的分支从「医疗 / 镇痛 / 通用」三条压成「有 tag 行为就用它，否则通用」；
tag `use` 的签名多了可选 `condition=None`（医药不需要、镇痛剂需要），已同步
`docs/ADD_CONTENT.md` 与 `.opencode/skills/weiren-new-item`。

**验证**：探针证明镇痛剂 tag 行为真的落地（状态 `analgesia_trauma (1, 10)`）、薯条失败修正
`0.25`（普通角色 `0.0`）、`ability.resolved` 已订阅；`compileall` / 74 单测 / 四个审计 /
冒烟 3 seeds 全绿；`docs/CORE.md` 重生成：735 → **732** 项、扩展点 54 → **51**、
核心内容 id 引用仍是 **0**。

### 第三轮：按「单语句转发」与「同形重复」继续合并

作者要求"能合并的尽量合并"。扫了两类：

**① 纯转发（一个函数只是换个名字再调另一个）→ 删掉，调用点直接调目标**：
`_ability_state`（死代码）、`_reduce_condition`（死代码）、`_take_tenant_item`、`_house_count`、
`_spend_role_mark`、`_create_visit_information`、`_now_iso`。

**② 同形重复 → 合成一个循环**：`dlc.py` 里 9 个 `load_*_dir` 结构完全一样
（glob 目录 → 逐文件交给 loader → 收集文件名），合成一个 `_load_dir(dlc_dir, subdir, loader, pattern=…, replace=…)`，
`load_single_dlc` 里直接调用它（顺序不变 = 注册顺序不变）。

**刻意没合并的**（同形但语义不同，合了反而更差，附理由）：
`session.InstancePool.allocate_*`（6 个按实体类型的分配器）、`content.py` 的注册表访问器、
`modifier_rules._Spec/_GateSpec` 的链式构件、`tenant` 的属性访问器——它们是**类型化的 API**，
合成 `allocate("tenant")` / `get(key)` 会丢掉类型与可读性；
`_emotion_weighted_key`（内含加权公式）、`_mission_rng`（从任务对象推导随机源参数）、
`_settle_turn_end_status_effects`（给 lifecycle 绑定节点名）、`full_log_text`（测试用的公开导出）、
`_loss_sanity` / `_consume_sanity` 等（`EngineProtocol` 的内容 API）同理保留。

**验证**：74 单测 + 审计 + 冒烟全绿；DLC 双包实跑一局正常；`docs/CORE.md`：732 → **714 项**。

## 罕见的专属机制不该进核心：`sanity_overflow_share` 后门拆掉

**作者指出**：`value_system._restore_sanity` 里出现了「星星」，怀疑把「溢出量的一半」这种
很少用到的机制塞进了主程序。核对结果——**一半对**：

- `bigstar` 的 100% 转星之印记走的是 `CHARACTER_VALUE_HOOKS`（**通用**的角色值钩子，行为在内容层）；
- 但伪人薯条的「溢出 50% 转暴露值」走的是核心里的
  `SCENARIO_HANDLERS[场景].get("sanity_overflow_share")` ——**核心按名字点名一个专属机制**，属实是后门。

**改法（作者的判断：罕见方法当个体专属，重复也无妨）**：核心**只发通用节点**，不再有任何专属入口：

```python
self._emit_node("sanity.restored", tenant=tenant, overflow=overflow)
tenant_hook = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get("sanity.restored")
if tenant_hook is not None:
    tenant_hook(self, tenant=tenant, overflow=overflow)
```

两边各自订阅同一节点：`bigstar`（角色作用域，100%）与 `pseudo_fries`（全局，50%）。
核心从此不知道"溢出该怎么用"。顺带把核心 docstring 里的内容名（「星星」「驭血魔化印记」）改成通用措辞
——`audit_separation` 只查注册名，这种"例子式"的内容名它抓不到。

**这条与 `docs/PRINCIPLES.md` §二.2 的关系**：那条讲"通用规则要删特例、留一条公共路径"；
这次补的是它的边界——**公共路径只该为"多处共用"而建**。只服务一个角色/场景的罕见机制，
就留在它自己的文件里（重复几遍没关系），核心最多提供一个**通用事件**。

**验证**：订阅核对（全局 `pseudo_fries.on_sanity_restored`、角色 `bigstar.collect_star_overflow`）；
探针证明一次溢出同时触发两个派发（`('global', 20.0), ('tenant', 20.0)`）；
`compileall` / 74 单测 / 审计 / 冒烟 4 seeds 全绿。

## 匹配令牌英文化：`path` / `source` 与调用点 `source` 全部改英文

**背景（作者指出）**：程序标识不该用中文。原先 `docs/ARCH.md` §4 是一份**中文令牌词表**，
于是 `spec(...).path("回合末消耗").source("角色技能", "ED Tear", "我不能没有购物袋")` 这种写法到处都是。

**做法**：一次性 AST 脚本，只改**令牌位置**的中文：
① 提供方 `path(...)` / `source(...)` 的参数（含 `source = (...)` 变量元组）；
② 调用点 `_apply_modifiers` / `_apply_chance` / `_eval_gate` 的 source 元组，
以及 `value_system` 那组 `_damage_*` / `_consume_*` / `_loss_*` / `_restore_*` 的第 3 个参数。
**专名一律映射到既有 id**（苯环→`benzene`、薯条→`fries`、沃尔玛购物袋→`walmart_bag`、
走你→`there_you_go`、女祭司→`priestess`、星云传说→`nebula_legend`…），其余见 `docs/ARCH.md` §4。

**关键耦合**：调用点的 `source` **同时是日志用词**（模板 `X因{source}{change_type}…理智`）。
所以拆成两层——代码里是英文令牌，日志走 `lang.source_label(令牌)` / `token_label(令牌)`，
文案住 `TEXT["source.<令牌>"]` / `TEXT["token.<令牌>"]`。`change_type` 同理
（`consume`/`damage`/`loss`/`restore`，通道映射表随之改英文键）。

**踩到的坑**：单测 `test_difficulty_start` 当场抓到一处不匹配（测试里还写着 `("开局","时运")`）——
正是"两边令牌不一致会**静默失效**"的典型。另有两个漏网（`走你` 没进映射表、DLC 的新词 `角色被动`），
补表重跑后归零。`tools/`、`tests/` 里的令牌也一并更新了。

**验证**：令牌位置**中文残留 0**（`weiren_game` 与 `dlc` 各扫一遍）；`compileall` / 74 单测 /
`audit_separation` / `audit_text`（error 0）/ `validate_content` / 冒烟 4 seeds 全绿；
冒烟日志**无令牌泄漏**（`因damage…` 之类）；无头对局正常。

## lang 全量迁移完成：base + 每个 DLC 的文字都住 lang 表

**做法**：写一次性迁移脚本（AST 扫 Python、状态机扫 `index.html` 的 JS/标记；脚本留临时目录、不进仓库），
只认**明确的展示位**：

- 内容构造器的展示字段（`A` / `I` / `L` / `CharacterDefinition` / `PseudoDefinition` /
  `InformationTemplate` / `MarkDefinition` / `MapDefinition` / `FateCard` / `StatusDefinition` / …）；
- 模块级文字表（`codex_*` / `labels` / `flavor` / `information_text` / `data/__init__` 的标签表）；
- **除 docstring 与数据键位置外的所有汉字字面量**；
- 前端：JS 字面量与模板串里的中文片段、静态标记文本与 `placeholder/title/aria-label`。

数据键（`spec/path/source`、`option/tag/key/resource/…` 参数、dict 键）**一律不碰**——参与规则命中，
禁止翻译。**匹配键留在原地是对的**（`tools/dump_text.py` 的 scan 会告诉你还剩哪些，都是这一类）。

**规模**：base `weiren_game/data/lang.py` **2487 键**；每个 DLC 一份（STAR 89 / likai_test 12 /
_template 5）；前端 chrome `ui.js.*` + `ui.markup.*` 约 300 条。迁移点合计约 **2400 处**。

**键名**：内容层用**既有 id**（`ability.<id>.desc` / `character.<id>.name` / `item.<id>.name`）——
语义、稳定、随定义走。系统层与前端是**按位置自动生成**的（`<模块>.<函数>.<n>`、`ui.js.<n>`、
`ui.markup.<n>`），**不是手写语义键**：这是为了在一次会话里覆盖全部文字而做的取舍。
**改名很便宜**（引用已集中在表里，改一处即可），日后再逐步语义化。

**DLC**：`dlc/<包>/lang.py`；包自己的模块写 `TEXT = pack_text_from_file(__file__)`
（`weiren_game/data/lang.py` 提供，按包目录缓存）。DLC 是按文件路径加载的（父包不存在），
所以不能用相对 import。**不做回退链、不做语言切换**（作者已定）。

**有意没做**：① **没统一漂移用词**（`损失/扣除/失去`、`数字%概率`）——有些"漂移"其实是不同语义
（作者指出），要逐条判断，工具只负责列出来；② 匹配键、docstring、`tools/`、`tests/` 自己的中文不动。

**踩到的坑（都已验证修掉）**：

- **前端 helper 不能叫 `t`**：页面里大量 `const t = STATE.tenants.find(...)`（租客）会**遮住**全局 helper，
  运行时报 `TypeError: t is not a function`（无头对局一跑就抓到 41 条）。改名为 `TXT` 后归零。
- **Python 3.11 的 f-string `format_spec` 位置不可靠**：`ast.get_source_segment` 可能返回整条 f-string，
  把 `{lost:.1f}` 拼坏。改成**从 spec 的常量段重建**。
- **f-string 表达式里的子字面量不能单独替换**：`f"{x or '数量'}"` 里的 `'数量'` 换成 `TEXT["…"]`
  会因引号冲突变成语法错误；改为「整条 f-string 一起处理，或跳过子字面量」。
- **HTML 标记里文本节点与属性重叠**：同一标签既有中文文本又有中文 `title` 时，两处替换会互相覆盖
  （`intelCount` 那行被拼坏）。改为**互斥处理 + 手工收尾**。

**验证**：`compileall` / 74 单测 / `audit_separation` / `audit_text`（error 0）/ `validate_content` /
冒烟 3 seeds 全绿；`dump_text` 复查（重复组 23 → 18）；**无头 CDP 对局 2 局 × 12 回合，JS 报错 0**；
启动器截图肉眼确认文字渲染正常（无 key 泄漏）。

## lang 定型：不做可插拔、每包一个公共 lang 文件；术语与概率写法同步固化

**术语规范（作者定）**

- **数值变化**：**消耗 / 流失 / 伤害 / 回复 是已定义的四种**，各管各的语义、不能互相替换；
  `减少` **没有定义过**，是代表 消耗/流失/伤害 的**泛称**（泛指时才用）；`损失 / 扣除 / 失去`
  是漂移，应改齐上面四个。
- **概率写法**：**`数字%可能`**（`25%可能xxxx`）是唯一格式；`数字%概率` 是要改的漂移。

两条都写进 `tools/dump_text.py` **现算**（实测：`数字%概率` 18 处、`损失/扣除/失去` 17 处、
`数字%可能` 已合规 23 处），不再靠记性。

**lang 方案（作者定，取代本文件上方 `docs/ROADMAP.md` §7 原先的"有序语言包 + 回退链"）**

- **不做可插拔语言包**：一个包（base = `weiren_game/data/`；每个 DLC = 它自己）带**一个公共 lang
  文件**，面向玩家的文字全放里面；源码里**不再写字面量**，一律引用 lang 条目。
- 形状：**扁平字典 + 语义键**，`TEXT["<模块>.<语义>"]`。模板写 `{名字}`，调用处 `.format(...)`；
  内容层的键用**既有 id** 拼（`ability.<id>.desc`），随定义走。
- **前端 chrome 也收进后端**：`GET /api/lang` 下发，`index.html` 用 `t(key)` 取字；静态标记
  `data-t` / `data-t-html` / `data-t-ph` / `data-t-aria`，`applyStaticText()` 在 boot 里跑。
- **数据键不搬**（`path` / `source` / tag / 性别 / 年龄 / 兴趣）——它们参与规则命中，禁止翻译。
- lang 表住**内容层**（`data/lang.py`）所以分离度自检仍全绿：系统层只出现 key，不出现内容名。

**已落地（本批，作为样板）**：`data/lang.py` + `/api/lang` + 前端取字机制；
`systems/cost_system.py`（同一 key 顺手消掉两处重复报错）与启动器 chrome 已迁。
无头 CDP 对局验证：启动器 → 创建对局 → 打到第 8 回合，JS 报错 0。余下按
系统层 → 内容层 → 前端 chrome → DLC 分批迁（见 `docs/ROADMAP.md` §7）。

## 文本盘点工具落地：`tools/dump_text.py`（并纠正「语料 990」这个错数）

**做了什么**：把上一轮两个一次性探针（查重、术语扫描）合成一个**只读**工具，叠在同一份语料上：
① 底表（来源文件 / 行号 / 文本 / 汉字数 → `text_table.tsv`，lang 的"搬运清单"）；
② 查重（占位符归一化后完全相同）；③ 术语一致性（词族计数 + 少数派**逐处列出原句**，
另附粗粒度风格指标）。词族**登记在工具里、不抄进 `docs/STYLE.md`**（STYLE 只留"一个概念一个词"，
避免清单和代码漂移），次数一律现算。退出码恒为 0：它是盘点，不是闸门。

**纠错**：上一轮把语料记成 **990**，实际是 **2990** —— 终端乱码把全角冒号后的 `2` 一并吃掉
（`语料：2990` 显示成 `语料：990`），照着屏上的数字抄就错了。`docs/ROADMAP.md` 已改回 2990，
并在 `AGENTS.md` §7 记下"计数读 UTF-8 产物文件、别读屏"。

**没做成"自动发现词族"**：试过用 n-gram 找"多数派加一个字"（`理智` → `理智值`）。
不加限定会得到几千对垃圾 —— `房客` 后面跟任何字都成了候选（跨词相邻）；限定"只在右侧加字 +
少数派跨 ≥2 个文件"后仍有 805 对。**没有分词就没有词边界**，所以放弃自动发现：
词族人工登记、计数机器现算，工具只盘点、不做判据（判据在 `docs/ROADMAP.md` §7「少数派才是漂移」）。

**验证**：工具复现了上一轮记录的全部数字（成句文本 2017 条 / 重复组 23 组；理智 217 / 理智值 10、
生命 203 / 生命值 19、损失 10 / 失去 4 / 扣除 3），口径对齐后才改的文档。

## 「导出的游戏记录不从第 1 回合开始」= 旧档缺字段，不是截断

**现象（玩家报告）**：存档界面导出的完整日志不是从第 1 回合开始。

**查证（读玩家存档得出）**：`saves/a10.json` 的 `log` 里**只有** `history / current_turn_actions / action_log`
——**没有 `entries` 字段**（消息日志）。而 `meta.version` 仍是 `2.1.0`，所以版本校验拦不住它。
`SessionLogState.entries` 是"完整对局日志（含未公开记录）：**随存档持久化**"这句注释所指的**后加字段**。
旧档从没把历史消息写进文件，读档后自然不可能恢复——**不是回溯截断**（那条路早就处理过：
`rewind_one_turn` 里显式保留 `log.entries`，注释写着"完整日志是单调历史"）。

**现状（已实测）**：同一个引擎新存的档**包含** `entries`（存一份 73 条），重载后 `export_full_log()`
从第 0/1 回合起完整输出。所以**新档没问题**，只有旧档缺。

**可选改进（未做）**：

1. 存档页/导出时对缺 `entries` 键的档给一句提示（判据就是"`log` 里没有 `entries`"），
   而不是让玩家以为日志被吞了。
2. 字段变更（`SessionLogState` 加 `entries`）**没有跟着改版本号**，`SaveMetadata.version` 仍是 `2.1.0`——
   将来再改存档结构时，要么升版本、要么在 `from_dict` 里做字段级迁移。

## 待做：把 AOE 折叠**统一到 log 层**（按形状归并，技能侧零代码）

**问题**：给"成批结算"做折叠（一条汇总 + 可点开的三列明细）时，我连着给三个技能**手写了 rows**：
薯条「炼狱扳机」（`pseudo_fries.infernal_trigger`）、洋葱「不可名状的低语」（`pseudo_onion.cast_whisper`）、
苯「希波克拉底诅咒」（`pseudo_benzene.cast_curse`）。这违反 `docs/PRINCIPLES.md` §二.2
（**普适规则要删特例、留一条公共路径**）——技能里出现 `rows.append` 就是信号：信息本该在更低的层产生。

**正解（玩家提出的方向）**：**在 log 层按"形状"归并**，而不是让每个技能自己组装明细。
理由：那些行的格式本来就受 `docs/STYLE.md` §11 约束，**形状是稳定的**，解析它们不需要认识任何内容。

**形状表**（系统层，`weiren_game/` 下新模块或 `engine` 内私有函数；**只认形状，不认内容名**）：

```
X因{source}流失{N}生命。      → 谁=X 多少=−N 生命  为什么=source
X因{source}消耗{N}理智。      → 谁=X 多少=−N 理智  为什么=source
X因{source}受到{N}生命伤害。  → 同上（生命）
X获得{N}层{状态}。           → 谁=X 多少=+N {状态} 为什么=source
…（把值层现有那几条 emit 的形状逐个登记）
```

**接法**：`_collect_flush()`（无 `rows` 时）→ 对收集到的每一行**按表匹配** →
命中的变成结构化明细行、**没命中的保持原文**（向后兼容，且内容层自己 `_log` 的自由文本不会丢）。
于是技能侧只剩"把这一段包起来并起个标题"：

```python
with engine._batch("不可名状的低语"):
    ...原有循环...
```

**落地三步**（都不大，按序做）：

1. `engine`：形状表 + `_collect_flush` 无 rows 时自动归并（含"没命中就回退原文"）。
2. 三个技能：删掉各自的 `rows.append`，只留标题（**净删代码**）。
3. 回归：探针跑三处 AOE，确认汇总条数/明细行数/未命中回退都对；`test_architecture` 与 `audit_text` 全绿。

**顺带**：DLC 的星云伪人（`pseudos/pseudo_STAR.py`）里也有多次判定/群攻，统一之后**自动受益**，
不需要再写第三份 rows 代码——这正是这条重构的价值。

## 休克不该被"回血"顺手解除：删掉一条没登记的规则

**现象（玩家报告）**：生命回到 5 以上，休克就消失了。

**查证**：`codex_mechanics.py`「休克」一节的四条里**没有**"自动解除"；而 `value_system._restore_health`
里写着 `if tenant.health > 0: shock = 0` —— 一条只存在于代码里的额外规则。它让休克形同虚设
（4 级休克在回合末有 25%×4 的死亡概率，但玩家只要回一次血就抹掉了）。

**做法**：删掉自动解除；休克只由明确写出的规则解除（现存唯一一处：厄瑞玻斯「死神·正位」的"移除全部状态"）。

**平衡账**：`docs/BALANCE.md`「全角色（通用规则）· 2026-09-18」。

**同类排查用的判据**：机制文档里没写的"顺手效果"，一律当 bug 处理——引擎不该替玩家和作者做没声明的决定
（同一天还处理了 `mdText` 的"引号强制换行"、`.tip-layer b{display:flex}` 这类没登记的行为）。

## 待修：替身被"当普通人驱逐"会留下悬空状态（复现到了，但袋子重复还没复现）

**玩家报告**：罗丁带购物袋搜索 → 被薯条替身顶替 → 柳七鱼驱逐 → 替身的购物袋"爆出来" + 真罗丁归来后又有一个 →
疑似**物资重复**；拖动那件物资还会报「该格没有这个物资」。

**复现脚本**：`%TEMP%\opencode\probe_fries_dupe.py`（造人 → 给袋 → 出发搜索 → `capture_searcher` → 跑 `end_turn` → 驱逐）。

**已确证（有日志与计数）**：若驱逐时 `tenant.is_pseudo` 还是 `False`，`_expel_tenant` 会走**普通驱逐分支**
（日志是「柳七鱼驱逐了**罗丁**」而不是「驱逐了**替身**；被绑架的罗丁**归来**」），于是：

- `pseudo.infiltrator_id` 与 `mission.captured` **继续挂着**（悬空状态）；
- 被绑架者**没有归位**，而替身被当普通人处理（`_remove_tenant_from_house`）。

→ **该修**：`_expel_tenant` 的分支判据不该只看 `is_pseudo`，还应认 `pseudo.infiltrator_id == tenant.id`
（替身身份是在**搜索返程**才打上的，任何一个分支漏掉都会留下悬空状态）。

**还没复现**：袋子变成两份。三次尝试（袋子在搜索前给 / 手动跑返回 / 跑回合循环）计数都是 1 份，
**前后端也一致**（除上面那次悬空驱逐时前端显示身上=0、后端对象还在）。要继续，先问清三件事：
① 袋子是**搜索前**给的还是**他被顶替之后**才给的；② "爆出来"是**仓库真多一件**还是只是播报；
③ "真罗丁回来"是**直接出现在屋里**（重建归位）还是**门外来的访客要接纳**（`returning_visit`）。

## 情绪「理智」改名「清醒」：术语撞名的源头治理

**起因**：玩家报告"混在拥有理智的情况下，还是无法解锁纯真的自我"。

**查证**：解锁判据是 `tenant.reason.layers >= 10` —— `reason` 是**情绪「理智」**（觉醒情绪，有强度/层数），
而玩家（和我）都把它读成了**理智值**（`tenant.sanity`，0~100 的数值）。两者毫无关系：
理智值 5 也能满足、理智值 90 也不满足。

**做法**：

- 显示名 理智 → **清醒**（`EmotionDefinition.label`，会自动流向 `AWAKENING_EMOTIONS`，所以日志/界面/图鉴一起变）；
  **内部 id 保持 `reason`** —— 存档里的 condition 键与代码引用都指着它，改名会断老存档。
- 所有面向玩家的文本改口径（技能名「情绪显现-清醒／癫狂」、技能正文、CLI 说明、违反条件时的报错）。
- 太极图（`DETAIL_SLOT`）未解锁时直接显示**进度**：「清醒情绪 N/10 层可固定方向与速度。」

**教训**：同一份文档里出现"理智值"和"理智情绪"两个东西时，**必须给其中一个换名字**；
光靠注释解释挡不住误解（玩家看的是界面）。

**平衡账**：`docs/BALANCE.md`「混 · 2026-09-18」（按玩家要求，改名也按平衡改动记账）。

## 图鉴 / 技能正文的排版 pass（规则 → `STYLE §12`，先做 4 条样板）

**为什么**：伪人图鉴（`codex_pack.py`，68 处 `**`）与机制教程（`codex_mechanics.py`，236 处）一直是
"分行 + 加粗"的写法，**角色技能描述没跟上**——44 条里只有 1 条用加粗、**0 条用换行**，
最长 228 字一坨。薯条那条图鉴好看，正是因为它按前一套写法写的（不是它特殊）。

**做法**：规则进 `docs/STYLE.md §12`；先改 4 条样板——`零叁贰玖·敏锐直觉`、`零叁贰玖·情报收集`、
`沙白·万事通`、`沙白·感知迟钝／困倦`（`·` 分行、数值 `**` 加粗、限制交给 chips）。

**顺手抓到的问题（都按新规则算违规）**：

- **chip 挂错**：我一开始给「敏锐直觉」加了「冷却 3 回合」——它其实属于同角色的「情报收集」
  （代码里 `_set_ability_cooldown(actor, ability_id, turn + 3)` 就在那一段）。**chip 不能凭印象挂**：
  它是对玩家可见的强度信息，挂错等于在界面上撒谎。
- **限制写了两遍**：`情报收集`、`沙白·万事通`、`沙白·鼓舞` 的正文里都重复了一句冷却说明（已删，留给 chip）。
  **同类还没改**：`火龙·呼朋引伴`（正文写"存活 3 回合后解锁 / 4 回合冷却"，chips 里已有）、
  `洋瘛·情绪剥离`（正文 `*该能力有 2 回合冷却时间。*` + chip）。
- **两件只有渲染才看得见的事**：① `mdText` **只在 `·` 和 `\n` 处换行**——"持有印记时：""*仅限…*"
  这类行若不显式断行，会**被吞进上一句**（源码里看不出）；② 复核探针一开始**手抄文本**，
  源码改了它还渲旧的 → 改成**从内容层导入真实 `AbilityDefinition`** 再渲染
  （角色模块暴露的是 `CHARACTER`，不是 `DEFINITION`——又一次"别猜，先 `dir()`"）。

**没做完**：23 条长描述里还有约 19 条待排（`厄瑞玻斯·命运抽牌`、`罗兹·驭血`、`青桃·持之以缓`、
`错潮·走你！`、`柳七鱼·不行，我要受不了了`、`ED Tear·我是一个沃尔玛购物袋`、`比格小星·大家的星星`、
`混` 的三条、`薯条·深度思考`…）。

## 命运牌：需要选人的牌，漏选要挡在前端（守卫）

**现象**：厄瑞玻斯·**死神正位**要玩家指定一名房客（`NEEDS_TARGET = {13: ("upright",)}`）。
前端本来就会正确判断"这张牌 + 这个方向需要选人"（`fateNeedsTarget()`），但结算函数是
`if (FATE.targetId) value.target_id = ...` —— **没选人就干脆不带**，请求照样发出去，
后端 `_require_home_tenant(None)` 抛 `未找到该房客。`，玩家看到的是**一句后端报错**，
而不是"先选人"的提示。

**改法**：`fateSettle()` 开头加一道前置守卫——需要选人且没选时，弹提示并**直接返回（不发请求）**；
提示文案取内容层下发的 `target.prompt`（不在前端另造措辞）。

**验证**（无头 CDP，注入 `FATE` 后直接调 `fateSettle`）：

| 场景 | 结果 |
| --- | --- |
| 需要选人、没选 | `/api/action` 调用 **0 次**，弹出「选择一名房客」 ✅ |
| 已选 `target_id=3` | 正常发出 1 次请求，`value = {index, orientation:"upright", target_id:3}` ✅ |

**同类风险：已普查，除本条外没有别的洞**（把前端所有"发送动作"的落点逐个过了一遍）：

| 提交点 | 必需输入 | 守卫 |
| --- | --- | --- |
| 命运牌·选人 | 房客 | 本轮补上 ✅ |
| 命运牌·选牌 / 方向 / 上供（`submitResolve`） | 牌（+ 方向 / 物资） | `if(!el){toast;return}` + 方向必填检查 ✅ |
| 指派搜索·地点 | 地点 | 默认预选第一处 + `if(!LOC_SEL)` 兜底 ✅ |
| 技能·选人 / 选项（`sendAbility` 各调用点） | 目标 / 选项 | 弹窗内 `if(!el){toast;return}` ✅ |
| 技能·数量 | 数量 | `Math.max(1, min(max, …))`，恒有值 ✅ |
| 开局 / 发现选择 | 卡片索引 | 由卡面点击提供，无"空提交"路径 ✅ |
| 通用 `resolveView` | 由调用方给 | 三个调用点：两处有守卫，第三处传 `null` 是"反悔取消"的语义 ✅ |
| 结束回合 | — | 门外有事件时后端**明确拒绝**并说明，属设计 ✅ |

**另一类（不修，但要知道）**：**过期值**——对话框开着时目标/地点状态若发生变化，
提交会带旧 id，后端 `RuleViolation` 拒绝并提示（安全失败）。实际很难触发：
待处理期间前端会吞掉除弹窗外的所有点击（见 `AGENTS §7` 的"全局点击守卫"）。

## 日志分层：玩家播报要精简，明细折叠（契约已定，实现分三步）

**问题**：`_log()` 的同一段文本既进玩家可见日志、也进存档完整日志。玩家于是读到一长串
「X装备了Y」「X卸下了Z」「X因…流失1.2理智」，每条独占一行，冗余且吵。

**形状（已实现，见下"现状"）**

1. **条目加一层明细**：日志条目扩成 `{"turn":…, "shown":…, "text":…, "detail":[…]}`，
   `detail` 是明细行数组（每行 `{label, value, note}` ＝ 谁 / 多少 / 为什么）。
   - 引擎侧：`_log(message, *, shown=True, detail=None)`；**没有 `detail` 时不写这个键**，
     旧存档与旧条目形状完全不变。
   - 前端侧：日志三元组从 `[turn, text]` 扩成 `[turn, text, detail]` —— JS 解构天然向后兼容
     （旧条目 `detail === undefined`，照现在的样子渲染）。
2. **合并靠"收集器"，不改各调用点**：`self._collect_start()` 之后、`self._collect_flush(汇总文本)`
   之前的可见播报**不立刻播**，但仍逐条写进完整日志；flush 只播**一条**汇总
   （`text` = 汇总，`detail` = 被收集的逐条）。
   这样「数值一样就合并」不必动 `value_system` 的调用点，只在批量结算的外层前后各插一行
   （回合末那圈 `for tenant` 因此**不用重新缩进**，diff 最小）。
3. **先迁这两类**：① **操作回执**（装备/卸下/整理携带位置——玩家自己点的，不必逐条播）；
   ② **回合末数值结算**（理智自然流失、生命自然流失、状态演化）——一条汇总 + 每人一行的明细，
   备注写明受哪些效果影响（羁绊 / 物资 / 状态）。

**顺序**：后端契约与 `_log_sink`（不动任何现有文案，零风险）→ 迁 ① → 迁 ② →
最后前端折叠（`index.html::renderLog()`：有 `detail` 的条目给可点标记，点开在下面铺明细）。

**现状（已落地）**

- 引擎：`_log(..., detail=…)`、`drain_message_entries()`（文本 + 明细）、`_collect_start/_collect_flush`；
  没有明细时**不写 `detail` 键**，旧存档与旧日志条目形状不变。
- 下发：`session.drain()` 发 `[[文本, 明细], …]`；`logEntries` 发 `[回合, 文本, 明细]`。
- 前端：`renderLog()` 对有明细的条目渲染「明细 N」按钮，点开铺出逐行（`.ld-toggle` / `.ld-box`）。
- 已迁移：**回合末基础结算**（理智消耗 + 高生命自然流失 —— 探针实测：玩家只见
  `回合末结算：N 名房客的理智与生命变化。` 一条，明细 12 行，完整日志逐条不少）；
  **装备 / 卸下 / 整理携带位置**三条改为 `shown=False`（只进完整日志）。
- 待办：① 明细目前是逐条原文，还差"谁 / 多少 / 为什么（羁绊·物资）"三列结构；
  ② `value_system` 的损失播报有重复动词（`因回合末消耗消耗2.0理智`）——`source` 与 `change_type`
  都是修饰器匹配键（`path("回合末消耗")`、source 里的"消耗/伤害/流失"）**不能改字符串**，
  要改的是那三行日志的**格式**（把动词提到前面、来源放括号里）。

**验收**：一个回合的回合末结算，玩家日志只多**一行**（可点开看每人明细）；
存档完整日志与「导出」仍能逐条看到原文，一条不少。

## 归属边界：只有 `dlc/`、`resourcepacks/` 开放，核心区自留

**要什么**：别人能给这个游戏加内容包，但不能改核心代码。所以定一条**可执行**的边界，而不是写在嘴上。

- **开放区**：`dlc/`、`resourcepacks/`（以新增文件为主，独立装载、同名覆盖）。
- **自留区**：其余一切 —— `weiren_game/`（核心与内置内容）、`tools/`、`tests/`、`docs/`、`design/`、
  根目录入口与配置、`.github/`、`.opencode/`。
- **落地**：`.github/CODEOWNERS`（自留区逐条声明 owner；开放区**刻意不列** —— CODEOWNERS 没有"取消归属"
  的写法）+ `.github/workflows/ownership-guard.yml` + `tools/audit_ownership.py`（同一套规则，本地可自查）
  + `CONTRIBUTING.md` / PR 模板写清提交路径。
- **守卫为什么放行作者**：作者在核心区工作是正当行为，所以 `audit_ownership.py` 只认 `--trusted`
  （`author_association` = OWNER/MEMBER/COLLABORATOR 时跳过）。因此它**不进**「每次改完的固定动作」，
  它是 PR 检查，不是提交流程。
- **还差一步（GitHub 网页）**：给 `main` 开分支保护（Require a pull request + Require review from Code Owners），
  并把 `ownership-guard` 设为 required status check；**不要**勾"Do not allow bypassing"，否则作者自己也会被卡。
  CODEOWNERS 只有配上分支保护才真正咬人。
- **说明**：fork 是 GitHub 的既定行为，仓库里禁止不了；能控的是**上游**这一侧。

## 伪人卡「已确认」：初访前技能生效也要刷新（`pseudo.known`）

**现象**：洋葱的「潮汐的诱惑」（搜索袭击）等技能在**初访前**就会生效，玩家看得到结果，
但门口那张伪人卡还停在「尚未确认」——卡片只看 `pseudo.revealed`，而它只在**初访**时置真。

**做法：把"对外可见"与"机制门控"拆开**

- `PseudoCommonState` 新增 `known`（进存档；旧存档缺字段回落 `False`）。它**只表示对外可见性**。
- 通用观察点 `information_system._observe_pseudo_skill()`（所有伪人技能触发都要经过它）
  在 `revealed` 仍为假时置 `known = True`，并记一条 `伪人已确认：<伪人>。`（只报一次）。
- 后端投影下发 `pseudo.known = revealed or known`；前端 6 处 `pd.revealed` 判据改用 `pd.known`；
  `engine._summary()` 同步，CLI 与 UI 口径一致。
- **为什么不直接把 `revealed` 置真**：内容层有多个被动拿 `revealed` 当"初访后"门控
  （`pseudo_onion.maybe_whisper`、`pseudo_benzene` 两处、`erebus` 审判牌），提前置真会把它们
  一并提前解锁 —— 那是**平衡改动**，不是这次要修的东西。
- **范围**：所有伪人通用（薯条 / 苯 / STAR 的搜索袭击同样在初访前触发）。
- **已知取舍**：① 日志顺序上「伪人已确认」排在技能效果那条之前（内容模块在技能开头调观察点）；
  ② 卡片一次给到完整态（含印记、解放/突破、技能表），等于把"初访揭示"提前。

## 待修：把「驱逐（指认）」改造成"选一个房客"的流程

> 定的方向：**驱逐本质就是"选一个房客"，且不可撤销** —— 所以它该套现成的选人范式，
> 而不是现在这样"每张头像右上角挂一颗小按钮 + 另写一个确认框"。

**驱逐有四个来源，只有"指认"是屋主的决定**（其余三个都不该有确认框）：

| 来源 | 触发 | 确认 |
| --- | --- | --- |
| 指认（屋主凭信息） | `expelBtn`（后端 `expellable` 才下发）→ `askExpel` → `accuse` | ✅ 需要 |
| 角色技能（柳七鱼 `six71.py:47`、罗兹 `rose.py:79`、厄瑞玻斯正义牌 `erebus.py:492`） | 技能流程里选目标房客 | 选人本身就是确认 |
| 伪人自身（薯条 `pseudo_fries.py:332`） | 自动 | — |
| 门外伪人（`ability_system.py:258`） | 自动 | — |

**要改成什么样**

1. **入口收敛成一个**：不再往每张头像上挂 `expel-btn`；改成**一个入口**（伪人卡 / 顶栏的「指认」）
   → 打开**选人弹窗**，列出本次可指认的房客（后端已给 `expellable`）。
   用现成的 `tenantChoiceCard` + `.choice-grid`（与「指派搜索」「技能目标」同形）。
2. **每张卡上带证据状态**：把 `expel_risk`（布尔）升级为**下发文本** ——
   现在那句"证据仅为待验证指认，判断有误会误逐无辜房客"是**写死在前端**的
   （`index.html:1934` 的 title 与 `1939` 的 `.expel-warn`），而判据在后端（`web_ui.py:632`）。
   按「提示语/机制说明由内容层下发」，**这句话要挪回内容层**，前端只渲染。
3. **选完再确认一次**（不可撤销）：复用同一条「屋主不可撤销决定」范式
   （`askConfirm({title, question, note, danger, yes, no, onYes})`，文案全部来自下发），
   顺手删掉 `.expel-foot` / `.expel-warn` 两个专属样式。

**顺带一起修的（同一族）**：`tenant / other_tenant` 类技能的选人弹窗目前**只有房客卡**，
看不出"这一步是驱逐"、也看不出对不同目标的不同结果（罗兹对人类 / 对伪人是两种结果）——
`TARGET_OPTIONS` 机制本来就支持 `[{value,label,desc}]`，把 `desc` 画进 `tenantChoiceCard` 的
`extra` 槽即可；不可撤销的技能再由内容声明一句 `confirm`。

**危险色（已定）**：驱逐是不可撤销的危险动作，一律走**现有语义色**，不新造颜色 ——
`--danger`（`#d46b63`，锁定 token）/ `--danger-1` / `--danger-2`（按钮渐变暗端）；
按钮直接用现成的 `.btn.danger`（确认框的「是」）、入口按钮沿用现有 `.expel-btn` 那套 danger 配色。
（这两处现在就已经是 danger 色了，所以"上色"不需要新写样式，只要**新的指认弹窗也照这套用**。）

**动手清单（按此顺序，1+2 一起做才不留半截）**

1. 后端：`expel_risk` 旁边补**内容层下发的文案**（`data/labels.py` 新增一张小表，
   如 `confirmed / pending` 各自的 `action / hint / confirm`，并登记进 `_BASE_CONTAINERS`），
   `web_ui` 逐房客下发 `expel = {action, hint, confirm, danger}`。
2. 前端：删掉每张头像上的 `expelBtn`；改为**一个入口**（伪人卡/顶栏「指认」）→
   用 `tenantChoiceCard` + `.choice-grid` 列出可指认房客（卡上带 `hint`）→
   选中后 `askConfirm`（danger）→ `accuse`。
3. 删 `.expel-foot` / `.expel-warn`；`askConfirm` 作为公共确认范式留下。
4. 技能的 `TARGET_OPTIONS.desc` 接线到 `tenantChoiceCard` 的 `extra` + `AbilityDefinition.confirm`。

> ⚠️ 为什么必须 1+2 一起改：只删入口不建新入口 = 指认功能直接消失。
> 所以这四步不要拆到不同轮次里做半截。

## 待修：命运抽牌还缺两步 —— ①需要选人的牌（死神正位等）②正/逆位那页也该是「发现」

> 2026-09-17 报告。**本轮只做诊断与方案，没动手**（改完的只有浮层风格与 3 张符号样板）。

### ① 需要选人的牌没有适配 —— 会卡住

> **已修完并端到端验过（同日）**：内容层 `NEEDS_TARGET` / `build_fate_view` 的 `target` /
> `resolve_fate_view` 收 `target_id`；前端第 ④ 步用「指派搜索」那套 `tenantChoiceCard` + `pickedEl`。
> **实测（CDP，种子 `abc`，抽到 `1 魔术师·正位 / 13 死神·正位 / 11 正义·逆位`）**：
> 选牌（stage1，bare）→ 上供槽（stage2，有面板底）→ **`继续`（空槽）→ stage4 = 选房客（2 张房客卡，bare）**
> → 选中后 **stage5 = 揭晓（结算/反悔）且 `FATE.targetId=1`** → 点「结算」后 `pending` 清空。
> **0 JS 异常**。也就是说：**死神·正位现在不会再卡住了**。

> ⚠️ **探针教训（当天踩，根因已查明）**：不是引擎"随机数顺序不同"，是**我探针错了两处**：
> ① 用了 `defer_start=False`（引擎按 `options[0]` **自动选人**），而网页是玩家手点的 —— 选出来的人和
> **实例 id** 都不一样；② 手动又调了一次 `_begin_start_pick()` —— 它**会重掷候选**，拿到的根本不是
> `new_game` 算好的那一份（要读 `engine._pending_choice["options"]`）。
> 而抽牌与定方向的随机流是**按 (事件, 房客实例 id) 派生**的（`erebus.py:273`
> `engine._rng(_event_id("fate.orientation"), actor.id)`），**不是一条全局流** ——
> 所以前面的人一变，牌面就变，这完全正确、不是 bug。
> **照浏览器的方式复现后两端完全对上**：第一轮候选 `['six71','tear','erebus']`（＝柳七鱼/ED Tear/厄瑞玻斯）、
> 抽到的牌 `(1,正位)(13,正位)(11,逆位)` —— 与浏览器逐项相同。
> **规矩**：要复现抽牌，用 `defer_start=True` + 读 `_pending_choice["options"]` + **做同样的选择**；
> 或者干脆按浏览器实际下发的 `number` 找牌。

- **症状**：抽到「死神」选正位后没有让你指定房客，流程卡在那里（正位效果是"指定一名房客，移除全部状态"）。
- **根因**：`resolve_fate_view`（内容层）**永远**传 `target_id=None`：
  `resolve_fate(engine, actor.id, number, orientation=chosen, target_id=None, sacrifice_item_id=item_id)`。
  而 `_card_13` 里是 `engine._require_home_tenant(target_id)` → `None` → 抛 "未找到该房客。"
  （命令行那条路 `resolve_interaction` 是**有**这一步的：`if card_number == 13 and effective_orientation == "upright": target_id = ui.choose_target(engine)`。
  **也就是说：只有 Web 这条腿没接上**，不是规则缺失。）
- **要改的三层**：
  1. **内容**（`build_fate_view`）：声明哪些牌要选人 —— `"target": {"required": [13], "prompt": "选择一名房客"}`，
     并把候选一并给出（内容能拿到 engine：`home_tenants()` → `[{"value": t.id, "label": 角色名}]`）。
  2. **web_ui**：把这组候选**投影成和技能目标同一张房客卡**（头像 / 生命 / 理智）——
     内容和其它地方一样只给 `value/label/desc`，不碰头像。参考现有 `condition_targets` 的做法。
  3. **前端**：在「方向」之后、**揭晓之前**插入一步"选人"（用现成的房客卡，`tenantChoiceCard`）；
     `fateSettle` 时把 `target_id` 一起发回去；`resolve_fate_view` 收下并透传。
- **核过全副牌了（同日）**：`_card_0`–`_card_21` 里**真正读 `target_id` 的只有 `_card_13` 这一处**
  （`erebus.py:504`，且只在**正位**分支；逆位是随机房客，不需要输入）。
  其余 21 张的 `target_id` 形参纯属统一签名，从不使用。**所以缺的输入只有"死神·正位选一名房客"这一个**。
  `building_fate_view` 的 `target.required` 只写 `[13]` 就够；以后哪张牌开始读 `target_id`，再往这里加。
- **另一种"额外选择"是定向**（命运之轮）：已由 `orientation.required` 覆盖 ✅（`erebus.py:265/281`），
  前端第 ③ 步就是它，不用另开机制。

### ② 正/逆位那一页也该是「发现」，而且两个方向也要符号

- **已改完（同日）**：第 ③ 步改用和「发现」/选牌**同一套卡片**（`pagedOptions` + `.card` + `.cn`/`.dc-av`/`.dc-name`）
  + `bare`（无背景板）；两个方向各带一个符号（`orientation.symbols` 由内容下发，
  图形在 `erebus_fate_symbols.ORIENTATION_SYMBOLS`：上箭头＝正位、下箭头＝逆位）。
- **实测（CDP）**：第 ③ 步 `cards=2 / 方向符号 2 个 / 旧的 sub-orient-btn 0 / bare=true`；
  选「正位」后进揭晓 `orientation="upright"`（选择确实带过去了）→ 结算后 `pending` 清空；0 JS 异常。
  ⚠️ 这一次是用 `FATE.stage=3` 直接叫出该步来验**渲染**（"上供买到这一步"的路由在同一天早些时候已经验过），
  没能走真路径的原因是那几个种子的物资池里**没有紫色及以上**的物资可上供。

## 待修：厄瑞玻斯「命运抽牌」的界面（玩家报告：定制的窗口都不见了）

> 2026-09-17 报告：现在只剩"选牌"那一步，而且**卡上看不到正位/逆位的效果**；
> 之前做好的「上供 / 定正逆位 / 反悔」这些窗口全都不出现。本轮只记录**预期**（玩家口述），**尚未修**。

**预期的四步**（全部由内容层声明；前端按 `submit` / `orientation` / `cancel_prompt` 渲染）：

1. **选牌**：**就用「发现」那套范式**——这是对的，不是问题；
   但每张卡**悬浮要能看到正位与逆位各自的效果**（`fateHoverStart` 那一套）。
2. **上供**：页面上方一个**紫色格子** —— 玩家可以把紫色及以上品质的物资**拖进去**；
   也可以**直接点「继续」跳过**。（上供换来的是下一步多一个"选正位／逆位"。）
3. **揭晓**：上供 / 跳过后，**先把结果告诉玩家**（牌面 + 该方向的效果）。
4. **反悔 / 结算**：**看到结果之后**，才给「反悔」和「结算」两个选择。

**「命运之轮」= 上供的替代品**：不交紫色物资，改为直接给出第 3 步那个"选正位／逆位"。

**实测（CDP，种子 `fate2`，厄瑞玻斯开局）—— 后端与前端都没坏，四步都能走到**：

| 步 | 实测内容 |
| --- | --- |
| 1 | 标题「命运抽牌」，3 张卡（`fateCardHtml`，悬浮显示正/逆位效果） |
| 2 | 「是否上交一件紫色及以上物资，改定所选牌的正逆位？」+ **「上供 / 不上供」两个按钮** |
| 3 | 「请选择这张牌的正位或逆位」+ **上供槽** + 物资池 4 格 + 正/逆位两个按钮 |
| 4 | 结算 / 反悔 |

下发里 `submit` / `orientation` / `cancel_prompt` **全在**，0 JS 异常。

**所以真正不符的不是"窗口丢了"，而是顺序与措辞**：

- 第 2 步被做成了"**先问 yes/no**"，而预期是**直接给一个紫色上供格 + 一个「继续」**；
- 预期里"**揭晓**"是独立的一步（先告诉你牌面与该方向的效果），再接「反悔 / 结算」；
  现在是把"上供 / 选方向 / 结算"挤在一条流水线上，中间没有"揭晓"。

→ 这是**内容声明的顺序问题**（`erebus.py` 的 `build_fate_view` 与前端的 `fateFlow` 步数），不是 bug。

**已按预期改完（同日）**：

- **内容层**：删掉 `offer_prompt / offer_yes / offer_no` 那条 yes/no 问句，改为
  `proceed: "继续"` + `proceed_hint`：**槽里放东西＝上供，空着直接继续＝不上供**。
- **前端**：`fateFlow` 的四步重排为 ①选牌 → ②上供（紫格 + 继续） → ③选方向（上供买了这一步；
  需要定向的牌直接从这里开始） → ④揭晓（牌 + 方向 + 效果）后才问「结算 / 反悔」；
  `fateOffer(yes/no)` 删掉，换成 `fateProceed()`（按槽里有没有东西决定下一站）。
- **实测（CDP，种子 `fate2`）**：第 1 步 3 张卡且下发里 `offer_prompt` 已消失；
  第 2 步 `submit-slot` 在、物资池 4 格、**不再有 yes/no 卡片**；空槽点「继续」→ 直接进第 4 步（结算/反悔两张卡）；0 JS 异常。
- **还没验到的两条分支**（下次补）：①往槽里放东西 → 第 3 步选方向；②需要定向的那张牌跳过第 2 步。
- **遗留小尾巴**：底部那个按钮现在显示的仍是弹窗通用的「确认」，而不是内容声明的 `proceed`——
  `openDialog` 的底部按钮文案还没参数化。要显示「继续」得给它加一个 label 参数（一行）。
- **踩坑（第二次栽）**：前端**注释**里写了内容词（`正位` / `逆位` / `牌面`），
  `audit_separation` 一样会报 `[内容文案]`——它扫的是文件文本，注释不豁免。前端注释一律用通用说法。

## 房客改名：沈屹 → 古雕塑（`stone`，16 号）

- **只改显示名**：`CharacterDefinition.name` 由"沈屹"改为"古雕塑"（与它的标签"像古雕塑"、
  以及形象描述一致）。`tenant_id` 仍是 `stone`、`source_id` 仍是 16，**都没动**。
- **为什么敢只改名字**：存档只认 `tenant_id` / 实例 id，不认显示名；
  改名不需要迁移，老存档照读（PRINCIPLES §13 的反面用法：名字不是身份）。
- 全库只有 `weiren_game/data/characters/stone.py` 提到过旧名（模块 docstring + 名字字段），
  已一并更新；`docs/`、`dlc/`、图鉴文案里没有引用。

## 专属面板的前端半：形状固定、内容填值（花尔维纳的田第一次跑通）

- **做法**：`#panelFloat` 锚在左栏（`.board-split` 内），右栏仓库保持露出，好把物资拖进去；
  格子复用 `slotInner()`（从 `slotCell` 里抽出来的"格子里画什么"），信息条复用 `slotHtml()` 的同一套词表。
- **四种关闭**：面板自带「关闭」按钮 / 点面板留白 / ESC / 再点技能。**不做遮罩**——
  仓库必须保持可拖，所以"点外围关闭"这条从一开始就不成立。
- **拖拽中不关**：留白处理器在 `_dragItem` 非空时直接返回。往格子里拖东西没对准、手一松落在底板上，
  那一刻最不该把界面关掉。
- **拖入 / 拖出都只是转发**：格子带 `onDrop` / `onTake`（**动作名由内容定**），
  前端只把"动作 + 物品 id + 来源"发回去；它不知道什么是水、什么是食物。
  产物拖到仓库／背包列也走同一条转发（**不是** `move_item`）——落点由内容决定。
- **入口**：`opens_panel` 的技能行渲染成开 / 关，点击**不调** `useAbility`（引擎也不结算它）。
- **浮窗可以拖**：按住标题栏拖动，位置按**视口比例**记进对局外设置
  （`game_config.json` 的 `panel_pos`：面板 key = 角色 id → `[左, 上]`，尺寸变了也不跑偏）；
  `panel_draggable` **默认开启**，关掉就不响应拖动。这两个字段走 `/api/settings`，
  收进来时校验成 `[0..1, 0..1]`，别的丢弃（玩家侧宽容，见 §14）。
- **踩坑（审计抓的）**：注释里写内容名也算泄漏——`audit_separation` 扫的是文件文本，注释不豁免。
  前端注释一律用通用词（"往里拖东西"），别写具体物品名。
- **验证**：`node --check`（抽出 `<script>` 校验）+ 无头 CDP 实测（真实服务、种子 `ui70`、真实对局）：
  开局拿到花尔维纳 → 点技能行打开（标题「田」、4 个格子、2 个可拖入格、底板 svg 都在）→
  点留白关闭 → 再点打开 → ESC 关闭 → **把仓库里的蒜瓣拖进地格，后端真的种下了**（state 里 `seed` 变成它）；
  0 JS 异常、0 控制台错误；旧的拖拽处理函数仍在。

## 交互原语的说明书放图鉴「机制」页

- **判断**：拖拽 / 双击 / 悬浮 / ESC / 浮窗三角 / 点留白关闭这些是**核心的交互原语**（形），
  不属于任何一位角色。玩家要查"能怎么操作"，合适的位置就是图鉴——它纯静态、启动器里也能开，
  天生是"开局前也能读"的参考书。
- **做法**：`data/codex_mechanics.py` 的 `MECHANICS` 新增一节「操作」，与既有各节同形
  （`title` / `tint` / `icon` / `entries`）。**不写进前端**——文案属于内容层。
- **与现场提示的关系**：图鉴负责**完整清单**，现场负责**恰好的提示**（toast、tooltip、
  格子上的锁与灰态）。两者不互相替代：让人在操作的那一刻知道下一步能做什么，才是手感。
- **不做的事**：图鉴里**不放"能按的动作"**。`codex_state()` 是纯静态、不接 `engine`
  （启动器里就能打开），而 `GET /api/codex` 是一次性缓存；混入动作会让"没有对局时按了怎么办"
  与缓存失效两件事都变复杂。

## 花尔维纳的「田」：面板与容器的第一个真实调用者

- **落地**：`data/characters/flowey.py` 声明 `CONTAINERS = {"field": FieldState}` 与
  `PANEL = (build_view, resolve_action)`；规则（水分 / 生长 / 干旱 / 枯死 / 采收）全在这个文件里，
  **核心一行没改**——只用上了上一轮开的两条缝。
- **面板的格子契约**（这次实际用到的字段）：`group`（哪块地）、`role`（`seed` / `product`）、
  `item`（只给 `item_id` + 数量，图标/品质由前端按目录补）、`locked`（能不能拖出）、
  `on_drop` / `on_take`（拖入 / 拖出时该发哪个动作，空 = 不接受）。
  **动作名由内容定**：前端只负责"把 `on_drop` 那个动作连同拖进来的物品发回去"，
  它不知道什么是"水"，也不知道"水"和"食物"该怎么区分——那都在内容层。
- **入口技能**：`AbilityDefinition.opens_panel = True` —— 这条"主动技能"不结算效果，
  只声明"我打开本角色的专属面板"。配套三处：前端把它渲染成开 / 关（点击**不调** `use_ability`）；
  引擎侧 `use_ability` 直接拒绝（不掷失败、不扣代价、不记冷却）；
  `tools/validate_content.py` 不再要求它有 `ACTIVE_DISPATCH` 处理函数。
- **几条判断**：
  - **种下即算浇过一遍水**（湿润度满）——否则第一回合必然掉到 0，起手就吃亏。
  - **满水再去浇会被拒绝**（且不消耗），走 `RuleViolation` → 前端 toast，与厄瑞玻斯
    "品质不足"同一条路。
  - **收成没收走之前不能接着种**：产物格与地格共用同一份记录，允许同格二次播种会让两茬互相覆盖。
  - **成熟即自动落产物格**（没有单独的"采收"动作）：玩家描述的是"熟了就能从里面取出来"。
  - **拖拽中不响应"点空白关面板"**：面板空白处的关闭处理器在拖拽进行中（`_dragItem` 非空）直接返回。
    否则拖矿泉水时对不准、手一松落在底板上，面板就没了——那是玩家最不想被打断的一刻。
  - **显示名用"湿润度"而不是"干燥度"**：数值满格 = 刚浇过水，叫"干燥度 3/3"会让玩家读反。
    （这是一个常量，想改回去是一行的事。）
- **踩坑**：第一版取物资用了 `Inventory.remove_first(item_id)` —— 它把**整摞**一起拿走
  （种一次吃掉 2 个）。取"1 件"要用 `Inventory.consume(item_id, 1)`（减 count、归零才移除实例）。
- **验证**：`tests/test_custom_ui.py` 7 项（容器进存档 / 面板形状 / 拖入规则 / 生长与采收 /
  干旱减产与枯死 / 收成未取走时不能复种 / 面板登记 / 状态下发投影）；全库 **73 单测** / `audit_separation` /
  `validate_content` / 冒烟全绿。


---

> **更早的记录（62 节）已归档**：`docs/archive/DECISIONS_2025-2026.md`。
> 归档是**非现行参考**，只在追溯「为什么当时这么改」时去看（见 `docs/archive/README.md`）。

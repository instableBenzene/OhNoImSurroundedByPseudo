# 核心方法总清单（`weiren_game/`，不含 `data/` 与 `webui/`）

> 由 `python tools/dump_core.py` 生成（生成于 2026-09-19）。**别手改本文件**——改代码后重跑。
> 目的：核心尽量不动。**要加内容先看 `docs/ADD_CONTENT.md` 的扩展点；只有『多处共用』的东西才考虑进核心**（判据见 `docs/PRINCIPLES.md` §二.2 与 `docs/DECISIONS.md`）。

**合计 680 项**（类 + 顶层函数 + 方法）。

说明：`说明` 列取函数/类的 docstring 首行；`参数` 列是签名（已去注解细节）。

## 扩展点：内容层往这里挂东西（50 处）

> 核心**只在通用节点/注册表上派发**；内容在各处登记。想加效果先在这里找挂点，找不到再考虑改核心。

| 文件 | 函数 | 钩子表 | 节点/键 |
| --- | --- | --- | --- |
| `weiren_game/content.py` | `register_item_hook` | `ITEM_HOOKS` | `—` |
| `weiren_game/engine.py` | `_notify_tenant_death` | `SCENARIO_HANDLERS` | `tenant_death` |
| `weiren_game/engine.py` | `_run_pseudo_end_effects` | `SCENARIO_HANDLERS` | `settle_end` |
| `weiren_game/engine.py` | `status_lines` | `SCENARIO_HANDLERS` | `progress_text` |
| `weiren_game/modifier_rules.py` | `gates_for` | `GATE_REGISTRY` | `—` |
| `weiren_game/modifier_rules.py` | `modifiers_for` | `MODIFIER_REGISTRY` | `—` |
| `weiren_game/modifier_rules.py` | `register_gate` | `GATE_REGISTRY` | `—` |
| `weiren_game/modifier_rules.py` | `register_modifier` | `MODIFIER_REGISTRY` | `—` |
| `weiren_game/systems/condition_system.py` | `_apply_emotion_end` | `SCENARIO_HANDLERS` | `emotion_end_extra` |
| `weiren_game/systems/condition_system.py` | `_emotion_application_blocked` | `NODE_HOOKS` | `condition.irritation.settle` |
| `weiren_game/systems/condition_system.py` | `_notify_emotion_increase` | `SCENARIO_HANDLERS` | `on_emotion_increase` |
| `weiren_game/systems/condition_system.py` | `_status_avoidance` | `NODE_HOOKS` | `armour.allows_status` |
| `weiren_game/systems/information_system.py` | `_create_random_information` | `SCENARIO_HANDLERS` | `observed_skills` |
| `weiren_game/systems/item_system.py` | `_item_tag_fn` | `TAG_BEHAVIORS` | `—` |
| `weiren_game/systems/item_system.py` | `use_item` | `NODE_HOOKS` | `item.use_wasted、keep` |
| `weiren_game/systems/marks_system.py` | `_emit_node` | `NODE_HOOKS` | `—` |
| `weiren_game/systems/personality_system.py` | `_personality_weights` | `NODE_HOOKS` | `personality.weights` |
| `weiren_game/systems/pseudo_system.py` | `_attempt_breakthrough` | `NODE_HOOKS` | `breakthrough.guard` |
| `weiren_game/systems/pseudo_system.py` | `_pseudo_attack_searchers` | `SCENARIO_HANDLERS` | `attack_searcher` |
| `weiren_game/systems/pseudo_system.py` | `_pseudo_encounter_chance` | `SCENARIO_HANDLERS` | `encounter_chance` |
| `weiren_game/systems/pseudo_system.py` | `_pseudo_handler` | `SCENARIO_HANDLERS` | `—` |
| `weiren_game/systems/pseudo_system.py` | `_resolve_pseudo_visit` | `CHARACTER_NODE_HOOKS、SCENARIO_HANDLERS` | `on_first_reveal、pseudo_visit、visit` |
| `weiren_game/systems/pseudo_system.py` | `_scenario_resist_penalty` | `SCENARIO_HANDLERS` | `search_resist_penalty` |
| `weiren_game/systems/pseudo_system.py` | `_search_resist_responder` | `CHARACTER_NODE_HOOKS、ITEM_HOOKS` | `pseudo_search_resist、search_resist` |
| `weiren_game/systems/pseudo_system.py` | `_target_lock_responder` | `CHARACTER_NODE_HOOKS` | `target_lock` |
| `weiren_game/systems/round_effects.py` | `_settle_base_end_effects` | `NODE_HOOKS、SCENARIO_HANDLERS` | `end_sanity_multiplier、end_turn_sanity_bonus、madness.available` |
| `weiren_game/systems/round_effects.py` | `_settle_held_items` | `ITEM_HOOKS` | `turn_end.held` |
| `weiren_game/systems/round_effects.py` | `_settle_other_end_effects` | `CHARACTER_NODE_HOOKS` | `end_turn_instance` |
| `weiren_game/systems/round_effects.py` | `_settle_pseudo_start_handlers` | `SCENARIO_HANDLERS` | `performance、start_passive` |
| `weiren_game/systems/round_effects.py` | `_settle_tenant_instance_start` | `ITEM_HOOKS、NODE_HOOKS、TURN_START_HOOKS` | `legend.turn_start、madness.available、madness.convert_excess、turn_start.backpack` |
| `weiren_game/systems/round_effects.py` | `_start_of_turn_effects` | `NODE_HOOKS` | `turn_start.maintain_guard` |
| `weiren_game/systems/search_system.py` | `_loot_for_mission` | `ITEM_HOOKS、NODE_HOOKS` | `loot.quality、loot.quality_weights、search.pool_weight` |
| `weiren_game/systems/search_system.py` | `_resolve_search_return` | `ITEM_HOOKS、NODE_HOOKS、SCENARIO_HANDLERS` | `captured_return、search.return.rest、search.return_mod` |
| `weiren_game/systems/search_system.py` | `_search_carry` | `NODE_HOOKS` | `search.carry_override` |
| `weiren_game/systems/search_system.py` | `_settle_search_bag_items` | `ITEM_HOOKS` | `search.return` |
| `weiren_game/systems/search_system.py` | `start_search` | `NODE_HOOKS、SCENARIO_HANDLERS、SEARCH_REWARD_HOOKS` | `blocks_search_dispatch、reward_ids、search.parameters.reset、search.reward、search.start.bond、search_behavior_delta` |
| `weiren_game/systems/value_system.py` | `_after_health_decrease` | `CHARACTER_VALUE_HOOKS` | `after_health_decrease` |
| `weiren_game/systems/value_system.py` | `_apply_armour` | `NODE_HOOKS` | `armour.apply` |
| `weiren_game/systems/value_system.py` | `_consume_health` | `NODE_HOOKS` | `health.transfer_receivers、value.health_consume.convert` |
| `weiren_game/systems/value_system.py` | `_consume_sanity` | `NODE_HOOKS` | `value.sanity_consume.convert` |
| `weiren_game/systems/value_system.py` | `_damage_health` | `NODE_HOOKS` | `health.transfer_receivers` |
| `weiren_game/systems/value_system.py` | `_reduce_sanity` | `NODE_HOOKS` | `sanity.after_decrease、sanity.floor` |
| `weiren_game/systems/value_system.py` | `_restore_sanity` | `CHARACTER_NODE_HOOKS` | `sanity.restored` |
| `weiren_game/systems/visitor_system.py` | `_on_accept_healing` | `NODE_HOOKS` | `visitor.accept_healing` |
| `weiren_game/systems/visitor_system.py` | `_on_tenant_accepted` | `CHARACTER_NODE_HOOKS` | `on_arrival、start_condition_trauma_disorder` |
| `weiren_game/systems/visitor_system.py` | `_pseudo_visitor_mark` | `SCENARIO_HANDLERS` | `visitor_mark` |
| `weiren_game/systems/visitor_system.py` | `_queue_human_visitor` | `NODE_HOOKS` | `visitor.supply` |
| `weiren_game/systems/visitor_system.py` | `_queue_scheduled_visitors` | `NODE_HOOKS` | `visitor.extra_interval` |
| `weiren_game/web_ui.py` | `_pseudo_card` | `SCENARIO_HANDLERS` | `card_info` |
| `weiren_game/web_ui.py` | `_pseudo_progress` | `SCENARIO_HANDLERS` | `progress_text` |

## 核心里的内容 id / 内容名引用（0 处）

> 正常情况下应为 0 或只剩**说明性**的注释/docstring。出现实质引用 = 又往核心塞了专属机制（见 `docs/DECISIONS.md` 的边界条目）。

（无）

## 引擎与调度（54 项）

### `weiren_game/engine.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class GameEngine**` | `` | Complete round loop and game rules, with deterministic event randomness. |
| GameEngine | `__init__` | `(self, state: GameState)` | 初始化引擎，绑定游戏状态并准备消息队列。 |
| GameEngine | `_autosave_before_discover` | `(self) -> None` | discover 是原子行为：开始前若已有存档路径则自动保存（不打扰玩家）。 |
| GameEngine | `_require_no_pending_choice` | `(self) -> None` | 存在待选（discover 未结算）时禁止其它行为。 |
| GameEngine | `choose_discover` | `(self, option: object) -> object` | 提交一次 discover 选择并解除待选状态。 |
| GameEngine | `_clear_pending_choice` | `(self) -> None` | 内部直接清除待选（自动选择/结算完成时）。 |
| GameEngine | `pending_view` | `(self) -> dict \| None` | 返回当前待处理交互的通用视图（prompt/options/cancel），供任意前端渲染。 |
| GameEngine | `resolve_view` | `(self, value: object) -> None` | 把玩家选择交回当前待处理交互的解析器（由内容声明）。 |
| GameEngine | `new_game` | `(cls, seed: str \| None=None, difficulty: str \| None=None, max_turns: int \| None=None, pseudo_id: str \| None=None, disabled_character_ids: Sequence[str] \| None=None, random_pseudo: bool \| None=None, start_choices: Sequence[str] \| None=None, defer_start: bool=False, map_id: str \| None=None) -> 'GameEngine'` | 按种子与参数创建一局新游戏，完成初始房客、地点与补给生成后返回引擎。 |
| GameEngine | `_begin_start_pick` | `(self) -> list[str]` | 计算下一次开局 Discover(3) 的候选，作为待选交出去。 |
| GameEngine | `commit_start_choice` | `(self, choice: str \| None=None) -> None` | 提交一次开局选人；全部选完后创建房客并完成开局。 |
| GameEngine | `_finish_start` | `(self, starters: list[str], pool: list[str]) -> None` | 开局收尾：创建初始房客、生成地点、激活羁绊并记录日志。 |
| GameEngine | `_start_loot_schedule` | `(self, draw_delta: int) -> list[tuple[str, int]]` | 开局补给次数表：基础为食物 2 / 医疗 1 / 工具 1 / 载体 1。 |
| GameEngine | `defer_search_report` | `(self, mission, text: str) -> None` | 记录"搜索期间发生、但应在房客返程时播报"的事件。 |
| GameEngine | `_generate_locations` | `(self) -> list[str]` | 按**本局地图**的名单 + 分组权重，确定本局可用的地点（默认 10 个）。 |
| GameEngine | `load` | `(cls, path: str \| Path) -> 'GameEngine'` | 从指定存档文件恢复引擎；版本不匹配时直接报错。 |
| GameEngine | `save` | `(self, path: str \| Path, *, quiet: bool=False) -> Path` | 将当前状态序列化后原子写入指定文件并返回目标路径。 |
| GameEngine | `drain_messages` | `(self) -> list[str]` | 取出并清空待展示的可见消息（只要文本；CLI 等旧入口用这个）。 |
| GameEngine | `drain_message_entries` | `(self) -> list[tuple[str, dict \| None]]` | 取出并清空可见消息（文本 + 明细），供前端渲染可折叠日志。 |
| GameEngine | `_collect_start` | `(self) -> None` | 开始收集可见播报（配合 `_collect_flush`）：块内不逐条播，仍逐条进完整日志。 |
| GameEngine | `_collect_flush` | `(self, summary: str='', *, title: str='', detail: dict \| None=None, rows: list[dict] \| None=None) -> None` | 把收集到的播报合并成**一条**汇总播出（明细可点开）。 |
| GameEngine | `_log` | `(self, message: str, *, shown: bool=True, detail: dict \| None=None, kind: str='') -> None` | 统一日志入口：`shown=True` 进玩家可见日志，否则只落完整日志。 |
| GameEngine | `_record_log` | `(self, message: str, detail: dict \| None=None) -> None` | 把一条文本记入完整对局日志，不进入玩家的可见消息队列。 |
| GameEngine | `_show_message` | `(self, message: str, detail: dict \| None=None, kind: str='') -> None` | 把一条文本同时记入日志并作为可见消息交给玩家（可带明细）。 |
| GameEngine | `_log_lines` | `(self) -> list[str]` | 将完整日志逐行渲染为文本（含未公开记录与对应回合号）。 |
| GameEngine | `export_full_log` | `(self) -> str` | 导出整局完整文本：元数据 + 全部消息日志 + 全部动作记录。 |
| GameEngine | `_record_action` | `(self, action: str, **data: Any) -> None` | 记录一条对局事件到当前回合与总动作日志（完整保留，不截断）。 |
| GameEngine | `character` | `(self, tenant: TenantState \| str) -> CharacterDefinition` | 按房客对象或角色 ID 返回对应的角色定义。 |
| GameEngine | `living_tenants` | `(self) -> list[TenantState]` | 返回当前仍存活的房客列表。 |
| GameEngine | `home_tenants` | `(self) -> list[TenantState]` | 返回当前在屋内的存活房客列表。 |
| GameEngine | `searching_tenants` | `(self) -> list[TenantState]` | 返回正在外出搜索的存活房客列表。 |
| GameEngine | `container` | `(self, tenant: TenantState, key: str) -> object \| None` | 取该房客的专属容器（不存在就按内容声明的类型建一个）；没声明过则返回 None。 |
| GameEngine | `panel_view` | `(self, tenant: TenantState) -> dict \| None` | 返回该房客的专属面板视图（内容声明 ``PANEL``）；没声明则返回 None。 |
| GameEngine | `panel_action` | `(self, tenant_id: int, action: str, *, slot: int \| None=None, item_id: str \| None=None, source: object=None) -> None` | 把面板动作转交给内容声明的处理器（核心不解其意，只转发）。 |
| GameEngine | `tenant_name` | `(self, tenant_id: int) -> str` | 按房客 ID 返回其角色名称；查无此人时返回“未知房客”。 |
| GameEngine | `_add_tenant` | `(self, character_id: str) -> TenantState` | 为可用角色登记一名新房客，分配 ID 与初始情绪后加入状态。 |
| GameEngine | `_require_home_tenant` | `(self, tenant_id: int \| None, *, must_act: bool=False) -> TenantState` | 校验房客在场、存活且满足行动条件后返回该房客。 |
| GameEngine | `_log_searching_summary` | `(self) -> None` | 回合开始阶段：打印仍在搜索中的房客摘要（与既有流程同位置）。 |
| GameEngine | `_run_pseudo_end_effects` | `(self) -> None` | 回合结束阶段：执行当前伪人场景注册的 settle_end 处理器。 |
| GameEngine | `start_turn` | `(self) -> None` | 开始新回合：记录快照并依次执行回合开始阶段的各类结算。 |
| GameEngine | `resume_to_action` | `(self) -> None` | 读档/回溯后回到玩家行动阶段：非行动阶段则推进（有待选/无房客/已结束时跳过）。 |
| GameEngine | `end_turn` | `(self) -> None` | 结束行动阶段，执行回合末结算并判断胜利或进入回合间歇。 |
| GameEngine | `_remove_tenant_from_house` | `(self, tenant: TenantState) -> None` | 把房客移出屋内的公共收尾：屋内死亡与驱逐共用同一条路径。 |
| GameEngine | `_kill_tenant` | `(self, tenant: TenantState, reason: str) -> None` | 处理房客死亡：触发替身驱逐等特殊分支，移出屋内并记录日志。 |
| GameEngine | `_notify_tenant_death` | `(self) -> None` | 房客死亡节点：通知当前伪人场景与角色光环/被动的死亡响应。 |
| GameEngine | `_check_survival` | `(self) -> None` | 房客全部死亡时以失败结局结束本局。 |
| GameEngine | `_finish` | `(self, victory: bool, ending: str) -> None` | 以给定胜负与结局文本结束本局游戏。 |
| GameEngine | `rewind_one_turn` | `(self) -> None` | 回退至上一回合开始前的快照并恢复状态。 |
| GameEngine | `emotion_visible` | `(self, tenant: object, key: str) -> bool` | 屋主是否能看到某情绪。 |
| GameEngine | `status_lines` | `(self) -> list[str]` | 生成包含伪人进度、房客状态与搜索任务的局面摘要文本。 |
| GameEngine | `inventory_lines` | `(self) -> list[str]` | 生成当前共享物资栏的逐行文本描述。 |
| GameEngine | `location_lines` | `(self) -> list[str]` | 生成本局可用地点的逐行文本描述。 |
| GameEngine | `codex_lines` | `(self) -> list[str]` | 生成图鉴统计文本；具体内容可在各自模块里追加统计行。 |
| GameEngine | `assert_invariants` | `(self) -> None` | 校验当前状态满足各项游戏不变量（供测试使用）。 |

## 核心系统（194 项）

### `weiren_game/systems/ability_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class AbilitySystemMixin**` | `` |  |
| AbilitySystemMixin | `_set_ability_cooldown` | `(self, tenant: Tenant, ability_id: str, until: int) -> None` | 把某主动技能的冷却写到其 AbilityState.cooldown_until。 |
| AbilitySystemMixin | `_mark_ability_used` | `(self, tenant: Tenant, ability_id: str) -> None` | 记录本回合已使用：冷却至少延到下一回合（不覆盖更长冷却）。 |
| AbilitySystemMixin | `_local_skill_module` | `(self, character_id: str)` | 返回角色档案模块（用于读取技能本地提供者）。 |
| AbilitySystemMixin | `_gate_local_skill` | `(self, actor: Tenant, ability: object, *, option: object, forced: bool, bypass: bool) -> None` | 公共技能门槛：本地条件判定 → 公共消耗流程（强制时代替为默认代价）。 |
| AbilitySystemMixin | `available_abilities` | `(self, tenant_id: int) -> list[tuple[str, str, str]]` | 返回指定房客可用主动能力的（能力id、名称、描述）列表。 |
| AbilitySystemMixin | `_ability_failed` | `(self, actor: Tenant, ability_id: str) -> bool` | 按房客状态累计失败概率并判定本次主动能力是否失效，同时结算该角色替身的暴露。 |
| AbilitySystemMixin | `use_ability` | `(self, actor_id: str, target_id: str \| None=None, ability_id: str \| None=None, option: str \| None=None, amount: int \| None=None, copied_ability_id: str \| None=None, secondary_target_id: str \| None=None, secondary_option: str \| None=None, secondary_amount: int \| None=None, force_max_amount: bool=False, forced: bool=False, _bypass_limits: bool=False) -> Any` | 校验阶段与冷却限制后执行主动能力，按角色分发到具体效果并记录行动日志。 |
| AbilitySystemMixin | `_mark_ability_failed` | `(self, reason: str='') -> None` | 技能私有失败标记：由可能失败的技能在失败分支调用。 |
| AbilitySystemMixin | `_run_ability_outcome` | `(self, actor: Tenant, ability_id: str) -> None` | 按“是否失败”派发 ability.used / ability.failed 节点。 |
| AbilitySystemMixin | `_skill_outcome` | `(self, actor: object, skill_id: str, success: bool) -> None` | 记录概率类技能本次的成功/失败（聚合，先不派发，避免多次判定）。 |
| AbilitySystemMixin | `_flush_skill_outcomes` | `(self) -> None` | 结算边界：每个技能按“是否至少成功一次”派发 used/failed。 |
| AbilitySystemMixin | `_expel_tenant` | `(self, tenant: Tenant, source: str, *, sanity_exempt_ids: set[str] \| None=None) -> None` | 驱逐指定房客：视同屋内死亡（仅播报不同），并结算同伴的理智损失。 |

### `weiren_game/systems/condition_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class ConditionSystemMixin**` | `` |  |
| ConditionSystemMixin | `_emotion_key_of` | `(self, tenant: Tenant, condition: Condition) -> str \| None` | 把 condition 反查为情绪键；非情绪条件返回 None。 |
| ConditionSystemMixin | `_notify_emotion_increase` | `(self, tenant: Tenant, key: str) -> None` | 情绪强度/层数增加后通知当前伪人场景（如洋葱“情绪显现”置 shown）。 |
| ConditionSystemMixin | `_condition_extra_effect_active` | `(self, tenant: Tenant, condition_name: str) -> bool` | 判断创伤/紊乱的额外效果是否未被止痛药压制、可以生效。 |
| ConditionSystemMixin | `_add_condition` | `(self, tenant: Tenant, condition: Condition, intensity: int, layers: int, source: str) -> bool` | 按字面量为创伤/紊乱直接追加强度与层数（可跨越 3/6/9 档），返回是否发生改变。 |
| ConditionSystemMixin | `_status_avoidance` | `(self, tenant: Tenant, condition: Condition, source: str) -> bool` | 判定本次状态施加是否被「免疫充能」或护甲抵挡。 |
| ConditionSystemMixin | `_set_condition` | `(self, tenant: Tenant, condition: Condition, intensity: int, layers: int, source: str) -> bool` | 将创伤/紊乱设定为目标强度与层数：目标强度更高则覆盖，否则按强度差概率提升层数。 |
| ConditionSystemMixin | `_worsen_condition` | `(self, tenant: Tenant, condition: Condition, times: int, source: str) -> int` | 按概率表尝试“恶化”创伤/紊乱若干次（低生命时追加次数），返回成功次数。 |
| ConditionSystemMixin | `_extend_condition` | `(self, tenant: Tenant, condition: Condition, times: int, source: str) -> int` | 按概率表尝试“延长”创伤/紊乱（增加层数，未激活则先激活），返回成功次数。 |
| ConditionSystemMixin | `_recover_condition` | `(condition: Condition, layers: int, intensity: int) -> None` | 按“先减层数、再减强度”的顺序削减创伤/紊乱，层数清零即移除状态。 |
| ConditionSystemMixin | `_emotion_application_blocked` | `(self, tenant: Tenant, key: str, source: str) -> bool` | 判断该情绪施加是否被拦截。 |
| ConditionSystemMixin | `_awakening_gain_multiplier` | `(self, tenant: Tenant) -> float` | 返回该性格性格及其羁绊档位对觉醒情绪获取量的放大系数。 |
| ConditionSystemMixin | `_apply_emotion` | `(self, tenant: Tenant, key: str, intensity: int, layers: int, source: str, *, scale_awakening: bool=True) -> bool` | 直接为单个情绪增加强度与层数（觉醒情绪按该性格系数放大，稀有情绪压回强度 1）。 |
| ConditionSystemMixin | `_strengthen_named_emotion` | `(self, tenant: Tenant, key: str, intensity: int, layers: int, source: str) -> bool` | 对单个情绪执行概率性恶化/延长（觉醒情绪先套用该性格增益）。 |
| ConditionSystemMixin | `_emotion_weighted_key` | `(self, tenant: Tenant, keys: Sequence[str], event_id: str \| int, event_suffix: Sequence[object]=()) -> str` | 按各情绪当前强度加权，从候选中随机选出一个情绪键。 |
| ConditionSystemMixin | `_adjust_emotion_set` | `(self, tenant: Tenant, group: str, intensity: int, layers: int, source: str) -> None` | 将直接增减量按手稿权重分摊到侵蚀/觉醒情绪组。 |
| ConditionSystemMixin | `_strengthen_emotion_set` | `(self, tenant: Tenant, group: str, intensity: int, layers: int, source: str) -> None` | 对侵蚀/觉醒情绪组执行概率性恶化/延长，避开 3/6/9 档并必要时落向稀有情绪。 |
| ConditionSystemMixin | `_reduce_emotion_set` | `(self, tenant: Tenant, group: str, intensity: int, layers: int, maximum_intensity: int=10) -> None` | 在情绪组内逐次削减当前强度最低的活跃情绪。 |
| ConditionSystemMixin | `_apply_status_end` | `(self, tenant: Tenant, condition: Condition, *, physical: bool, label: str) -> None` | 回合末演化创伤/紊乱：按强度损失生命/理智，并概率自发恶化、衰减层数。 |
| ConditionSystemMixin | `_apply_emotion_end` | `(self, tenant: Tenant, condition: Condition, label: str) -> None` | 回合末演化情绪：按强度/层数概率自发恶化并固定衰减一层。 |

### `weiren_game/systems/cost_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class CostSystemMixin**` | `` |  |
| CostSystemMixin | `_forced_cost_terms` | `(self, branch: object) -> list[object]` | 被强制发动时的 cost 条目：优先技能自带 forced_terms，否则用公共默认。 |
| CostSystemMixin | `_select_branch` | `(self, ability: object, *, option: str \| None=None, forced: bool=False) -> object` | 按 option / 强制标志选择本次使用的 Branch。 |
| CostSystemMixin | `_resolve_branch_cost` | `(self, branch: object, *, payer: object, target: object \| None, forced: bool, include_optional: bool) -> list[object]` | 把分支 cost 侧解析成“本次实际要支付”的条目列表。 |
| CostSystemMixin | `_expr_error` | `(self, expr: object, tag_map: dict[str, object], *, payer: object, target: object \| None, forced: bool, include_optional: bool) -> str \| None` | 计算 cost 表达式的首个不可满足错误；or 分支任一满足即通过。 |
| CostSystemMixin | `_collect_expr` | `(self, expr: object, tag_map: dict[str, object], *, payer: object, target: object \| None, forced: bool, include_optional: bool) -> list[object]` | 按 and/or 语义挑选本次实际支付的 cost 条目。 |
| CostSystemMixin | `_ref_error` | `(self, ref: object, tag_map: dict[str, object], *, payer: object, target: object \| None, forced: bool, include_optional: bool) -> str \| None` | 返回单个表达式引用的不可满足错误（供 or 短路使用）。 |
| CostSystemMixin | `_single_term_error` | `(self, term: object, payer: object) -> str \| None` | 只检查单条 cost Term 是否满足。 |
| CostSystemMixin | `_ability_costs_payable` | `(self, payer: object, costs: list[object], *, target: object \| None=None, forced: bool=False, include_optional: bool=False) -> str \| None` | 侦测一组 cost Term：返回第一条无法满足的原因，满足则 None。 |
| CostSystemMixin | `_cost_pack_payable` | `(self, payer: object, ability: object, *, option: str \| None=None, target: object \| None=None, forced: bool=False, include_optional: bool=False) -> str \| None` | 按技能分支选择后统一侦测。 |
| CostSystemMixin | `_pay_ability_costs` | `(self, payer: object, costs: list[object], *, target: object \| None=None, forced: bool=False, include_optional: bool=False) -> None` | 支付一组 cost Term（effect Term 不会出现在本层）。 |
| CostSystemMixin | `_pay_cost_pack` | `(self, payer: object, ability: object, *, option: str \| None=None, target: object \| None=None, forced: bool=False, include_optional: bool=False) -> None` | 按技能分支选择后统一支付（普通与强制共用）。 |
| CostSystemMixin | `_resolve_amount` | `(self, term: object, payer: object) -> float` | 解析数量：amount=None 表示取该资源当前最大可用。 |
| CostSystemMixin | `_role_mark_count` | `(self, payer: object, key: str) -> float` | 读取角色的印记资源：统一取自房客印记池。 |
|  | `**class _EmptyBranch**` | `` | 无分支技能的空默认分支（此时本层什么都不扣）。 |
| _EmptyBranch | `__init__` | `(self) -> None` | 构造一个无分支技能的空占位分支。 |

### `weiren_game/systems/information_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class InformationSystemMixin**` | `` |  |
| InformationSystemMixin | `_create_random_information` | `(self, verified: bool, source: str, allowed_kinds: set[str] \| None=None) -> Information` | 随机生成一条信息：按允许种类选择模板或特殊事件并决定真伪，按需立即核实。 |
| InformationSystemMixin | `_observe_visit_information` | `(self, subtype: str, *, character_id: str='', tenant_id: int=0, location_id: str='', returned: bool=True) -> None` | 对应访客事件实际发生时，核实匹配的待验证来访预告并结算结果。 |
| InformationSystemMixin | `_observe_pseudo_skill` | `(self, skill_id: str) -> None` | 伪人技能实际触发时，核实其预告信息的真伪并结算。 |
| InformationSystemMixin | `_verify_location_information` | `(self, location_id: str) -> None` | 从声明地点搜索归来后，核实该地点的物资与修正信息并结算。 |
| InformationSystemMixin | `_discern_one_information` | `(self, tenant: Tenant, *, false_only: bool=False) -> bool` | 由指定房客的被动效果识破一条待验证信息（可仅限虚假信息）。 |
| InformationSystemMixin | `_verify_information_object` | `(self, info: Information) -> None` | 将单条信息置为证实或证伪状态，记录验证信息并结算其效果。 |
| InformationSystemMixin | `_resolve_information_effect` | `(self, info: Information) -> None` | 按信息种类与最终状态结算具体效果，包括地点修正、情绪揭示与状态模板。 |
| InformationSystemMixin | `_apply_pending_information_effects` | `(self) -> None` | 回合末结算各条待验证状态信息的持续影响，并按固定概率自动核实。 |
| InformationSystemMixin | `_expire_information` | `(self) -> None` | 将超过有效期或使用次数上限的信息标记为已失效。 |
| InformationSystemMixin | `_invalidate_target_information` | `(self) -> None` | 使指向已死亡、离屋或受震房客的状态类信息提前失效。 |
| InformationSystemMixin | `information_text` | `(self, info: Information) -> str` | 返回带状态标签与来源的信息展示文本。 |

### `weiren_game/systems/item_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class ItemSystemMixin**` | `` |  |
| ItemSystemMixin | `_tenant_item_ids` | `(self, tenant: Tenant) -> list[str]` | 返回房客背包当前全部物品 ID（每个实例一条，按槽位顺序）。 |
| ItemSystemMixin | `_tenant_item_group_count` | `(self, tenant: Tenant) -> int` | 按“每实例占一格”计算房客背包当前占用组数。 |
| ItemSystemMixin | `_return_tenant_items` | `(self, tenant: Tenant) -> None` | 把房客背包中的全部物资归还屋主仓库（可堆叠品按堆叠合并）。 |
| ItemSystemMixin | `_spill_tenant_overflow` | `(self, tenant: Tenant) -> None` | 容量缩小时，把超出当前格数的物资移回屋主仓库（不凭空消失）。 |
| ItemSystemMixin | `move_item` | `(self, *, container: str, from_slot: int, to_slot: int, tenant_id: int \| None=None) -> None` | 在仓库或某房客背包内把一件物资移动到指定格（目标已占用则交换）。 |
| ItemSystemMixin | `_item_tag_fn` | `(self, item: ItemDefinition, name: str)` | 按物品 tag 顺序找行为模块里的某个钩子（先命中先执行，找不到返回 None）。 |
| ItemSystemMixin | `_add_house_item` | `(self, item_id: str, durability: int=0, count: int=1)` | 在屋主仓库中创建一个新物品实例并返回它。 |
| ItemSystemMixin | `_merge_house_item` | `(self, item_id: str, amount: int, durability: int=0) -> None` | 按 stack_size 把若干单位并入屋主仓库（可堆叠品合并，否则逐件新实例）。 |
| ItemSystemMixin | `_gain_loot_item` | `(self, item_id: str, event_name: str, *suffix: object) -> None` | 战利品授予：可堆叠品按 obtain_range 掷出数量后并入仓库（不可堆叠固定 1）。 |
| ItemSystemMixin | `_gain_item` | `(self, item_id: str, amount: int=1, *, process_carrier: bool=True) -> None` | 将物品以实例形式加入屋主仓库；信息载体与手机即时兑换为信息。 |
| ItemSystemMixin | `transfer_item` | `(self, from_id: int, to_id: int, item_id: str, *, slot: int \| None=None, target_slot: int \| None=None) -> None` | 把一件物资从一名房客的背包移到另一名房客的背包（可指定目标格）。 |
| ItemSystemMixin | `migrate_carriers` | `(self) -> None` | "获得即兑换"的信息载体（keep=False）不该留存：读档时统一兑换为信息。 |
| ItemSystemMixin | `_take_item` | `(self, item_id: str, inventory=None, *, spot=None) -> int` | 从指定容器（默认屋主仓库）消耗 1 个单位并返回其耐久。 |
| ItemSystemMixin | `_durability_multiplier` | `(self) -> float` | 返回全局耐久消耗倍率（下限为 0）。 |
| ItemSystemMixin | `_fragile_chance` | `(self, base: float, tenant: Tenant \| None=None) -> float` | 计算物品易损概率，叠加羁绊与性格修饰后限制在 5% 至 100%。 |
| ItemSystemMixin | `_consume_durability` | `(self, item_id: str, amount: int, *, tenant: Tenant \| None=None, inventory=None, spot=None) -> bool` | 消耗指定容器（默认屋主仓库）最靠前一件同款耐久品的耐久。 |
| ItemSystemMixin | `equip_item` | `(self, tenant_id: int, item_id: str, *, source_tenant: int \| None=None, slot: int \| None=None, target_slot: int \| None=None) -> None` | 行动阶段把一件物资装入指定屋内房客的背包（可指定来源与目标格）。 |
| ItemSystemMixin | `unequip_item` | `(self, tenant_id: int, item_id: str, *, slot: int \| None=None, target_slot: int \| None=None) -> None` | 卸下房客携带的物品，连同耐久放回物资栏（可指定目标格）。 |
| ItemSystemMixin | `use_item` | `(self, item_id: str, tenant_id: int \| None=None, condition: str \| None=None, *, source_tenant: int \| None=None, slot: int \| None=None) -> None` | 行动阶段使用物资：校验限制后分派至医疗、镇痛或普通消耗流程。 |
| ItemSystemMixin | `_spend_item_use` | `(self, item_id: str, item: ItemDefinition, tenant: Tenant \| None=None, cost: int \| None=None, *, inventory=None, spot=None) -> None` | 按耐久、消耗品或易损规则结算一次物品使用代价。 |
| ItemSystemMixin | `_use_general_item` | `(self, item: ItemDefinition, tenant: Tenant, *, inventory=None, spot=None) -> None` | 经 on_use 效果注册表执行普通消耗品效果，并结算使用代价与该角色加成。 |

### `weiren_game/systems/marks_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class MarksSystemMixin**` | `` | 通用印记机制（种类与上下限由角色档案的 MARKS 声明）。 |
| MarksSystemMixin | `_mark_definition` | `(self, tenant: object, mark_id: str)` | 返回该角色某印记的定义（无则 None）。 |
| MarksSystemMixin | `_mark_count` | `(self, tenant: object, mark_id: str) -> float` | 返回该房客某印记的累计数值。 |
| MarksSystemMixin | `_gain_mark` | `(self, tenant: object, mark_id: str, amount: float=1.0, *, external: bool=False)` | 获得印记（按定义上限钳制），派发 mark.gained / mark.reached。 |
| MarksSystemMixin | `_consume_mark` | `(self, tenant: object, mark_id: str, amount: float=1.0, *, external: bool=False) -> float` | 消耗印记（实例编号最小者优先），派发 mark.consumed，返回实际消耗。 |
| MarksSystemMixin | `_dispatch_mark_node` | `(self, kind: str, tenant: object, mark_id: str, amount: float) -> None` | 按 gained/consumed/reached 派发印记节点钩子。 |
| MarksSystemMixin | `_emit_node` | `(self, node: str, **context: object) -> None` | 派发通用内容节点（door.* / item.* / bond.* / tenant.* 等）。 |
| MarksSystemMixin | `_set_global_event` | `(self, event_id: str, value: float=0.0, layers: int=1) -> None` | 设置/刷新一个全局事件（世界级条件）。 |
| MarksSystemMixin | `_global_event_active` | `(self, event_id: str) -> bool` | 全局事件是否生效。 |
| MarksSystemMixin | `_global_event_value` | `(self, event_id: str, default: float=0.0) -> float` | 全局事件数值（未生效返回默认值）。 |
| MarksSystemMixin | `_consume_global_event` | `(self, event_id: str) -> object` | 一次性消费一个全局事件（返回实例或 None）。 |
| MarksSystemMixin | `_decay_global_events` | `(self) -> None` | 回合末：全部全局事件剩余回合 -1，归 0 移除。 |
| MarksSystemMixin | `_apply_modifiers` | `(self, effect_type: str, base: float, source: object=(), context: object=None) -> float` | 统一入口：收集某通道的修饰器并编译（不含概率收敛）。 |
| MarksSystemMixin | `_eval_gate` | `(self, gate_type: str, source: object=(), context: object=None, base: bool=False) -> bool` | 统一闸门入口：收集某闸门的贡献项并做逻辑聚合。 |
| MarksSystemMixin | `_suppress_pseudo` | `(self, layers: int, capabilities: object=None) -> None` | 禁用伪人的指定行为位（默认 visit/cast/breakthrough/auto_expel）。 |
| MarksSystemMixin | `_pseudo_capability` | `(self, name: str) -> bool` | 伪人某行为位是否可用（未处于对应禁用事件中）。 |
| MarksSystemMixin | `_pseudo_enters_house` | `(self) -> bool` | 当前伪人是否会亲自到访（推动门口事件）。 |
| MarksSystemMixin | `_has_persona` | `(self, tenant: object, persona: str) -> bool` | 房客是否持有某个人设（人设即隐藏 condition）。 |
| MarksSystemMixin | `_personas_of` | `(self, tenant: object) -> list[str]` | 返回房客当前持有的人设列表（按状态表内顺序）。 |
| MarksSystemMixin | `_set_personas` | `(self, tenant: object, values: list[str]) -> None` | 整体设置房客人设（清除未列出的，写入列出的）。 |

### `weiren_game/systems/personality_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class PersonalitySystemMixin**` | `` |  |
| PersonalitySystemMixin | `_tenant_personalities` | `(self, tenant: Tenant) -> tuple[str, str]` | 返回房客当前的主/副性格（按权重表顺序，缺省回退到角色默认值）。 |
| PersonalitySystemMixin | `_is_personality` | `(self, tenant: Tenant, personality: str) -> bool` | 判断房客是否具备指定性格：需存活、未休克且消沉值低于 1001。 |
| PersonalitySystemMixin | `_personality_weights` | `(self) -> dict[str, float]` | 汇总各房客主/副性格的羁绊权重（跳过休克与高消沉房客）。 |
| PersonalitySystemMixin | `bond_levels` | `(self) -> dict[str, int]` | 将性格权重折算为羁绊等级：由各人格模块声明取整规则。 |
| PersonalitySystemMixin | `_bond_tier` | `(self, personality: str, level: int \| None=None) -> int` | 根据羁绊等级返回该性格达到的最高档位（默认由当前羁绊等级换算）。 |
| PersonalitySystemMixin | `_activate_new_bonds` | `(self, *, initial: bool=False) -> None` | 激活达到门槛的新羁绊：档位与激活奖励由各人格模块声明。 |
| PersonalitySystemMixin | `_passive_available` | `(self, tenant: Tenant, event_id: str='passive') -> bool` | 判定被动本回合是否可用：休克直接禁用，创伤/紊乱与高消沉增加失效概率。 |

### `weiren_game/systems/pseudo_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class PseudoSystemMixin**` | `` |  |
| PseudoSystemMixin | `_roll_next_pseudo_visit` | `(self, after_turn: int) -> int` | 伪人到访日历：每次未到访按难度递增概率，到访后回到起始概率。 |
| PseudoSystemMixin | `_pseudo_actions_suppressed` | `(self) -> bool` | 当前伪人“主动行为（cast）”是否被禁用（描述层称“压制”）。 |
| PseudoSystemMixin | `pseudo_in_house` | `(self) -> bool` | 屋内是否**真的有**伪人（替身已回屋）。 |
| PseudoSystemMixin | `_skill_respond_skill` | `(self, skill: str, stage: str, *, mode: str, caster: object, target: Tenant \| None=None, mission: SearchMission \| None=None, event: str \| None=None, penalty: float \| None=None) -> bool` | 技能响应技能：返回 True 表示该响应阻止了本次技能。 |
| PseudoSystemMixin | `_target_lock_responder` | `(self, tenant: Tenant, event: str, penalty: float) -> bool` | 目标锁定响应：该角色/该角色等让技能无法选中该目标。 |
| PseudoSystemMixin | `_search_resist_responder` | `(self, mission: SearchMission, tenant: Tenant, event: str, penalty: float) -> bool` | 搜索抵御响应：携带防具与该角色“走你！”。 |
| PseudoSystemMixin | `_resolve_pseudo_visit` | `(self) -> None` | 结算伪人到访：压制期无效果，首次到访揭示伪人，之后按伪人种类触发拜访逻辑。 |
| PseudoSystemMixin | `_attempt_breakthrough` | `(self, reason: str) -> bool` | 尝试结算一次伪人突破：先处理回溯与房客守卫等防御，未被阻止则宣布失败。 |
| PseudoSystemMixin | `_pseudo_attack_searchers` | `(self) -> None` | 按遭遇概率逐一对在外搜索的房客发起伪人袭击，并按伪人类型结算袭击效果。 |
| PseudoSystemMixin | `_scenario_resist_penalty` | `(self) -> float` | 返回当前伪人场景注册的搜索抵御惩罚（缺省 0）。 |
| PseudoSystemMixin | `_pseudo_encounter_chance` | `(self, mission: SearchMission, tenant: Tenant) -> float` | 计算伪人对指定搜索房客的遭遇概率（综合状态、携带物与被动修正）。 |
| PseudoSystemMixin | `_break_search_tool` | `(self, mission: SearchMission, tenant: Tenant, item_id: str) -> None` | 将损坏的防具工具从任务携带中移除并重算搜索参数。 |
| PseudoSystemMixin | `_set_pseudo_marks` | `(self, target: float) -> bool` | 外界把伪人印记直接改写为 target；受“不可被外界修改”声明保护。 |
| PseudoSystemMixin | `_pseudo_handler` | `(self, name: str)` | 返回当前伪人场景注册的处理器（无则 None）。 |
| PseudoSystemMixin | `accusation_evidence` | `(self, tenant_id: int) -> dict` | 纯查询：该房客名下有效的指认信息进度（供 UI 判断屋主能否直接驱逐）。 |
| PseudoSystemMixin | `accuse` | `(self, tenant_id: int) -> None` | 屋主指认某房客为伪人：满足证据条件时按目标真伪驱逐替身或误逐房客。 |

### `weiren_game/systems/random_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class RandomSystemMixin**` | `` |  |
| RandomSystemMixin | `_rng` | `(self, event_id: str \| int, *suffix: object) -> random.Random` | 按回合、事件 ID 与调用次数取得确定性随机源，并递增调用计数。 |
| RandomSystemMixin | `_seeded_rng` | `(self, *parts: object) -> random.Random` | 用种子与参数派生确定性随机源，保证同一局结果可复现。 |
| RandomSystemMixin | `_mission_rng` | `(self, mission: SearchMission, stream: str, index: int=0) -> random.Random` | 为指定搜索任务派生独立的确定性随机源。 |
| RandomSystemMixin | `_weighted_choice` | `(self, values: Iterable[tuple[Any, float]], event_id: str \| None=None, rng: random.Random \| None=None, event_suffix: Sequence[object]=()) -> Any` | 按权重从候选中随机选取一项并返回。 |
| RandomSystemMixin | `discover` | `(self, pool: Sequence[Any], *, count: int=3, constraint: Callable[[Any], bool] \| None=None, required: Sequence[Any] \| None=None, event_id: str \| None=None, event_suffix: Sequence[object]=()) -> list[Any]` | 发现（discover）：按种子从候选池抽出 ``count`` 个互不重复的选项。 |
| RandomSystemMixin | `_weighted_sample` | `(self, entries: Sequence[tuple[Any, float]], count: int, rng: random.Random, required: Sequence[Any] \| None=None) -> list[Any]` | 按权重不放回抽 ``count`` 个；``required`` 中的值保证至少出现一个。 |
| RandomSystemMixin | `_weighted_pick` | `(entries: Sequence[tuple[Any, float]], rng: random.Random) -> Any` | 按权重随机挑一个（``entries`` 至少一项）。 |
| RandomSystemMixin | `_start_loot_draw` | `(self, pool: Sequence[str], count: int, fortune: float=0.0, *suffix: object) -> list[str]` | 开局补给抽取：按品质权重 × 时运修正从类别池中抽 ``count`` 件（允许重复）。 |

### `weiren_game/systems/round_effects.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class RoundEffectsSystemMixin**` | `` |  |
| RoundEffectsSystemMixin | `_settle_emotion_values` | `(self) -> None` | 结算各房客侵蚀/觉醒情绪对隐藏消沉值的影响，并套用理智区间等修正。 |
| RoundEffectsSystemMixin | `_run_house_item_start_hooks` | `(self) -> None` | 实例回合初·屋主仓库 scope：按 ITEM_HOOKS["turn_start.house"] 扫描。 |
| RoundEffectsSystemMixin | `_settle_tenant_instance_start` | `(self) -> None` | 实例回合初·房客/背包 scope：顺序与重构前一致。 |
| RoundEffectsSystemMixin | `_settle_pseudo_start_handlers` | `(self) -> None` | 实例回合初·伪人 scope：start_passive/performance 查 SCENARIO_HANDLERS。 |
| RoundEffectsSystemMixin | `_start_of_turn_effects` | `(self) -> None` | 回合初实例节点总调度：屋主仓库→房客/背包→羁绊→房客光环→伪人。 |
| RoundEffectsSystemMixin | `_settle_base_end_effects` | `(self) -> None` | 结算回合末基础消耗：按人物/羁绊修正汇总理智消耗与高生命自然流失。 |
| RoundEffectsSystemMixin | `_settle_buff_debuff_effects` | `(self) -> None` | 回合末依次结算创伤、紊乱及各情绪的自行演化。 |
| RoundEffectsSystemMixin | `_decay_conditions` | `(self) -> None` | 回合末公共衰减：所有状态层数 -1，归零移除。 |
| RoundEffectsSystemMixin | `_settle_held_items` | `(self) -> None` | 回合末结算房客**携带中的物资**：先发实例钩子（内容按 item_id 登记）， |
| RoundEffectsSystemMixin | `_grant_learned_passive` | `(self, tenant: Tenant, ability_id: str) -> None` | 把书籍研读获得的永久被动登记为该房客的 learned 技能状态。 |
| RoundEffectsSystemMixin | `_settle_other_end_effects` | `(self) -> None` | 结算其余回合末效果：高生命自然回复、休克与离屋判定，并清理临时全局修正。 |
| RoundEffectsSystemMixin | `_settle_turn_end_status_effects` | `(self) -> None` | 回合末状态效果：让各 condition 在自己的回合末效果节点兑现。 |
| RoundEffectsSystemMixin | `_run_status_effect_node` | `(self, node: str, tenant: Tenant \| None=None) -> None` | 执行状态效果节点：传入房客时只处理该房客，缺省扫描全体屋内房客。 |
|  | `_difficulty_sanity_modifier` | `(context: object)` | 难度：回合末理智消耗修正。 |

### `weiren_game/systems/search_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class SearchSystemMixin**` | `` |  |
| SearchSystemMixin | `_quality_matches` | `(selector: str, quality: int) -> bool` | 判断品质选择器（如 low/high/blue/gold 等）是否匹配给定品质等级。 |
| SearchSystemMixin | `_random_item` | `(self, *, required_tags: Sequence[str]=(), minimum_quality: int=0, fortune: float=0.0, event_id: str='item.any', event_suffix: Sequence[object]=()) -> str` | 按最低品质与标签约束加权随机返回一件可搜索物资的 id。 |
| SearchSystemMixin | `_active_location_modifiers` | `(self, location_id: str) -> list[dict[str, float]]` | 返回指定地点当前已证实且仍在生效的信息修正定义列表。 |
| SearchSystemMixin | `_consume_location_modifier_uses` | `(self, location_id: str) -> None` | 消耗指定地点的信息修正使用次数，用尽时将该信息置为失效。 |
| SearchSystemMixin | `_loot_for_mission` | `(self, mission: SearchMission, behavior_index: int) -> str` | 按行为序号结算一次搜索掉落：经品质与标签加权后返回具体物资 id。 |
| SearchSystemMixin | `_search_carry` | `(self, tenant: Tenant) -> int` | 返回房客当前的搜索携带容量（优先取覆盖值，否则取角色定义值）。 |
| SearchSystemMixin | `tenant_carry_capacity` | `(self, tenant: Tenant) -> int` | 房客当前携带格数 = 角色基础容量 + 性格/物资的「携带」修饰。 |
| SearchSystemMixin | `start_search` | `(self, tenant_id: int, location_id: str) -> None` | 校验条件后发起一次搜索：确定时长、成功率与随机序列，创建任务并派出房客。 |
| SearchSystemMixin | `_recalculate_search` | `(self, mission: SearchMission) -> None` | 重算搜索任务的成功行为索引、奖励与满载行为，推算出实际返回回合。 |
| SearchSystemMixin | `_advance_searches_and_returns` | `(self) -> None` | 推进各搜索任务一个回合，对到期的任务执行返回结算并清出列表。 |
| SearchSystemMixin | `_resolve_search_return` | `(self, mission: SearchMission, tenant: Tenant) -> None` | 结算单个搜索任务的返回：处理濒死/死亡、归途伤害、奖励入库与装备损耗。 |
| SearchSystemMixin | `_settle_search_bag_items` | `(self, mission: SearchMission, tenant: Tenant) -> None` | 结算房客背包在搜索返程中的耐久消耗、易损损耗与可能的破损。 |
|  | `_search_status_modifier` | `(context: object)` |  |
|  | `_difficulty_search_modifier` | `(context: object)` |  |

### `weiren_game/systems/value_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class ValueSystemMixin**` | `` |  |
| ValueSystemMixin | `_health_protection_multiplier` | `(self, tenant: Tenant, amount: float, *, consume: bool) -> float` | 返回需转嫁的固定量（减伤本身已由 healthConsume/healthDamage 修饰器处理）。 |
| ValueSystemMixin | `_consume_held_durability` | `(self, tenant: Tenant, held: ItemInstance, amount: int) -> bool` | 消耗装备耐久，损坏时移除装备并返回 True。 |
| ValueSystemMixin | `_apply_armour` | `(self, tenant: Tenant, amount: float) -> float` | 按最先装备的护甲减免本次伤害并消耗对应耐久。 |
| ValueSystemMixin | `_damage_health` | `(self, tenant: Tenant, amount: float, source: str) -> float` | 对房客造成生命伤害，应用难度倍率、护甲与减伤并结算该性格分担。 |
| ValueSystemMixin | `_consume_health` | `(self, tenant: Tenant, amount: float, source: str) -> float` | 尝试消耗指定量生命（不足则失败），受修饰影响并可转嫁为理智消耗。 |
| ValueSystemMixin | `_loss_health` | `(self, tenant: Tenant, amount: float, source: str) -> float` | 按流失语义扣减生命，并应用回合末人物/性格修饰。 |
| ValueSystemMixin | `_restore_health` | `(self, tenant: Tenant, amount: float, source: str=TEXT['systems.value_system._restore_health.1']) -> float` | 回复生命至上限，返回实际回复量。 |
| ValueSystemMixin | `_consume_sanity` | `(self, tenant: Tenant, amount: float, source: str) -> float` | 尝试消耗指定量理智（不足则失败），可转嫁为生命伤害。 |
| ValueSystemMixin | `_damage_sanity` | `(self, tenant: Tenant, amount: float, source: str) -> float` | 对理智造成包含难度倍率的伤害。 |
| ValueSystemMixin | `_loss_sanity` | `(self, tenant: Tenant, amount: float, source: str) -> float` | 以流失语义扣减理智（不设下限）。 |
| ValueSystemMixin | `_reduce_sanity` | `(self, tenant: Tenant, amount: float, source: str, *, floor_zero: bool, change_type: str) -> float` | 统一削减理智：应用冻结保护、角色减半等修饰并触发后续效果。 |
| ValueSystemMixin | `_restore_sanity` | `(self, tenant: Tenant, amount: float, source: str=TEXT['systems.value_system._restore_sanity.1']) -> float` | 回复理智；溢出多少、怎么用，交给内容层（发 `sanity.restored` 节点）。 |
| ValueSystemMixin | `_after_health_decrease` | `(self, tenant: Tenant, amount: float) -> None` | 生命下降后结算内容层登记的角色连锁（`CHARACTER_VALUE_HOOKS`）。 |
| ValueSystemMixin | `_after_health_changed` | `(self) -> None` | 生命数值变动后的角色光环统一入口（按注册表执行）。 |
| ValueSystemMixin | `_natural_high_health_recovery` | `(self, tenant: Tenant) -> None` | 高生命房客在回合末按概率自然恢复创伤/紊乱。 |
|  | `_difficulty_health_damage_modifier` | `(context: object)` | 难度：生命伤害的最终百分比乘算。 |
|  | `_difficulty_sanity_damage_modifier` | `(context: object)` | 难度：理智伤害的最终百分比乘算。 |

### `weiren_game/systems/visitor_system.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class VisitorSystemMixin**` | `` |  |
| VisitorSystemMixin | `_return_departed_tenants` | `(self) -> None` | 为到达返回回合且尚无事件的暂时离开房客生成敲门事件。 |
| VisitorSystemMixin | `_queue_scheduled_visitors` | `(self) -> None` | 按伪人到访日程生成门口事件，伪人未到期则排队普通访客，并补入额外访客。 |
| VisitorSystemMixin | `_queue_human_visitor` | `(self, reason: str \| None=None, *, force_supply: bool=False) -> None` | 从访客名册排队一位人类访客；名册为空时视规则改为补给事件。 |
| VisitorSystemMixin | `handle_next_door_event` | `(self, decision: str='inspect') -> None` | 处理门口首个事件：按类型结算人类接纳/拒绝、补给领取或伪人到访。 |
| VisitorSystemMixin | `_visitor_arrived` | `(self, *, counts_as_visit: bool=False) -> None` | 访客到达的统一结算：按条件累计伪人恐惧印记。 |
| VisitorSystemMixin | `_pseudo_visitor_mark` | `(self) -> None` | 访客到达标记：由当前伪人场景注册的 visitor_mark 决定是否累加。 |
| VisitorSystemMixin | `_on_tenant_accepted` | `(self, tenant: Tenant) -> None` | 新房客入住时结算其带来的赠礼（该角色、该角色、该角色等）。 |
| VisitorSystemMixin | `_on_accept_healing` | `(self, accepted: Tenant \| None) -> None` | 按该性格性格与羁绊等级，为屋内房客结算接纳访客时的治愈效果。 |

## 效果内核（52 项）

### `weiren_game/modifier_rules.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class Modifier**` | `` | 一个修饰器对象（定义，无实例）。 |
|  | `register_modifier` | `(modifier: Modifier) -> None` | 登记一个修饰器到其调用点。 |
|  | `_source_tokens` | `(source: object) -> set[str]` |  |
|  | `_matches` | `(modifier: Modifier, tokens: set[str]) -> bool` | 修饰器是否命中：不写 path = 全命中；any=有交集，all=子集。 |
|  | `modifiers_for` | `(effect_type: str, source: object=()) -> list[Modifier]` | 返回订阅该通道、且 ``path ∩ source ≠ ∅`` 的修饰器。 |
|  | `flat_add` | `(effect_type: str, value: float, path: tuple[str, ...]=(), modifier_id: str='') -> Modifier` | 简写：普通固定加算（游戏内最常用之一）。 |
|  | `percent_add` | `(effect_type: str, value: float, path: tuple[str, ...]=(), modifier_id: str='') -> Modifier` | 简写：普通百分比加算（游戏内最常用之一）。 |
|  | `**class _Spec**` | `` | 链式构造器：``spec(effect_type).final().percent(...)...``。 |
| _Spec | `__init__` | `(self, effect_type: str) -> None` |  |
| _Spec | `normal` | `(self) -> '_Spec'` |  |
| _Spec | `final` | `(self) -> '_Spec'` |  |
| _Spec | `flat` | `(self, value: float) -> '_Spec'` |  |
| _Spec | `percent` | `(self, value: float) -> '_Spec'` |  |
| _Spec | `mul` | `(self, value: float, limit: float \| None=None) -> '_Spec'` |  |
| _Spec | `max` | `(self, value: float) -> '_Spec'` |  |
| _Spec | `min` | `(self, value: float) -> '_Spec'` |  |
| _Spec | `certain` | `(self, value: float) -> '_Spec'` |  |
| _Spec | `path` | `(self, *tags: str) -> '_Spec'` |  |
| _Spec | `source` | `(self, *tags: str) -> '_Spec'` |  |
| _Spec | `id` | `(self, modifier_id: str) -> '_Spec'` |  |
| _Spec | `match` | `(self, mode: str) -> '_Spec'` |  |
| _Spec | `build` | `(self) -> Modifier` |  |
|  | `spec` | `(effect_type: str='') -> _Spec` | 开始链式声明一个修饰器。 |
|  | `register_modifier_provider` | `(effect_type: str, provider: object) -> None` | 登记一个“条件满足时返回修饰器”的提供者。 |
|  | `collect_modifiers` | `(effect_type: str, source: object=(), context: object=None) -> list[Modifier]` | 收集某调用点当前应生效的全部修饰器（静态 + 条件式 provider）。 |
|  | `_signed_limit` | `(limit: float, change: float) -> float` | 把 limit 归一到与变化量同号的方向。 |
|  | `_within_limit` | `(change: float, limit: float) -> bool` | 该修饰器自身产生的变化量是否落在 limit 允许范围内。 |
|  | `calculate_modified_amount` | `(base: float, modifiers: object) -> float` | 按规格顺序编译一组（已判定生效的）修饰器，返回最终数值。 |
|  | `**class Gate**` | `` | 一个布尔闸门的贡献项（定义，无实例）。 |
|  | `register_gate` | `(gate_item: object) -> None` | 登记一个闸门贡献项到其闸门键。 |
|  | `register_gate_provider` | `(gate_type: str, provider: object) -> None` | 登记一个「条件满足时返回闸门贡献」的提供者。 |
|  | `gates_for` | `(gate_type: str, source: object=()) -> list[Gate]` | 返回订阅该闸门、且 ``path`` 命中调用点 ``source`` 的静态贡献项。 |
|  | `collect_gates` | `(gate_type: str, source: object=(), context: object=None) -> list[Gate]` | 收集某闸门当前应生效的全部贡献项（静态 + 条件式 provider）。 |
|  | `evaluate_gate` | `(base: bool, gates: object) -> bool` | 逻辑聚合：``any`` 抬为真（OR）、``veto`` 压为假（NOT）。 |
|  | `**class _GateSpec**` | `` | 链式构造器：``gate(gate_type).path(...).match(...).any()/veto()``。 |
| _GateSpec | `__init__` | `(self, gate_type: str) -> None` |  |
| _GateSpec | `path` | `(self, *tags: str) -> '_GateSpec'` |  |
| _GateSpec | `source` | `(self, *tags: str) -> '_GateSpec'` |  |
| _GateSpec | `match` | `(self, mode: str) -> '_GateSpec'` |  |
| _GateSpec | `any` | `(self, value: bool=True) -> '_GateSpec'` | 命中即把闸门抬为真（OR）。 |
| _GateSpec | `veto` | `(self, value: bool=True) -> '_GateSpec'` | 命中即把闸门压为假（NOT / 否决）。 |
| _GateSpec | `id` | `(self, gate_id: str) -> '_GateSpec'` |  |
| _GateSpec | `build` | `(self) -> Gate` |  |
|  | `gate` | `(gate_type: str='') -> _GateSpec` | 开始链式声明一个布尔闸门贡献项。 |

### `weiren_game/probability.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `single_guarantee` | `(value: float) -> float \| None` | 把“必定”值归一为 0.0/1.0；普通概率返回 None。 |
|  | `resolve` | `(base: float, guarantees: object=()) -> float` | 按统一规则结算最终概率。 |

### `weiren_game/effects/health_sanity.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `_permanent_immunity` | `(engine: object) -> bool` | a-10：房客常驻免疫创伤与紊乱（难度词条）。 |
|  | `_consume_immunity` | `(tenant: object) -> bool` | 消耗一点「高生命免疫」充能；强度归零即自然移除。 |
|  | `high_health_status_immunity` | `(engine: object, tenant: object, source: str='') -> bool` | 创伤/紊乱的状态施加闸门（原稿：生命 ≥95 且无创伤/紊乱时，每回合首次免疫）。 |
|  | `refresh_high_health_immunity` | `(engine: object, tenant: object) -> None` | 回合开始：满足「生命 ≥95 且无创伤/紊乱」则给予 1 强度 1 层。 |
|  | `decay_high_health_immunity` | `(engine: object, tenant: object) -> None` | 回合末：未被消耗的免疫扣 1 层，层数归零即消失（a-10 常驻不衰减）。 |
|  | `grant_permanent_trauma_disorder_immunity` | `(engine: object, tenant: object) -> None` | a-10：房客入住时一次性获得 99 点免疫充能（常驻免疫）。 |

## 内容边界与包管理（71 项）

### `weiren_game/content.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class ContentManager**` | `` | 内容注册/查询的统一入口。 |
| ContentManager | `__init__` | `(self) -> None` | 绑定共享内容包并初始化已装载包名单。 |
| ContentManager | `ensure_base` | `(self) -> None` | 校验内置 base 内容包在位；缺失视为启动失败。 |
| ContentManager | `register_character` | `(self, definition: object, *, replace: bool=False) -> None` | 登记一位房客档案（``replace`` 允许高位内容包覆盖同 id）。 |
| ContentManager | `register_character_module` | `(self, character_id: str, module: object) -> None` | 登记角色行为模块。 |
| ContentManager | `register_item` | `(self, item: object, *, category: str, replace: bool=False) -> None` | 登记一件物资（``replace`` 允许高位内容包覆盖同 id）。 |
| ContentManager | `register_item_hook` | `(self, item_id: str, node_map: object) -> None` | 登记一件物资的生命周期 hook（与共享 ITEM_HOOKS 原位合并）。 |
| ContentManager | `register_item_effect` | `(self, item_id: str, effect: object) -> None` | 登记一件指名物的 on_use 效果。 |
| ContentManager | `register_location` | `(self, location: object, *, replace: bool=False) -> None` | 登记一个地点（``replace`` 允许高位内容包覆盖同 id）。 |
| ContentManager | `register_information_template` | `(self, template: object, *, replace: bool=False) -> None` | 登记一条信息模板（``replace`` 允许高位内容包覆盖同 id）。 |
| ContentManager | `register_location_modifier` | `(self, template_id: str, modifier: object) -> None` | 登记地点信息修正。 |
| ContentManager | `register_pseudo` | `(self, module: object, *, replace: bool=False) -> None` | 登记一个伪人场景模块（``replace`` 允许高位内容包覆盖同 id）。 |
| ContentManager | `register_tag_module` | `(self, tag: str, module: object) -> None` | 登记一个 tag 的行为模块。 |
| ContentManager | `register_personality_module` | `(self, personality_id: str, module: object) -> None` | 登记一个性格（羁绊）模块（base 与 DLC 共用同一注册路径）。 |
| ContentManager | `register_status_definition` | `(self, definition: object) -> None` | 登记一个状态定义。 |
| ContentManager | `register_emotion_definition` | `(self, definition: object) -> None` | 登记一个情绪定义（同步键集合、显现标记与 data 层标签表）。 |
| ContentManager | `register_map_group` | `(self, group: str, weight: int=20, *, required: bool=False) -> None` | 把一个地点分组纳入开局抽取。 |
| ContentManager | `register_location_group` | `(self, group: str, label: str, icon: str='i-gate') -> None` | 登记一个地点分组的中文名与图标。 |
| ContentManager | `register_item_tag_label` | `(self, tag: str, label: str) -> None` | 登记一个物品 tag 的中文名。 |
| ContentManager | `register_item_category_label` | `(self, category: str, label: str) -> None` | 登记一个物品分类的中文名。 |
| ContentManager | `register_map_location` | `(self, map_id: str, location_id: str) -> None` | 把某个地点加进已有地图的名单（DLC 想让自己的地点进"城郊小镇"时用）。 |
| ContentManager | `register_item_tag_icon` | `(self, tag: str, icon: str, *, priority: int \| None=None) -> None` | 登记 tag 图标（可选优先序）。 |
| ContentManager | `register_information_kind_label` | `(self, kind: str, label: str) -> None` | 登记一种信息类型的中文名。 |
| ContentManager | `register_resource_pack` | `(self, module: object, *, pack: str='') -> None` | 登记一个资源包模块（贴图零件 ``SYMBOLS`` + 主题 ``THEME``）。 |
| ContentManager | `apply_item_tags` | `(self, tag: str, entries: object) -> None` | 把 tag 合并进命中物品。 |
| ContentManager | `ensure_captured` | `(self) -> None` | 确保 base 快照已抓取（幂等）；**必须在装载任何内容包之前调用**。 |
| ContentManager | `capture_base` | `(self) -> None` | 记录内置 base 的当前注册状态，供运行期装卸 DLC 时回滚。 |
| ContentManager | `overlay_resourcepack_base` | `(self) -> None` | 把**内置材质**（``data/resourcepack/``）重新盖到当前资源包容器上。 |
| ContentManager | `capture_resourcepack_baseline` | `(self) -> None` | 记录"内容包装载完之后"的资源包状态，作为独立资源包的叠加起点。 |
| ContentManager | `restore_resourcepack_baseline` | `(self) -> None` | 把资源包容器回滚到**外观基线**（没有基线时退回 base 材质）。 |
| ContentManager | `restore_base` | `(self) -> None` | 把注册表恢复到 base 快照（撤销所有 DLC 登记）并重置包清单。 |
| ContentManager | `overlay_base` | `(self) -> None` | 让 base **重新赢过**当前注册表里它已有的键（包优先级用）。 |
| ContentManager | `set_packs` | `(self, order: object) -> None` | 按给定顺序（高→低优先级）设置启用包清单；base 恒存在（缺失则垫底）。 |
| ContentManager | `pack_order` | `(self) -> tuple[str, ...]` | 返回启用包清单（**高→低优先级**，含 base）。 |
| ContentManager | `characters` | `(self) -> dict` | 房客档案目录（角色 id → 定义）。 |
| ContentManager | `items` | `(self) -> dict` | 物资目录（item_id → 定义）。 |
| ContentManager | `locations` | `(self) -> dict` | 地点目录（location_id → 定义）。 |
| ContentManager | `pseudos` | `(self) -> dict` | 伪人场景目录（场景键 → 定义）。 |
| ContentManager | `register_pack` | `(self, name: str) -> None` | 登记一个已装载的内容包名。 |
| ContentManager | `manifest` | `(self) -> tuple[str, ...]` | 返回当前启动的启用包清单（含内置 base 包，按名排序）。 |
| ContentManager | `validate_catalogue` | `(self) -> None` | 自检当前内容目录。 |
|  | `_clone` | `(value: object) -> object` | 复制容器（dict/list/set），叶子对象共享；用于可重复的 base 快照。 |

### `weiren_game/config.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class GameConfig**` | `` | 对局外设定（不随存档变化）。 |
|  | `load_config` | `(path: str \| Path=CONFIG_PATH) -> GameConfig` | 读取 config 文件并覆盖默认值；文件缺失/损坏时返回默认配置。 |
|  | `save_config` | `(config: GameConfig, path: str \| Path=CONFIG_PATH) -> Path` | 把配置原子写回文件。 |

### `weiren_game/dlc.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `dlc_root` | `(root: str \| Path \| None=None) -> Path` | 返回 DLC 根目录（默认游戏根目录下的 dlc/）。 |
|  | `available_dlcs` | `(root: str \| Path \| None=None) -> list[Path]` | 列出根目录下可作为 DLC 的文件夹（按名称排序）。 |
|  | `read_manifest` | `(dlc_dir: Path) -> dict[str, Any]` | 读取 DLC 的 dlc.json 元数据；缺失或损坏返回空 dict。 |
|  | `_version_tuple` | `(version: str) -> tuple[int, ...]` | 把版本字符串解析为可比较的整数元组。 |
|  | `import_file` | `(path: Path, module_name: str)` | 按文件路径导入一个 Python 模块。 |
|  | `_dlc_module_name` | `(dlc_name: str, *parts: str) -> str` | 为 DLC 文件生成唯一且可复现的模块名。 |
|  | `load_character_file` | `(path: Path, character_id: str, *, replace: bool=False) -> None` | 注册一个 DLC 角色及其能力模块。 |
|  | `load_item_file` | `(path: Path, *, replace: bool=False) -> None` | 注册一个 DLC 物资文件（CATEGORY + ITEMS）。 |
|  | `load_location_file` | `(path: Path, *, replace: bool=False) -> None` | 注册 DLC 地点；可选 ``MAP_GROUPS`` 把新分组纳入开局抽取。 |
|  | `load_information_file` | `(path: Path, *, replace: bool=False) -> None` | 注册 DLC 信息模板与可选地点修正。 |
|  | `load_pseudo_file` | `(path: Path, *, replace: bool=False) -> None` | 注册一个 DLC 伪人模块（需暴露 DEFINITION、State、HANDLERS）。 |
|  | `load_codex_file` | `(path: Path) -> None` | 装载一个 DLC 图鉴模块：调用其 register(ctx)，或读取 SECTIONS。 |
|  | `_load_dir` | `(dlc_dir: Path, subdir: str, loader, *, pattern: str='*.py', replace: bool \| None=None) -> list[str]` | 装载 ``<包>/<subdir>/<pattern>``：逐文件交给 ``loader``，返回文件名（去扩展名）列表。 |
|  | `load_tag_file` | `(path: Path) -> None` | 把 DLC tags/*.json 合并进现有物品 tag。 |
|  | `load_personality_file` | `(path: Path) -> None` | 注册一个 DLC 性格（羁绊）模块：文件名即性格键。 |
|  | `load_status_file` | `(path: Path) -> None` | 注册一个 DLC 状态/情绪文件（可选暴露 STATUSES、EMOTIONS）。 |
|  | `load_resourcepack_file` | `(path: Path) -> None` | 注册一个资源包文件（贴图零件 ``SYMBOLS`` / 主题 ``THEME``）。 |
|  | `load_tag_behavior_file` | `(path: Path) -> None` | 注册一个 tag 行为模块（文件名即 tag）。 |
|  | `load_maps_dir` | `(dlc_dir: Path) -> list[str]` | 装载资料包自带的 maps/<id>/map.py（一张地图一个文件夹）。 |
|  | `load_single_dlc` | `(name: str, root: str \| Path \| None=None, *, replace: bool=True) -> None` | 装载名为 name 的单个 DLC；重复装载会被跳过。 |
|  | `_normalize_order` | `(order: Sequence[str] \| None, available: set[str]) -> list[str]` | 规整包优先级序列：丢弃未知包名、去重、保证 base 存在（缺失则垫底）。 |
|  | `apply_pack_order` | `(order: Sequence[str], root: str \| Path \| None=None) -> list[str]` | 按**内容包优先级**重建注册表（免重启）。 |
|  | `loaded_dlcs` | `() -> list[str]` | 返回已装载成功的 DLC 名列表。 |
|  | `load_configured_dlc` | `() -> list[str]` | 按总配置 ``pack_order`` 装载启动 DLC（默认只有 base）。 |

### `weiren_game/lifecycle.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class Node**` | `` | 回合级与动作级节点的统一常量。 |
|  | `**class AbilityLaunch**` | `` | A 对 B 发动能力的分类与阶段。 |

## 数据模型与状态（182 项）

### `weiren_game/models.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class SearchMission**` | `` | 一次搜索任务本身的状态；携带物一律从派出房客的背包实时读取。 |
| SearchMission | `from_dict` | `(cls, raw: dict[str, Any]) -> 'SearchMission'` | 将存档字典反序列化为 SearchMission。 |
| SearchMission | `to_dict` | `(self) -> dict[str, Any]` | 将搜索任务状态序列化为字典。 |
|  | `**class DoorEvent**` | `` |  |
|  | `**class Information**` | `` |  |
|  | `**class VisitorState**` | `` | Door-side flow: who is waiting outside and how often they were turned away. |
| VisitorState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'VisitorState'` | 将访客状态字典反序列化为 VisitorState。 |
| VisitorState | `to_dict` | `(self) -> dict[str, Any]` | 将访客状态序列化为字典。 |
|  | `**class LocationState**` | `` | The ten locations available this run. |
| LocationState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'LocationState'` | 将地点状态字典反序列化为 LocationState。 |
| LocationState | `to_dict` | `(self) -> dict[str, Any]` | 将本局可用地点序列化为字典。 |
|  | `**class GameEventState**` | `` | Events waiting at the door plus rule event counters. |
| GameEventState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'GameEventState'` | 将事件字典反序列化为 GameEventState，含门口事件解析。 |
| GameEventState | `to_dict` | `(self) -> dict[str, Any]` | 将门口事件与事件计数序列化为字典。 |
|  | `**class WorldState**` | `` | Everything that happens outside the house doors. |
| WorldState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'WorldState'` | 将世界状态字典反序列化为 WorldState 及各子状态。 |
| WorldState | `to_dict` | `(self) -> dict[str, Any]` | 将门外世界与搜索任务状态序列化为字典。 |
|  | `**class BondState**` | `` | Active personality bonds inside the house. |
| BondState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'BondState'` | 将羁绊状态字典反序列化为 BondState。 |
| BondState | `to_dict` | `(self) -> dict[str, Any]` | 将激活羁绊列表序列化为字典。 |
|  | `**class HouseState**` | `` | Everything owned by the house: tenants, shared inventory and clues. |
| HouseState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'HouseState'` | 将房屋状态字典反序列化为 HouseState，含房客与信息。 |
| HouseState | `to_dict` | `(self) -> dict[str, Any]` | 将房客、物资与信息等房屋状态序列化为字典。 |
|  | `**class SessionLogState**` | `` | Replay snapshots and action history kept outside the rules state. |
| SessionLogState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'SessionLogState'` | 将回放日志字典反序列化为 SessionLogState。 |
| SessionLogState | `to_dict` | `(self) -> dict[str, Any]` | 将回放与行动历史序列化为字典。 |
|  | `**class GameState**` | `` | 分层运行时状态：meta/flow/round/ids/world/house/pseudo_state/ |
| GameState | `__init__` | `(self, *, meta: SaveMetadata, flow: GameFlowState \| None=None, round: RoundActionState \| None=None, ids: InstancePool \| None=None, world: WorldState \| None=None, house: HouseState \| None=None, pseudo_state: PseudoRuntime \| None=None, log: SessionLogState \| None=None) -> None` | 创建分层 GameState，缺省容器以默认状态补齐。 |
| GameState | `to_dict` | `(self, include_history: bool=True) -> dict[str, Any]` | 严格序列化：将各分层状态汇总为存档字典，可排除历史日志。 |
| GameState | `from_dict` | `(cls, raw: dict[str, Any]) -> 'GameState'` | 严格反序列化：由字典构造分层 GameState，未知字段将报错。 |

### `weiren_game/tenant.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `register_container_type` | `(character_id: str, key: str, cls: type) -> None` | 登记一个角色专属容器的类型（由内容侧的 `CONTAINERS` 声明驱动）。 |
|  | `_restore_containers` | `(character_id: str, raw: object) -> dict[str, object]` | 按类型表反序列化专属容器；**没声明过的 key / 坏数据一律跳过**（玩家侧宽容）。 |
|  | `status_caps` | `(status_id: str) -> tuple[int, int]` | 返回已知状态定义的上限（intensity_max, layers_max）。 |
|  | `**class TenantState**` | `` | 单个住户的运行时状态。 |
| TenantState | `__post_init__` | `(self) -> None` | 校验房客 ID 与角色 ID 均非空，否则抛出 ValueError。 |
| TenantState | `home_turns` | `(self) -> int` | 入住回合计数（存于 turn_counters）。 |
| TenantState | `home_turns` | `(self, value: int) -> None` | 设置入住回合计数。 |
| TenantState | `skip_until_turn` | `(self) -> int` | “无法行动”锁到期回合（存于 action_locks["all"]）。 |
| TenantState | `skip_until_turn` | `(self, value: int) -> None` | 设置“无法行动”锁到期回合。 |
| TenantState | `search_locked_until` | `(self) -> int` | 搜索锁到期回合（存于 action_locks["search"]）。 |
| TenantState | `search_locked_until` | `(self, value: int) -> None` | 设置搜索锁到期回合。 |
| TenantState | `condition` | `(self, status_id: str) -> Condition` | 按状态 ID 获取或创建对应的 Condition 实例。 |
| TenantState | `set_status` | `(self, status_id: str, *, intensity: int=1, layers: int=1) -> None` | 设置状态，按注册定义上限钳制强度与层数；无效则移除该状态。 |
| TenantState | `clear_status` | `(self, status_id: str) -> None` | 移除指定状态。 |
| TenantState | `has_ability` | `(self, ability_id: str) -> bool` | 判断住户是否持有指定技能 ID。 |
| TenantState | `ability_state` | `(self, ability_id: str) -> AbilityState \| None` | 返回指定技能 ID 的首个技能状态，未持有则返回 None。 |
| TenantState | `trauma` | `(self) -> Condition` | 创伤状态（conditions["trauma"]）。 |
| TenantState | `trauma` | `(self, value: Condition) -> None` | 整体替换创伤状态。 |
| TenantState | `disorder` | `(self) -> Condition` | 紊乱状态（conditions["disorder"]）。 |
| TenantState | `disorder` | `(self, value: Condition) -> None` | 整体替换紊乱状态。 |
| TenantState | `irritation` | `(self) -> Condition` | 烦躁情绪状态。 |
| TenantState | `irritation` | `(self, value: Condition) -> None` | 整体替换烦躁情绪状态。 |
| TenantState | `reason` | `(self) -> Condition` | 理智（稀有觉醒）情绪状态。 |
| TenantState | `reason` | `(self, value: Condition) -> None` | 整体替换清醒情绪状态。 |
| TenantState | `madness` | `(self) -> Condition` | 癫狂（稀有侵蚀）情绪状态。 |
| TenantState | `madness` | `(self, value: Condition) -> None` | 整体替换癫狂情绪状态。 |
| TenantState | `shock` | `(self) -> int` | 休克强度。 |
| TenantState | `shock` | `(self, value: int) -> None` | 设置休克强度（0..4，与定义上限一致）。 |
| TenantState | `shock_layers` | `(self) -> int` | 休克层数。 |
| TenantState | `shock_layers` | `(self, value: int) -> None` | 设置休克层数（0..99）。 |
| TenantState | `from_dict` | `(cls, raw: dict[str, object]) -> 'TenantState'` | 从字典还原 TenantState，并递归还原嵌套的状态对象。 |
| TenantState | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典，嵌套对象一并转为字典。 |

### `weiren_game/session.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class SaveMetadata**` | `` | 存档封套元数据：版本、随机种子与难度。 |
| SaveMetadata | `from_dict` | `(cls, raw: dict[str, object]) -> 'SaveMetadata'` | 从字典还原 SaveMetadata。 |
| SaveMetadata | `to_dict` | `(self) -> dict[str, str]` | 序列化为普通字典。 |
|  | `**class GameFlowState**` | `` | 回合与流程进度状态（当前回合、阶段、上限与结局标记）。 |
| GameFlowState | `__post_init__` | `(self) -> None` | 校验 phase 属于预定义阶段集合，否则抛出 ValueError。 |
| GameFlowState | `from_dict` | `(cls, raw: dict[str, object]) -> 'GameFlowState'` | 从字典还原 GameFlowState。 |
| GameFlowState | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |
|  | `**class InstancePool**` | `` | 所有实体实例 ID 的唯一分配器。 |
| InstancePool | `allocate_tenant` | `(self) -> int` | 分配下一个房客实例 ID（从 1 起递增）。 |
| InstancePool | `allocate_item` | `(self) -> int` | 分配下一个物品实例 ID（从 1 起递增）。 |
| InstancePool | `allocate_information` | `(self) -> int` | 分配下一个信息实例 ID（从 1 起递增）。 |
| InstancePool | `allocate_search` | `(self) -> int` | 分配下一个搜索任务实例 ID（从 1 起递增）。 |
| InstancePool | `allocate_pseudo` | `(self) -> int` | 分配下一个伪人运行时实例 ID（从 1 起递增）。 |
| InstancePool | `allocate_mark` | `(self) -> int` | 分配下一个印记实例 ID（从 1 起递增）。 |
| InstancePool | `from_dict` | `(cls, raw: dict[str, object]) -> 'InstancePool'` | 从字典还原 InstancePool。 |
| InstancePool | `to_dict` | `(self) -> dict[str, int]` | 序列化为普通字典。 |
|  | `**class RoundActionState**` | `` | 每个回合开始时重置的限制与计数。 |
| RoundActionState | `from_dict` | `(cls, raw: dict[str, object]) -> 'RoundActionState'` | 从字典还原 RoundActionState。 |
| RoundActionState | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |

### `weiren_game/condition.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class StatusDefinition**` | `` | 一种状态的静态描述。 |
| StatusDefinition | `show` | `(self, field: str) -> bool` | 返回指定字段是否在 UI 上显示。 |
|  | `**class EmotionDefinition**` | `` | 情绪状态，归属侵蚀或觉醒族且可能为稀有。 |
|  | `register_status_definition` | `(definition: StatusDefinition) -> None` | 注册一个由内容对象携带的状态定义（覆盖同 id 旧定义）。 |
|  | `_register_reveal_event` | `(emotion_key: str) -> None` | 为一种情绪登记「情绪显现」**全局事件**定义。 |
|  | `register_emotion_definition` | `(definition: EmotionDefinition) -> None` | 注册一种情绪（覆盖同 id 旧定义），并同步键集合、显现标记与 data 层标签表。 |
|  | `**class Condition**` | `` | 单个状态实例：强度（严重度）与层数（持续）的组合，0/0 表示未激活。 |
| Condition | `__post_init__` | `(self) -> None` | 初始化时立即钳制强度与层数。 |
| Condition | `active` | `(self) -> bool` | 是否处于激活状态（强度与层数均大于 0）。 |
| Condition | `clamp` | `(self, *, intensity_max: int=10, layers_max: int=99) -> None` | 将强度与层数钳制在 0 到上限之间，任一为 0 则一并归零。 |
| Condition | `clear` | `(self) -> None` | 将强度与层数清零，使状态转为未激活。 |
| Condition | `from_dict` | `(cls, raw: dict[str, object]) -> 'Condition'` | 从字典还原 Condition 实例。 |
| Condition | `to_dict` | `(self) -> dict[str, int]` | 序列化为普通字典。 |

### `weiren_game/global_event.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class GlobalEventDefinition**` | `` | 一种全局事件的静态描述。 |
|  | `register_global_event` | `(definition: GlobalEventDefinition) -> None` | 注册一个全局事件定义（覆盖同 id 旧定义）。 |
|  | `emotion_reveal_event` | `(emotion_key: str) -> str` | 返回某情绪的「情绪显现」全局事件键（唯一来源，读写都走它）。 |
|  | `**class GlobalEventInstance**` | `` | 一个全局事件实例：数值（如倍率/贡献）与剩余回合。 |
| GlobalEventInstance | `active` | `(self) -> bool` | 是否仍在生效（剩余回合 > 0）。 |
| GlobalEventInstance | `from_dict` | `(cls, raw: dict[str, object]) -> 'GlobalEventInstance'` | 从字典还原 GlobalEventInstance。 |
| GlobalEventInstance | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |
|  | `**class GlobalEventState**` | `` | 世界持有的全局事件实例表：event_id → GlobalEventInstance。 |
| GlobalEventState | `set` | `(self, event_id: str, value: float=0.0, layers: int=1) -> None` | 设置/刷新一个全局事件（取较长剩余回合）。 |
| GlobalEventState | `instance` | `(self, event_id: str) -> GlobalEventInstance \| None` | 返回指定事件的实例（无则 None）。 |
| GlobalEventState | `active` | `(self, event_id: str) -> bool` | 指定事件是否生效。 |
| GlobalEventState | `value_of` | `(self, event_id: str, default: float=0.0) -> float` | 返回生效事件的数值，未生效则返回默认值。 |
| GlobalEventState | `consume` | `(self, event_id: str) -> GlobalEventInstance \| None` | 移除并返回指定事件实例（一次性消费）。 |
| GlobalEventState | `decay` | `(self) -> None` | 回合末衰减：所有事件剩余回合 -1，归 0 移除。 |
| GlobalEventState | `from_dict` | `(cls, raw: dict[str, object]) -> 'GlobalEventState'` | 从字典还原全局事件表。 |
| GlobalEventState | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |

### `weiren_game/marks.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class MarkInstance**` | `` | 单个印记实例：唯一编号 + 印记种类 + 数值（层数/数量）。 |
| MarkInstance | `from_dict` | `(cls, raw: dict[str, object]) -> 'MarkInstance'` | 从字典还原 MarkInstance。 |
| MarkInstance | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |
|  | `**class MarkPool**` | `` | 一名房客持有的全部印记实例（按实例编号升序保存）。 |
| MarkPool | `add` | `(self, instance: MarkInstance) -> MarkInstance` | 加入一个印记实例并按实例编号排序。 |
| MarkPool | `instances_of` | `(self, mark_id: str) -> list[MarkInstance]` | 返回指定种类的印记实例（编号升序）。 |
| MarkPool | `count` | `(self, mark_id: str) -> float` | 累计指定种类的印记数值。 |
| MarkPool | `remove_value` | `(self, mark_id: str, value: float) -> bool` | 移除指定种类中数值等于 value 的一个实例（用于牌面移除）。 |
| MarkPool | `consume` | `(self, mark_id: str, amount: float) -> float` | 按实例编号从小到大消耗指定印记，返回实际消耗量。 |
| MarkPool | `from_dict` | `(cls, raw: dict[str, object]) -> 'MarkPool'` | 从字典还原 MarkPool。 |
| MarkPool | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |

### `weiren_game/items.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class ItemInstance**` | `` | 单个物品实例，含唯一实例 ID 与运行时数量、耐久和持有回合。 |
| ItemInstance | `__post_init__` | `(self) -> None` | 校验数量至少为 1、耐久不可为负。 |
| ItemInstance | `from_dict` | `(cls, raw: dict[str, object]) -> 'ItemInstance'` | 从字典还原 ItemInstance。 |
| ItemInstance | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |
|  | `**class Inventory**` | `` | 有序的物品实例集合；列表顺序即槽位顺序。 |
| Inventory | `__iter__` | `(self) -> Iterator[ItemInstance]` | 迭代内部物品实例列表。 |
| Inventory | `__len__` | `(self) -> int` | 返回物品实例的数量。 |
| Inventory | `add` | `(self, item: ItemInstance, *, plot: int \| None=None) -> None` | 把物品放进背包：未指定槽位时自动取最小空闲格。 |
| Inventory | `move_to` | `(self, instance: 'ItemInstance', plot: int) -> None` | 把已有实例移动到指定槽位；目标被占用时与原占用者交换槽位。 |
| Inventory | `_next_free_slot_excluding` | `(self, excluded: set['ItemInstance']) -> int` | 返回未被其余实例占用的最小槽位（最多跳过 99 格）。 |
| Inventory | `at_plot` | `(self, plot: int) -> 'ItemInstance \| None'` | 按槽位编号返回对应实例，空格返回 None。 |
| Inventory | `_next_free_slot` | `(self) -> int` | 返回当前容器中最小的空闲槽位编号。 |
| Inventory | `instance` | `(self, instance_id: str) -> ItemInstance \| None` | 按实例 ID 查找物品，未找到返回 None。 |
| Inventory | `remove` | `(self, instance_id: str) -> ItemInstance \| None` | 按实例 ID 移除并返回该物品，不存在则返回 None。 |
| Inventory | `remove_first` | `(self, item_id: str) -> ItemInstance \| None` | 移除槽位最靠前的指定物品实例并返回，未持有则返回 None。 |
| Inventory | `consume` | `(self, item_id: str, amount: int=1) -> int` | 按“单位”消耗物品：可堆叠就减 count，归零才移除实例；返回实际消耗数。 |
| Inventory | `count` | `(self, item_id: str) -> int` | 统计指定物品 ID 的累计数量。 |
| Inventory | `earliest` | `(self, predicate: Callable[[ItemInstance], bool]) -> ItemInstance \| None` | 返回槽位顺序中首个满足条件的物品，无则返回 None。 |
| Inventory | `all_with` | `(self, predicate: Callable[[ItemInstance], bool]) -> list[ItemInstance]` | 返回所有满足条件的物品实例。 |
| Inventory | `by_item_id` | `(self, item_id: str) -> list[ItemInstance]` | 返回指定物品 ID 的全部实例。 |
| Inventory | `from_dict` | `(cls, raw: dict[str, object]) -> 'Inventory'` | 从字典还原 Inventory，并逐项还原物品实例。 |
| Inventory | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |

### `weiren_game/ability.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class AbilityState**` | `` | 单个技能实例的运行时状态。 |
| AbilityState | `from_dict` | `(cls, raw: dict[str, object]) -> 'AbilityState'` | 从字典还原 AbilityState。 |
| AbilityState | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |

### `weiren_game/pseudo.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class PseudoCommonState**` | `` | 剧本通用进度：揭露、已知、来访次数与解放标记。 |
| PseudoCommonState | `from_dict` | `(cls, raw: dict[str, object]) -> 'PseudoCommonState'` | 从字典还原 PseudoCommonState。 |
| PseudoCommonState | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典。 |
|  | `**class PseudoRuntime**` | `` | 单个剧本伪人的完整运行时状态。 |
| PseudoRuntime | `__post_init__` | `(self) -> None` | 按场景模块暴露的 State 类补建当前场景子状态。 |
| PseudoRuntime | `scenario` | `(self) -> Any` | 返回当前剧本对应的专属子状态。 |
| PseudoRuntime | `_scenario_attr` | `(self) -> str` | 返回当前剧本内部子状态的属性名（去掉 pseudo_ 前缀）。 |
| PseudoRuntime | `__getattr__` | `(self, name: str) -> Any` | 按旧式扁平访问将字段转发到所属子状态。 |
| PseudoRuntime | `__setattr__` | `(self, name: str, value: Any) -> None` | 按旧式扁平赋值将字段写入所属子状态。 |
| PseudoRuntime | `from_dict` | `(cls, raw: dict[str, object]) -> 'PseudoRuntime'` | 从字典还原 PseudoRuntime，并还原各子状态。 |
| PseudoRuntime | `to_dict` | `(self) -> dict[str, object]` | 序列化为普通字典，子状态一并转为字典。 |

### `weiren_game/types.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class EngineProtocol**` | `` | 角色模块可见的最小引擎接口（方法列表即各角色模块会调用的引擎 API， |
| EngineProtocol | `_log` | `(self, message: str, *, shown: bool=True) -> None` |  |
| EngineProtocol | `_record_log` | `(self, message: str) -> None` |  |
| EngineProtocol | `_show_message` | `(self, message: str) -> None` |  |
| EngineProtocol | `_rng` | `(self, event_id: object)` |  |
| EngineProtocol | `_passive_available` | `(self, tenant: object, event_id: str='passive') -> bool` |  |
| EngineProtocol | `home_tenants` | `(self)` |  |
| EngineProtocol | `living_tenants` | `(self)` |  |
| EngineProtocol | `character` | `(self, tenant: object)` |  |
| EngineProtocol | `_require_home_tenant` | `(self, tenant_id: int \| None, *, must_act: bool=False)` |  |
| EngineProtocol | `_restore_health` | `(self, tenant: object, amount: float, source: str=TEXT['types._restore_health.1'])` |  |
| EngineProtocol | `_loss_health` | `(self, tenant: object, amount: float, source: str)` |  |
| EngineProtocol | `_consume_health` | `(self, tenant: object, amount: float, source: str)` |  |
| EngineProtocol | `_damage_health` | `(self, tenant: object, amount: float, source: str)` |  |
| EngineProtocol | `_restore_sanity` | `(self, tenant: object, amount: float, source: str=TEXT['types._restore_sanity.1'])` |  |
| EngineProtocol | `_consume_sanity` | `(self, tenant: object, amount: float, source: str)` |  |
| EngineProtocol | `_damage_sanity` | `(self, tenant: object, amount: float, source: str)` |  |
| EngineProtocol | `_loss_sanity` | `(self, tenant: object, amount: float, source: str)` |  |
| EngineProtocol | `_recover_condition` | `(self, condition: object, layers: int, intensity: int) -> None` |  |
| EngineProtocol | `_verify_information_object` | `(self, info: object) -> None` |  |
| EngineProtocol | `_create_random_information` | `(self, truth: bool, source: str, kinds: object)` |  |
| EngineProtocol | `_gain_item` | `(self, item_id: str, amount: int=1, *, process_carrier: bool=True) -> None` |  |
| EngineProtocol | `_set_ability_cooldown` | `(self, tenant: object, ability_id: str, until: int) -> None` |  |
| EngineProtocol | `_mark_ability_used` | `(self, tenant: object, ability_id: str) -> None` |  |
| EngineProtocol | `_queue_human_visitor` | `(self, text: str, *, force_supply: bool=False) -> None` |  |

## 交互层（83 项）

### `weiren_game/cli.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `_configure_console` | `() -> None` | 将标准输出与错误流配置为 UTF-8 编码。 |
|  | `_print_messages` | `(engine: GameEngine) -> None` | 打印并排空引擎的全部待处理消息。 |
|  | `_choose` | `(prompt: str, values: list[str], *, allow_blank: bool=False) -> str \| None` | 读取用户输入，返回合法编号或 ID；允许空值时返回 None。 |
|  | `_yes` | `(prompt: str) -> bool` | 判断用户确认输入是否属于是类应答（1/y/是 等）。 |
|  | `_home_ids` | `(engine: GameEngine, *, exclude: str \| None=None) -> list[str]` | 返回屋内房客 ID 列表，可排除指定房客。 |
|  | `show_status` | `(engine: GameEngine) -> None` | 逐行打印引擎提供的当前局面状态。 |
|  | `show_inventory` | `(engine: GameEngine) -> None` | 打印屋内物资清单及各物资的耐久说明。 |
|  | `show_locations` | `(engine: GameEngine) -> None` | 打印本局可搜索的地点列表。 |
|  | `show_codex` | `(engine: GameEngine) -> None` | 打印原稿内容总览：角色、物资、地点、信息、命运抽牌与伪人。 |
|  | `handle_door` | `(engine: GameEngine) -> None` | 处理下一个门口事件；人形访客询问接纳或拒绝，其余按回车推进。 |
|  | `start_search` | `(engine: GameEngine) -> None` | 选择可外出的房客、地点与携带物资并发起一次搜索。 |
|  | `use_item` | `(engine: GameEngine) -> None` | 选择物资与目标房客并执行一次使用。 |
|  | `equip_item` | `(engine: GameEngine) -> None` | 为房客装备装甲、书籍或角色专属携带物。 |
|  | `unequip_item` | `(engine: GameEngine) -> None` | 选择房客并卸下其一件常驻装备。 |
|  | `_choose_target` | `(engine: GameEngine, exclude: str \| None=None) -> str \| None` | 在屋内房客中交互选择目标 ID，无候选项时返回 None。 |
|  | `use_ability` | `(engine: GameEngine) -> None` | 选择使用者、主动能力、目标与附加选项后执行，并处理命运抽牌结算。 |
|  | `show_information` | `(engine: GameEngine) -> None` | 按状态优先级打印当前全部信息。 |
|  | `accuse` | `(engine: GameEngine) -> None` | 让玩家指认一名屋内房客为伪人。 |
|  | `run` | `(engine: GameEngine, save_path: Path) -> int` | 运行终端主循环直至胜负分晓，返回进程退出码。 |
|  | `build_parser` | `() -> argparse.ArgumentParser` | 解析命令行参数并返回参数对象。 |
|  | `main` | `(argv: list[str] \| None=None) -> int` | 程序入口：配置控制台、新建或读取存档并进入游戏主循环。 |

### `weiren_game/web_ui.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `avatar_of` | `(character_id: str) -> str` | 角色自声明的头像图标（模块属性 AVATAR），缺省用通用头像。 |
|  | `persona_display` | `(engine, tenant) -> str` | 房客卡的运行时性格显示：内容可经模块 ``PERSONA_LABEL`` 钩子覆写（如未固定自我时）。 |
|  | `_location_supply` | `(location) -> str` | 把地点的掉落/修正压成一句简述（供搜索选择界面显示）。 |
|  | `_location_drop` | `(location) -> list[dict]` | 掉落的**结构化**视图：``[{tags, weight}]``（界面分行显示，不再是一长句）。 |
|  | `_location_mechanics` | `(location) -> list[str]` | 地点特殊设定，逐条（界面用小列表渲染）。 |
|  | `_item_icon` | `(item) -> str` |  |
|  | `_pseudo_progress` | `(engine, scenario_id: str) -> str` | 伪人场景的进度摘要文本（由内容层提供）。 |
|  | `_pseudo_card` | `(engine, scenario_id: str) -> dict \| None` | 伪人卡：解放/突破进度 + 技能 + 印记阈值（由内容层提供）。 |
|  | `_pseudo_slot` | `(engine, scenario_id: str) -> list[dict]` | 伪人袖珍卡的小面板：内容声明 ``CARD_SLOT``（与房客小面板同一种条目形状）。 |
|  | `_visitor_preview` | `(character_id: str \| None) -> dict \| None` | 门外访客的简要信息（用于悬浮查看）。 |
|  | `_item_entry` | `(item, count: int, durability: int=0) -> list` | 把物品定义 + 数量映射为前端渲染条目。 |
|  | `_slot_entries` | `(instances, size: int) -> list` | 把一组带 plot 槽位的物品实例铺成定长数组（空格为 None）。 |
|  | `_condition_chips` | `(tenant) -> list[list[str]]` | 房客的可视状态 chip：遍历全部已注册状态，情绪另走 emotions。 |
|  | `_project_tiers` | `(raw_tiers: object, scale: int) -> list[dict]` | 把档位声明投影为刻度：``at`` 或 ``(at, 标注, 刻度配色)``。 |
|  | `_mark_row` | `(mark: object, current: int) -> dict` | 一个印记的展示行（含进度条与悬停提示）。 |
|  | `_project_slot` | `(items: object, mark_rows: dict[str, dict]) -> list[dict]` | 把内容声明的小面板条目投影成前端可渲染的形状（房客与伪人共用）。 |
|  | `_detail_slot` | `(engine: GameEngine, tenant, mark_rows: dict[str, dict]) -> list[dict]` | 房客详情页的小面板：内容声明 ``DETAIL_SLOT``，没声明就回退为"列出自己的印记"。 |
|  | `_panel_item_entry` | `(raw: object) -> list \| None` | 面板格子里的物品：内容只给 item_id / 数量 / 耐久，投影成与仓库同一种条目。 |
|  | `_project_panel` | `(engine: GameEngine, tenant, mark_rows: dict[str, dict]) -> dict \| None` | 房客专属面板：内容声明 ``PANEL``，核心只把条目投影成前端能画的样子。 |
|  | `resolve_pack_asset` | `(pack: str, filename: str) -> Path \| None` | 按包名解析素材位文件：base（空包名）/ 独立资源包 / DLC 内嵌。 |
|  | `resource_pack_state` | `() -> dict` | 资源包：贴图零件 + 主题（前端启动时取回并应用；内置为默认材质）。 |
|  | `avatar_art` | `(character_id: str) -> dict` | 角色头像视图：整张（``full``）或「形状 × 专属特征 × 点缀色」的组装。 |
|  | `pseudo_avatar_art` | `(pseudo_id: str) -> dict` | 伪人**自己**的头像视图。 |
|  | `_expel_texts` | `(evidence: dict) -> dict` | 指认（驱逐）的界面文案：**内容层给词**，这里只按"证据是否已证实"挑一份下发。 |
|  | `_ability_target_options` | `(engine: GameEngine, actor, ability_id: str) -> list[dict]` | 技能选人时每个候选的**逐项说明**（内容声明 `TARGET_OPTIONS` 时才有）。 |
|  | `_global_event_rows` | `(engine: GameEngine) -> list[dict]` | 把生效中的全局事件映射为界面行：图标 + 名称 + 剩余回合 + 内容。 |
|  | `build_state` | `(engine: GameEngine) -> dict` | 把引擎状态映射为前端需要的 JSON（只取前端渲染所需字段）。 |
|  | `_map_shelter` | `(engine) -> str` | 屋子显示名：**只认地图的 `shelter`**（base 地图恒在，所以不需要第二份兜底）。 |
|  | `_map_menu` | `() -> list[dict]` | 可选地图列表：默认地图（base）排最前。 |
|  | `menu_state` | `() -> dict` | 返回启动器数据：可安装 DLC、难度分层说明、伪人与当前设置。 |
|  | `art_url` | `(kind: str, entity_id: str) -> str` | 地点 / 信息 / 伪人图标的 URL（内容层文件，资料包/资源包可覆盖）。 |
|  | `_safe_filename` | `(name: str) -> str` | 把用户输入的存档名转成安全的文件名（去路径分隔符与非法字符）。 |
|  | `_read_index` | `() -> dict` |  |
|  | `_write_index` | `(index: dict) -> None` |  |
|  | `_save_summary` | `(path: Path, index: dict) -> dict \| None` |  |
|  | `list_saves` | `() -> list` | 列出 saves/ 下的存档摘要（按修改时间倒序）。 |
|  | `**class Session**` | `` | 单局会话：持有引擎并执行动作。 |
| Session | `__init__` | `(self) -> None` |  |
| Session | `new_game` | `(self, options: dict) -> None` |  |
| Session | `flush_pending_save` | `(self) -> None` | 新对局在选完开局成员后自动落盘一次（等待选择期间不可保存）。 |
| Session | `abort_start` | `(self) -> bool` | 开局「发现」还没选完就强行退出：丢掉这场**还没真正开始**的局。 |
| Session | `load_save` | `(self, filename: str) -> None` |  |
| Session | `delete_save` | `(self, filename: str) -> None` |  |
| Session | `drain` | `(self) -> list[str]` |  |
| Session | `perform` | `(self, payload: dict) -> None` |  |
|  | `_codex_extra` | `(character_id: str) -> list` | 角色自声明的图鉴补充内容（如命运牌、persona）；缺失则返回空。 |
|  | `codex_state` | `() -> dict` | 图鉴数据：全部静态内容，不依赖任何对局。 |
|  | `apply_dlc` | `(order: list, resourcepack_order: list \| None=None) -> dict` | 运行期热切换内容包（免重启）：按优先级重建注册表并持久化配置。 |
|  | `apply_settings` | `(payload: dict) -> None` | 把启动器设置持久化到 game_config.json。 |
|  | `make_handler` | `(session: Session, *, quit_server=None)` |  |
|  | `run_server` | `(port: int=DEFAULT_PORT, *, open_browser: bool=True) -> None` |  |
|  | `main` | `(argv: list[str] \| None=None) -> int` |  |

### `weiren_game/ui.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `_pairs` | `(options)` | 把 ``[value, ...]`` 或 ``[(value, label), ...]`` 规范成 ``[(value, label)]``。 |
|  | `**class UserInterface**` | `` | 前端需要实现的交互接口。 |
| UserInterface | `message` | `(self, text: str) -> None` | 显示一条信息（可为纯文本）。 |
| UserInterface | `choose` | `(self, prompt: str, options, *, allow_blank: bool=False)` | 从 options 中选择一项，返回其 value；allow_blank 时空输入返回 None。 |
| UserInterface | `confirm` | `(self, prompt: str) -> bool` | 是/否确认。 |
| UserInterface | `choose_target` | `(self, engine, exclude=None)` | 选择一名屋内房客，返回实例 id；无目标返回 None。 |
|  | `**class CliUI**` | `` | 命令行实现：读取标准输入。 |
| CliUI | `message` | `(self, text: str) -> None` |  |
| CliUI | `choose` | `(self, prompt: str, options, *, allow_blank: bool=False)` |  |
| CliUI | `confirm` | `(self, prompt: str) -> bool` |  |

## 外围（44 项）

### `weiren_game/text.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `segments` | `(text: str)` | 把标记文本拆成 ``(片段, bold, italic)`` 序列（不含标记本身）。 |
|  | `strip_markup` | `(text: str) -> str` | 去掉加粗/斜体标记，返回纯文本（保留换行）。 |
|  | `render_markup` | `(text: str, *, ansi: bool=True) -> str` | 把标记渲染为 ANSI 样式；``ansi=False`` 时退化为纯文本。 |

### `weiren_game/log_shape.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `row_from_line` | `(line: str) -> dict \| None` | 把一行播报解析成 `{label, value, note}`；认不出形状就返回 None。 |
|  | `rows_from_lines` | `(lines: list) -> list[dict]` | 一批播报 → 明细行；**认不出的行保持原文**（向后兼容，永不丢信息）。 |

### `weiren_game/random_log.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class LoggedRandom**` | `` | 在 random.Random 之上把每次抽取写入完整对局日志。 |
| LoggedRandom | `__init__` | `(self, seed: object, label: str, logger: Callable[[str], None]) -> None` |  |
| LoggedRandom | `_note` | `(self, kind: str, value: object) -> None` |  |
| LoggedRandom | `random` | `(self) -> float` |  |
| LoggedRandom | `_randbelow` | `(self, n: int) -> int` |  |
|  | `**class _LoggedFloat**` | `` | 浮点子类：参与比较时写出“骰点 关系 阈值 → 生效/不生效”。 |
| _LoggedFloat | `__new__` | `(cls, value: float, label: str, sequence: int, logger: Callable[[str], None]) -> '_LoggedFloat'` |  |
| _LoggedFloat | `_judge` | `(self, symbol: str, other: object, result: bool) -> bool` |  |
| _LoggedFloat | `__reduce__` | `(self) -> tuple[object, tuple[float]]` | 序列化/复制时还原为普通 float，避免被当作包装对象传递。 |
| _LoggedFloat | `__lt__` | `(self, other: object) -> bool` |  |
| _LoggedFloat | `__le__` | `(self, other: object) -> bool` |  |
| _LoggedFloat | `__gt__` | `(self, other: object) -> bool` |  |
| _LoggedFloat | `__ge__` | `(self, other: object) -> bool` |  |

### `weiren_game/paths.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `app_base` | `() -> Path` | 可写根目录：打包后 = 可执行文件所在目录；源码运行 = 项目根目录。 |
|  | `saves_dir` | `() -> Path` | 存档目录：可用环境变量 WEIREN_SAVES_DIR 隔离（测试/脚本务必用它，勿动用户存档）。 |
|  | `resource_dir` | `(name: str='') -> Path` | 只读资源目录：打包后 = 解包目录(_MEIPASS)；源码运行 = 包内目录。 |

### `weiren_game/exceptions.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `**class RuleViolation**` | `` | Raised when a requested player action is not legal. |

### `weiren_game/avatars.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `avatar_hash` | `(identifier: str) -> int` | 与前端 ``avatarHash`` 同算法（x*31 + code，无符号 32 位）。 |
|  | `_pack_dirs` | `(*, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> list[Path]` | 按**低 → 高**优先级列出各内容包/资源包的根目录。 |
|  | `avatar_index` | `(*, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> dict[str, dict[str, Path]]` | 三张表：section → {id: 文件路径}（按优先级覆盖，高者赢）。 |
|  | `resolve_avatar_part` | `(section: str, part_id: str, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> Path \| None` | 按 id 找零件文件（只接受裸 id / 裸文件名，防目录穿越）。 |
|  | `avatar_mode` | `(*, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> str` | 当前**最终生效**的头像模式：``art``（默认，立绘优先）或 ``parts``（一律零件组装）。 |
|  | `part_markup` | `(path: Path, *, colors: dict \| None=None) -> str` | 读零件文件；若它用了色槽，就把 ``var(--a/b/c…)`` 换成具体颜色后返回**内联标记**。 |
|  | `avatar_view` | `(character_id: str, module: object \| None, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> dict` | 某个角色的头像视图：整张 → 形状/特征/点缀色（组装）。 |

### `weiren_game/item_icons.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `quality_color` | `(quality: int) -> str` | 品质色（🔒 锁定 token，资源包改不动）。 |
|  | `item_icon_index` | `(*, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> dict[str, dict[str, Path]]` | 两张表：``item`` → {item_id: 文件}、``tag`` → {tag: 文件}（高优先级覆盖低者）。 |
|  | `tag_order` | `(tags) -> list[str]` | 物品标签的取图顺序：具象标签优先（内容层登记表），其余按原顺序补在后面。 |
|  | `resolve_item_icon` | `(item_id: str, tags, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> Path \| None` | 按"专属 → 标签兜底"找图标文件（只接受裸 id / 裸 tag，防目录穿越）。 |
|  | `item_icon_markup` | `(item, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> str` | 物品图标的内联标记：底色→``currentColor``（界面给 ``--ink``）、特征色→品质色。 |

### `weiren_game/icon_files.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `icon_index` | `(section: str, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> dict[str, Path]` | ``{id: 文件}``（按优先级覆盖，同 id 高者赢）。 |
|  | `resolve_icon` | `(section: str, icon_id: str, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> Path \| None` | 按 id 找图标文件（只接受裸 id，防目录穿越）。 |
|  | `icon_url` | `(section: str, icon_id: str, *, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> str` | 图标的 URL（找不到返回空串，界面回退内置单线图标）。 |

### `weiren_game/asset_layers.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `layer_roots` | `(*, dlc_root: str \| Path \| None=None, rp_root: str \| Path \| None=None) -> list[Path]` | 按**低 → 高**优先级列出各资料包 / 资源包的根目录（不含 base 层）。 |

### `weiren_game/resourcepack_loader.py`

| 类 | 方法 | 参数 | 说明 |
| --- | --- | --- | --- |
|  | `_normalize_order` | `(order: 'list[str] \| tuple[str, ...] \| None', available: set[str]) -> list[str]` | 规整资源包优先级序列：丢弃未知项、去重、保证 ``base`` 存在（缺失则垫底）。 |
|  | `resourcepack_root` | `(root: str \| Path \| None=None) -> Path` | 资源包根目录（默认游戏根目录下的 resourcepacks/）。 |
|  | `available_resourcepacks` | `(root: str \| Path \| None=None) -> list[Path]` | 列出可用资源包目录（跳过 `_`/`.` 开头，以及保留名 `base`）。 |
|  | `resourcepack_label` | `(name: str, root: str \| Path \| None=None) -> str` | 资源包的显示名（pack.json 的 label > name > 目录名）。 |
|  | `load_single_resourcepack` | `(name: str, root: str \| Path \| None=None) -> None` | 套用一个独立资源包（重复套用会被跳过）。 |
|  | `apply_resourcepack_order` | `(order: 'list[str] \| tuple[str, ...]', root: str \| Path \| None=None) -> list[str]` | 按位次（**高 → 低**）套用资源包；``base`` 行 = 内置材质，**位次可调**。 |


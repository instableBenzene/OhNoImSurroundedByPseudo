# 核心符号的引用面（`weiren_game/`，不含 `data/` 与 `webui/`）

> 由 `python tools/dump_core.py --refs` 生成（生成于 2026-09-19）。**别手改**。
> 口径：**AST 扫描**——注释与 docstring 不算引用；收 `.名字` / 裸 `名字` /
> `from x import 名字` / 恰好等于名字的字符串（`getattr(obj, "名字")` 派发）。
> **只算运行时**（`weiren_game/` + `dlc/`）；`tests/` 与 `tools/` 单独标注。
> `引用处` 列的是**调用者的方法名**（`模块.类.方法`，已去重、不含行号）；
> **同一个文件**只表示调用者在同一个模块里（内部 helper），不是自引用。
> **>5 次算高频，只记数**；0 次=可疑死代码（名字级匹配，保守）。

| 文件 | 类 | 方法 | 引用数 | 同文件 | 跨文件 | 引用处（≤5 时列出） |
| --- | --- | --- | --- | --- | --- | --- |
| `weiren_game/engine.py` | GameEngine | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/engine.py` | GameEngine | `_autosave_before_discover` | 1 | 0 | 1 | `systems.random_system.RandomSystemMixin.discover` |
| `weiren_game/engine.py` | GameEngine | `_require_no_pending_choice` | 10 | 2 | 8 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `choose_discover` | 1 | 0 | 1 | `web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `_clear_pending_choice` | 4 | 2 | 2 | `data.characters.erebus.cancel_fate`、`data.characters.erebus.resolve_fate`、`engine.GameEngine.commit_start_choice`、`engine.GameEngine.new_game` |
| `weiren_game/engine.py` | GameEngine | `pending_view` | 1 | 0 | 1 | `web_ui.build_state` |
| `weiren_game/engine.py` | GameEngine | `resolve_view` | 1 | 0 | 1 | `web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `new_game` | 3 | 0 | 3 | `cli.main`、`web_ui.Handler.do_POST`、`web_ui.Session.new_game` |
| `weiren_game/engine.py` | GameEngine | `_begin_start_pick` | 2 | 2 | 0 | `engine.GameEngine.commit_start_choice`、`engine.GameEngine.new_game` |
| `weiren_game/engine.py` | GameEngine | `commit_start_choice` | 1 | 0 | 1 | `web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `_finish_start` | 2 | 2 | 0 | `engine.GameEngine.commit_start_choice`、`engine.GameEngine.new_game` |
| `weiren_game/engine.py` | GameEngine | `_start_loot_schedule` | 1 | 1 | 0 | `engine.GameEngine._finish_start` |
| `weiren_game/engine.py` | GameEngine | `defer_search_report` | 3 | 0 | 3 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR.attack_searcher`、`data.pseudos.pseudo_benzene.attack_searcher`、`data.pseudos.pseudo_onion.attack_searcher` |
| `weiren_game/engine.py` | GameEngine | `_generate_locations` | 1 | 1 | 0 | `engine.GameEngine._finish_start` |
| `weiren_game/engine.py` | GameEngine | `load` | 4 | 0 | 4 | `cli.main`、`web_ui.Handler.do_GET`、`web_ui.Session.load_save`、`web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `save` | 6 | 1 | 5 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `drain_messages` | 2 | 0 | 2 | `cli._print_messages`、`web_ui.Session.new_game` |
| `weiren_game/engine.py` | GameEngine | `drain_message_entries` | 1 | 0 | 1 | `web_ui.Session.drain` |
| `weiren_game/engine.py` | GameEngine | `_collect_start` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `_collect_flush` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `_log` | 94 | 9 | 85 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `_record_log` | 6 | 2 | 4 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `_show_message` | 2 | 2 | 0 | `engine.GameEngine._collect_flush`、`engine.GameEngine._log` |
| `weiren_game/engine.py` | GameEngine | `_log_lines` | 1 | 1 | 0 | `engine.GameEngine.export_full_log` |
| `weiren_game/engine.py` | GameEngine | `export_full_log` | 1 | 0 | 1 | `web_ui.Handler.do_GET` |
| `weiren_game/engine.py` | GameEngine | `_record_action` | 12 | 1 | 11 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `character` | 79 | 4 | 75 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `living_tenants` | 9 | 4 | 5 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `home_tenants` | 79 | 2 | 77 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `searching_tenants` | 2 | 1 | 1 | `engine.GameEngine.assert_invariants`、`web_ui.build_state` |
| `weiren_game/engine.py` | GameEngine | `container` | 8 | 0 | 8 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `panel_view` | 1 | 0 | 1 | `web_ui._project_panel` |
| `weiren_game/engine.py` | GameEngine | `panel_action` | 1 | 0 | 1 | `web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `tenant_name` | 3 | 2 | 1 | `engine.GameEngine._log_searching_summary`、`engine.GameEngine.status_lines`、`systems.information_system.InformationSystemMixin._create_random_information` |
| `weiren_game/engine.py` | GameEngine | `_add_tenant` | 2 | 1 | 1 | `engine.GameEngine._finish_start`、`systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/engine.py` | GameEngine | `_require_home_tenant` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `_log_searching_summary` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/engine.py` | GameEngine | `_run_pseudo_end_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/engine.py` | GameEngine | `start_turn` | 2 | 1 | 1 | `engine.GameEngine.resume_to_action`、`web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `resume_to_action` | 3 | 0 | 3 | `cli.run`、`web_ui.Session.load_save`、`web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `end_turn` | 3 | 1 | 2 | `cli.run`、`engine.GameEngine.end_turn`、`web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `_remove_tenant_from_house` | 2 | 1 | 1 | `engine.GameEngine._kill_tenant`、`systems.ability_system.AbilitySystemMixin._expel_tenant` |
| `weiren_game/engine.py` | GameEngine | `_kill_tenant` | 3 | 0 | 3 | `data.pseudos.pseudo_fries.expel_infiltrator`、`systems.round_effects.RoundEffectsSystemMixin._settle_other_end_effects`、`systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/engine.py` | GameEngine | `_notify_tenant_death` | 1 | 1 | 0 | `engine.GameEngine._remove_tenant_from_house` |
| `weiren_game/engine.py` | GameEngine | `_check_survival` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/engine.py` | GameEngine | `_finish` | 7 | 2 | 5 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `rewind_one_turn` | 3 | 0 | 3 | `cli.run`、`systems.pseudo_system.PseudoSystemMixin._attempt_breakthrough`、`web_ui.Session.perform` |
| `weiren_game/engine.py` | GameEngine | `emotion_visible` | 6 | 2 | 4 | （高频，略） |
| `weiren_game/engine.py` | GameEngine | `status_lines` | 1 | 0 | 1 | `cli.show_status` |
| `weiren_game/engine.py` | GameEngine | `inventory_lines` | 1 | 0 | 1 | `cli.show_inventory` |
| `weiren_game/engine.py` | GameEngine | `location_lines` | 1 | 0 | 1 | `cli.show_locations` |
| `weiren_game/engine.py` | GameEngine | `codex_lines` | 1 | 0 | 1 | `cli.show_codex` |
| `weiren_game/engine.py` | GameEngine | `assert_invariants` | **0** | 0 | 0 | 仅被测试/工具引用：`tests.test_pseudo_fate.PseudoTests.test_three_pseudos_and_mutual_exclusivity` `tests.test_round_flow.RoundFlowTests.test_full_playthrough_and_invariants` `tools.smoke_simulation.play` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_set_ability_cooldown` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_mark_ability_used` | 1 | 1 | 0 | `systems.ability_system.AbilitySystemMixin.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_local_skill_module` | 2 | 1 | 1 | `data.characters.chaos.use_permission_transfer`、`systems.ability_system.AbilitySystemMixin._gate_local_skill` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_gate_local_skill` | 1 | 1 | 0 | `systems.ability_system.AbilitySystemMixin.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `available_abilities` | 1 | 0 | 1 | `cli.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_ability_failed` | 1 | 1 | 0 | `systems.ability_system.AbilitySystemMixin.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `use_ability` | 4 | 0 | 4 | `cli.run`、`cli.use_ability`、`data.characters.chaos.use_permission_transfer`、`web_ui.Session.perform` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_mark_ability_failed` | 1 | 1 | 0 | `systems.ability_system.AbilitySystemMixin.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_run_ability_outcome` | 1 | 1 | 0 | `systems.ability_system.AbilitySystemMixin.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_skill_outcome` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_flush_skill_outcomes` | 3 | 1 | 2 | `engine.GameEngine.end_turn`、`engine.GameEngine.start_turn`、`systems.ability_system.AbilitySystemMixin.use_ability` |
| `weiren_game/systems/ability_system.py` | AbilitySystemMixin | `_expel_tenant` | 4 | 0 | 4 | `data.characters.erebus._card_11`、`data.characters.rose.use_rose_expel`、`data.characters.six71.use_cannot_stand`、`systems.pseudo_system.PseudoSystemMixin.accuse` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_emotion_key_of` | 3 | 3 | 0 | `systems.condition_system.ConditionSystemMixin._apply_emotion_end`、`systems.condition_system.ConditionSystemMixin._extend_condition`、`systems.condition_system.ConditionSystemMixin._worsen_condition` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_notify_emotion_increase` | 5 | 5 | 0 | `systems.condition_system.ConditionSystemMixin._apply_emotion`、`systems.condition_system.ConditionSystemMixin._apply_emotion_end`、`systems.condition_system.ConditionSystemMixin._extend_condition`、`systems.condition_system.ConditionSystemMixin._strengthen_emotion_set`、`systems.condition_system.ConditionSystemMixin._worsen_condition` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_condition_extra_effect_active` | 5 | 0 | 5 | `cli.start_search`、`systems.ability_system.AbilitySystemMixin._ability_failed`、`systems.personality_system.PersonalitySystemMixin._passive_available`、`systems.search_system.SearchSystemMixin.start_search`、`systems.search_system._search_status_modifier` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_add_condition` | 1 | 0 | 1 | `data.characters.erebus._card_8` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_status_avoidance` | 4 | 4 | 0 | `systems.condition_system.ConditionSystemMixin._add_condition`、`systems.condition_system.ConditionSystemMixin._extend_condition`、`systems.condition_system.ConditionSystemMixin._set_condition`、`systems.condition_system.ConditionSystemMixin._worsen_condition` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_set_condition` | 1 | 0 | 1 | `data.information._resolve_supply_dispute` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_worsen_condition` | 7 | 2 | 5 | （高频，略） |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_extend_condition` | 7 | 2 | 5 | （高频，略） |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_recover_condition` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_emotion_application_blocked` | 3 | 3 | 0 | `systems.condition_system.ConditionSystemMixin._apply_emotion`、`systems.condition_system.ConditionSystemMixin._strengthen_emotion_set`、`systems.condition_system.ConditionSystemMixin._strengthen_named_emotion` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_awakening_gain_multiplier` | 4 | 4 | 0 | `systems.condition_system.ConditionSystemMixin._adjust_emotion_set`、`systems.condition_system.ConditionSystemMixin._apply_emotion`、`systems.condition_system.ConditionSystemMixin._strengthen_emotion_set`、`systems.condition_system.ConditionSystemMixin._strengthen_named_emotion` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_apply_emotion` | 4 | 1 | 3 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR._add_anxiety`、`data.pseudos.pseudo_onion.attack_searcher`、`data.pseudos.pseudo_onion.cast_whisper`、`systems.condition_system.ConditionSystemMixin._adjust_emotion_set` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_strengthen_named_emotion` | 2 | 0 | 2 | `data.information._resolve_odd_smile`、`data.information._resolve_tense_nerves` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_emotion_weighted_key` | 2 | 2 | 0 | `systems.condition_system.ConditionSystemMixin._adjust_emotion_set`、`systems.condition_system.ConditionSystemMixin._strengthen_emotion_set` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_adjust_emotion_set` | 4 | 0 | 4 | `data.information._resolve_tense_nerves`、`data.items.food._effect_double_mint`、`data.items.food._effect_weird_beans`、`data.items.information_carriers.ancient_legend_start_of_turn` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_strengthen_emotion_set` | 4 | 0 | 4 | `data.information._resolve_suppressed_sobbing`、`data.items.food._effect_spicy_beef`、`data.pseudos.pseudo_fries.mind_play`、`data.pseudos.pseudo_fries.pending_performance_information` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_reduce_emotion_set` | 11 | 0 | 11 | （高频，略） |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_apply_status_end` | 1 | 0 | 1 | `systems.round_effects.RoundEffectsSystemMixin._settle_buff_debuff_effects` |
| `weiren_game/systems/condition_system.py` | ConditionSystemMixin | `_apply_emotion_end` | 1 | 0 | 1 | `systems.round_effects.RoundEffectsSystemMixin._settle_buff_debuff_effects` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_forced_cost_terms` | 2 | 2 | 0 | `systems.cost_system.CostSystemMixin._cost_pack_payable`、`systems.cost_system.CostSystemMixin._resolve_branch_cost` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_select_branch` | 2 | 2 | 0 | `systems.cost_system.CostSystemMixin._cost_pack_payable`、`systems.cost_system.CostSystemMixin._pay_cost_pack` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_resolve_branch_cost` | 1 | 1 | 0 | `systems.cost_system.CostSystemMixin._pay_cost_pack` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_expr_error` | 4 | 4 | 0 | `systems.cost_system.CostSystemMixin._cost_pack_payable`、`systems.cost_system.CostSystemMixin._ref_error`、`systems.cost_system.CostSystemMixin._resolve_branch_cost`、`systems.cost_system._expr_error.ref_error` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_collect_expr` | 2 | 2 | 0 | `systems.cost_system.CostSystemMixin._collect_expr`、`systems.cost_system.CostSystemMixin._resolve_branch_cost` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_ref_error` | 1 | 1 | 0 | `systems.cost_system.CostSystemMixin._collect_expr` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_single_term_error` | 2 | 2 | 0 | `systems.cost_system.CostSystemMixin._ref_error`、`systems.cost_system._expr_error.ref_error` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_ability_costs_payable` | 2 | 1 | 1 | `systems.ability_system.AbilitySystemMixin._gate_local_skill`、`systems.cost_system.CostSystemMixin._cost_pack_payable` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_cost_pack_payable` | **0** | 0 | 0 | 仅被测试/工具引用：`tests.test_abilities_cost.AbilityCostTests.test_cost_expressions_and_turns` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_pay_ability_costs` | 4 | 1 | 3 | `data.characters.onion.use_emotion_strip`、`data.characters.zero329.use_intent_awareness`、`systems.ability_system.AbilitySystemMixin._gate_local_skill`、`systems.cost_system.CostSystemMixin._pay_cost_pack` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_pay_cost_pack` | **0** | 0 | 0 | 仅被测试/工具引用：`tests.test_abilities_cost.AbilityCostTests.test_cost_expressions_and_turns` `tests.test_abilities_cost.AbilityCostTests.test_forced_and_normal_cost_packs` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_resolve_amount` | 3 | 3 | 0 | `systems.cost_system.CostSystemMixin._ability_costs_payable`、`systems.cost_system.CostSystemMixin._pay_ability_costs`、`systems.cost_system.CostSystemMixin._single_term_error` |
| `weiren_game/systems/cost_system.py` | CostSystemMixin | `_role_mark_count` | 3 | 3 | 0 | `systems.cost_system.CostSystemMixin._ability_costs_payable`、`systems.cost_system.CostSystemMixin._resolve_amount`、`systems.cost_system.CostSystemMixin._single_term_error` |
| `weiren_game/systems/cost_system.py` | _EmptyBranch | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_create_random_information` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_observe_visit_information` | 2 | 0 | 2 | `systems.search_system.SearchSystemMixin._resolve_search_return`、`systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_observe_pseudo_skill` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_verify_location_information` | 1 | 0 | 1 | `systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_discern_one_information` | 1 | 0 | 1 | `data.personalities.suspicious.start_of_turn_bond` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_verify_information_object` | 10 | 5 | 5 | （高频，略） |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_resolve_information_effect` | 2 | 2 | 0 | `systems.information_system.InformationSystemMixin._create_random_information`、`systems.information_system.InformationSystemMixin._verify_information_object` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_apply_pending_information_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_expire_information` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `_invalidate_target_information` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/information_system.py` | InformationSystemMixin | `information_text` | 1 | 0 | 1 | `cli.show_information` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_tenant_item_ids` | 2 | 0 | 2 | `data.pseudos.pseudo_fries.encounter_chance`、`systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_tenant_item_group_count` | 3 | 0 | 3 | `engine.GameEngine.assert_invariants`、`engine.GameEngine.status_lines`、`systems.search_system.SearchSystemMixin._recalculate_search` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_return_tenant_items` | 1 | 0 | 1 | `engine.GameEngine._remove_tenant_from_house` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_spill_tenant_overflow` | 4 | 3 | 1 | `systems.item_system.ItemSystemMixin.equip_item`、`systems.item_system.ItemSystemMixin.transfer_item`、`systems.item_system.ItemSystemMixin.unequip_item`、`systems.search_system.SearchSystemMixin._settle_search_bag_items` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `move_item` | 2 | 1 | 1 | `systems.item_system.ItemSystemMixin.move_item`、`web_ui.Session.perform` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_item_tag_fn` | 2 | 2 | 0 | `systems.item_system.ItemSystemMixin._use_general_item`、`systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_add_house_item` | 1 | 1 | 0 | `systems.item_system.ItemSystemMixin._merge_house_item` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_merge_house_item` | 4 | 3 | 1 | `data.characters.flowey._action_take`、`systems.item_system.ItemSystemMixin._gain_item`、`systems.item_system.ItemSystemMixin._return_tenant_items`、`systems.item_system.ItemSystemMixin._spill_tenant_overflow` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_gain_loot_item` | 1 | 0 | 1 | `systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_gain_item` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `transfer_item` | 1 | 0 | 1 | `web_ui.Session.perform` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `migrate_carriers` | 1 | 0 | 1 | `engine.GameEngine.load` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_take_item` | 4 | 2 | 2 | `data.characters.erebus.resolve_fate`、`data.items.food._garlic_seasoning`、`systems.item_system.ItemSystemMixin._spend_item_use`、`systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_durability_multiplier` | 2 | 1 | 1 | `systems.item_system.ItemSystemMixin._consume_durability`、`systems.value_system.ValueSystemMixin._consume_held_durability` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_fragile_chance` | 8 | 1 | 7 | （高频，略） |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_consume_durability` | 1 | 1 | 0 | `systems.item_system.ItemSystemMixin._spend_item_use` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `equip_item` | 3 | 0 | 3 | `cli.equip_item`、`cli.run`、`web_ui.Session.perform` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `unequip_item` | 3 | 0 | 3 | `cli.run`、`cli.unequip_item`、`web_ui.Session.perform` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `use_item` | 3 | 0 | 3 | `cli.run`、`cli.use_item`、`web_ui.Session.perform` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_spend_item_use` | 5 | 2 | 3 | `data.personalities.suspicious.item_use_wasted`、`data.tags._medical.use_medical`、`data.tags.anodyne.use`、`systems.item_system.ItemSystemMixin._use_general_item`、`systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/systems/item_system.py` | ItemSystemMixin | `_use_general_item` | 1 | 1 | 0 | `systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_mark_definition` | 2 | 2 | 0 | `systems.marks_system.MarksSystemMixin._consume_mark`、`systems.marks_system.MarksSystemMixin._gain_mark` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_mark_count` | 14 | 0 | 14 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_gain_mark` | 8 | 0 | 8 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_consume_mark` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_dispatch_mark_node` | 2 | 2 | 0 | `systems.marks_system.MarksSystemMixin._consume_mark`、`systems.marks_system.MarksSystemMixin._gain_mark` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_emit_node` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_set_global_event` | 15 | 1 | 14 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_global_event_active` | 5 | 1 | 4 | `data.pseudos.pseudo_onion._onion_reveal_gate`、`data.pseudos.pseudo_onion.emotion_end_extra`、`systems.marks_system.MarksSystemMixin._pseudo_capability`、`systems.pseudo_system.PseudoSystemMixin._attempt_breakthrough`、`systems.visitor_system.VisitorSystemMixin._queue_human_visitor` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_global_event_value` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_consume_global_event` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_decay_global_events` | 1 | 0 | 1 | `engine.GameEngine.end_turn` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_apply_modifiers` | 15 | 0 | 15 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_eval_gate` | 2 | 0 | 2 | `engine.GameEngine.emotion_visible`、`systems.condition_system.ConditionSystemMixin._emotion_application_blocked` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_suppress_pseudo` | 3 | 0 | 3 | `DLC_Character_STAR_V1.0.0.characters.STAR._resolve_door`、`data.characters.erebus._card_21`、`data.characters.peach.justice_execution_guard` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_pseudo_capability` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_pseudo_enters_house` | 3 | 0 | 3 | `data.characters.erebus._card_0`、`systems.pseudo_system.PseudoSystemMixin._attempt_breakthrough`、`systems.visitor_system.VisitorSystemMixin._queue_scheduled_visitors` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_has_persona` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_personas_of` | 2 | 0 | 2 | `data.characters.fries.detail_slot`、`data.characters.fries.grant_persona` |
| `weiren_game/systems/marks_system.py` | MarksSystemMixin | `_set_personas` | 1 | 0 | 1 | `data.characters.fries.grant_persona` |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `_tenant_personalities` | 5 | 2 | 3 | `engine.GameEngine.status_lines`、`systems.personality_system.PersonalitySystemMixin._is_personality`、`systems.personality_system.PersonalitySystemMixin._personality_weights`、`web_ui.build_state`、`web_ui.persona_display` |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `_is_personality` | 31 | 0 | 31 | （高频，略） |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `_personality_weights` | 2 | 1 | 1 | `systems.personality_system.PersonalitySystemMixin.bond_levels`、`web_ui.build_state._option_view` |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `bond_levels` | 17 | 2 | 15 | （高频，略） |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `_bond_tier` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `_activate_new_bonds` | 3 | 0 | 3 | `engine.GameEngine._finish_start`、`lifecycle.(模块级)`、`systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/systems/personality_system.py` | PersonalitySystemMixin | `_passive_available` | 50 | 0 | 50 | （高频，略） |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_roll_next_pseudo_visit` | 3 | 1 | 2 | `engine.GameEngine.new_game`、`systems.pseudo_system.PseudoSystemMixin._attempt_breakthrough`、`systems.visitor_system.VisitorSystemMixin._queue_scheduled_visitors` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_pseudo_actions_suppressed` | 12 | 2 | 10 | （高频，略） |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `pseudo_in_house` | 4 | 0 | 4 | `data.characters.erebus._card_11`、`data.characters.zero329.start_of_turn`、`systems.information_system.InformationSystemMixin._create_random_information`、`systems.round_effects.RoundEffectsSystemMixin._settle_pseudo_start_handlers` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_skill_respond_skill` | 9 | 1 | 8 | （高频，略） |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_target_lock_responder` | 1 | 1 | 0 | `systems.pseudo_system.PseudoSystemMixin._skill_respond_skill` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_search_resist_responder` | 1 | 1 | 0 | `systems.pseudo_system.PseudoSystemMixin._skill_respond_skill` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_resolve_pseudo_visit` | 1 | 0 | 1 | `systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_attempt_breakthrough` | 5 | 0 | 5 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR.visit`、`data.pseudos.pseudo_benzene.visit`、`data.pseudos.pseudo_fries.infernal_trigger`、`data.pseudos.pseudo_fries.settle_end`、`data.pseudos.pseudo_onion.visit` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_pseudo_attack_searchers` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_scenario_resist_penalty` | 2 | 2 | 0 | `systems.pseudo_system.PseudoSystemMixin._pseudo_attack_searchers`、`systems.pseudo_system.PseudoSystemMixin._skill_respond_skill` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_pseudo_encounter_chance` | 1 | 1 | 0 | `systems.pseudo_system.PseudoSystemMixin._pseudo_attack_searchers` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_break_search_tool` | 3 | 0 | 3 | `data.items.character_items._resist_flintlock`、`data.items.tools_armor._resist_crowbar`、`data.items.tools_armor._resist_sports_shoes` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_set_pseudo_marks` | 1 | 0 | 1 | `data.characters.erebus._card_9` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `_pseudo_handler` | 6 | 1 | 5 | （高频，略） |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `accusation_evidence` | 2 | 1 | 1 | `systems.pseudo_system.PseudoSystemMixin.accuse`、`web_ui.build_state` |
| `weiren_game/systems/pseudo_system.py` | PseudoSystemMixin | `accuse` | 4 | 1 | 3 | `cli.accuse`、`cli.run`、`systems.pseudo_system.PseudoSystemMixin.accuse`、`web_ui.Session.perform` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_rng` | 67 | 3 | 64 | （高频，略） |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_seeded_rng` | 3 | 2 | 1 | `systems.random_system.RandomSystemMixin._mission_rng`、`systems.random_system.RandomSystemMixin._rng`、`systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_mission_rng` | 3 | 0 | 3 | `systems.search_system.SearchSystemMixin._loot_for_mission`、`systems.search_system.SearchSystemMixin._recalculate_search`、`systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_weighted_choice` | 5 | 1 | 4 | `engine.GameEngine._generate_locations`、`systems.condition_system.ConditionSystemMixin._emotion_weighted_key`、`systems.random_system.RandomSystemMixin._start_loot_draw`、`systems.search_system.SearchSystemMixin._loot_for_mission`、`systems.search_system.SearchSystemMixin._random_item` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `discover` | 5 | 1 | 4 | `data.characters.erebus.draw_fate`、`engine.GameEngine._begin_start_pick`、`engine.GameEngine.new_game`、`systems.random_system.RandomSystemMixin.discover`、`web_ui.Session.perform` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_weighted_sample` | 1 | 1 | 0 | `systems.random_system.RandomSystemMixin.discover` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_weighted_pick` | 1 | 1 | 0 | `systems.random_system.RandomSystemMixin._weighted_sample` |
| `weiren_game/systems/random_system.py` | RandomSystemMixin | `_start_loot_draw` | 1 | 0 | 1 | `engine.GameEngine._finish_start` |
| `weiren_game/systems/round_effects.py` |  | `_difficulty_sanity_modifier` | 1 | 1 | 0 | `systems.round_effects.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_emotion_values` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_run_house_item_start_hooks` | 1 | 1 | 0 | `systems.round_effects.RoundEffectsSystemMixin._start_of_turn_effects` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_tenant_instance_start` | 1 | 1 | 0 | `systems.round_effects.RoundEffectsSystemMixin._start_of_turn_effects` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_pseudo_start_handlers` | 1 | 1 | 0 | `systems.round_effects.RoundEffectsSystemMixin._start_of_turn_effects` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_start_of_turn_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_base_end_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_buff_debuff_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_decay_conditions` | 1 | 1 | 0 | `systems.round_effects.RoundEffectsSystemMixin._settle_other_end_effects` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_held_items` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_grant_learned_passive` | 1 | 0 | 1 | `data.items.information_carriers._book_held_end_of_turn` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_other_end_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_settle_turn_end_status_effects` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/round_effects.py` | RoundEffectsSystemMixin | `_run_status_effect_node` | 2 | 2 | 0 | `systems.round_effects.RoundEffectsSystemMixin._settle_tenant_instance_start`、`systems.round_effects.RoundEffectsSystemMixin._settle_turn_end_status_effects` |
| `weiren_game/systems/search_system.py` |  | `_search_status_modifier` | 1 | 1 | 0 | `systems.search_system.(模块级)` |
| `weiren_game/systems/search_system.py` |  | `_difficulty_search_modifier` | 1 | 1 | 0 | `systems.search_system.(模块级)` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_quality_matches` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin._loot_for_mission` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_random_item` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_active_location_modifiers` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_consume_location_modifier_uses` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_loot_for_mission` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin._recalculate_search` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_search_carry` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin.tenant_carry_capacity` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `tenant_carry_capacity` | 7 | 1 | 6 | （高频，略） |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `start_search` | 3 | 0 | 3 | `cli.run`、`cli.start_search`、`web_ui.Session.perform` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_recalculate_search` | 5 | 1 | 4 | `data.characters.wrongwave.try_resist`、`data.items.character_items._resist_flintlock`、`data.pseudos.pseudo_fries.capture_searcher`、`systems.pseudo_system.PseudoSystemMixin._break_search_tool`、`systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_advance_searches_and_returns` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_resolve_search_return` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin._advance_searches_and_returns` |
| `weiren_game/systems/search_system.py` | SearchSystemMixin | `_settle_search_bag_items` | 1 | 1 | 0 | `systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/systems/value_system.py` |  | `_difficulty_health_damage_modifier` | 1 | 1 | 0 | `systems.value_system.(模块级)` |
| `weiren_game/systems/value_system.py` |  | `_difficulty_sanity_damage_modifier` | 1 | 1 | 0 | `systems.value_system.(模块级)` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_health_protection_multiplier` | 2 | 2 | 0 | `systems.value_system.ValueSystemMixin._consume_health`、`systems.value_system.ValueSystemMixin._damage_health` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_consume_held_durability` | 4 | 0 | 4 | `data.items.tools_armor._ghillie_search_return`、`data.items.tools_armor.apply_armour`、`data.items.tools_armor.armour_allows_status`、`systems.round_effects.RoundEffectsSystemMixin._settle_held_items` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_apply_armour` | 1 | 1 | 0 | `systems.value_system.ValueSystemMixin._damage_health` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_damage_health` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_consume_health` | 1 | 0 | 1 | `data.characters.chaos.use_permission_transfer` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_loss_health` | 7 | 2 | 5 | （高频，略） |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_restore_health` | 24 | 0 | 24 | （高频，略） |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_consume_sanity` | 11 | 0 | 11 | （高频，略） |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_damage_sanity` | 2 | 0 | 2 | `data.information._resolve_suppressed_sobbing`、`systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_loss_sanity` | 3 | 0 | 3 | `data.characters.erebus.apply_health_consume_conversion`、`data.characters.rose.use_rose_expel`、`systems.condition_system.ConditionSystemMixin._apply_status_end` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_reduce_sanity` | 3 | 3 | 0 | `systems.value_system.ValueSystemMixin._consume_sanity`、`systems.value_system.ValueSystemMixin._damage_sanity`、`systems.value_system.ValueSystemMixin._loss_sanity` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_restore_sanity` | 37 | 0 | 37 | （高频，略） |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_after_health_decrease` | 3 | 3 | 0 | `systems.value_system.ValueSystemMixin._consume_health`、`systems.value_system.ValueSystemMixin._damage_health`、`systems.value_system.ValueSystemMixin._loss_health` |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_after_health_changed` | 7 | 4 | 3 | （高频，略） |
| `weiren_game/systems/value_system.py` | ValueSystemMixin | `_natural_high_health_recovery` | 1 | 0 | 1 | `systems.round_effects.RoundEffectsSystemMixin._settle_other_end_effects` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_return_departed_tenants` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_queue_scheduled_visitors` | 1 | 0 | 1 | `lifecycle.(模块级)` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_queue_human_visitor` | 3 | 1 | 2 | `data.characters.dragon.party_focus`、`data.characters.dragon.use_call_friends`、`systems.visitor_system.VisitorSystemMixin._queue_scheduled_visitors` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `handle_next_door_event` | 2 | 0 | 2 | `cli.handle_door`、`web_ui.Session.perform` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_visitor_arrived` | 1 | 1 | 0 | `systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_pseudo_visitor_mark` | 2 | 2 | 0 | `systems.visitor_system.VisitorSystemMixin._visitor_arrived`、`systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_on_tenant_accepted` | 2 | 1 | 1 | `engine.GameEngine._finish_start`、`systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/systems/visitor_system.py` | VisitorSystemMixin | `_on_accept_healing` | 2 | 2 | 0 | `systems.visitor_system.VisitorSystemMixin._on_tenant_accepted`、`systems.visitor_system.VisitorSystemMixin.handle_next_door_event` |
| `weiren_game/modifier_rules.py` |  | `register_modifier` | 1 | 1 | 0 | `modifier_rules.(模块级)` |
| `weiren_game/modifier_rules.py` |  | `_source_tokens` | 4 | 4 | 0 | `modifier_rules.collect_gates`、`modifier_rules.collect_modifiers`、`modifier_rules.gates_for`、`modifier_rules.modifiers_for` |
| `weiren_game/modifier_rules.py` |  | `_matches` | 4 | 4 | 0 | `modifier_rules.collect_gates`、`modifier_rules.collect_modifiers`、`modifier_rules.gates_for`、`modifier_rules.modifiers_for` |
| `weiren_game/modifier_rules.py` |  | `modifiers_for` | 2 | 2 | 0 | `modifier_rules.(模块级)`、`modifier_rules.collect_modifiers` |
| `weiren_game/modifier_rules.py` |  | `flat_add` | 1 | 1 | 0 | `modifier_rules.(模块级)` |
| `weiren_game/modifier_rules.py` |  | `percent_add` | 1 | 1 | 0 | `modifier_rules.(模块级)` |
| `weiren_game/modifier_rules.py` |  | `spec` | 97 | 1 | 96 | （高频，略） |
| `weiren_game/modifier_rules.py` |  | `register_modifier_provider` | 43 | 1 | 42 | （高频，略） |
| `weiren_game/modifier_rules.py` |  | `collect_modifiers` | 17 | 1 | 16 | （高频，略） |
| `weiren_game/modifier_rules.py` |  | `_signed_limit` | 1 | 1 | 0 | `modifier_rules.calculate_modified_amount` |
| `weiren_game/modifier_rules.py` |  | `_within_limit` | 1 | 1 | 0 | `modifier_rules.calculate_modified_amount` |
| `weiren_game/modifier_rules.py` |  | `calculate_modified_amount` | 17 | 1 | 16 | （高频，略） |
| `weiren_game/modifier_rules.py` |  | `register_gate` | 1 | 1 | 0 | `modifier_rules.(模块级)` |
| `weiren_game/modifier_rules.py` |  | `register_gate_provider` | 11 | 1 | 10 | （高频，略） |
| `weiren_game/modifier_rules.py` |  | `gates_for` | 2 | 2 | 0 | `modifier_rules.(模块级)`、`modifier_rules.collect_gates` |
| `weiren_game/modifier_rules.py` |  | `collect_gates` | 3 | 1 | 2 | `modifier_rules.(模块级)`、`systems.marks_system.<import>`、`systems.marks_system.MarksSystemMixin._eval_gate` |
| `weiren_game/modifier_rules.py` |  | `evaluate_gate` | 3 | 1 | 2 | `modifier_rules.(模块级)`、`systems.marks_system.<import>`、`systems.marks_system.MarksSystemMixin._eval_gate` |
| `weiren_game/modifier_rules.py` |  | `gate` | 12 | 1 | 11 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/modifier_rules.py` | _Spec | `normal` | 6 | 6 | 0 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `final` | 8 | 2 | 6 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `flat` | 42 | 5 | 37 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `percent` | 12 | 4 | 8 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `mul` | 15 | 0 | 15 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `max` | 113 | 2 | 111 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `min` | 53 | 2 | 51 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `certain` | 4 | 2 | 2 | `data.characters.demit._demit_resist_modifier`、`data.personalities.loner._loner_success_modifier`、`modifier_rules._Spec.certain`、`modifier_rules.calculate_modified_amount` |
| `weiren_game/modifier_rules.py` | _Spec | `path` | 120 | 9 | 111 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `source` | 122 | 11 | 111 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `id` | 131 | 0 | 131 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `match` | 26 | 7 | 19 | （高频，略） |
| `weiren_game/modifier_rules.py` | _Spec | `build` | 6 | 4 | 2 | （高频，略） |
| `weiren_game/modifier_rules.py` | _GateSpec | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/modifier_rules.py` | _GateSpec | `path` | 120 | 9 | 111 | （高频，略） |
| `weiren_game/modifier_rules.py` | _GateSpec | `source` | 122 | 11 | 111 | （高频，略） |
| `weiren_game/modifier_rules.py` | _GateSpec | `match` | 26 | 7 | 19 | （高频，略） |
| `weiren_game/modifier_rules.py` | _GateSpec | `any` | 41 | 5 | 36 | （高频，略） |
| `weiren_game/modifier_rules.py` | _GateSpec | `veto` | 2 | 2 | 0 | `modifier_rules._GateSpec.veto`、`modifier_rules.evaluate_gate` |
| `weiren_game/modifier_rules.py` | _GateSpec | `id` | 131 | 0 | 131 | （高频，略） |
| `weiren_game/modifier_rules.py` | _GateSpec | `build` | 6 | 4 | 2 | （高频，略） |
| `weiren_game/probability.py` |  | `single_guarantee` | 4 | 2 | 2 | `probability.(模块级)`、`probability.resolve`、`systems.pseudo_system.<import>`、`systems.pseudo_system.PseudoSystemMixin._pseudo_encounter_chance` |
| `weiren_game/probability.py` |  | `resolve` | 43 | 1 | 42 | （高频，略） |
| `weiren_game/effects/health_sanity.py` |  | `_permanent_immunity` | 4 | 4 | 0 | `effects.health_sanity.decay_high_health_immunity`、`effects.health_sanity.grant_permanent_trauma_disorder_immunity`、`effects.health_sanity.high_health_status_immunity`、`effects.health_sanity.refresh_high_health_immunity` |
| `weiren_game/effects/health_sanity.py` |  | `_consume_immunity` | 1 | 1 | 0 | `effects.health_sanity.high_health_status_immunity` |
| `weiren_game/effects/health_sanity.py` |  | `high_health_status_immunity` | 3 | 1 | 2 | `effects.health_sanity.(模块级)`、`systems.condition_system.<import>`、`systems.condition_system.ConditionSystemMixin._status_avoidance` |
| `weiren_game/effects/health_sanity.py` |  | `refresh_high_health_immunity` | 5 | 1 | 4 | `effects.health_sanity.(模块级)`、`systems.round_effects.<import>`、`systems.round_effects.RoundEffectsSystemMixin._settle_tenant_instance_start`、`systems.visitor_system.<import>`、`systems.visitor_system.VisitorSystemMixin._on_tenant_accepted` |
| `weiren_game/effects/health_sanity.py` |  | `decay_high_health_immunity` | 3 | 1 | 2 | `condition.(模块级)`、`condition.<import>`、`effects.health_sanity.(模块级)` |
| `weiren_game/effects/health_sanity.py` |  | `grant_permanent_trauma_disorder_immunity` | 3 | 1 | 2 | `effects.health_sanity.(模块级)`、`systems.visitor_system.<import>`、`systems.visitor_system.VisitorSystemMixin._on_tenant_accepted` |
| `weiren_game/content.py` |  | `_clone` | 6 | 6 | 0 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/content.py` | ContentManager | `ensure_base` | 1 | 0 | 1 | `dlc.apply_pack_order` |
| `weiren_game/content.py` | ContentManager | `register_character` | 3 | 1 | 2 | `content.ContentManager.register_character`、`data.__init__.<import>`、`dlc.load_character_file` |
| `weiren_game/content.py` | ContentManager | `register_character_module` | 3 | 1 | 2 | `content.ContentManager.register_character_module`、`data.__init__.<import>`、`dlc.load_character_file` |
| `weiren_game/content.py` | ContentManager | `register_item` | 3 | 1 | 2 | `content.ContentManager.register_item`、`data.__init__.<import>`、`dlc.load_item_file` |
| `weiren_game/content.py` | ContentManager | `register_item_hook` | 1 | 0 | 1 | `dlc.load_item_file` |
| `weiren_game/content.py` | ContentManager | `register_item_effect` | 1 | 0 | 1 | `dlc.load_item_file` |
| `weiren_game/content.py` | ContentManager | `register_location` | 3 | 1 | 2 | `content.ContentManager.register_location`、`data.__init__.<import>`、`dlc.load_location_file` |
| `weiren_game/content.py` | ContentManager | `register_information_template` | 3 | 1 | 2 | `content.ContentManager.register_information_template`、`data.__init__.<import>`、`dlc.load_information_file` |
| `weiren_game/content.py` | ContentManager | `register_location_modifier` | 3 | 1 | 2 | `content.ContentManager.register_location_modifier`、`data.__init__.<import>`、`dlc.load_information_file` |
| `weiren_game/content.py` | ContentManager | `register_pseudo` | 3 | 1 | 2 | `content.ContentManager.register_pseudo`、`data.__init__.<import>`、`dlc.load_pseudo_file` |
| `weiren_game/content.py` | ContentManager | `register_tag_module` | 4 | 1 | 3 | `content.<import>`、`data.__init__.<import>`、`data.tags.__init__.(模块级)`、`dlc.load_tag_behavior_file` |
| `weiren_game/content.py` | ContentManager | `register_personality_module` | 3 | 1 | 2 | `content.<import>`、`data.personalities.__init__.(模块级)`、`dlc.load_personality_file` |
| `weiren_game/content.py` | ContentManager | `register_status_definition` | 20 | 1 | 19 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `register_emotion_definition` | 2 | 1 | 1 | `content.<import>`、`dlc.load_status_file` |
| `weiren_game/content.py` | ContentManager | `register_map_group` | 2 | 1 | 1 | `content.<import>`、`dlc.load_location_file` |
| `weiren_game/content.py` | ContentManager | `register_location_group` | 3 | 1 | 2 | `content.<import>`、`data.labels.(模块级)`、`dlc.load_location_file` |
| `weiren_game/content.py` | ContentManager | `register_item_tag_label` | 3 | 1 | 2 | `DLC_Character_STAR_V1.0.0.__init__.register`、`content.<import>`、`data.labels.(模块级)` |
| `weiren_game/content.py` | ContentManager | `register_item_category_label` | 2 | 1 | 1 | `content.<import>`、`data.labels.(模块级)` |
| `weiren_game/content.py` | ContentManager | `register_map_location` | 3 | 1 | 2 | `content.<import>`、`data.__init__.<import>`、`data.maps.__init__.(模块级)` |
| `weiren_game/content.py` | ContentManager | `register_item_tag_icon` | 3 | 1 | 2 | `DLC_Character_STAR_V1.0.0.__init__.register`、`content.<import>`、`data.labels.(模块级)` |
| `weiren_game/content.py` | ContentManager | `register_information_kind_label` | 2 | 1 | 1 | `content.<import>`、`data.labels.(模块级)` |
| `weiren_game/content.py` | ContentManager | `register_resource_pack` | 2 | 0 | 2 | `dlc.load_resourcepack_file`、`resourcepack_loader.load_single_resourcepack` |
| `weiren_game/content.py` | ContentManager | `apply_item_tags` | 4 | 1 | 3 | `content.<import>`、`data.__init__.<import>`、`data.items.__init__._load_tag_files`、`dlc.load_tag_file` |
| `weiren_game/content.py` | ContentManager | `ensure_captured` | 3 | 0 | 3 | `dlc.apply_pack_order`、`dlc.load_configured_dlc`、`dlc.load_single_dlc` |
| `weiren_game/content.py` | ContentManager | `capture_base` | 1 | 1 | 0 | `content.ContentManager.ensure_captured` |
| `weiren_game/content.py` | ContentManager | `overlay_resourcepack_base` | 1 | 0 | 1 | `resourcepack_loader.apply_resourcepack_order` |
| `weiren_game/content.py` | ContentManager | `capture_resourcepack_baseline` | 1 | 0 | 1 | `dlc.apply_pack_order` |
| `weiren_game/content.py` | ContentManager | `restore_resourcepack_baseline` | 1 | 0 | 1 | `resourcepack_loader.apply_resourcepack_order` |
| `weiren_game/content.py` | ContentManager | `restore_base` | 1 | 0 | 1 | `dlc.apply_pack_order` |
| `weiren_game/content.py` | ContentManager | `overlay_base` | 1 | 0 | 1 | `dlc.apply_pack_order` |
| `weiren_game/content.py` | ContentManager | `set_packs` | 1 | 0 | 1 | `dlc.apply_pack_order` |
| `weiren_game/content.py` | ContentManager | `pack_order` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `characters` | 18 | 0 | 18 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `items` | 144 | 2 | 142 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `locations` | 32 | 0 | 32 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `pseudos` | 19 | 0 | 19 | （高频，略） |
| `weiren_game/content.py` | ContentManager | `register_pack` | 1 | 0 | 1 | `dlc.load_single_dlc` |
| `weiren_game/content.py` | ContentManager | `manifest` | 5 | 0 | 5 | `avatars.avatar_mode`、`dlc.load_single_dlc`、`engine.GameEngine.load`、`engine.GameEngine.new_game`、`resourcepack_loader.load_single_resourcepack` |
| `weiren_game/content.py` | ContentManager | `validate_catalogue` | 3 | 1 | 2 | `content.ContentManager.validate_catalogue`、`data.__init__.(模块级)`、`dlc.load_single_dlc` |
| `weiren_game/config.py` |  | `load_config` | 1 | 1 | 0 | `config.(模块级)` |
| `weiren_game/config.py` |  | `save_config` | 4 | 1 | 3 | `config.(模块级)`、`web_ui.<import>`、`web_ui.apply_dlc`、`web_ui.apply_settings` |
| `weiren_game/dlc.py` |  | `dlc_root` | 14 | 2 | 12 | （高频，略） |
| `weiren_game/dlc.py` |  | `available_dlcs` | 6 | 2 | 4 | （高频，略） |
| `weiren_game/dlc.py` |  | `read_manifest` | 3 | 1 | 2 | `dlc.load_single_dlc`、`resourcepack_loader.<import>`、`resourcepack_loader.load_single_resourcepack` |
| `weiren_game/dlc.py` |  | `_version_tuple` | 3 | 1 | 2 | `dlc.load_single_dlc`、`resourcepack_loader.<import>`、`resourcepack_loader.load_single_resourcepack` |
| `weiren_game/dlc.py` |  | `import_file` | 13 | 11 | 2 | （高频，略） |
| `weiren_game/dlc.py` |  | `_dlc_module_name` | 13 | 11 | 2 | （高频，略） |
| `weiren_game/dlc.py` |  | `load_character_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_item_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_location_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_information_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_pseudo_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_codex_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `_load_dir` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_tag_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_personality_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_status_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_resourcepack_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_tag_behavior_file` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_maps_dir` | 1 | 1 | 0 | `dlc.load_single_dlc` |
| `weiren_game/dlc.py` |  | `load_single_dlc` | 3 | 1 | 2 | `dlc.apply_pack_order`、`web_ui.<import>`、`web_ui.Session.new_game` |
| `weiren_game/dlc.py` |  | `_normalize_order` | 3 | 2 | 1 | `dlc.apply_pack_order`、`dlc.load_configured_dlc`、`resourcepack_loader.apply_resourcepack_order` |
| `weiren_game/dlc.py` |  | `apply_pack_order` | 3 | 1 | 2 | `dlc.load_configured_dlc`、`web_ui.<import>`、`web_ui.apply_dlc` |
| `weiren_game/dlc.py` |  | `loaded_dlcs` | 2 | 0 | 2 | `web_ui.<import>`、`web_ui.menu_state` |
| `weiren_game/dlc.py` |  | `load_configured_dlc` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/models.py` | SearchMission | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | SearchMission | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | VisitorState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | VisitorState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | LocationState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | LocationState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | GameEventState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | GameEventState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | WorldState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | WorldState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | BondState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | BondState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | HouseState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | HouseState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | SessionLogState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/models.py` | SessionLogState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | GameState | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/models.py` | GameState | `to_dict` | 10 | 3 | 7 | （高频，略） |
| `weiren_game/models.py` | GameState | `from_dict` | 13 | 3 | 10 | （高频，略） |
| `weiren_game/tenant.py` |  | `register_container_type` | 1 | 0 | 1 | `data.characters.__init__.<import>` |
| `weiren_game/tenant.py` |  | `_restore_containers` | 1 | 1 | 0 | `tenant.TenantState.from_dict` |
| `weiren_game/tenant.py` |  | `status_caps` | 2 | 2 | 0 | `tenant.(模块级)`、`tenant.TenantState.set_status` |
| `weiren_game/tenant.py` | TenantState | `__post_init__` | 0 | 0 | 0 |  |
| `weiren_game/tenant.py` | TenantState | `home_turns` | 3 | 1 | 2 | `data.characters.dragon.requirements_call_friends`、`systems.round_effects.RoundEffectsSystemMixin._settle_tenant_instance_start`、`tenant.TenantState.home_turns` |
| `weiren_game/tenant.py` | TenantState | `home_turns` | 3 | 1 | 2 | `data.characters.dragon.requirements_call_friends`、`systems.round_effects.RoundEffectsSystemMixin._settle_tenant_instance_start`、`tenant.TenantState.home_turns` |
| `weiren_game/tenant.py` | TenantState | `skip_until_turn` | 7 | 1 | 6 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `skip_until_turn` | 7 | 1 | 6 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `search_locked_until` | 4 | 1 | 3 | `cli.start_search`、`data.characters.sandwhite.search_rest`、`systems.search_system.SearchSystemMixin.start_search`、`tenant.TenantState.search_locked_until` |
| `weiren_game/tenant.py` | TenantState | `search_locked_until` | 4 | 1 | 3 | `cli.start_search`、`data.characters.sandwhite.search_rest`、`systems.search_system.SearchSystemMixin.start_search`、`tenant.TenantState.search_locked_until` |
| `weiren_game/tenant.py` | TenantState | `condition` | 75 | 7 | 68 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `set_status` | 23 | 0 | 23 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `clear_status` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `has_ability` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `ability_state` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `trauma` | 34 | 1 | 33 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `trauma` | 34 | 1 | 33 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `disorder` | 33 | 1 | 32 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `disorder` | 33 | 1 | 32 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `irritation` | 18 | 1 | 17 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `irritation` | 18 | 1 | 17 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `reason` | 14 | 1 | 13 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `reason` | 14 | 1 | 13 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `madness` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `madness` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `shock` | 19 | 2 | 17 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `shock` | 19 | 2 | 17 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `shock_layers` | 6 | 1 | 5 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `shock_layers` | 6 | 1 | 5 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `from_dict` | 13 | 2 | 11 | （高频，略） |
| `weiren_game/tenant.py` | TenantState | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/session.py` | SaveMetadata | `from_dict` | 13 | 0 | 13 | （高频，略） |
| `weiren_game/session.py` | SaveMetadata | `to_dict` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/session.py` | GameFlowState | `__post_init__` | 0 | 0 | 0 |  |
| `weiren_game/session.py` | GameFlowState | `from_dict` | 13 | 0 | 13 | （高频，略） |
| `weiren_game/session.py` | GameFlowState | `to_dict` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/session.py` | InstancePool | `allocate_tenant` | 1 | 0 | 1 | `engine.GameEngine._add_tenant` |
| `weiren_game/session.py` | InstancePool | `allocate_item` | 2 | 0 | 2 | `DLC_Character_STAR_V1.0.0.characters.STAR.initial_setup`、`systems.item_system.ItemSystemMixin._add_house_item` |
| `weiren_game/session.py` | InstancePool | `allocate_information` | 3 | 0 | 3 | `data.pseudos.pseudo_fries.create_accusation`、`data.pseudos.pseudo_fries.performance`、`systems.information_system.InformationSystemMixin._create_random_information` |
| `weiren_game/session.py` | InstancePool | `allocate_search` | 1 | 0 | 1 | `systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/session.py` | InstancePool | `allocate_pseudo` | 1 | 0 | 1 | `engine.GameEngine.new_game` |
| `weiren_game/session.py` | InstancePool | `allocate_mark` | 2 | 0 | 2 | `data.characters.erebus.initial_setup`、`systems.marks_system.MarksSystemMixin._gain_mark` |
| `weiren_game/session.py` | InstancePool | `from_dict` | 13 | 0 | 13 | （高频，略） |
| `weiren_game/session.py` | InstancePool | `to_dict` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/session.py` | RoundActionState | `from_dict` | 13 | 0 | 13 | （高频，略） |
| `weiren_game/session.py` | RoundActionState | `to_dict` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/condition.py` |  | `register_status_definition` | 20 | 0 | 20 | （高频，略） |
| `weiren_game/condition.py` |  | `_register_reveal_event` | 2 | 2 | 0 | `condition.(模块级)`、`condition.register_emotion_definition` |
| `weiren_game/condition.py` |  | `register_emotion_definition` | 2 | 0 | 2 | `content.<import>`、`dlc.load_status_file` |
| `weiren_game/condition.py` | StatusDefinition | `show` | 3 | 0 | 3 | `cli.show_codex`、`web_ui._condition_chips`、`web_ui.build_state` |
| `weiren_game/condition.py` | Condition | `__post_init__` | 0 | 0 | 0 |  |
| `weiren_game/condition.py` | Condition | `active` | 69 | 0 | 69 | （高频，略） |
| `weiren_game/condition.py` | Condition | `clamp` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/condition.py` | Condition | `clear` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/condition.py` | Condition | `from_dict` | 13 | 0 | 13 | （高频，略） |
| `weiren_game/condition.py` | Condition | `to_dict` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/global_event.py` |  | `register_global_event` | 7 | 1 | 6 | （高频，略） |
| `weiren_game/global_event.py` |  | `emotion_reveal_event` | 9 | 1 | 8 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventInstance | `active` | 69 | 2 | 67 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventInstance | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventInstance | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventState | `set` | 32 | 0 | 32 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventState | `instance` | 24 | 3 | 21 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventState | `active` | 69 | 2 | 67 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventState | `value_of` | 3 | 0 | 3 | `likai_test.characters.likai.initial_setup`、`likai_test.characters.likai.tenant_death`、`systems.marks_system.MarksSystemMixin._global_event_value` |
| `weiren_game/global_event.py` | GlobalEventState | `consume` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventState | `decay` | 1 | 0 | 1 | `systems.marks_system.MarksSystemMixin._decay_global_events` |
| `weiren_game/global_event.py` | GlobalEventState | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/global_event.py` | GlobalEventState | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/marks.py` | MarkInstance | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/marks.py` | MarkInstance | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/marks.py` | MarkPool | `add` | 24 | 0 | 24 | （高频，略） |
| `weiren_game/marks.py` | MarkPool | `instances_of` | 4 | 1 | 3 | `data.characters.erebus.detail_slot`、`data.characters.erebus.draw_fate`、`data.characters.erebus.initial_setup`、`marks.MarkPool.consume` |
| `weiren_game/marks.py` | MarkPool | `count` | 36 | 0 | 36 | （高频，略） |
| `weiren_game/marks.py` | MarkPool | `remove_value` | 1 | 0 | 1 | `data.characters.erebus._card_0` |
| `weiren_game/marks.py` | MarkPool | `consume` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/marks.py` | MarkPool | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/marks.py` | MarkPool | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/items.py` | ItemInstance | `__post_init__` | 0 | 0 | 0 |  |
| `weiren_game/items.py` | ItemInstance | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/items.py` | ItemInstance | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/items.py` | Inventory | `__iter__` | 0 | 0 | 0 |  |
| `weiren_game/items.py` | Inventory | `__len__` | 0 | 0 | 0 |  |
| `weiren_game/items.py` | Inventory | `add` | 24 | 0 | 24 | （高频，略） |
| `weiren_game/items.py` | Inventory | `move_to` | 2 | 0 | 2 | `systems.item_system.ItemSystemMixin.equip_item`、`systems.item_system.ItemSystemMixin.move_item` |
| `weiren_game/items.py` | Inventory | `_next_free_slot_excluding` | 1 | 1 | 0 | `items.Inventory.add` |
| `weiren_game/items.py` | Inventory | `at_plot` | 5 | 0 | 5 | `systems.item_system.ItemSystemMixin.equip_item`、`systems.item_system.ItemSystemMixin.move_item`、`systems.item_system.ItemSystemMixin.transfer_item`、`systems.item_system.ItemSystemMixin.unequip_item`、`systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/items.py` | Inventory | `_next_free_slot` | 1 | 1 | 0 | `items.Inventory.add` |
| `weiren_game/items.py` | Inventory | `instance` | 24 | 2 | 22 | （高频，略） |
| `weiren_game/items.py` | Inventory | `remove` | 19 | 1 | 18 | （高频，略） |
| `weiren_game/items.py` | Inventory | `remove_first` | 5 | 0 | 5 | `data.characters.wrongwave.try_resist`、`systems.item_system.ItemSystemMixin.equip_item`、`systems.item_system.ItemSystemMixin.transfer_item`、`systems.item_system.ItemSystemMixin.unequip_item`、`systems.pseudo_system.PseudoSystemMixin._break_search_tool` |
| `weiren_game/items.py` | Inventory | `consume` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/items.py` | Inventory | `count` | 36 | 5 | 31 | （高频，略） |
| `weiren_game/items.py` | Inventory | `earliest` | 2 | 0 | 2 | `data.items.character_items._resist_flintlock`、`systems.item_system.ItemSystemMixin._consume_durability` |
| `weiren_game/items.py` | Inventory | `all_with` | 1 | 0 | 1 | `engine.GameEngine.inventory_lines` |
| `weiren_game/items.py` | Inventory | `by_item_id` | 1 | 0 | 1 | `systems.item_system.ItemSystemMixin._merge_house_item` |
| `weiren_game/items.py` | Inventory | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/items.py` | Inventory | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/ability.py` | AbilityState | `from_dict` | 13 | 0 | 13 | （高频，略） |
| `weiren_game/ability.py` | AbilityState | `to_dict` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/pseudo.py` | PseudoCommonState | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/pseudo.py` | PseudoCommonState | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/pseudo.py` | PseudoRuntime | `__post_init__` | 0 | 0 | 0 |  |
| `weiren_game/pseudo.py` | PseudoRuntime | `scenario` | 5 | 0 | 5 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR._seed`、`data.pseudos.pseudo_fries.on_sanity_restored`、`data.pseudos.pseudo_fries.settle_end`、`systems.pseudo_system.PseudoSystemMixin._set_pseudo_marks`、`web_ui.build_state` |
| `weiren_game/pseudo.py` | PseudoRuntime | `_scenario_attr` | 2 | 2 | 0 | `pseudo.PseudoRuntime.__post_init__`、`pseudo.PseudoRuntime.scenario` |
| `weiren_game/pseudo.py` | PseudoRuntime | `__getattr__` | 0 | 0 | 0 |  |
| `weiren_game/pseudo.py` | PseudoRuntime | `__setattr__` | 2 | 1 | 1 | `models.GameState.__init__`、`pseudo.PseudoRuntime.__setattr__` |
| `weiren_game/pseudo.py` | PseudoRuntime | `from_dict` | 13 | 1 | 12 | （高频，略） |
| `weiren_game/pseudo.py` | PseudoRuntime | `to_dict` | 10 | 1 | 9 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `home_tenants` | 79 | 0 | 79 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_log` | 94 | 0 | 94 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `character` | 79 | 0 | 79 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_require_home_tenant` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_finish` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_collect_flush` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_collect_start` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `defer_search_report` | 3 | 0 | 3 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR.attack_searcher`、`data.pseudos.pseudo_benzene.attack_searcher`、`data.pseudos.pseudo_onion.attack_searcher` |
| `weiren_game/types.py` | EngineProtocol | `emotion_visible` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_clear_pending_choice` | 4 | 0 | 4 | `data.characters.erebus.cancel_fate`、`data.characters.erebus.resolve_fate`、`engine.GameEngine.commit_start_choice`、`engine.GameEngine.new_game` |
| `weiren_game/types.py` | EngineProtocol | `_record_action` | 12 | 0 | 12 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_kill_tenant` | 3 | 0 | 3 | `data.pseudos.pseudo_fries.expel_infiltrator`、`systems.round_effects.RoundEffectsSystemMixin._settle_other_end_effects`、`systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/types.py` | EngineProtocol | `container` | 8 | 0 | 8 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `living_tenants` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_passive_available` | 50 | 0 | 50 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_is_personality` | 31 | 0 | 31 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_bond_tier` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `bond_levels` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_rng` | 67 | 0 | 67 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `discover` | 5 | 0 | 5 | `data.characters.erebus.draw_fate`、`engine.GameEngine._begin_start_pick`、`engine.GameEngine.new_game`、`systems.random_system.RandomSystemMixin.discover`、`web_ui.Session.perform` |
| `weiren_game/types.py` | EngineProtocol | `_restore_sanity` | 37 | 0 | 37 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_restore_health` | 24 | 0 | 24 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_consume_sanity` | 11 | 0 | 11 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_damage_health` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_consume_held_durability` | 4 | 0 | 4 | `data.items.tools_armor._ghillie_search_return`、`data.items.tools_armor.apply_armour`、`data.items.tools_armor.armour_allows_status`、`systems.round_effects.RoundEffectsSystemMixin._settle_held_items` |
| `weiren_game/types.py` | EngineProtocol | `_loss_health` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_after_health_changed` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_loss_sanity` | 3 | 0 | 3 | `data.characters.erebus.apply_health_consume_conversion`、`data.characters.rose.use_rose_expel`、`systems.condition_system.ConditionSystemMixin._apply_status_end` |
| `weiren_game/types.py` | EngineProtocol | `_consume_health` | 1 | 0 | 1 | `data.characters.chaos.use_permission_transfer` |
| `weiren_game/types.py` | EngineProtocol | `_damage_sanity` | 2 | 0 | 2 | `data.information._resolve_suppressed_sobbing`、`systems.search_system.SearchSystemMixin._resolve_search_return` |
| `weiren_game/types.py` | EngineProtocol | `_skill_outcome` | 17 | 0 | 17 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_set_ability_cooldown` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_expel_tenant` | 4 | 0 | 4 | `data.characters.erebus._card_11`、`data.characters.rose.use_rose_expel`、`data.characters.six71.use_cannot_stand`、`systems.pseudo_system.PseudoSystemMixin.accuse` |
| `weiren_game/types.py` | EngineProtocol | `_local_skill_module` | 2 | 0 | 2 | `data.characters.chaos.use_permission_transfer`、`systems.ability_system.AbilitySystemMixin._gate_local_skill` |
| `weiren_game/types.py` | EngineProtocol | `use_ability` | 4 | 0 | 4 | `cli.run`、`cli.use_ability`、`data.characters.chaos.use_permission_transfer`、`web_ui.Session.perform` |
| `weiren_game/types.py` | EngineProtocol | `_set_global_event` | 15 | 0 | 15 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_mark_count` | 14 | 0 | 14 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_gain_mark` | 8 | 0 | 8 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_has_persona` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_consume_mark` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_global_event_value` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_consume_global_event` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_emit_node` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_suppress_pseudo` | 3 | 0 | 3 | `DLC_Character_STAR_V1.0.0.characters.STAR._resolve_door`、`data.characters.erebus._card_21`、`data.characters.peach.justice_execution_guard` |
| `weiren_game/types.py` | EngineProtocol | `_global_event_active` | 5 | 0 | 5 | `data.pseudos.pseudo_onion._onion_reveal_gate`、`data.pseudos.pseudo_onion.emotion_end_extra`、`systems.marks_system.MarksSystemMixin._pseudo_capability`、`systems.pseudo_system.PseudoSystemMixin._attempt_breakthrough`、`systems.visitor_system.VisitorSystemMixin._queue_human_visitor` |
| `weiren_game/types.py` | EngineProtocol | `_personas_of` | 2 | 0 | 2 | `data.characters.fries.detail_slot`、`data.characters.fries.grant_persona` |
| `weiren_game/types.py` | EngineProtocol | `_pseudo_capability` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_pseudo_enters_house` | 3 | 0 | 3 | `data.characters.erebus._card_0`、`systems.pseudo_system.PseudoSystemMixin._attempt_breakthrough`、`systems.visitor_system.VisitorSystemMixin._queue_scheduled_visitors` |
| `weiren_game/types.py` | EngineProtocol | `_set_personas` | 1 | 0 | 1 | `data.characters.fries.grant_persona` |
| `weiren_game/types.py` | EngineProtocol | `_reduce_emotion_set` | 11 | 0 | 11 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_recover_condition` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_adjust_emotion_set` | 4 | 0 | 4 | `data.information._resolve_tense_nerves`、`data.items.food._effect_double_mint`、`data.items.food._effect_weird_beans`、`data.items.information_carriers.ancient_legend_start_of_turn` |
| `weiren_game/types.py` | EngineProtocol | `_extend_condition` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_strengthen_emotion_set` | 4 | 0 | 4 | `data.information._resolve_suppressed_sobbing`、`data.items.food._effect_spicy_beef`、`data.pseudos.pseudo_fries.mind_play`、`data.pseudos.pseudo_fries.pending_performance_information` |
| `weiren_game/types.py` | EngineProtocol | `_worsen_condition` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_apply_emotion` | 4 | 0 | 4 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR._add_anxiety`、`data.pseudos.pseudo_onion.attack_searcher`、`data.pseudos.pseudo_onion.cast_whisper`、`systems.condition_system.ConditionSystemMixin._adjust_emotion_set` |
| `weiren_game/types.py` | EngineProtocol | `_strengthen_named_emotion` | 2 | 0 | 2 | `data.information._resolve_odd_smile`、`data.information._resolve_tense_nerves` |
| `weiren_game/types.py` | EngineProtocol | `_add_condition` | 1 | 0 | 1 | `data.characters.erebus._card_8` |
| `weiren_game/types.py` | EngineProtocol | `_set_condition` | 1 | 0 | 1 | `data.information._resolve_supply_dispute` |
| `weiren_game/types.py` | EngineProtocol | `_observe_pseudo_skill` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_create_random_information` | 7 | 0 | 7 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_verify_information_object` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_discern_one_information` | 1 | 0 | 1 | `data.personalities.suspicious.start_of_turn_bond` |
| `weiren_game/types.py` | EngineProtocol | `_pseudo_actions_suppressed` | 12 | 0 | 12 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_skill_respond_skill` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_attempt_breakthrough` | 5 | 0 | 5 | `DLC_Character_STAR_V1.0.0.pseudos.pseudo_STAR.visit`、`data.pseudos.pseudo_benzene.visit`、`data.pseudos.pseudo_fries.infernal_trigger`、`data.pseudos.pseudo_fries.settle_end`、`data.pseudos.pseudo_onion.visit` |
| `weiren_game/types.py` | EngineProtocol | `_break_search_tool` | 3 | 0 | 3 | `data.items.character_items._resist_flintlock`、`data.items.tools_armor._resist_crowbar`、`data.items.tools_armor._resist_sports_shoes` |
| `weiren_game/types.py` | EngineProtocol | `_pseudo_handler` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `pseudo_in_house` | 4 | 0 | 4 | `data.characters.erebus._card_11`、`data.characters.zero329.start_of_turn`、`systems.information_system.InformationSystemMixin._create_random_information`、`systems.round_effects.RoundEffectsSystemMixin._settle_pseudo_start_handlers` |
| `weiren_game/types.py` | EngineProtocol | `_set_pseudo_marks` | 1 | 0 | 1 | `data.characters.erebus._card_9` |
| `weiren_game/types.py` | EngineProtocol | `_random_item` | 9 | 0 | 9 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_recalculate_search` | 5 | 0 | 5 | `data.characters.wrongwave.try_resist`、`data.items.character_items._resist_flintlock`、`data.pseudos.pseudo_fries.capture_searcher`、`systems.pseudo_system.PseudoSystemMixin._break_search_tool`、`systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/types.py` | EngineProtocol | `_fragile_chance` | 8 | 0 | 8 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_gain_item` | 10 | 0 | 10 | （高频，略） |
| `weiren_game/types.py` | EngineProtocol | `_spend_item_use` | 5 | 0 | 5 | `data.personalities.suspicious.item_use_wasted`、`data.tags._medical.use_medical`、`data.tags.anodyne.use`、`systems.item_system.ItemSystemMixin._use_general_item`、`systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/types.py` | EngineProtocol | `_take_item` | 4 | 0 | 4 | `data.characters.erebus.resolve_fate`、`data.items.food._garlic_seasoning`、`systems.item_system.ItemSystemMixin._spend_item_use`、`systems.item_system.ItemSystemMixin.use_item` |
| `weiren_game/types.py` | EngineProtocol | `_merge_house_item` | 4 | 0 | 4 | `data.characters.flowey._action_take`、`systems.item_system.ItemSystemMixin._gain_item`、`systems.item_system.ItemSystemMixin._return_tenant_items`、`systems.item_system.ItemSystemMixin._spill_tenant_overflow` |
| `weiren_game/types.py` | EngineProtocol | `_tenant_item_ids` | 2 | 0 | 2 | `data.pseudos.pseudo_fries.encounter_chance`、`systems.search_system.SearchSystemMixin.start_search` |
| `weiren_game/types.py` | EngineProtocol | `_pay_ability_costs` | 4 | 0 | 4 | `data.characters.onion.use_emotion_strip`、`data.characters.zero329.use_intent_awareness`、`systems.ability_system.AbilitySystemMixin._gate_local_skill`、`systems.cost_system.CostSystemMixin._pay_cost_pack` |
| `weiren_game/types.py` | EngineProtocol | `_queue_human_visitor` | 3 | 0 | 3 | `data.characters.dragon.party_focus`、`data.characters.dragon.use_call_friends`、`systems.visitor_system.VisitorSystemMixin._queue_scheduled_visitors` |
| `weiren_game/types.py` | EngineProtocol | `_grant_learned_passive` | 1 | 0 | 1 | `data.items.information_carriers._book_held_end_of_turn` |
| `weiren_game/cli.py` |  | `_configure_console` | 1 | 1 | 0 | `cli.main` |
| `weiren_game/cli.py` |  | `_print_messages` | 8 | 8 | 0 | （高频，略） |
| `weiren_game/cli.py` |  | `_choose` | 7 | 7 | 0 | （高频，略） |
| `weiren_game/cli.py` |  | `_yes` | 1 | 1 | 0 | `cli.use_ability._collect` |
| `weiren_game/cli.py` |  | `_home_ids` | 3 | 3 | 0 | `cli._choose_target`、`cli.equip_item`、`cli.use_item` |
| `weiren_game/cli.py` |  | `show_status` | 4 | 4 | 0 | `cli.accuse`、`cli.equip_item`、`cli.run`、`cli.use_item` |
| `weiren_game/cli.py` |  | `show_inventory` | 1 | 1 | 0 | `cli.run` |
| `weiren_game/cli.py` |  | `show_locations` | 2 | 2 | 0 | `cli.run`、`cli.start_search` |
| `weiren_game/cli.py` |  | `show_codex` | 2 | 2 | 0 | `cli.main`、`cli.run` |
| `weiren_game/cli.py` |  | `handle_door` | 1 | 1 | 0 | `cli.run` |
| `weiren_game/cli.py` |  | `start_search` | 3 | 2 | 1 | `cli.run`、`cli.start_search`、`web_ui.Session.perform` |
| `weiren_game/cli.py` |  | `use_item` | 3 | 2 | 1 | `cli.run`、`cli.use_item`、`web_ui.Session.perform` |
| `weiren_game/cli.py` |  | `equip_item` | 3 | 2 | 1 | `cli.equip_item`、`cli.run`、`web_ui.Session.perform` |
| `weiren_game/cli.py` |  | `unequip_item` | 3 | 2 | 1 | `cli.run`、`cli.unequip_item`、`web_ui.Session.perform` |
| `weiren_game/cli.py` |  | `_choose_target` | 2 | 2 | 0 | `cli.accuse`、`cli.use_ability._collect` |
| `weiren_game/cli.py` |  | `use_ability` | 4 | 2 | 2 | `cli.run`、`cli.use_ability`、`data.characters.chaos.use_permission_transfer`、`web_ui.Session.perform` |
| `weiren_game/cli.py` |  | `show_information` | 1 | 1 | 0 | `cli.run` |
| `weiren_game/cli.py` |  | `accuse` | 4 | 2 | 2 | `cli.accuse`、`cli.run`、`systems.pseudo_system.PseudoSystemMixin.accuse`、`web_ui.Session.perform` |
| `weiren_game/cli.py` |  | `run` | 1 | 1 | 0 | `cli.main` |
| `weiren_game/cli.py` |  | `build_parser` | 1 | 1 | 0 | `cli.main` |
| `weiren_game/cli.py` |  | `main` | 4 | 1 | 3 | `__main__.(模块级)`、`__main__.<import>`、`cli.(模块级)`、`web_ui.(模块级)` |
| `weiren_game/web_ui.py` |  | `avatar_of` | 4 | 4 | 0 | `web_ui._visitor_preview`、`web_ui.build_state`、`web_ui.build_state._option_view`、`web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `persona_display` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_location_supply` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_location_drop` | 2 | 2 | 0 | `web_ui.build_state`、`web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `_location_mechanics` | 2 | 2 | 0 | `web_ui.build_state`、`web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `_item_icon` | 3 | 3 | 0 | `web_ui._item_entry`、`web_ui.build_state._option_view`、`web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `_pseudo_progress` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_pseudo_card` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_pseudo_slot` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_visitor_preview` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_item_entry` | 2 | 2 | 0 | `web_ui._panel_item_entry`、`web_ui._slot_entries` |
| `weiren_game/web_ui.py` |  | `_slot_entries` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_condition_chips` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_project_tiers` | 2 | 2 | 0 | `web_ui._mark_row`、`web_ui._project_slot` |
| `weiren_game/web_ui.py` |  | `_mark_row` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_project_slot` | 3 | 3 | 0 | `web_ui._detail_slot`、`web_ui._project_panel`、`web_ui._pseudo_slot` |
| `weiren_game/web_ui.py` |  | `_detail_slot` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_panel_item_entry` | 1 | 1 | 0 | `web_ui._project_panel` |
| `weiren_game/web_ui.py` |  | `_project_panel` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `resolve_pack_asset` | 1 | 1 | 0 | `web_ui.Handler.do_GET` |
| `weiren_game/web_ui.py` |  | `resource_pack_state` | 1 | 1 | 0 | `web_ui.Handler.do_GET` |
| `weiren_game/web_ui.py` |  | `avatar_art` | 3 | 3 | 0 | `web_ui.build_state`、`web_ui.build_state._option_view`、`web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `pseudo_avatar_art` | 1 | 1 | 0 | `web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `_expel_texts` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_ability_target_options` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_global_event_rows` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `build_state` | 2 | 2 | 0 | `web_ui.Handler.do_GET`、`web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` |  | `_map_shelter` | 1 | 1 | 0 | `web_ui.build_state` |
| `weiren_game/web_ui.py` |  | `_map_menu` | 1 | 1 | 0 | `web_ui.menu_state` |
| `weiren_game/web_ui.py` |  | `menu_state` | 2 | 2 | 0 | `web_ui.Handler.do_GET`、`web_ui.apply_dlc` |
| `weiren_game/web_ui.py` |  | `art_url` | 2 | 2 | 0 | `web_ui.build_state`、`web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `_safe_filename` | 1 | 1 | 0 | `web_ui.Session.new_game` |
| `weiren_game/web_ui.py` |  | `_read_index` | 4 | 4 | 0 | `web_ui.Session.delete_save`、`web_ui.Session.flush_pending_save`、`web_ui.Session.perform`、`web_ui.list_saves` |
| `weiren_game/web_ui.py` |  | `_write_index` | 3 | 3 | 0 | `web_ui.Session.delete_save`、`web_ui.Session.flush_pending_save`、`web_ui.Session.perform` |
| `weiren_game/web_ui.py` |  | `_save_summary` | 1 | 1 | 0 | `web_ui.list_saves` |
| `weiren_game/web_ui.py` |  | `list_saves` | 1 | 1 | 0 | `web_ui.Handler.do_GET` |
| `weiren_game/web_ui.py` |  | `_codex_extra` | 1 | 1 | 0 | `web_ui.codex_state` |
| `weiren_game/web_ui.py` |  | `codex_state` | 1 | 1 | 0 | `web_ui.Handler.do_GET` |
| `weiren_game/web_ui.py` |  | `apply_dlc` | 1 | 1 | 0 | `web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` |  | `apply_settings` | 1 | 1 | 0 | `web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` |  | `make_handler` | 1 | 1 | 0 | `web_ui.run_server` |
| `weiren_game/web_ui.py` |  | `run_server` | 1 | 1 | 0 | `web_ui.main` |
| `weiren_game/web_ui.py` |  | `main` | 4 | 1 | 3 | `__main__.(模块级)`、`__main__.<import>`、`cli.(模块级)`、`web_ui.(模块级)` |
| `weiren_game/web_ui.py` | Session | `__init__` | 1 | 0 | 1 | `random_log.LoggedRandom.__init__` |
| `weiren_game/web_ui.py` | Session | `new_game` | 3 | 2 | 1 | `cli.main`、`web_ui.Handler.do_POST`、`web_ui.Session.new_game` |
| `weiren_game/web_ui.py` | Session | `flush_pending_save` | 2 | 2 | 0 | `web_ui.Handler.do_POST`、`web_ui.Session.new_game` |
| `weiren_game/web_ui.py` | Session | `abort_start` | 1 | 1 | 0 | `web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` | Session | `load_save` | 1 | 1 | 0 | `web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` | Session | `delete_save` | 1 | 1 | 0 | `web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` | Session | `drain` | 2 | 2 | 0 | `web_ui.Handler.do_GET`、`web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` | Session | `perform` | 1 | 1 | 0 | `web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` | Handler | `log_message` | **0** | 0 | 0 | ⚠️ 无引用 |
| `weiren_game/web_ui.py` | Handler | `_send_json` | 2 | 2 | 0 | `web_ui.Handler.do_GET`、`web_ui.Handler.do_POST` |
| `weiren_game/web_ui.py` | Handler | `_send_file` | 1 | 1 | 0 | `web_ui.Handler.do_GET` |
| `weiren_game/web_ui.py` | Handler | `_send_text` | 1 | 1 | 0 | `web_ui.Handler.do_GET` |
| `weiren_game/web_ui.py` | Handler | `do_GET` | **0** | 0 | 0 | ⚠️ 无引用 |
| `weiren_game/web_ui.py` | Handler | `do_POST` | **0** | 0 | 0 | ⚠️ 无引用 |
| `weiren_game/ui.py` |  | `_pairs` | 1 | 1 | 0 | `ui.CliUI.choose` |
| `weiren_game/ui.py` | UserInterface | `message` | 5 | 0 | 5 | `cli._print_messages`、`data.characters.erebus.resolve_interaction`、`engine.GameEngine._log`、`engine.GameEngine._record_log`、`engine.GameEngine._show_message` |
| `weiren_game/ui.py` | UserInterface | `choose` | 2 | 1 | 1 | `data.characters.erebus.resolve_interaction`、`ui.UserInterface.choose_target` |
| `weiren_game/ui.py` | UserInterface | `confirm` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/ui.py` | UserInterface | `choose_target` | 1 | 0 | 1 | `data.characters.erebus.resolve_interaction` |
| `weiren_game/ui.py` | CliUI | `message` | 5 | 0 | 5 | `cli._print_messages`、`data.characters.erebus.resolve_interaction`、`engine.GameEngine._log`、`engine.GameEngine._record_log`、`engine.GameEngine._show_message` |
| `weiren_game/ui.py` | CliUI | `choose` | 2 | 1 | 1 | `data.characters.erebus.resolve_interaction`、`ui.UserInterface.choose_target` |
| `weiren_game/ui.py` | CliUI | `confirm` | 6 | 0 | 6 | （高频，略） |
| `weiren_game/text.py` |  | `segments` | 2 | 2 | 0 | `text.render_markup`、`text.strip_markup` |
| `weiren_game/text.py` |  | `strip_markup` | 1 | 1 | 0 | `text.render_markup` |
| `weiren_game/text.py` |  | `render_markup` | 2 | 0 | 2 | `cli.<import>`、`cli.show_codex` |
| `weiren_game/log_shape.py` |  | `row_from_line` | 1 | 1 | 0 | `log_shape.rows_from_lines` |
| `weiren_game/log_shape.py` |  | `rows_from_lines` | 2 | 0 | 2 | `engine.<import>`、`engine.GameEngine._collect_flush` |
| `weiren_game/random_log.py` | LoggedRandom | `__init__` | 1 | 1 | 0 | `random_log.LoggedRandom.__init__` |
| `weiren_game/random_log.py` | LoggedRandom | `_note` | 2 | 2 | 0 | `random_log.LoggedRandom._randbelow`、`random_log.LoggedRandom.random` |
| `weiren_game/random_log.py` | LoggedRandom | `random` | 65 | 3 | 62 | （高频，略） |
| `weiren_game/random_log.py` | LoggedRandom | `_randbelow` | 1 | 1 | 0 | `random_log.LoggedRandom._randbelow` |
| `weiren_game/random_log.py` | _LoggedFloat | `__new__` | 1 | 1 | 0 | `random_log._LoggedFloat.__new__` |
| `weiren_game/random_log.py` | _LoggedFloat | `_judge` | 4 | 4 | 0 | `random_log._LoggedFloat.__ge__`、`random_log._LoggedFloat.__gt__`、`random_log._LoggedFloat.__le__`、`random_log._LoggedFloat.__lt__` |
| `weiren_game/random_log.py` | _LoggedFloat | `__reduce__` | 0 | 0 | 0 |  |
| `weiren_game/random_log.py` | _LoggedFloat | `__lt__` | 1 | 1 | 0 | `random_log._LoggedFloat.__lt__` |
| `weiren_game/random_log.py` | _LoggedFloat | `__le__` | 1 | 1 | 0 | `random_log._LoggedFloat.__le__` |
| `weiren_game/random_log.py` | _LoggedFloat | `__gt__` | 1 | 1 | 0 | `random_log._LoggedFloat.__gt__` |
| `weiren_game/random_log.py` | _LoggedFloat | `__ge__` | 1 | 1 | 0 | `random_log._LoggedFloat.__ge__` |
| `weiren_game/paths.py` |  | `app_base` | 12 | 2 | 10 | （高频，略） |
| `weiren_game/paths.py` |  | `saves_dir` | 3 | 1 | 2 | `paths.(模块级)`、`web_ui.(模块级)`、`web_ui.<import>` |
| `weiren_game/paths.py` |  | `resource_dir` | 3 | 1 | 2 | `paths.(模块级)`、`web_ui.(模块级)`、`web_ui.<import>` |
| `weiren_game/avatars.py` |  | `avatar_hash` | 1 | 1 | 0 | `avatars.avatar_view` |
| `weiren_game/avatars.py` |  | `_pack_dirs` | 2 | 2 | 0 | `avatars.avatar_index`、`avatars.avatar_mode` |
| `weiren_game/avatars.py` |  | `avatar_index` | 2 | 2 | 0 | `avatars.avatar_view`、`avatars.resolve_avatar_part` |
| `weiren_game/avatars.py` |  | `resolve_avatar_part` | 2 | 0 | 2 | `web_ui.<import>`、`web_ui.Handler.do_GET` |
| `weiren_game/avatars.py` |  | `avatar_mode` | 4 | 2 | 2 | `avatars.avatar_mode`、`avatars.avatar_view`、`web_ui.<import>`、`web_ui.pseudo_avatar_art` |
| `weiren_game/avatars.py` |  | `part_markup` | 1 | 1 | 0 | `avatars.avatar_view` |
| `weiren_game/avatars.py` |  | `avatar_view` | 3 | 0 | 3 | `web_ui.<import>`、`web_ui.avatar_art`、`web_ui.pseudo_avatar_art` |
| `weiren_game/item_icons.py` |  | `quality_color` | 2 | 2 | 0 | `item_icons.(模块级)`、`item_icons.item_icon_markup` |
| `weiren_game/item_icons.py` |  | `item_icon_index` | 2 | 2 | 0 | `item_icons.(模块级)`、`item_icons.resolve_item_icon` |
| `weiren_game/item_icons.py` |  | `tag_order` | 2 | 2 | 0 | `item_icons.(模块级)`、`item_icons.resolve_item_icon` |
| `weiren_game/item_icons.py` |  | `resolve_item_icon` | 2 | 2 | 0 | `item_icons.(模块级)`、`item_icons.item_icon_markup` |
| `weiren_game/item_icons.py` |  | `item_icon_markup` | 5 | 1 | 4 | `item_icons.(模块级)`、`web_ui.<import>`、`web_ui._item_entry`、`web_ui.build_state._option_view`、`web_ui.codex_state` |
| `weiren_game/icon_files.py` |  | `icon_index` | 2 | 2 | 0 | `icon_files.(模块级)`、`icon_files.resolve_icon` |
| `weiren_game/icon_files.py` |  | `resolve_icon` | 4 | 2 | 2 | `icon_files.(模块级)`、`icon_files.icon_url`、`web_ui.<import>`、`web_ui.Handler.do_GET` |
| `weiren_game/icon_files.py` |  | `icon_url` | 3 | 1 | 2 | `icon_files.(模块级)`、`web_ui.<import>`、`web_ui.art_url` |
| `weiren_game/asset_layers.py` |  | `layer_roots` | 7 | 1 | 6 | （高频，略） |
| `weiren_game/resourcepack_loader.py` |  | `_normalize_order` | 3 | 1 | 2 | `dlc.apply_pack_order`、`dlc.load_configured_dlc`、`resourcepack_loader.apply_resourcepack_order` |
| `weiren_game/resourcepack_loader.py` |  | `resourcepack_root` | 5 | 3 | 2 | `resourcepack_loader.available_resourcepacks`、`resourcepack_loader.load_single_resourcepack`、`resourcepack_loader.resourcepack_label`、`web_ui.<import>`、`web_ui.menu_state` |
| `weiren_game/resourcepack_loader.py` |  | `available_resourcepacks` | 5 | 1 | 4 | `resourcepack_loader.apply_resourcepack_order`、`web_ui.<import>`、`web_ui.apply_dlc`、`web_ui.apply_settings`、`web_ui.menu_state` |
| `weiren_game/resourcepack_loader.py` |  | `resourcepack_label` | 2 | 0 | 2 | `web_ui.<import>`、`web_ui.menu_state` |
| `weiren_game/resourcepack_loader.py` |  | `load_single_resourcepack` | 1 | 1 | 0 | `resourcepack_loader.apply_resourcepack_order` |
| `weiren_game/resourcepack_loader.py` |  | `apply_resourcepack_order` | 3 | 0 | 3 | `dlc.<import>`、`dlc.apply_pack_order`、`dlc.load_configured_dlc` |
## EngineProtocol vs 实测内容面

> 协议是「内容能碰到什么引擎 API」的权威（`weiren_game/types.py`）。下面非空说明协议该更新了。

- **内容在用、协议未声明（0）**：无
- **协议声明、内容未用（0）**：无

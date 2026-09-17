"""回合初/回合末各阶段的结算（顺序由 lifecycle 阶段表声明）。"""

from __future__ import annotations

import math

from weiren_game.content import CONTENT
from weiren_game.probability import resolve
from weiren_game.data import (
    AWAKENING_EMOTIONS,
    DIFFICULTIES,
    EROSION_EMOTIONS,
    EVENT_IDS,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.tenant import TenantState as Tenant
from weiren_game.effects.health_sanity import refresh_high_health_immunity

class RoundEffectsSystemMixin:

    def _settle_emotion_values(self) -> None:
        """结算各房客侵蚀/觉醒情绪对隐藏消沉值的影响，并套用理智区间等修正。"""
        from weiren_game.data import CHARACTER_VALUE_HOOKS

        for tenant in self.home_tenants():
            erosion_conditions = [tenant.condition(key) for key in EROSION_EMOTIONS]
            awakening_conditions = [tenant.condition(key) for key in AWAKENING_EMOTIONS]
            depression_i = sum(c.intensity for c in erosion_conditions if c.active)
            depression_l = max((c.layers for c in erosion_conditions if c.active), default=0)
            elation_i = sum(c.intensity for c in awakening_conditions if c.active)
            elation_l = max((c.layers for c in awakening_conditions if c.active), default=0)
            if tenant.sanity > 90:
                multiplier = .2
            elif tenant.sanity > 80:
                multiplier = .5
            elif tenant.sanity > 70:
                multiplier = .8
            elif tenant.sanity > 50:
                multiplier = .5
            elif tenant.sanity > 30:
                multiplier = 1.3
            elif tenant.sanity > 10:
                multiplier = 1.7
            else:
                multiplier = 2.0
            # The manuscript applies the sanity-band modifier to the complete
            # emotionValue change, not only to its erosion half.
            change = (depression_i * depression_l - elation_i * elation_l) * multiplier
            change = self._apply_modifiers(
                "depressionChange", change, ("消沉", tenant.character_id),
                {"tenant": tenant, "change": change},
            )
            if change:
                tenant.depression = max(-10000.0, min(10000.0, tenant.depression + change))
                # The numerical depression value is explicitly hidden from the
                # homeowner.  Keep it deterministic internally without leaking
                # either the delta or total through the event log.
                self._log(f"情绪结算：{self.character(tenant).name}的隐藏消沉值发生了变化。")

    def _run_house_item_start_hooks(self) -> None:
        """实例回合初·屋主仓库 scope：按 ITEM_HOOKS["turn_start.house"] 扫描。"""
        from weiren_game.data import ITEM_HOOKS

        for item_id, node_map in ITEM_HOOKS.items():
            if self._house_count(item_id) <= 0:
                continue
            for hook in node_map.get("turn_start.house", {}).values():
                hook(self)

    def _settle_tenant_instance_start(self) -> None:
        """实例回合初·房客/背包 scope：顺序与重构前一致。"""
        from weiren_game.data import NODE_HOOKS, TURN_START_HOOKS

        madness_active = any(
            hook(self, at_turn_end=False)
            for hook in NODE_HOOKS.get("madness.available", ())
        )
        for tenant in list(self.home_tenants()):
            tenant.home_turns += 1
            # 回合初补能：高生命免疫（a-10 为常驻满充）。
            refresh_high_health_immunity(self, tenant)
            if tenant.madness.layers >= 10 and madness_active:
                # “所有额外的癫狂” leaves the base layer in place.
                for hook in NODE_HOOKS.get("madness.convert_excess", ()):
                    hook(self, tenant, emotions_active=madness_active)

            # 背包实例回合初效果按 ITEM_HOOKS 扫描。
            from weiren_game.data import ITEM_HOOKS

            for held in list(tenant.inventory.items):
                node_hooks = ITEM_HOOKS.get(held.item_id, {}).get(
                    "turn_start.backpack", {}
                )
                for hook in node_hooks.values():
                    hook(self, tenant, held)
            for hook in NODE_HOOKS.get("legend.turn_start", ()):
                hook(self, tenant)

            self._run_status_effect_node("turn_start.status_effects", tenant)

            turn_start_handler = TURN_START_HOOKS.get(tenant.character_id)
            if turn_start_handler is not None:
                turn_start_handler(self, tenant)

    def _settle_pseudo_start_handlers(self) -> None:
        """实例回合初·伪人 scope：start_passive/performance 查 SCENARIO_HANDLERS。

        ``start_passive``（如洋葱“先兆低语”）对局开始即生效，不要求已揭示；
        仅当对应行为位（cast）被禁用时跳过。
        """
        from weiren_game.data import SCENARIO_HANDLERS

        handlers = SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {})
        start_passive = handlers.get("start_passive")
        if (
            start_passive is not None
            and not self._pseudo_actions_suppressed()
        ):
            start_passive(self)
        performance_handler = handlers.get("performance")
        if performance_handler is not None and self.pseudo_in_house():
            performance_handler(self)

    def _start_of_turn_effects(self) -> None:
        """回合初实例节点总调度：屋主仓库→房客/背包→羁绊→房客光环→伪人。"""
        self._run_house_item_start_hooks()
        self._settle_tenant_instance_start()

        # 羁绊 scope（位置与重构前一致）。
        bonds = self.bond_levels()
        from weiren_game.data.personalities import BOND_TURN_START_HOOKS

        for hook in BOND_TURN_START_HOOKS.values():
            hook(self, bonds)

        # 持之以恒：回合初把到期保护转为永续“已保护过”标记。
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("turn_start.maintain_guard", ()):
            hook(self)

        self._settle_pseudo_start_handlers()

    def _settle_base_end_effects(self) -> None:
        """结算回合末基础消耗：按人物/羁绊修正汇总理智消耗与高生命自然流失。"""
        from weiren_game.data import CHARACTER_VALUE_HOOKS

        bonds = self.bond_levels()
        from weiren_game.data import NODE_HOOKS, SCENARIO_HANDLERS

        multiplier_handler = SCENARIO_HANDLERS.get(
            self.state.pseudo_state.scenario_id, {}
        ).get("end_sanity_multiplier")
        end_sanity_multiplier = (
            float(multiplier_handler(self))
            if multiplier_handler is not None
            else 1.0
        )
        madness_active = any(
            hook(self, at_turn_end=True)
            for hook in NODE_HOOKS.get("madness.available", ())
        )

        # 这一段会逐人播报理智/生命变化；收起明细，只在最后播一条汇总（玩家可点开看）。
        self._collect_start()
        tenant_count = len(self.home_tenants())
        for tenant in list(self.home_tenants()):
            definition = self.character(tenant)
            sanity_cost = 1.0
            if tenant.sanity >= 70:
                sanity_cost = 2.0
            if tenant.sanity >= 90:
                sanity_cost += 2.0
            from weiren_game.data import SCENARIO_HANDLERS

            end_bonus_handler = SCENARIO_HANDLERS.get(
                self.state.pseudo_state.scenario_id, {}
            ).get("end_turn_sanity_bonus")
            if end_bonus_handler is not None:
                sanity_cost += end_bonus_handler(self, tenant)
            sanity_cost = self._apply_modifiers(
                "sanityConsume", sanity_cost,
                ("回合末消耗", tenant.character_id), {"tenant": tenant},
            )
            self._consume_sanity(tenant, max(0, sanity_cost), "回合末消耗")

            if tenant.health >= 70:
                self._loss_health(tenant, 3 + (2 if tenant.health >= 90 else 0), "高生命值自然流失")
            from weiren_game.data.personalities import BOND_END_HEALTH_HOOKS

            for _personality_id, end_health_hook in BOND_END_HEALTH_HOOKS.items():
                end_health_hook(self, tenant)

        self._collect_flush(f"回合末结算：{tenant_count} 名房客的理智与生命变化。")

    def _settle_buff_debuff_effects(self) -> None:
        """回合末依次结算创伤、紊乱及各情绪的自行演化。"""
        for tenant in list(self.home_tenants()):
            self._apply_status_end(tenant, tenant.trauma, physical=True, label="创伤")
            self._apply_status_end(tenant, tenant.disorder, physical=False, label="紊乱")
            for key, label in {**EROSION_EMOTIONS, **AWAKENING_EMOTIONS}.items():
                self._apply_emotion_end(tenant, tenant.condition(key), label)

    def _decay_conditions(self) -> None:
        """回合末公共衰减：所有状态层数 -1，归零移除。

        规则只有这一句：``condition`` 在回合末走一个层数 -1 的公共函数。
        各状态的"可能 +1"（创伤/紊乱恶化、情绪强化、休克回层）留在各自逻辑里；
        ``permanent`` 状态回满、``auto_decay=False`` 的自管状态跳过，均由定义声明，
        不在这里写特例。
        """
        from weiren_game.condition import STATUS_DEFINITIONS

        for tenant in list(self.home_tenants()):
            for status_id, condition in list(tenant.conditions.items()):
                if not condition.active:
                    continue
                definition = STATUS_DEFINITIONS.get(status_id)
                if definition is None:
                    continue
                if definition.permanent:
                    condition.layers = definition.layers_max
                elif definition.auto_decay:
                    condition.layers -= 1
                    if condition.layers <= 0:
                        tenant.clear_status(status_id)

    def _settle_books_and_equipment(self) -> None:
        """回合末结算装备书籍的研读进度、装备耐久消耗与该物资易损。"""
        for tenant in list(self.home_tenants()):
            for held in list(tenant.inventory.items):
                held.held_turns += 1
                # 物品专属回合末效果（书籍研读/该物资易损等）按 ITEM_HOOKS 扫描。
                from weiren_game.data import ITEM_HOOKS

                node_hooks = ITEM_HOOKS.get(held.item_id, {}).get(
                    "turn_end.held", {}
                )
                for hook in node_hooks.values():
                    hook(self, tenant, held)
                if held in tenant.inventory.items and ITEMS[held.item_id].durable:
                    self._consume_held_durability(tenant, held, 1)

    def _grant_learned_passive(self, tenant: Tenant, ability_id: str) -> None:
        """把书籍研读获得的永久被动登记为该房客的 learned 技能状态。"""
        from weiren_game.ability import AbilityState

        if not tenant.has_ability(ability_id):
            tenant.abilities.append(AbilityState(ability_id, acquisition="learned"))

    def _settle_other_end_effects(self) -> None:
        """结算其余回合末效果：高生命自然回复、休克与离屋判定，并清理临时全局修正。"""
        for tenant in list(self.home_tenants()):
            self._natural_high_health_recovery(tenant)
            if tenant.health <= 5:
                chance = resolve((5 - tenant.health) * .20)
                if self._rng(EVENT_IDS["shock.apply"], tenant.id).random() < chance:
                    tenant.shock = min(4, max(1, tenant.shock + 1))
                    tenant.shock_layers = min(99, max(2, tenant.shock_layers + 2))
            if tenant.shock:
                death_chance = tenant.shock * .25
                if self._rng(EVENT_IDS["shock.death"], tenant.id).random() < death_chance:
                    self._kill_tenant(tenant, "在休克中死亡")
                    continue
                if self._rng(EVENT_IDS["shock.layers"], tenant.id).random() < death_chance:
                    tenant.shock_layers = min(99, tenant.shock_layers + 1)

        for tenant in list(self.home_tenants()):
            if tenant.depression <= 100 or tenant.is_pseudo:
                continue
            chance = resolve(tenant.depression / 1000 - .05)
            if self._rng(EVENT_IDS["depression.leave"], tenant.id).random() < chance:
                tenant.leave_count += 1
                duration = math.floor((tenant.depression / 200) * tenant.leave_count)
                duration = max(2, min(5 * tenant.leave_count, duration))
                tenant.at_home = False
                tenant.temporarily_away = True
                tenant.return_turn = self.state.flow.turn + duration
                self._log(f"{self.character(tenant).name}被消沉压垮，离屋{duration}回合。")


        # 实例回合末收口（房客 scope）：健康结算完成后执行角色实例效果
        # （该伪人“重症监护”在此确定是否继续绑定并结算 10 理智消耗）。
        from weiren_game.data import CHARACTER_NODE_HOOKS

        for tenant in list(self.home_tenants()):
            hooks = CHARACTER_NODE_HOOKS.get(tenant.character_id, {})
            end_instance = hooks.get("end_turn_instance")
            if end_instance is not None:
                end_instance(self, tenant)
        # 通用回合末衰减放在最后：先让各状态自我演化（可能 +1），再统一 -1。
        self._decay_conditions()

    def _settle_turn_end_status_effects(self) -> None:
        """回合末状态效果：让各 condition 在自己的回合末效果节点兑现。"""
        self._run_status_effect_node("turn_end.status_effects")

    def _run_status_effect_node(
        self, node: str, tenant: Tenant | None = None
    ) -> None:
        """执行状态效果节点：传入房客时只处理该房客，缺省扫描全体屋内房客。

        回合初逐房客结算各自的状态效果，必须限定到该房客；回合末则是
        全屋一次性结算，因此调用时不再传房客。
        """
        from weiren_game.condition import STATUS_DEFINITIONS

        targets = [tenant] if tenant is not None else list(self.home_tenants())
        for current in targets:
            for status_id, condition in list(current.conditions.items()):
                if not condition.active:
                    continue
                definition = STATUS_DEFINITIONS.get(status_id)
                if definition is None or node not in definition.nodes:
                    continue
                hook = definition.hook
                if hook is not None:
                    hook(self, current)


def _difficulty_sanity_modifier(context: object):
    """难度：回合末理智消耗修正。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    bonus = DIFFICULTIES[engine.state.meta.difficulty]["end_sanity_bonus"]
    if bonus:
        yield spec("sanityConsume").path("回合末消耗").flat(float(bonus)).source("难度")


from weiren_game.modifier_rules import register_modifier_provider as _regds
_regds("sanityConsume", _difficulty_sanity_modifier)

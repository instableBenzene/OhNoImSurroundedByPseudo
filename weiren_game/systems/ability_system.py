"""主动能力调度与技能状态管理（能力门槛/成本交由 cost_system 与各角色模块）。"""

from __future__ import annotations

from weiren_game.probability import resolve


from typing import Any

from weiren_game.content import CONTENT
from weiren_game.data import (
    ABILITY_DISPATCH,
    CHARACTER_MODULES,
    EVENT_IDS,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from importlib import import_module
from weiren_game.tenant import TenantState as Tenant
from weiren_game.systems.cost_system import _DEFAULT_FORCED_COST_TERMS

from weiren_game.exceptions import RuleViolation


class AbilitySystemMixin:

    # -------------------------------------------------------------- active skills
    def _ability_state(self, tenant: Tenant, ability_id: str):
        """返回房客对应技能状态的运行时对象（缺失时返回 None）。"""
        return tenant.ability_state(ability_id)

    def _set_ability_cooldown(self, tenant: Tenant, ability_id: str, until: int) -> None:
        """把某主动技能的冷却写到其 AbilityState.cooldown_until。"""
        state = tenant.ability_state(ability_id)
        if state:
            state.cooldown_until = max(0, int(until))

    def _mark_ability_used(self, tenant: Tenant, ability_id: str) -> None:
        """记录本回合已使用：冷却至少延到下一回合（不覆盖更长冷却）。"""
        state = tenant.ability_state(ability_id)
        if state:
            state.cooldown_until = max(state.cooldown_until, self.state.flow.turn + 1)

    def _local_skill_module(self, character_id: str):
        """返回角色档案模块（用于读取技能本地提供者）。"""
        module = CHARACTER_MODULES.get(character_id)
        if module is not None:
            return module
        return import_module(f"weiren_game.data.characters.{character_id}")

    def _ability_has_local_cost(self, character_id: str, ability_id: str) -> bool:
        """技能是否通过本地 costs_<ability_id> 提供 cost。"""
        module = self._local_skill_module(character_id)
        return callable(getattr(module, f"costs_{ability_id}", None))

    def _gate_local_skill(
        self,
        actor: Tenant,
        ability: object,
        *,
        option: object,
        forced: bool,
        bypass: bool,
    ) -> None:
        """公共技能门槛：本地条件判定 → 公共消耗流程（强制时代替为默认代价）。"""
        module = self._local_skill_module(actor.character_id)
        requirements = getattr(module, f"requirements_{ability.id}", None)
        if requirements:
            error = requirements(self, actor, bypass=bypass)
            if error:
                raise RuleViolation(error)
        costs_fn = getattr(module, f"costs_{ability.id}", None)
        if costs_fn is None:
            return
        if forced:
            costs = list(_DEFAULT_FORCED_COST_TERMS)
        else:
            costs = list(costs_fn(self, actor, option=option))
        error = self._ability_costs_payable(actor, costs)
        if error:
            raise RuleViolation(error)
        self._pay_ability_costs(actor, costs)

    def available_abilities(self, tenant_id: int) -> list[tuple[str, str, str]]:
        """返回指定房客可用主动能力的（能力id、名称、描述）列表。"""
        tenant = self.state.house.tenants.get(tenant_id)
        if not tenant:
            return []
        return [(ability.id, ability.name, ability.description) for ability in self.character(tenant).actives]

    def _ability_failed(self, actor: Tenant, ability_id: str) -> bool:
        """按房客状态累计失败概率并判定本次主动能力是否失效，同时结算该角色替身的暴露。"""
        chance = 0.0
        if actor.depression > 1000:
            return True
        if actor.depression > 500:
            chance += .50
        if self._condition_extra_effect_active(actor, "trauma") and 3 <= actor.trauma.intensity <= 5:
            chance += {3: .25, 4: .30, 5: .35}[actor.trauma.intensity]
        if self._condition_extra_effect_active(actor, "disorder") and 6 <= actor.disorder.intensity <= 8:
            chance += {6: .25, 7: .30, 8: .35}[actor.disorder.intensity]
        if self._condition_extra_effect_active(actor, "trauma") and actor.trauma.intensity == 9:
            chance += .10
        if self._condition_extra_effect_active(actor, "disorder") and actor.disorder.intensity == 10:
            chance += .10
        from weiren_game.data import SCENARIO_HANDLERS

        fail_modifier = SCENARIO_HANDLERS.get(
            self.state.pseudo_state.scenario_id, {}
        ).get("ability_fail_modifier")
        if fail_modifier is not None:
            chance = fail_modifier(self, actor, chance)
        fail_chance = resolve(
            chance,
            ([1.0] if chance >= 1.0 else []) + ([0.0] if chance <= 0 else []),
        )
        failed = self._rng(
            EVENT_IDS["ability.fail"], actor.id, ability_id
        ).random() < fail_chance
        fail_resolved = SCENARIO_HANDLERS.get(
            self.state.pseudo_state.scenario_id, {}
        ).get("ability_fail_resolved")
        if fail_resolved is not None:
            fail_resolved(self, actor, ability_id, failed)
        return failed

    def use_ability(
        self,
        actor_id: str,
        target_id: str | None = None,
        ability_id: str | None = None,
        option: str | None = None,
        amount: int | None = None,
        copied_ability_id: str | None = None,
        secondary_target_id: str | None = None,
        secondary_option: str | None = None,
        secondary_amount: int | None = None,
        force_max_amount: bool = False,
        forced: bool = False,
        _bypass_limits: bool = False,
    ) -> Any:
        """校验阶段与冷却限制后执行主动能力，按角色分发到具体效果并记录行动日志。"""
        if not _bypass_limits:
            self._require_no_pending_choice()
        if self.state.flow.phase != "action":
            raise RuleViolation("只能在玩家行动阶段使用能力。")
        actor = self._require_home_tenant(actor_id, must_act=True)
        definition = self.character(actor)
        if actor.shock or actor.abilities_disabled:
            raise RuleViolation("该房客的主动能力已失效。")
        if not definition.actives:
            raise RuleViolation(f"{definition.name}没有主动能力。")
        ability = next((value for value in definition.actives if value.id == ability_id), None)
        if ability is None:
            ability = definition.actives[0]
        if getattr(ability, "opens_panel", False):
            # 只负责打开专属面板的技能：不掷失败、不付代价、不记冷却，也不该走结算。
            raise RuleViolation(f"“{ability.name}”在界面里打开，不走技能结算。")
        state = actor.ability_state(ability.id)
        cooldown = state.cooldown_until if state else 0
        if not _bypass_limits and self.state.flow.turn < cooldown:
            raise RuleViolation(f"能力冷却中，要到第{cooldown}回合才能使用。")
        if self._ability_failed(actor, ability.id):
            if getattr(ability, "per_turn", False):
                self._mark_ability_used(actor, ability.id)
            self._log(f"{definition.name}尝试使用“{ability.name}”，但能力失效。")
            self._mark_ability_failed("能力失效")
            self._run_ability_outcome(actor, ability.id)
            return None
        self._gate_local_skill(
            actor,
            ability,
            option=option,
            forced=forced,
            bypass=_bypass_limits,
        )
        # 技能默认成功；只有技能内部显式标记失败才算失败。
        self._ability_release_failed = False
        result: Any = None
        handler = ABILITY_DISPATCH.get(actor.character_id, {}).get(ability.id)
        if handler is None:
            raise RuleViolation("该房客没有可主动结算的原稿能力。")
        result = handler(
            self,
            actor,
            ability_id=ability.id,
            target_id=target_id,
            option=option,
            amount=amount,
            copied_ability_id=copied_ability_id,
            secondary_target_id=secondary_target_id,
            secondary_option=secondary_option,
            secondary_amount=secondary_amount,
            force_max_amount=force_max_amount,
            forced=forced,
            bypass=_bypass_limits,
        )

        if not _bypass_limits and getattr(ability, "per_turn", False):
            self._mark_ability_used(actor, ability.id)
        self._record_action(
            "ability", actor=actor.id, ability=ability.id, target=target_id,
            option=option, amount=amount, copied_ability=copied_ability_id,
            secondary_target=secondary_target_id, secondary_option=secondary_option,
            secondary_amount=secondary_amount,
        )
        self._log(f"{definition.name}使用了“{ability.name}”。")
        self._run_ability_outcome(actor, ability.id)
        self._flush_skill_outcomes()
        return result

    def _mark_ability_failed(self, reason: str = "") -> None:
        """技能私有失败标记：由可能失败的技能在失败分支调用。"""
        self._ability_release_failed = True
        if reason:
            self._record_log(f"技能释放失败：{reason}")

    def _run_ability_outcome(self, actor: Tenant, ability_id: str) -> None:
        """按“是否失败”派发 ability.used / ability.failed 节点。"""
        from weiren_game.data import ABILITY_FAILED_HOOKS, ABILITY_USED_HOOKS

        failed = getattr(self, "_ability_release_failed", False)
        hooks = ABILITY_FAILED_HOOKS if failed else ABILITY_USED_HOOKS
        for hook in hooks:
            hook(self, actor, ability_id)
        self._ability_release_failed = False

    def _skill_outcome(self, actor: object, skill_id: str, success: bool) -> None:
        """记录概率类技能本次的成功/失败（聚合，先不派发，避免多次判定）。"""
        if skill_id not in self._skill_outcome_records:
            self._skill_outcome_records[skill_id] = bool(success)
        else:
            self._skill_outcome_records[skill_id] = (
                self._skill_outcome_records[skill_id] or bool(success)
            )

    def _flush_skill_outcomes(self) -> None:
        """结算边界：每个技能按“是否至少成功一次”派发 used/failed。"""
        if not self._skill_outcome_records:
            return
        from weiren_game.data import ABILITY_FAILED_HOOKS, ABILITY_USED_HOOKS

        for skill_id, success in self._skill_outcome_records.items():
            hooks = ABILITY_USED_HOOKS if success else ABILITY_FAILED_HOOKS
            for hook in hooks:
                hook(self, None, skill_id)
        self._skill_outcome_records.clear()

    def _expel_tenant(
        self, tenant: Tenant, source: str, *, sanity_exempt_ids: set[str] | None = None
    ) -> None:
        """驱逐指定房客：视同屋内死亡（仅播报不同），并结算同伴的理智损失。"""
        if not tenant.alive:
            return
        if tenant.is_pseudo:
            handler = self._pseudo_handler("expel_infiltrator")
            if handler is not None:
                handler(self, source)
            return
        self._remove_tenant_from_house(tenant)
        # 重后果（红色）：驱逐不可撤销，而且会牵动羁绊与其余房客。
        self._log(f"{source}驱逐了{self.character(tenant).name}。", kind="danger")
        exempt = sanity_exempt_ids or set()
        for other in self.home_tenants():
            if other.id not in exempt:
                self._consume_sanity(other, 5, "同伴被驱逐")


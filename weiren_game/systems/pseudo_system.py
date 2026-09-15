"""伪人到访/主动技能/突破与搜索袭击的调度（效果实现位于各伪人场景模块）。"""

from __future__ import annotations

from collections import Counter

from weiren_game.content import CONTENT
from weiren_game.data import (
    DIFFICULTIES,
    EVENT_IDS,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.models import SearchMission
from weiren_game.tenant import TenantState as Tenant

from weiren_game.exceptions import RuleViolation

class PseudoSystemMixin:
    # 屋主直接驱逐（指认）所需证据：1 条已证实，或这么多条待验证。
    ACCUSE_PENDING_NEED = 3

    def _roll_next_pseudo_visit(self, after_turn: int) -> int:
        """伪人到访日历：每次未到访按难度递增概率，到访后回到起始概率。

        a0 基准：起始 15%，每次错过 +15%（15→30→45→60…，命中即回 15%）。
        a3/a-3 改变起始值与增量（20%/10%）。
        """
        setting = DIFFICULTIES.get(
            self.state.meta.difficulty,
            {"pseudo_start_chance": .15, "pseudo_step": .15},
        )
        start = float(setting.get("pseudo_start_chance", .15))
        step = float(setting.get("pseudo_step", .15))
        from weiren_game.probability import resolve

        for offset in range(1, 200):
            chance = resolve(start + step * (offset - 1))
            if self._rng(EVENT_IDS["pseudo.calendar"], offset).random() < chance:
                return after_turn + offset
        return after_turn + 200

    def _pseudo_actions_suppressed(self) -> bool:
        """当前伪人“主动行为（cast）”是否被禁用（描述层称“压制”）。

        这是对行为位 ``cast`` 的禁用判定，不代表一个叫“压制”的通用状态。
        """
        return not self._pseudo_capability("cast")

    def pseudo_in_house(self) -> bool:
        """屋内是否**真的有**伪人（替身已回屋）。

        ``infiltrator_id`` 在**绑架发生**时就写入（此时人还在外），因此不能只判它非空：
        必须确认该房客在屋、存活、且已被标记为伪人。凡是"驱逐/指认/处理**屋内**伪人"
        的判定都应走这里。
        """
        tenant_id = self.state.pseudo_state.infiltrator_id
        if not tenant_id:
            return False
        tenant = self.state.house.tenants.get(tenant_id)
        return bool(
            tenant is not None
            and tenant.alive
            and tenant.at_home
            and tenant.is_pseudo
        )
    def _skill_respond_skill(
        self,
        skill: str,
        stage: str,
        *,
        mode: str,
        caster: object,
        target: Tenant | None = None,
        mission: SearchMission | None = None,
        event: str | None = None,
        penalty: float | None = None,
    ) -> bool:
        """技能响应技能：返回 True 表示该响应阻止了本次技能。

        参数即“谁对谁”：mode 是 A→B 组合（AbilityLaunch.HUMAN_HUMAN /
        HUMAN_PSEUDO / PSEUDO_HUMAN / PSEUDO_PSEUDO），caster 是施法者，
        target 是被施法者（lock/resist 阶段）。

        规则按 (mode, stage) 判断适用面：
        - cast：施法方守卫（压制/抵挡）绑定施法者=伪人，故 mode 为
          PSEUDO_HUMAN 或 PSEUDO_PSEUDO 时都命中，与被施法者是谁无关；
        - lock：目标侧锁定仅存在于“伪人→人类”；
        - resist：搜索携带物抵御仅存在于“伪人→人类”；
        - after：预留。
        """
        from weiren_game.lifecycle import AbilityLaunch

        if stage == "cast":
            if mode in {
                AbilityLaunch.PSEUDO_HUMAN,
                AbilityLaunch.PSEUDO_PSEUDO,
            }:
                if self._pseudo_actions_suppressed():
                    self._log(
                        f"{self.state.pseudo_state.name}当前受到压制，{skill}未能发动。"
                    )
                    return True
            return False
        if stage == "lock":
            if mode != AbilityLaunch.PSEUDO_HUMAN or target is None:
                return False
            return self._target_lock_responder(target, event or "", penalty or 0.0)
        if stage == "resist":
            if (
                mode != AbilityLaunch.PSEUDO_HUMAN
                or target is None
                or mission is None
            ):
                return False
            event = event or f"resist.{self.state.pseudo_state.scenario_id}.{target.id}"
            if penalty is None:
                penalty = self._scenario_resist_penalty()
            return self._search_resist_responder(mission, target, event, penalty)
        return False

    def _target_lock_responder(
        self, tenant: Tenant, event: str, penalty: float
    ) -> bool:
        """目标锁定响应：该角色/该角色等让技能无法选中该目标。"""
        from weiren_game.data import CHARACTER_NODE_HOOKS

        resister = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get("target_lock")
        return bool(
            resister is not None
            and resister(self, tenant, event, success_penalty=penalty)
        )

    def _search_resist_responder(
        self, mission: SearchMission, tenant: Tenant, event: str, penalty: float
    ) -> bool:
        """搜索抵御响应：携带防具与该角色“走你！”。"""
        resisted = False
        from weiren_game.data import ITEM_HOOKS

        # 携带工具的抵御规则按 ITEM_HOOKS["<item_id>"]["search_resist"] 扫描。
        tool_occurrences: Counter[str] = Counter()
        for held in tenant.inventory.items:
            node_hooks = ITEM_HOOKS.get(held.item_id, {}).get("search_resist", {})
            if not node_hooks:
                continue
            occurrence = tool_occurrences[held.item_id]
            tool_occurrences[held.item_id] += 1
            for hook in node_hooks.values():
                if hook(self, mission, tenant, event, penalty, occurrence):
                    resisted = True
                    break
            if resisted:
                break
        from weiren_game.data import CHARACTER_NODE_HOOKS

        resister = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get(
            "pseudo_search_resist"
        )
        if resister is not None and not resisted:
            resisted = resister(self, mission, tenant, event, penalty=penalty)
        if resisted:
            self._log(
                f"{self.character(tenant).name}抵御了{self.state.pseudo_state.name}的搜索技能。"
            )
        return resisted
# PseudoActiveAbility.execute()
# │
# ├─ ① selectTargets()
# │
# ├─ ② validateTarget()
# │      │
# │      └─ avoidance / 规避
# │
# ├─ ③ applyEffect()
# │      │
# │      └─ resistance / 抵御
# │
# ├─ ④ resolveEffect()
# │
# └─ ⑤ triggerAffectedTenantAbilities()

    # --------------------------------------------------------------- pseudo visits
    def _resolve_pseudo_visit(self) -> None:
        """结算伪人到访：压制期无效果，首次到访揭示伪人，之后按伪人种类触发拜访逻辑。"""
        pseudo = self.state.pseudo_state
        if not self._pseudo_capability("visit"):
            self._log(f"{pseudo.name}受到压制，来访没有产生效果。")
            return
        pseudo.visit_count += 1
        from weiren_game.data import CHARACTER_NODE_HOOKS

        for tenant in self.home_tenants():
            visit_hook = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get(
                "pseudo_visit"
            )
            if visit_hook is not None:
                visit_hook(self, tenant)
        if not pseudo.revealed:
            pseudo.revealed = True
            from weiren_game.data import SCENARIO_HANDLERS

            reveal_handler = SCENARIO_HANDLERS.get(pseudo.scenario_id, {}).get(
                "on_first_reveal"
            )
            if reveal_handler is not None:
                reveal_handler(self)
            self._log(f"伪人初访：你确认了{pseudo.name}。初访不会触发突破。")
            self._create_visit_information(True, "伪人初访")
            return
        from weiren_game.data import SCENARIO_HANDLERS

        visit_handler = SCENARIO_HANDLERS.get(pseudo.scenario_id, {}).get("visit")
        if visit_handler is not None:
            visit_handler(self)

    def _attempt_breakthrough(self, reason: str) -> bool:
        """尝试结算一次伪人突破：先处理回溯与房客守卫等防御，未被阻止则宣布失败。"""
        if not self._pseudo_capability("breakthrough"):
            return False
        if self._global_event_active("guard.rewind"):
            self.rewind_one_turn()
            # The snapshot was captured while the guard was still armed, so it
            # must be consumed again after restoration.  Also postpone the
            # scheduled visit that caused this breakthrough.
            self._consume_global_event("guard.rewind")
            if self._pseudo_enters_house():
                self.state.world.visitors.next_pseudo_turn = max(
                    self.state.world.visitors.next_pseudo_turn,
                    self._roll_next_pseudo_visit(self.state.flow.turn),
                )
            self._log("回溯触发：本次突破被取消，已回到回溯前局面。")
            return False
        from weiren_game.data import NODE_HOOKS

        if any(hook(self) for hook in NODE_HOOKS.get("breakthrough.guard", ())):
            return False
        self._finish(False, reason)
        return True

    def _pseudo_attack_searchers(self) -> None:
        """按遭遇概率逐一对在外搜索的房客发起伪人袭击，并按伪人类型结算袭击效果。"""
        pseudo = self.state.pseudo_state
        if pseudo.liberated or self._pseudo_actions_suppressed():
            return
        for attempt in range(1):
            for mission in list(self.state.world.missions):
                if pseudo.scenario_id in mission.attacked_pseudos:
                    continue
                tenant = self.state.house.tenants.get(mission.tenant_id)
                if not tenant or not tenant.alive:
                    continue
                chance = self._pseudo_encounter_chance(mission, tenant)
                suffix = ""
                if self._rng(EVENT_IDS["pseudo.encounter"], pseudo.scenario_id, tenant.id, suffix).random() >= chance:
                    continue
                if pseudo.scenario_id not in mission.attacked_pseudos:
                    mission.attacked_pseudos.append(pseudo.scenario_id)
                event = f"resist.{pseudo.scenario_id}.{tenant.id}"
                penalty = self._scenario_resist_penalty()
                from weiren_game.lifecycle import AbilityLaunch

                if self._skill_respond_skill(
                    "搜索袭击", "cast",
                    mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
                ):
                    continue
                if self._skill_respond_skill(
                    "搜索袭击", "lock",
                    mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
                    target=tenant, event=event, penalty=penalty,
                ):
                    continue
                if self._skill_respond_skill(
                    "搜索袭击", "resist",
                    mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
                    target=tenant, mission=mission, event=event, penalty=penalty,
                ):
                    continue
                from weiren_game.data import SCENARIO_HANDLERS

                attack_handler = SCENARIO_HANDLERS.get(pseudo.scenario_id, {}).get(
                    "attack_searcher"
                )
                if attack_handler is not None:
                    attack_handler(self, mission, tenant)

    def _scenario_resist_penalty(self) -> float:
        """返回当前伪人场景注册的搜索抵御惩罚（缺省 0）。"""
        from weiren_game.data import SCENARIO_HANDLERS

        handler = SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {}).get(
            "search_resist_penalty"
        )
        return float(handler(self)) if handler is not None else 0.0

    def _pseudo_encounter_chance(self, mission: SearchMission, tenant: Tenant) -> float:
        """计算伪人对指定搜索房客的遭遇概率（综合状态、携带物与被动修正）。"""
        pseudo = self.state.pseudo_state
        from weiren_game.data import SCENARIO_HANDLERS

        chance_handler = SCENARIO_HANDLERS.get(pseudo.scenario_id, {}).get("encounter_chance")
        chance = (
            float(chance_handler(self, mission, tenant))
            if chance_handler is not None
            else .50
        )
        from weiren_game.probability import resolve, single_guarantee

        guarantees: list[float] = []
        guarantee = single_guarantee(chance)
        if guarantee is not None:
            guarantees.append(guarantee)
        resolved = resolve(chance, guarantees)
        if resolved in (0.0, 1.0):
            return resolved
        source = ("伪人技能", "遭遇", pseudo.scenario_id, tenant.character_id)
        context = {"mission": mission, "tenant": tenant}
        chance = self._apply_modifiers("chance", chance, source, context)
        chance *= self._global_event_value("encounter.rate.multiplier", 1.0)
        return resolve(chance, guarantees)

    def _break_search_tool(self, mission: SearchMission, tenant: Tenant, item_id: str) -> None:
        """将损坏的防具工具从任务携带中移除并重算搜索参数。"""
        self._take_tenant_item(tenant, item_id)
        self._recalculate_search(mission)
        self._log(f"{ITEMS[item_id].name}在抵御伪人时损坏。")

    def _set_pseudo_marks(self, target: float) -> bool:
        """外界把伪人印记直接改写为 target；受“不可被外界修改”声明保护。"""
        from weiren_game.data import PSEUDOS

        definition = PSEUDOS.get(self.state.pseudo_state.scenario_id)
        if definition is None or not getattr(definition, "mark_field", ""):
            self._log("当前的伪人没有可被改写的印记。")
            return False
        if getattr(definition, "mark_externally_locked", False):
            label = getattr(definition, "mark_label", "") or "印记"
            self._log(f"{label}无法被外界修改。")
            return False
        setattr(self.state.pseudo_state.scenario(), definition.mark_field, target)
        return True

    def _pseudo_handler(self, name: str):
        """返回当前伪人场景注册的处理器（无则 None）。"""
        from weiren_game.data import SCENARIO_HANDLERS

        return SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {}).get(name)

    # ------------------------------------------------------------- infiltration
    def accusation_evidence(self, tenant_id: int) -> dict:
        """纯查询：该房客名下有效的指认信息进度（供 UI 判断屋主能否直接驱逐）。

        不掷骰、不写状态；``ready`` 为真即 ``accuse`` 会通过证据校验。
        """
        infos = [
            info for info in self.state.house.information
            if info.kind == "pseudo_inhome" and info.status in {"pending", "confirmed"}
            and tenant_id in info.target_ids
        ]
        confirmed = sum(1 for info in infos if info.status == "confirmed")
        pending = sum(1 for info in infos if info.status == "pending")
        return {
            "infos": infos,
            "confirmed": confirmed,
            "pending": pending,
            "ready": bool(confirmed) or pending >= self.ACCUSE_PENDING_NEED,
        }

    def accuse(self, tenant_id: int) -> None:
        """屋主指认某房客为伪人：满足证据条件时按目标真伪驱逐替身或误逐房客。"""
        target = self._require_home_tenant(tenant_id)
        evidence = self.accusation_evidence(tenant_id)
        if not evidence["ready"]:
            raise RuleViolation("需要1条已证实或3条待验证的同目标指认信息。")
        for info in evidence["infos"]:
            info.status = "expired"
        if target.is_pseudo:
            handler = self._pseudo_handler("expel_infiltrator")
            if handler is not None:
                handler(self, "屋主指认")
        else:
            self._expel_tenant(target, "错误指认")
        self._record_action("accuse", tenant=tenant_id)


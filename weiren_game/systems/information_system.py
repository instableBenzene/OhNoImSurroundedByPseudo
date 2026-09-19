"""信息实例的生成、核验、识别与回合结算。"""

from __future__ import annotations


from typing import Any

from weiren_game.content import CONTENT
from weiren_game.data import (
    AWAKENING_EMOTIONS,
    EROSION_EMOTIONS,
    EVENT_IDS,
    INFORMATION_TEMPLATES,
    LOCATION_INFORMATION_MODIFIERS,
)
from weiren_game.data.lang import TEXT
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.models import Information
from weiren_game.tenant import TenantState as Tenant

from weiren_game.exceptions import RuleViolation

class InformationSystemMixin:

    # --------------------------------------------------------------- information
    def _create_random_information(
        self,
        verified: bool,
        source: str,
        allowed_kinds: set[str] | None = None,
    ) -> Information:
        """随机生成一条信息：按允许种类选择模板或特殊事件并决定真伪，按需立即核实。"""
        allowed = allowed_kinds or {
            "material_reward", "location_modifier", "state", "visit",
            "pseudo_skill", "pseudo_inhome", "emotion_reveal",
        }
        template_pool = [value for value in INFORMATION_TEMPLATES.values() if value.kind in allowed]
        special: list[str] = []
        if "visit" in allowed:
            special.append("pseudo_visit")
            if self.state.world.visitors.visitor_pool:
                special.append("human_visit")
            if any(value.temporarily_away for value in self.living_tenants()):
                special.append("returning_visit")
            if self.state.world.missions:
                special.append("search_return")
        if "pseudo_skill" in allowed:
            special.append("pseudo_skill")
        if "pseudo_inhome" in allowed and self.pseudo_in_house():
            special.append("pseudo_inhome")
        if "emotion_reveal" in allowed and self.home_tenants():
            special.append("emotion_reveal")
        candidates: list[tuple[str, Any]] = [("template", value) for value in template_pool] + [("special", value) for value in special]
        if not candidates:
            candidates = [("special", "pseudo_visit")]
        choice_type, choice = self._rng(EVENT_IDS["information.type"]).choice(candidates)
        truth_chance = .45 if self.state.world.global_events.active("information.false_lock") else .70
        truth = verified or self._rng(EVENT_IDS["information.truth"]).random() < truth_chance
        info_id = self.state.ids.allocate_information()
        status = "confirmed" if verified else "pending"

        if choice_type == "template":
            template = choice
            location_id = template.location_id
            if template.kind == "material_reward" and not location_id:
                location_id = self._rng(EVENT_IDS["information.location"]).choice(self.state.world.locations.available_locations)
            targets: list[str] = []
            text = template.description
            if "[地点]" in text:
                # ""location_id"" stores the location actually claimed by the
                # information.  Searching that place verifies or refutes it.
                text = text.replace("[地点]", LOCATIONS[location_id].name)
            if template.kind == "state":
                home = self.home_tenants()
                count = 2 if len(home) >= 2 else len(home)
                selected = self._rng(EVENT_IDS["information.state.targets"]).sample(home, count) if count else []
                targets = [tenant.id for tenant in selected]
                if selected:
                    text = text.replace("A", self.character(selected[0]).name)
                if len(selected) > 1:
                    text = text.replace("B", self.character(selected[1]).name)
            info = Information(
                info_instance_id=info_id, title=template.name, text=text, status=status,
                gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + template.duration,
                truth=truth, kind=template.kind, source=source, template_id=template.id,
                location_id=location_id, target_ids=targets,
                data={"reward_ids": list(template.reward_ids)},
            )
        elif choice == "pseudo_visit":
            predicted = self.state.world.visitors.next_pseudo_turn
            shown = predicted if truth else max(self.state.flow.turn + 1, predicted + self._rng(EVENT_IDS["information.visit.offset"]).choice((-1, 1, 2)))
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.1"],
                text=TEXT["systems.information_system._create_random_information.2"].format(p1=source, p2=self.state.pseudo_state.name, p3=shown),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=truth, kind="visit", subtype="pseudo_visit", source=source,
                data={"predicted_turn": shown, "actual_turn": predicted},
            )
        elif choice == "human_visit":
            actual = self.state.world.visitors.visitor_pool[0]
            claim = actual
            if not truth:
                alternatives = [key for key in self.state.world.visitors.visitor_pool[1:] if key != actual]
                claim = self._rng(EVENT_IDS["information.human.false"]).choice(alternatives) if alternatives else ""
            claim_name = CHARACTERS[claim].name if claim else TEXT["systems.information_system._create_random_information.3"]
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.4"],
                text=TEXT["systems.information_system._create_random_information.5"].format(p1=source, p2=claim_name),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=truth, kind="visit", subtype="human_visit", source=source,
                data={"claimed_character": claim, "actual_character": actual},
            )
        elif choice == "returning_visit":
            away = [value for value in self.living_tenants() if value.temporarily_away]
            target = self._rng(EVENT_IDS["information.returning.target"]).choice(away)
            actual_turn = target.return_turn
            shown_turn = actual_turn if truth else max(self.state.flow.turn + 1, actual_turn + self._rng(EVENT_IDS["information.returning.offset"]).choice((-1, 1, 2)))
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.6"],
                text=TEXT["systems.information_system._create_random_information.7"].format(p1=source, p2=self.character(target).name, p3=shown_turn),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=truth, kind="visit", subtype="returning_visit", source=source,
                target_ids=[target.id],
                data={"predicted_turn": shown_turn, "actual_turn": actual_turn},
            )
        elif choice == "search_return":
            mission = self._rng(EVENT_IDS["information.search_return.target"]).choice(self.state.world.missions)
            actual_turn = self.state.flow.turn + mission.remain_search_turns
            shown_turn = actual_turn if truth else max(self.state.flow.turn + 1, actual_turn + self._rng(EVENT_IDS["information.search_return.offset"]).choice((-1, 1, 2)))
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.8"],
                text=TEXT["systems.information_system._create_random_information.9"].format(p1=source, p2=self.tenant_name(mission.tenant_id), p3=shown_turn, p4=LOCATIONS[mission.location_id].name),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=truth, kind="visit", subtype="search_return", source=source,
                target_ids=[mission.tenant_id], location_id=mission.location_id,
                data={"predicted_turn": shown_turn, "actual_turn": actual_turn},
            )
        elif choice == "pseudo_skill":
            prediction = "trigger" if truth else "suppress"
            from weiren_game.data import SCENARIO_HANDLERS

            skills_handler = SCENARIO_HANDLERS.get(
                self.state.pseudo_state.scenario_id, {}
            ).get("observed_skills")
            # 内容层给出 (id, 展示名) 对：id 用于核验匹配，展示名用于文本，
            # 系统层不得把内部技能 id 直接展示给玩家。
            skill_pairs: list[tuple[str, str]] = []
            for entry in (skills_handler(self) if skills_handler is not None else ()):
                if isinstance(entry, (tuple, list)) and len(entry) >= 2:
                    skill_pairs.append((str(entry[0]), str(entry[1])))
                else:
                    skill_pairs.append((str(entry), str(entry)))
            if not skill_pairs:
                skill_pairs = [("", TEXT["systems.information_system._create_random_information.10"])]
            skill_id, skill_label = self._rng(
                EVENT_IDS["information.pseudo_skill.id"]
            ).choice(skill_pairs)
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.11"],
                text=TEXT["systems.information_system._create_random_information.12"].format(p1=source, p2=self.state.pseudo_state.name, p3='将' if prediction == 'trigger' else '不会', p4=skill_label),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=truth, kind="pseudo_skill", source=source,
                data={"pseudo_id": self.state.pseudo_state.scenario_id, "skill_id": skill_id, "prediction": prediction},
            )
        elif choice == "pseudo_inhome":
            candidates_tenant = self.home_tenants()
            target = None
            if truth and self.pseudo_in_house():
                target = self.state.house.tenants[self.state.pseudo_state.infiltrator_id]
            elif candidates_tenant:
                # A generated *false* accusation must not accidentally select
                # Fries' substitute and turn itself into a true statement.
                humans = [tenant for tenant in candidates_tenant if not tenant.is_pseudo]
                target = self._rng(EVENT_IDS["information.accusation.target"]).choice(humans or candidates_tenant)
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.13"],
                text=TEXT["systems.information_system._create_random_information.14"].format(p1=source, p2=self.character(target).name if target else '某位房客'),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=bool(target and target.is_pseudo), kind="pseudo_inhome", source=source,
                target_ids=[target.id] if target else [],
            )
        else:  # emotion_reveal
            target = self._rng(EVENT_IDS["information.emotion.target"]).choice(self.home_tenants())
            emotion_key = self._rng(EVENT_IDS["information.emotion.type"]).choice(
                list(EROSION_EMOTIONS) + list(AWAKENING_EMOTIONS)
            )
            label = {**EROSION_EMOTIONS, **AWAKENING_EMOTIONS}[emotion_key]
            duration = self._rng(EVENT_IDS["information.emotion.duration"]).randint(2, 4)
            info = Information(
                info_instance_id=info_id, title=TEXT["systems.information_system._create_random_information.15"],
                text=TEXT["systems.information_system._create_random_information.16"].format(p1=source, p2=self.character(target).name, p3=label),
                status=status, gained_turn=self.state.flow.turn, expires_turn=self.state.flow.turn + 5,
                truth=truth, kind="emotion_reveal", subtype=emotion_key, source=source,
                target_ids=[target.id], data={"reveal_duration": duration},
            )

        self.state.house.information.append(info)
        if info.status == "pending":
            from weiren_game.data import INFORMATION_CREATED_HOOKS

            for hook in INFORMATION_CREATED_HOOKS:
                hook(self, info)
        if verified:
            self._resolve_information_effect(info)
        return info

    def _observe_visit_information(
        self,
        subtype: str,
        *,
        character_id: str = "",
        tenant_id: int = 0,
        location_id: str = "",
        returned: bool = True,
    ) -> None:
        """对应访客事件实际发生时，核实匹配的待验证来访预告并结算结果。"""
        for info in self.state.house.information:
            if info.status != "pending" or info.kind != "visit" or info.subtype != subtype:
                continue
            if subtype == "human_visit":
                info.truth = info.data.get("claimed_character") == character_id
            elif subtype == "pseudo_visit":
                info.truth = int(info.data.get("predicted_turn", -1)) == self.state.flow.turn
            elif subtype == "returning_visit":
                if tenant_id not in info.target_ids:
                    continue
                info.truth = int(info.data.get("predicted_turn", -1)) == self.state.flow.turn
            elif subtype == "search_return":
                if tenant_id not in info.target_ids:
                    continue
                info.truth = (
                    returned and info.location_id == location_id
                    and int(info.data.get("predicted_turn", -1)) == self.state.flow.turn
                )
            self._verify_information_object(info)

    def _observe_pseudo_skill(self, skill_id: str) -> None:
        """伪人技能实际触发时，核实其预告信息的真伪并结算。

        技能可能在初访**之前**就产生玩家看得到的结果（如搜索袭击），
        因此这里顺手把伪人对外标为「已确认」：卡片随即显示身份与印记，
        不再停在「尚未确认」。机制门控仍以 `revealed`（初访）为准。
        """
        pseudo = self.state.pseudo_state
        if not pseudo.revealed and not pseudo.known:
            pseudo.known = True
            self._log(TEXT["systems.information_system._observe_pseudo_skill.1"].format(p1=pseudo.name))
        for info in self.state.house.information:
            if (
                info.status == "pending" and info.kind == "pseudo_skill"
                and info.data.get("pseudo_id") == pseudo.scenario_id
                and info.data.get("skill_id") == skill_id
            ):
                info.truth = info.data.get("prediction") == "trigger"
                self._verify_information_object(info)

    def _verify_location_information(self, location_id: str) -> None:
        """从声明地点搜索归来后，核实该地点的物资与修正信息并结算。"""
        for info in self.state.house.information:
            if (
                info.status == "pending"
                and info.kind in {"material_reward", "location_modifier"}
                and info.location_id == location_id
            ):
                self._verify_information_object(info)

    def _discern_one_information(self, tenant: Tenant, *, false_only: bool = False) -> bool:
        """由指定房客的被动效果识破一条待验证信息（可仅限虚假信息）。"""
        candidates = [
            info for info in self.state.house.information
            if info.status == "pending" and (not false_only or not info.truth)
        ]
        if not candidates:
            return False
        self._verify_information_object(candidates[0])
        self._log(TEXT["systems.information_system._discern_one_information.1"].format(p1=self.character(tenant).name))
        return True

    def _verify_information_object(self, info: Information) -> None:
        """将单条信息置为证实或证伪状态，记录验证信息并结算其效果。"""
        if self.state.world.global_events.active("information.false_lock"):
            self._log(TEXT["systems.information_system._verify_information_object.1"].format(p1=info.title))
            return
        info.status = "confirmed" if info.truth else "refuted"
        info.verified_turn = self.state.flow.turn
        info.expires_turn = self.state.flow.turn + 10
        self._resolve_information_effect(info)
        self._log(TEXT["systems.information_system._verify_information_object.2"].format(p1='证实' if info.truth else '证伪', p2=info.title))
        self._emit_node("information.verified", info=info)

    def _resolve_information_effect(self, info: Information) -> None:
        """按信息种类与最终状态结算具体效果，包括地点修正、情绪揭示与状态模板。"""
        if info.resolved:
            return
        if info.kind == "location_modifier" and info.status == "confirmed":
            modifier = LOCATION_INFORMATION_MODIFIERS.get(info.template_id or "", {})
            if "turns" in modifier:
                info.data["active_until"] = self.state.flow.turn + int(modifier["turns"])
            return
        if info.kind == "emotion_reveal" and info.status == "confirmed":
            # 情绪显现是**世界级事件**（该情绪对所有房客可见），不再挂在某名房客身上。
            from weiren_game.global_event import emotion_reveal_event

            duration = int(info.data.get("reveal_duration", 2))
            self._set_global_event(emotion_reveal_event(info.subtype), 1.0, max(1, duration))
            info.resolved = True
            return
        if info.kind != "state":
            return
        targets = [self.state.house.tenants[key] for key in info.target_ids if key in self.state.house.tenants and self.state.house.tenants[key].alive]
        if not targets:
            return
        confirmed = info.status == "confirmed"
        refuted = info.status == "refuted"
        template = info.template_id
        from weiren_game.data import INFORMATION_STATE_EFFECTS

        effect_entry = INFORMATION_STATE_EFFECTS.get(template or "", {})
        resolve_fn = effect_entry.get("resolve")
        if resolve_fn is not None:
            resolve_fn(self, info, targets)
        info.resolved = confirmed or refuted

    def _apply_pending_information_effects(self) -> None:
        """回合末结算各条待验证状态信息的持续影响，并按固定概率自动核实。"""
        for info in self.state.house.information:
            if info.status != "pending" or info.kind != "state":
                continue
            targets = [self.state.house.tenants[key] for key in info.target_ids if key in self.state.house.tenants and self.state.house.tenants[key].alive]
            template = info.template_id
            from weiren_game.data import INFORMATION_STATE_EFFECTS

            pending_fn = INFORMATION_STATE_EFFECTS.get(template or "", {}).get(
                "pending"
            )
            if pending_fn is not None:
                pending_fn(self, info, targets)
            # State information can auto-resolve at end; probability was not
            # fixed in the source, so the implementation uses a stable 20%.
            if self._rng(EVENT_IDS["information.auto_verify"], info.info_instance_id).random() < .20:
                self._verify_information_object(info)

    def _expire_information(self) -> None:
        """将超过有效期或使用次数上限的信息标记为已失效。"""
        for info in self.state.house.information:
            active_until = info.data.get("active_until")
            if (
                info.status == "confirmed" and active_until is not None
                and self.state.flow.turn > int(active_until)
            ):
                info.status = "expired"
            if info.status != "expired" and self.state.flow.turn >= info.expires_turn:
                info.status = "expired"

    def _invalidate_target_information(self) -> None:
        """使指向已死亡、离屋或受震房客的状态类信息提前失效。"""
        for info in self.state.house.information:
            if (
                info.status == "expired" or not info.target_ids
                or info.kind not in {"state", "pseudo_inhome", "emotion_reveal"}
            ):
                continue
            for target_id in info.target_ids:
                target = self.state.house.tenants.get(target_id)
                if not target or not target.alive or not target.at_home or target.shock:
                    info.status = "expired"
                    break

    def information_text(self, info: Information) -> str:
        """返回带状态标签与来源的信息展示文本。"""
        label = {"pending": TEXT["systems.information_system.information_text.1"], "confirmed": TEXT["systems.information_system.information_text.2"], "refuted": TEXT["systems.information_system.information_text.3"], "expired": TEXT["systems.information_system.information_text.4"]}.get(info.status, info.status)
        return TEXT["systems.information_system.information_text.5"].format(p1=label, p2=info.text, p3=info.source)

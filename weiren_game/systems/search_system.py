"""搜索任务的发起、推进、返程结算与掉落抽取。"""

from __future__ import annotations


import math
from collections import Counter
from typing import Sequence

from weiren_game.content import CONTENT
from weiren_game.probability import resolve
from weiren_game.data import (
    DIFFICULTIES,
    EROSION_EMOTIONS,
    EVENT_IDS,
    LOCATION_INFORMATION_MODIFIERS,
    QUALITY_WEIGHTS,
    SEARCH_REWARD_HOOKS,
)
from weiren_game.data.lang import TEXT
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.models import SearchMission
from weiren_game.tenant import TenantState as Tenant

from weiren_game.exceptions import RuleViolation

class SearchSystemMixin:

    # -------------------------------------------------------------- loot/search
    @staticmethod
    def _quality_matches(selector: str, quality: int) -> bool:
        """判断品质选择器（如 low/high/blue/gold 等）是否匹配给定品质等级。"""
        return {
            "low": quality <= 2,
            "high": quality >= 3,
            "blue": quality == 2,
            "blue_plus": quality >= 2,
            "purple": quality == 3,
            "gold": quality == 4,
            "gold_plus": quality >= 4,
            "red": quality == 5,
        }.get(selector, False)

    def _random_item(
        self,
        *,
        required_tags: Sequence[str] = (),
        minimum_quality: int = 0,
        fortune: float = 0.0,
        event_id: str = "item.any",
        event_suffix: Sequence[object] = (),
    ) -> str:
        """按最低品质与标签约束加权随机返回一件可搜索物资的 id。"""
        candidates = [
            item for item in ITEMS.values()
            if item.searchable and item.quality >= minimum_quality
            and all(tag in item.tags for tag in required_tags)
        ]
        if not candidates and required_tags:
            candidates = [
                item for item in ITEMS.values()
                if item.searchable and item.quality >= minimum_quality
                and any(tag in item.tags for tag in required_tags)
            ]
        if not candidates:
            candidates = [item for item in ITEMS.values() if item.searchable]
        quality_counts = Counter(item.quality for item in candidates)
        weighted = [
            (item.item_id, (QUALITY_WEIGHTS[item.quality] / quality_counts[item.quality])
             * max(.01, 1 + fortune * .1 * (item.quality + 2)))
            for item in candidates
        ]
        return self._weighted_choice(weighted, event_id, event_suffix=event_suffix)

    def _active_location_modifiers(self, location_id: str) -> list[dict[str, float]]:
        """返回指定地点当前已证实且仍在生效的信息修正定义列表。"""
        result: list[dict[str, float]] = []
        for info in self.state.house.information:
            if (
                info.kind == "location_modifier" and info.status == "confirmed"
                and info.location_id == location_id and not info.resolved
                and int(info.data.get("active_until", self.state.flow.turn)) >= self.state.flow.turn
            ):
                definition = LOCATION_INFORMATION_MODIFIERS.get(info.template_id or "", {})
                result.append(definition)
        return result

    def _consume_location_modifier_uses(self, location_id: str) -> None:
        """消耗指定地点的信息修正使用次数，用尽时将该信息置为失效。"""
        for info in self.state.house.information:
            if info.kind != "location_modifier" or info.status != "confirmed" or info.location_id != location_id:
                continue
            definition = LOCATION_INFORMATION_MODIFIERS.get(info.template_id or "", {})
            if "uses" not in definition:
                continue
            used = int(info.data.get("uses", 0)) + 1
            info.data["uses"] = used
            if used >= int(definition["uses"]):
                info.status = "expired"

    def _loot_for_mission(self, mission: SearchMission, behavior_index: int) -> str:
        """按行为序号结算一次搜索掉落：经品质与标签加权后返回具体物资 id。"""
        location = LOCATIONS[mission.location_id]
        tenant = self.state.house.tenants[mission.tenant_id]
        rng_tags = self._mission_rng(mission, "loot.tags", behavior_index)
        required_tags = self._weighted_choice(location.tag_distribution, rng=rng_tags)

        quality_weights = list(QUALITY_WEIGHTS)
        for selector, multiplier in location.quality_modifiers:
            quality_weights = [
                weight * (multiplier if self._quality_matches(selector, quality) else 1.0)
                for quality, weight in enumerate(quality_weights)
            ]
        tag_multipliers = list(location.item_tag_modifiers)
        for modifier in mission.loot_modifiers:
            for key, multiplier in modifier.items():
                if key.startswith("quality:"):
                    selector = key.split(":", 1)[1]
                    quality_weights = [
                        weight * (float(multiplier) if self._quality_matches(selector, quality) else 1.0)
                        for quality, weight in enumerate(quality_weights)
                    ]
                elif key.startswith("tag:"):
                    tag_multipliers.append((key.split(":", 1)[1], float(multiplier)))

        from weiren_game.data import ITEM_HOOKS, NODE_HOOKS

        for hook in NODE_HOOKS.get("loot.quality_weights", ()):
            hook(self, mission, tenant, quality_weights)

        # 携带工具对掉落品质的修正按 ITEM_HOOKS["loot.quality"] 扫描（每个
        # 物品 ID 只生效一次）。
        seen_tools: set[str] = set()
        for held in tenant.inventory.items:
            if held.item_id in seen_tools:
                continue
            seen_tools.add(held.item_id)
            node_hooks = ITEM_HOOKS.get(held.item_id, {}).get("loot.quality", {})
            for hook in node_hooks.values():
                quality_weights = hook(self, tenant, mission, quality_weights)
        for quality in range(6):
            quality_weights[quality] *= max(.01, 1 + mission.fortune * .1 * (quality + 2))
        quality = self._weighted_choice(list(enumerate(quality_weights)), rng=self._mission_rng(mission, "loot.quality", behavior_index))

        candidates = [
            item for item in ITEMS.values()
            if item.searchable and item.quality == quality
            and all(tag in item.tags for tag in required_tags)
        ]
        if not candidates:
            candidates = [
                item for item in ITEMS.values()
                if item.searchable and item.quality == quality
                and (not required_tags or any(tag in item.tags for tag in required_tags))
            ]
        if not candidates:
            candidates = [item for item in ITEMS.values() if item.searchable and item.quality == quality]
        if not candidates:
            candidates = [item for item in ITEMS.values() if item.searchable]
        weights: list[tuple[str, float]] = []
        for item in candidates:
            weight = 1.0
            for tag, multiplier in tag_multipliers:
                if tag in item.tags:
                    weight *= multiplier
            from weiren_game.data import NODE_HOOKS

            for hook in NODE_HOOKS.get("search.pool_weight", ()):
                pool_weight = hook(self, item.item_id)
                if pool_weight is not None:
                    weight = pool_weight
            weights.append((item.item_id, weight))
        return self._weighted_choice(weights, rng=self._mission_rng(mission, "loot.item", behavior_index))

    def _search_carry(self, tenant: Tenant) -> int:
        """返回房客当前的搜索携带容量（优先取覆盖值，否则取角色定义值）。"""
        definition = self.character(tenant)
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("search.carry_override", ()):
            override = hook(self, tenant)
            if override is not None:
                return int(override)
        return definition.carry

    def tenant_carry_capacity(self, tenant: Tenant) -> int:
        """房客当前携带格数 = 角色基础容量 + 性格/物资的「携带」修饰。

        界面格数、装备/转移上限与搜索容量统一走这一入口，避免出现
        “背包显示 2 格、搜索却按 7 格结算”之类的错位。

        关键：把**基础容量**作为 base 交给 `search`·`携带` 修饰器管线演算，
        让 flat / percent / mul / limit / final 各阶段都作用在真实数值上；
        而不是先算出加算增量再补回（那样乘算与百分比会被 0 基值吃掉）。
        """
        base = self._search_carry(tenant)
        value = self._apply_modifiers(
            "search", float(base), ("search", "carry", tenant.character_id),
            {"tenant": tenant},
        )
        return max(1, int(value))

    def start_search(
        self,
        tenant_id: int,
        location_id: str,
    ) -> None:
        """校验条件后发起一次搜索：确定时长、成功率与随机序列，创建任务并派出房客。"""
        self._require_no_pending_choice()
        if self.state.flow.phase != "action":
            raise RuleViolation(TEXT["systems.search_system.start_search.1"])
        if self.state.round.searched_this_turn:
            raise RuleViolation(TEXT["systems.search_system.start_search.2"])
        tenant = self._require_home_tenant(tenant_id, must_act=True)
        from weiren_game.data import SCENARIO_HANDLERS

        dispatch_blocker = SCENARIO_HANDLERS.get(
            self.state.pseudo_state.scenario_id, {}
        ).get("blocks_search_dispatch")
        if dispatch_blocker is not None and dispatch_blocker(self, tenant):
            raise RuleViolation(TEXT["systems.search_system.start_search.3"])
        if tenant.shock or tenant.search_locked_until >= self.state.flow.turn:
            raise RuleViolation(TEXT["systems.search_system.start_search.4"])
        trauma_blocks = tenant.trauma.intensity == 6 and self._condition_extra_effect_active(tenant, "trauma")
        disorder_blocks = tenant.disorder.intensity == 6 and self._condition_extra_effect_active(tenant, "disorder")
        if trauma_blocks or disorder_blocks:
            raise RuleViolation(TEXT["systems.search_system.start_search.5"])
        if location_id not in LOCATIONS:
            raise RuleViolation(TEXT["systems.search_system.start_search.6"])
        if location_id not in self.state.world.locations.available_locations:
            raise RuleViolation(TEXT["systems.search_system.start_search.7"])
        location = LOCATIONS[location_id]
        all_loadout = self._tenant_item_ids(tenant)
        from weiren_game.data import ITEM_HOOKS

        carry = self.tenant_carry_capacity(tenant)
        rng = self._rng(EVENT_IDS["search.parameters"], tenant.id)
        lower = math.floor(carry * .75) + 1
        upper = max(lower, math.floor(carry * 1.5))
        initial_turns = rng.randint(lower, upper)
        turn_modifier = location.turn_delta
        success_rate = .50 + tenant.search_bonus
        fortune = (
            tenant.fortune_bonus
            + max(-5, min(5, -math.floor(tenant.depression / 200)))
        )
        if tenant.is_pseudo:
            penalty = self._pseudo_handler("infiltrator_search_penalty")
            if penalty is not None:
                fortune -= penalty(self, tenant)

        from weiren_game.data import NODE_HOOKS

        guaranteed: list[str] = []
        for hook in NODE_HOOKS.get("search.start.bond", ()):
            carry, success_rate = hook(self, tenant, carry, success_rate, guaranteed)
        # A 类纯数值修正 → search / chance 通道
        context = {"tenant": tenant, "rng": rng, "location": location}
        # 把「基础搜索回合」作为 base 交给修饰器管线，让 flat / percent / mul 都
        # 作用在真实数值上；再换算回初始回合之上的增量，兼容既有的 reset hook。
        search_base_turns = initial_turns + location.turn_delta
        turn_modifier = int(
            self._apply_modifiers(
                "search", float(search_base_turns),
                ("search", "turn", tenant.character_id), context,
            )
        ) - initial_turns
        success_rate = self._apply_modifiers(
            "chance", success_rate, ("search", TEXT["systems.search_system.start_search.11"], tenant.character_id), context
        )
        for hook in NODE_HOOKS.get("search.parameters.reset", ()):
            initial_turns, turn_modifier = hook(
                self, tenant, initial_turns, turn_modifier
            )

        occupied_groups = len(all_loadout)
        if occupied_groups > carry:
            raise RuleViolation(TEXT["systems.search_system.start_search.12"].format(p1=carry, p2=occupied_groups))

        fortune = int(
            self._apply_modifiers(
                "search", float(fortune),
                ("search", "luck", tenant.character_id), context,
            )
        )

        reward_handler = SEARCH_REWARD_HOOKS.get(tenant.character_id)
        if reward_handler is not None:
            reward_handler(self, tenant, guaranteed)
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("search.reward", ()):
            hook(self, tenant, guaranteed)
        for info in self.state.house.information:
            if info.kind == "material_reward" and info.status == "confirmed" and not info.resolved:
                if info.location_id == location_id:
                    candidates = list(info.data.get("reward_ids", []))
                    reward_slots = max(0, carry - occupied_groups)
                    if candidates and len(guaranteed) < reward_slots:
                        guaranteed.append(rng.choice(candidates))
                        info.resolved = True
                        info.status = "expired"

        mission_number = self.state.ids.allocate_search()
        difficulty = DIFFICULTIES[self.state.meta.difficulty]
        search_turns = max(1, initial_turns + turn_modifier)
        behavior_multiplier = self._seeded_rng(
            self.state.flow.turn, mission_number, "search.behavior_multiplier", 0
        ).uniform(.75, 1.50)
        behavior_count = max(
            1,
            math.floor(search_turns * behavior_multiplier)
            + location.behavior_delta
            + int(difficulty.get("search_behavior_delta", 0)),
        )
        mission = SearchMission(
            tenant_id=tenant.id,
            location_id=location_id,
            base_search_turns=initial_turns,
            search_turns=search_turns,
            search_behavior_count=behavior_count,
            carry_capacity=max(1, carry),
            search_success_rate=resolve(success_rate),
            guaranteed_rewards=guaranteed,
            search_start_turn=self.state.flow.turn,
            search_instance_id=mission_number,
            fortune=max(-10, min(10, fortune)),
            loot_modifiers=[dict(value) for value in self._active_location_modifiers(location_id)],
            loot_context={},
        )
        mission.random_sequence = [
            self._mission_rng(mission, "success", index).random()
            for index in range(mission.search_behavior_count)
        ]
        # 先离屋再结算奖励：搜索者在屋外，其性格/羁绊不应再计入屋内加权
        # （否则 start_search 的首次掉落与之后的 _recalculate_search 不一致）。
        tenant.at_home = False
        tenant.search_bonus = 0.0
        tenant.fortune_bonus = 0
        self._recalculate_search(mission)
        self.state.world.missions.append(mission)
        self.state.round.searched_this_turn = True
        self._consume_location_modifier_uses(location_id)
        self._record_action(
            "search", tenant=tenant.id, location=location_id,
            tool=None, loadout=list(all_loadout),
        )
        self._log(
            TEXT["systems.search_system.start_search.15"].format(p1=self.character(tenant).name, p2=location.name, p3=mission.search_turns, p4=mission.search_behavior_count)
        )
        self._log(
            TEXT["systems.search_system.start_search.16"].format(p1=mission.search_success_rate, p2=mission.carry_capacity, p3=occupied_groups)
        )

    def _recalculate_search(self, mission: SearchMission) -> None:
        """重算搜索任务的成功行为索引、奖励与满载行为，推算出实际返回回合。"""
        # Extend the fixed sequence if a later effect increases behaviour count.
        while len(mission.random_sequence) < mission.search_behavior_count:
            index = len(mission.random_sequence)
            mission.random_sequence.append(self._mission_rng(mission, "success", index).random())
        mission.success_behavior_indices = [
            index + 1 for index, value in enumerate(mission.random_sequence[: mission.search_behavior_count])
            if value < mission.search_success_rate
        ]
        tenant = self.state.house.tenants[mission.tenant_id]
        reward_slots = max(0, mission.carry_capacity - self._tenant_item_group_count(tenant))
        guaranteed = mission.guaranteed_rewards[:reward_slots]
        ordinary_slots = max(0, reward_slots - len(guaranteed))
        selected_indices = mission.success_behavior_indices[:ordinary_slots]
        ordinary = [self._loot_for_mission(mission, index) for index in selected_indices]
        mission.rewards = guaranteed + ordinary
        mission.bag_full_behavior_index = None
        if len(mission.rewards) >= reward_slots and reward_slots > 0:
            if len(guaranteed) >= reward_slots:
                mission.bag_full_behavior_index = 0
            elif selected_indices:
                mission.bag_full_behavior_index = selected_indices[-1]
        if mission.bag_full_behavior_index is None:
            mission.actual_search_turns = max(1, mission.search_turns)
        else:
            saved = max(0, mission.search_behavior_count - mission.bag_full_behavior_index)
            mission.actual_search_turns = max(1, mission.search_turns - saved)
        mission.remain_search_turns = max(0, mission.actual_search_turns - mission.elapsed_search_turns)

    def _advance_searches_and_returns(self) -> None:
        """推进各搜索任务一个回合，对到期的任务执行返回结算并清出列表。"""
        remaining: list[SearchMission] = []
        for mission in self.state.world.missions:
            tenant = self.state.house.tenants.get(mission.tenant_id)
            if not tenant or not tenant.alive:
                continue
            mission.elapsed_search_turns += 1
            mission.remain_search_turns = max(0, mission.actual_search_turns - mission.elapsed_search_turns)
            if mission.remain_search_turns > 0:
                remaining.append(mission)
                continue
            self._resolve_search_return(mission, tenant)
        self.state.world.missions = remaining


    def _resolve_search_return(self, mission: SearchMission, tenant: Tenant) -> None:
        """结算单个搜索任务的返回：处理濒死/死亡、归途伤害、奖励入库与装备损耗。"""
        returned = False
        if tenant.health < 0:
            mission.rewards.clear()
            if self._rng(EVENT_IDS["search.near_death"], tenant.id).random() < .05:
                tenant.health = 0
                tenant.shock = max(1, tenant.shock)
                tenant.shock_layers = max(2, tenant.shock_layers)
                tenant.at_home = True
                # A near-death survivor loses every carried item in the bag.
                tenant.inventory.items.clear()
                returned = True
                self._log(TEXT["systems.search_system._resolve_search_return.1"].format(p1=self.character(tenant).name))
            else:
                self._observe_visit_information(
                    "search_return", tenant_id=tenant.id,
                    location_id=mission.location_id, returned=False,
                )
                self._kill_tenant(tenant, TEXT["systems.search_system._resolve_search_return.2"])
                return
        else:
            tenant.at_home = True
            returned = True
            avoid_statuses = False
            return_damage = 10.0
            from weiren_game.data import ITEM_HOOKS

            for held in tenant.inventory.items:
                node_hooks = ITEM_HOOKS.get(held.item_id, {}).get(
                    "search.return_mod", {}
                )
                for hook in node_hooks.values():
                    return_damage, avoid = hook(self, tenant, held, return_damage)
                    avoid_statuses = avoid_statuses or bool(avoid)
            self._damage_health(tenant, return_damage, "search_return")
            self._damage_sanity(tenant, 10, "search_return")
            avoidable_statuses = (tenant.trauma, tenant.disorder, *(tenant.condition(key) for key in EROSION_EMOTIONS))
            if avoid_statuses and any(condition.active for condition in avoidable_statuses):
                mission.loot_context["ghillie_avoidance"] = 1.0
            if not avoid_statuses:
                for condition in (tenant.trauma, tenant.disorder):
                    if condition.active:
                        self._worsen_condition(tenant, condition, 1, TEXT["systems.search_system._resolve_search_return.5"])
                        self._extend_condition(tenant, condition, 3, TEXT["systems.search_system._resolve_search_return.6"])
                for key in EROSION_EMOTIONS:
                    condition = tenant.condition(key)
                    if condition.active:
                        self._worsen_condition(tenant, condition, 1, TEXT["systems.search_system._resolve_search_return.7"])
                        self._extend_condition(tenant, condition, 3, TEXT["systems.search_system._resolve_search_return.8"])
            for item_id in mission.rewards:
                self._gain_loot_item(item_id, "search.gain", tenant.id)
            reward_text = "、".join(ITEMS[item_id].name for item_id in mission.rewards) or TEXT["systems.search_system._resolve_search_return.9"]
            self._log(TEXT["systems.search_system._resolve_search_return.10"].format(p1=self.character(tenant).name, p2=LOCATIONS[mission.location_id].name, p3=reward_text))
            for report in getattr(mission, "reports", ()):
                self._log(report)

        self._observe_visit_information(
            "search_return", tenant_id=tenant.id,
            location_id=mission.location_id, returned=returned,
        )
        if returned:
            self._verify_location_information(mission.location_id)

        from weiren_game.data import SCENARIO_HANDLERS

        captured_handler = SCENARIO_HANDLERS.get(
            self.state.pseudo_state.scenario_id, {}
        ).get("captured_return")
        if mission.captured and captured_handler is not None:
            captured_handler(self, mission, tenant)

        self._settle_search_bag_items(mission, tenant)
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("search.return.rest", ()):
            hook(self, tenant)

    def _settle_search_bag_items(self, mission: SearchMission, tenant: Tenant) -> None:
        """结算房客背包在搜索返程中的耐久消耗、易损损耗与可能的破损。"""
        from weiren_game.data import ITEM_HOOKS

        for held in list(tenant.inventory.items):
            node_hooks = ITEM_HOOKS.get(held.item_id, {}).get("search.return", {})
            for hook in node_hooks.values():
                hook(self, tenant, held, mission)
        # 若返程中损坏了购物袋等容量来源，超出的物资需放回仓库。
        self._spill_tenant_overflow(tenant)


# 搜索成功率：创伤/紊乱/消沉的通用修正（provider 化）。
def _search_status_modifier(context: object):
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    penalties = (0, .10, .15, .20, .25, .30)
    if engine._condition_extra_effect_active(tenant, "trauma"):
        yield spec("chance").path("search").flat(-penalties[min(5, tenant.trauma.intensity)])
    if engine._condition_extra_effect_active(tenant, "disorder"):
        yield spec("chance").path("search").flat(-penalties[min(5, tenant.disorder.intensity)])
    if tenant.depression < 0:
        yield spec("chance").path("search").flat(min(.20, max(.05, -tenant.depression * .0002)))
    elif tenant.depression > 500:
        yield spec("chance").path("search").flat(-min(.20, max(.05, tenant.depression * .0002)))


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _search_status_modifier)


def _difficulty_search_modifier(context: object):
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    diff = DIFFICULTIES[engine.state.meta.difficulty]
    if diff.get("search_turn_delta"):
        yield spec("search").path("turn").flat(float(diff["search_turn_delta"])).source("difficulty")
    if diff.get("fortune_delta"):
        yield spec("search").path("luck").flat(float(diff["fortune_delta"])).source("difficulty")
    if diff.get("start_fortune_delta"):
        # 只在开局补给的调用点生效（source 含「开局」），不污染搜索时运。
        yield (
            spec("search").path("setup").flat(float(diff["start_fortune_delta"]))
            .source("difficulty", "setup")
        )


from weiren_game.modifier_rules import register_modifier_provider as _regd
_regd("search", _difficulty_search_modifier)


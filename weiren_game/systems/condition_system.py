"""状态/情绪的统一施加、演化与结算（含免疫与档位修正判定）。"""

from __future__ import annotations


import math
from typing import Sequence

from weiren_game.content import CONTENT
from weiren_game.data import (
    AWAKENING_EMOTIONS,
    EROSION_EMOTIONS,
    EVENT_IDS,
    EXTEND_PROBABILITIES,
    RARE_EMOTIONS,
    STATUS_PRIMARY_LOSS,
    STATUS_SECONDARY_LOSS,
    WORSEN_PROBABILITIES,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.models import Condition
from weiren_game.tenant import TenantState as Tenant

class ConditionSystemMixin:
    def _emotion_key_of(self, tenant: Tenant, condition: Condition) -> str | None:
        """把 condition 反查为情绪键；非情绪条件返回 None。"""
        for key in {**EROSION_EMOTIONS, **AWAKENING_EMOTIONS, **RARE_EMOTIONS}:
            if tenant.condition(key) is condition:
                return key
        return None

    def _notify_emotion_increase(self, tenant: Tenant, key: str) -> None:
        """情绪强度/层数增加后通知当前伪人场景（如洋葱“情绪显现”置 shown）。"""
        from weiren_game.data import SCENARIO_HANDLERS

        handler = SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {}).get(
            "on_emotion_increase"
        )
        if handler is not None:
            handler(self, tenant, key)

    def _condition_extra_effect_active(self, tenant: Tenant, condition_name: str) -> bool:
        """判断创伤/紊乱的额外效果是否未被止痛药压制、可以生效。"""
        from weiren_game.condition import STATUS_DEFINITIONS

        for definition in STATUS_DEFINITIONS.values():
            if (
                condition_name in definition.suppresses_conditions
                and definition.hook is not None
                and definition.hook(self, tenant, condition_name)
            ):
                return False
        return True

    # ----------------------------------------------------------- statuses/emotions
    def _add_condition(
        self,
        tenant: Tenant,
        condition: Condition,
        intensity: int,
        layers: int,
        source: str,
    ) -> bool:
        """按字面量为创伤/紊乱直接追加强度与层数（可跨越 3/6/9 档），返回是否发生改变。"""
        intensity = max(0, int(intensity))
        layers = max(0, int(layers))
        if not (intensity or layers) or self._status_avoidance(tenant, condition, source):
            return False
        before = (condition.intensity, condition.layers)
        condition.intensity = min(10, max(1, condition.intensity + intensity))
        condition.layers = min(99, max(1, condition.layers + layers))
        condition.clamp(intensity_max=10)
        return before != (condition.intensity, condition.layers)

    def _status_avoidance(self, tenant: Tenant, condition: Condition, source: str) -> bool:
        """判定本次状态施加是否被「免疫充能」或护甲抵挡。"""
        if condition is tenant.trauma or condition is tenant.disorder:
            from weiren_game.effects.health_sanity import high_health_status_immunity

            # 高生命免疫（a-10 为常驻）：消耗一点隐藏强度抵挡本次施加。
            if high_health_status_immunity(self, tenant, source):
                return True
            from weiren_game.data import NODE_HOOKS

            for hook in NODE_HOOKS.get("armour.allows_status", ()):
                if hook(self, tenant, source):
                    return True
        return False

    def _set_condition(self, tenant: Tenant, condition: Condition, intensity: int, layers: int, source: str) -> bool:
        """将创伤/紊乱设定为目标强度与层数：目标强度更高则覆盖，否则按强度差概率提升层数。"""
        if intensity <= 0 or layers <= 0 or self._status_avoidance(tenant, condition, source):
            return False
        if condition.intensity < intensity:
            condition.intensity, condition.layers = intensity, layers
        elif condition.layers < layers:
            difference = condition.intensity - intensity
            chance = 1.0 if difference == 0 else max(.01, 1 / difference)
            if self._rng(EVENT_IDS["condition.set"], source, tenant.id).random() < chance:
                condition.layers = layers
        condition.clamp(intensity_max=10)
        return True

    def _worsen_condition(self, tenant: Tenant, condition: Condition, times: int, source: str) -> int:
        """按概率表尝试“恶化”创伤/紊乱若干次（低生命时追加次数），返回成功次数。"""
        if times <= 0 or self._status_avoidance(tenant, condition, source):
            return 0
        repeats = times
        if (condition is tenant.trauma or condition is tenant.disorder) and tenant.health <= 50:
            repeats += max(0, math.floor((55 - tenant.health) / 5))
        successes = 0
        for index in range(min(40, repeats)):
            current = condition.intensity
            if current >= 10:
                break
            chance = WORSEN_PROBABILITIES[current]
            if self._rng(EVENT_IDS["condition.worsen"], source, tenant.id, index).random() < chance:
                condition.intensity = max(1, current + 1)
                condition.layers = max(1, condition.layers)
                successes += 1
        condition.clamp(intensity_max=10)
        if successes > 0:
            emotion_key = self._emotion_key_of(tenant, condition)
            if emotion_key is not None:
                self._notify_emotion_increase(tenant, emotion_key)
        return successes

    def _extend_condition(self, tenant: Tenant, condition: Condition, times: int, source: str) -> int:
        """按概率表尝试“延长”创伤/紊乱（增加层数，未激活则先激活），返回成功次数。"""
        if times <= 0 or self._status_avoidance(tenant, condition, source):
            return 0
        repeats = times
        if (condition is tenant.trauma or condition is tenant.disorder) and tenant.health <= 50:
            repeats += max(0, math.floor((60 - tenant.health) / 10))
        successes = 0
        for index in range(min(40, repeats)):
            if not condition.active:
                condition.intensity = condition.layers = 1
                successes += 1
                continue
            current = min(9, condition.intensity)
            chance = EXTEND_PROBABILITIES[current]
            if self._rng(EVENT_IDS["condition.extend"], source, tenant.id, index).random() < chance:
                condition.intensity = max(1, condition.intensity)
                condition.layers = min(99, max(1, condition.layers) + 1)
                successes += 1
        condition.clamp(intensity_max=10)
        if successes > 0:
            emotion_key = self._emotion_key_of(tenant, condition)
            if emotion_key is not None:
                self._notify_emotion_increase(tenant, emotion_key)
        return successes

    @staticmethod
    def _recover_condition(condition: Condition, layers: int, intensity: int) -> None:
        """按“先减层数、再减强度”的顺序削减创伤/紊乱，层数清零即移除状态。"""
        # Recovery is ordered exactly as specified: remove layers first.  An
        # active condition cannot be reduced below intensity 1; overflow from
        # an intensity reduction removes additional layers instead.
        condition.layers -= max(0, layers)
        if condition.layers <= 0:
            condition.clear()
            return
        requested = max(0, intensity)
        removable = min(requested, max(0, condition.intensity - 1))
        condition.intensity -= removable
        condition.layers -= requested - removable
        condition.clamp(intensity_max=10)

    @staticmethod
    def _reduce_condition(condition: Condition, intensity: int, layers: int) -> None:
        """削减创伤/紊乱的静态入口，将削减量转发给 _recover_condition。"""
        GameEngine._recover_condition(condition, layers, intensity)

    def _emotion_application_blocked(self, tenant: Tenant, key: str, source: str) -> bool:
        """判断该情绪施加是否被拦截。

        三层（先通用、再纯闸门、最后结算点）：
        1. **通用基础谓词**：状态自带 `blocked_emotions` + hook（如「平静-洋葱」）；
        2. **纯闸门** `emotion.apply.block`：内容声明（`path=("施加", 情绪键)`），
           如角色自身的侵蚀免疫、物品提供的侵蚀免疫、角色自身的烦躁免疫；
        3. **结算点**：可能掷骰/带副作用者（如某角色的概率安抚 + 附带收益），
           保留为节点 hook `condition.irritation.settle`（闸门是纯查询，不在此掷骰）。
        """
        from weiren_game.condition import STATUS_DEFINITIONS

        for definition in STATUS_DEFINITIONS.values():
            if (
                key in definition.blocked_emotions
                and definition.hook is not None
                and definition.hook(self, tenant)
            ):
                return True
        if self._eval_gate(
            "emotion.apply.block",
            source=("施加", key),
            context={"tenant": tenant, "key": key, "source": source},
        ):
            return True
        if key == "irritation":
            from weiren_game.data import NODE_HOOKS

            for hook in NODE_HOOKS.get("condition.irritation.settle", ()):
                if hook(self, tenant):
                    return True
        return False

    def _awakening_gain_multiplier(self, tenant: Tenant) -> float:
        """返回该性格性格及其羁绊档位对觉醒情绪获取量的放大系数。"""
        return self._apply_modifiers(
            "awakeningGain", 1.0, ("觉醒", tenant.character_id), {"tenant": tenant}
        )

    def _apply_emotion(
        self, tenant: Tenant, key: str, intensity: int, layers: int,
        source: str, *, scale_awakening: bool = True,
    ) -> bool:
        """直接为单个情绪增加强度与层数（觉醒情绪按该性格系数放大，稀有情绪压回强度 1）。"""
        if self._emotion_application_blocked(tenant, key, source):
            return False
        if key in AWAKENING_EMOTIONS and scale_awakening:
            multiplier = self._awakening_gain_multiplier(tenant)
            intensity = math.ceil(intensity * multiplier) if intensity else 0
            layers = math.ceil(layers * multiplier) if layers else 0
        if key in RARE_EMOTIONS:
            intensity = 1 if intensity else 0
        condition = tenant.condition(key)
        if not condition.active:
            condition.intensity, condition.layers = max(1, intensity), max(1, layers)
            condition.clamp(intensity_max=10)
            self._notify_emotion_increase(tenant, key)
            return True
        before = (condition.intensity, condition.layers)
        condition.intensity = min(10, condition.intensity + max(0, intensity))
        condition.layers = min(99, condition.layers + max(0, layers))
        condition.clamp(intensity_max=10)
        if key in RARE_EMOTIONS and condition.active:
            condition.intensity = 1
        self._notify_emotion_increase(tenant, key)
        return before != (condition.intensity, condition.layers)

    def _strengthen_named_emotion(
        self, tenant: Tenant, key: str, intensity: int, layers: int, source: str
    ) -> bool:
        """对单个情绪执行概率性恶化/延长（觉醒情绪先套用该性格增益）。"""
        if self._emotion_application_blocked(tenant, key, source):
            return False
        if key in AWAKENING_EMOTIONS:
            multiplier = self._awakening_gain_multiplier(tenant)
            intensity = math.ceil(intensity * multiplier) if intensity else 0
            layers = math.ceil(layers * multiplier) if layers else 0
        condition = tenant.condition(key)
        before = (condition.intensity, condition.layers)
        if key not in RARE_EMOTIONS:
            self._worsen_condition(tenant, condition, intensity, source)
        self._extend_condition(tenant, condition, layers, source)
        if key in RARE_EMOTIONS and condition.active:
            condition.intensity = 1
        return before != (condition.intensity, condition.layers)

    def _emotion_weighted_key(
        self,
        tenant: Tenant,
        keys: Sequence[str],
        event_id: str | int,
        event_suffix: Sequence[object] = (),
    ) -> str:
        """按各情绪当前强度加权，从候选中随机选出一个情绪键。"""
        return self._weighted_choice(
            [(key, 20 + 15 * tenant.condition(key).intensity) for key in keys],
            event_id,
            event_suffix=event_suffix,
        )

    def _adjust_emotion_set(self, tenant: Tenant, group: str, intensity: int, layers: int, source: str) -> None:
        """将直接增减量按手稿权重分摊到侵蚀/觉醒情绪组。"""
        keys = list(EROSION_EMOTIONS if group == "erosion" else AWAKENING_EMOTIONS)
        if group == "awakening":
            multiplier = self._awakening_gain_multiplier(tenant)
            intensity = math.ceil(intensity * multiplier) if intensity else 0
            layers = math.ceil(layers * multiplier) if layers else 0
        for index in range(max(intensity, layers)):
            key = self._emotion_weighted_key(
                tenant, keys, EVENT_IDS["emotion.adjust"],
                event_suffix=(group, source, index),
            )
            self._apply_emotion(
                tenant, key, 1 if index < intensity else 0,
                1 if index < layers else 0, source, scale_awakening=False,
            )

    def _strengthen_emotion_set(self, tenant: Tenant, group: str, intensity: int, layers: int, source: str) -> None:
        """对侵蚀/觉醒情绪组执行概率性恶化/延长，避开 3/6/9 档并必要时落向稀有情绪。"""
        keys = list(EROSION_EMOTIONS if group == "erosion" else AWAKENING_EMOTIONS)
        if group == "awakening":
            multiplier = self._awakening_gain_multiplier(tenant)
            intensity = math.ceil(intensity * multiplier)
            layers = math.ceil(layers * multiplier)
        for index in range(max(intensity, layers)):
            candidates = [key for key in keys if not (index < intensity and tenant.condition(key).intensity in {3, 6, 9})]
            if not candidates:
                rare_key = "madness" if group == "erosion" else "reason"
                candidates = [rare_key] if tenant.condition(rare_key).active else []
            if not candidates:
                continue
            key = self._emotion_weighted_key(
                tenant, candidates, EVENT_IDS["emotion.select"],
                event_suffix=(group, source, index),
            )
            if self._emotion_application_blocked(tenant, key, source):
                continue
            condition = tenant.condition(key)
            if index < intensity and key not in RARE_EMOTIONS:
                self._worsen_condition(tenant, condition, 1, source)
            if index < layers:
                self._extend_condition(tenant, condition, 1, source)
            self._notify_emotion_increase(tenant, key)

    def _reduce_emotion_set(self, tenant: Tenant, group: str, intensity: int, layers: int, maximum_intensity: int = 10) -> None:
        """在情绪组内逐次削减当前强度最低的活跃情绪。"""
        keys = list(EROSION_EMOTIONS if group == "erosion" else AWAKENING_EMOTIONS)
        for _ in range(max(intensity, layers)):
            active = [key for key in keys if tenant.condition(key).active and tenant.condition(key).intensity <= maximum_intensity]
            if not active:
                break
            key = min(active, key=lambda value: (tenant.condition(value).intensity, tenant.condition(value).layers, value))
            condition = tenant.condition(key)
            if intensity > 0:
                condition.intensity -= 1; intensity -= 1
            if layers > 0:
                condition.layers -= 1; layers -= 1
            condition.clamp(intensity_max=10)

    def _apply_status_end(self, tenant: Tenant, condition: Condition, *, physical: bool, label: str) -> None:
        """回合末演化创伤/紊乱：按强度损失生命/理智，并概率自发恶化、衰减层数。"""
        if not condition.active:
            return
        level = max(1, min(10, condition.intensity))
        primary = STATUS_PRIMARY_LOSS[level]
        secondary = STATUS_SECONDARY_LOSS[level]
        if physical:
            self._loss_health(tenant, primary, label)
            if secondary:
                self._loss_sanity(tenant, secondary, label)
        else:
            self._loss_sanity(tenant, primary, label)
            if secondary:
                self._loss_health(tenant, secondary, label)
        if physical:
            intensity_chance = (0, .10, .15, .20, .25, .30, .50, .60, .70, .80, 0)[level]
            layer_chance = (0, .05, .10, .10, .15, .15, .20, .30, .50, .75, 1.0)[level]
        else:
            intensity_chance = (0, .05, .10, .10, .15, .15, .20, .30, .50, .75, 0)[level]
            layer_chance = (0, .10, .15, .20, .25, .30, .50, .60, .70, .80, 1.0)[level]
        if self._rng(EVENT_IDS["status.self.intensity"], label, tenant.id).random() < intensity_chance:
            condition.intensity = min(10, condition.intensity + 1)
        if self._rng(EVENT_IDS["status.self.layer"], label, tenant.id).random() < layer_chance:
            condition.layers = min(99, condition.layers + 1)
        condition.clamp(intensity_max=10)

    def _apply_emotion_end(self, tenant: Tenant, condition: Condition, label: str) -> None:
        """回合末演化情绪：按强度/层数概率自发恶化并固定衰减一层。"""
        if not condition.active:
            return
        rare = label in RARE_EMOTIONS.values()
        from weiren_game.probability import resolve

        intensity_chance = resolve(condition.intensity * condition.layers / 100)
        layer_chance = resolve(condition.intensity ** 2 / 100)
        if not rare and self._rng(EVENT_IDS["emotion.self.intensity"], label, tenant.id).random() < intensity_chance:
            condition.intensity = min(10, condition.intensity + 1)
        if self._rng(EVENT_IDS["emotion.self.layer"], label, tenant.id).random() < layer_chance:
            condition.layers = min(99, condition.layers + 1)
        emotion_key = self._emotion_key_of(tenant, condition)
        if emotion_key is not None:
            from weiren_game.data import SCENARIO_HANDLERS

            extra_handler = SCENARIO_HANDLERS.get(
                self.state.pseudo_state.scenario_id, {}
            ).get("emotion_end_extra")
            if extra_handler is not None:
                extra_handler(self, tenant, condition, emotion_key)
            self._notify_emotion_increase(tenant, emotion_key)
        condition.clamp(intensity_max=10)
        if rare and condition.active:
            condition.intensity = 1

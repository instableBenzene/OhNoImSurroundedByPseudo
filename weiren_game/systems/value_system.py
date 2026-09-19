"""生命/理智/状态数值的消耗与回复结算（含角色与物品修饰）。"""

from __future__ import annotations

import math

from weiren_game.content import CONTENT
from weiren_game.data import (
    CHARACTER_NODE_HOOKS,
    CHARACTER_VALUE_HOOKS,
    DIFFICULTIES,
    EVENT_IDS,
)
from weiren_game.data.lang import TEXT, source_label, token_label
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.tenant import TenantState as Tenant
from weiren_game.items import ItemInstance

class ValueSystemMixin:

    # ------------------------------------------------------- value-change pipeline
    def _health_protection_multiplier(
        self, tenant: Tenant, amount: float, *, consume: bool
    ) -> float:
        """返回需转嫁的固定量（减伤本身已由 healthConsume/healthDamage 修饰器处理）。"""
        from weiren_game.data.personalities import HEALTH_PROTECTION_HOOKS

        transferred = 0.0
        for _personality_id, hook in HEALTH_PROTECTION_HOOKS.items():
            _added, shared = hook(self, tenant, amount, consume=consume)
            transferred += shared
        return transferred

    def _consume_held_durability(self, tenant: Tenant, held: ItemInstance, amount: int) -> bool:
        """消耗装备耐久，损坏时移除装备并返回 True。"""
        cost = max(1, math.ceil(amount * self._durability_multiplier()))
        held.durability -= cost
        if held.durability <= 0:
            tenant.inventory.items.remove(held)
            self._log(TEXT["systems.value_system._consume_held_durability.1"].format(p1=self.character(tenant).name, p2=ITEMS[held.item_id].name))
            return True
        return False

    def _apply_armour(self, tenant: Tenant, amount: float) -> float:
        """按最先装备的护甲减免本次伤害并消耗对应耐久。"""
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("armour.apply", ()):
            return hook(self, tenant, amount)
        return amount

    def _damage_health(self, tenant: Tenant, amount: float, source: str) -> float:
        """对房客造成生命伤害，应用难度倍率、护甲与减伤并结算该性格分担。"""
        if amount <= 0 or not tenant.alive:
            return 0.0
        base = self._apply_modifiers(
            "healthDamage", amount,
            ("damage", source, tenant.character_id), {"tenant": tenant, "consume": False},
        )
        armoured = self._apply_armour(tenant, base)
        transferred = self._health_protection_multiplier(tenant, base, consume=False)
        actual = armoured
        before = tenant.health
        tenant.health = max(-100.0, tenant.health - actual)
        self._after_health_changed()
        lost = max(0.0, before - tenant.health)
        self._after_health_decrease(tenant, lost)
        # Rose can heal to full as a consequence of taking damage, which may
        # release the current ICU target immediately.
        self._after_health_changed()
        self._log(TEXT["systems.value_system._damage_health.2"].format(p1=self.character(tenant).name, p2=source_label(source), p3=lost))
        if transferred > 0:
            from weiren_game.data import NODE_HOOKS

            receivers: list[object] = []
            for hook in NODE_HOOKS.get("health.transfer_receivers", ()):
                receivers = hook(self, tenant)
                if receivers:
                    break
            if receivers:
                share = transferred / len(receivers)
                for receiver in receivers:
                    self._loss_health(receiver, share, "bond_share")
        return lost

    def _consume_health(self, tenant: Tenant, amount: float, source: str) -> float:
        """尝试消耗指定量生命（不足则失败），受修饰影响并可转嫁为理智消耗。"""
        if amount <= 0 or not tenant.alive:
            return 0.0
        if tenant.health < amount:
            self._log(TEXT["systems.value_system._consume_health.1"].format(p1=self.character(tenant).name, p2=amount, p3=source_label(source)))
            return 0.0
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("value.health_consume.convert", ()):
            converted = hook(self, tenant, amount, source)
            if converted is not None:
                return converted
        amount = self._apply_modifiers(
            "healthConsume", amount,
            ("consume", source, tenant.character_id), {"tenant": tenant, "consume": True},
        )
        transferred = self._health_protection_multiplier(tenant, amount, consume=True)
        before = tenant.health
        tenant.health = max(0.0, tenant.health - amount)
        self._after_health_changed()
        lost = max(0.0, before - tenant.health)
        self._after_health_decrease(tenant, lost)
        self._after_health_changed()
        self._log(TEXT["systems.value_system._consume_health.3"].format(p1=self.character(tenant).name, p2=source_label(source), p3=lost))
        if transferred > 0:
            from weiren_game.data import NODE_HOOKS

            receivers: list[object] = []
            for hook in NODE_HOOKS.get("health.transfer_receivers", ()):
                receivers = hook(self, tenant)
                if receivers:
                    break
            for receiver in receivers:
                self._loss_health(receiver, transferred / len(receivers), "personality_bond_share")
        return lost

    def _loss_health(self, tenant: Tenant, amount: float, source: str) -> float:
        """按流失语义扣减生命，并应用回合末人物/性格修饰。"""
        if amount <= 0 or not tenant.alive:
            return 0.0
        amount = self._apply_modifiers(
            "healthLoss", amount,
            ("health_loss", source, tenant.character_id), {"tenant": tenant},
        )
        before = tenant.health
        tenant.health = max(-100.0, tenant.health - amount)
        self._after_health_changed()
        lost = max(0.0, before - tenant.health)
        self._after_health_decrease(tenant, lost)
        self._after_health_changed()
        self._log(TEXT["systems.value_system._loss_health.2"].format(p1=self.character(tenant).name, p2=source_label(source), p3=lost))
        return lost

    def _restore_health(self, tenant: Tenant, amount: float, source: str = TEXT["systems.value_system._restore_health.1"]) -> float:
        """回复生命至上限，返回实际回复量。

        注意：**不再顺手清除休克**。休克只由**内容层明确声明的效果**解除
        （现存唯一一处是"移除全部状态"）；旧代码"只要回血到 >0 就清休克"是没登记的额外规则，
        等于让休克形同虚设（玩家报告过）。
        """
        if amount <= 0 or not tenant.alive:
            return 0.0
        before = tenant.health
        tenant.health = min(tenant.max_health, tenant.health + amount)
        restored = tenant.health - before
        self._after_health_changed()
        return restored

    def _consume_sanity(self, tenant: Tenant, amount: float, source: str) -> float:
        """尝试消耗指定量理智（不足则失败），可转嫁为生命伤害。"""
        if amount <= 0 or not tenant.alive:
            return 0.0
        if tenant.sanity < amount:
            self._log(TEXT["systems.value_system._consume_sanity.1"].format(p1=self.character(tenant).name, p2=amount, p3=source_label(source)))
            return 0.0
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("value.sanity_consume.convert", ()):
            converted = hook(self, tenant, amount, source)
            if converted is not None:
                return converted
        return self._reduce_sanity(tenant, amount, source, floor_zero=True, change_type="consume")

    def _damage_sanity(self, tenant: Tenant, amount: float, source: str) -> float:
        """对理智造成包含难度倍率的伤害。"""
        value = self._apply_modifiers(
            "sanityDamage", amount,
            ("damage", source, tenant.character_id), {"tenant": tenant},
        )
        return self._reduce_sanity(tenant, value, source, floor_zero=False, change_type="damage")

    def _loss_sanity(self, tenant: Tenant, amount: float, source: str) -> float:
        """以流失语义扣减理智（不设下限）。"""
        return self._reduce_sanity(tenant, amount, source, floor_zero=False, change_type="loss")

    def _reduce_sanity(self, tenant: Tenant, amount: float, source: str, *, floor_zero: bool, change_type: str) -> float:
        """统一削减理智：应用冻结保护、角色减半等修饰并触发后续效果。"""
        if amount <= 0 or not tenant.alive:
            return 0.0
        from weiren_game.data import NODE_HOOKS

        channel = {"consume": "sanityConsume", "damage": "sanityDamage", "loss": "sanityLoss"}.get(
            change_type, "sanityLoss"
        )
        amount = self._apply_modifiers(
            channel, amount, (change_type, tenant.character_id),
            {"tenant": tenant, "change_type": change_type},
        )
        before = tenant.sanity
        lower = 0.0 if floor_zero else -100.0
        target = tenant.sanity - amount
        guard_floor = None
        for hook in NODE_HOOKS.get("sanity.floor", ()):
            value = hook(self, tenant, before, target)
            if value is not None:
                guard_floor = value if guard_floor is None else max(guard_floor, value)
        effective_lower = (
            max(lower, guard_floor) if guard_floor is not None else lower
        )
        tenant.sanity = max(effective_lower, target)
        lost = before - tenant.sanity
        if lost > 0:
            self._emit_node(
                "sanity.lost",
                tenant=tenant,
                lost=lost,
                change_type=change_type,
            )
        for hook in NODE_HOOKS.get("sanity.after_decrease", ()):
            hook(self, tenant)
        self._log(TEXT["systems.value_system._reduce_sanity.1"].format(p1=self.character(tenant).name, p2=source_label(source), p3=token_label(change_type), p4=lost))
        return lost

    def _restore_sanity(self, tenant: Tenant, amount: float, source: str = TEXT["systems.value_system._restore_sanity.1"]) -> float:
        """回复理智；溢出多少、怎么用，交给内容层（发 `sanity.restored` 节点）。"""
        if amount <= 0 or not tenant.alive:
            return 0.0
        amount = self._apply_modifiers(
            "sanityRestore", amount, ("restore", tenant.character_id),
            {"tenant": tenant},
        )
        before = tenant.sanity
        raw_after = tenant.sanity + amount
        cap = tenant.max_sanity
        tenant.sanity = min(cap, raw_after)
        overflow = max(0.0, raw_after - cap)
        # 核心只发**通用节点**：谁关心溢出谁自己登记（全局 `NODE_HOOKS` / 角色
        # `CHARACTER_NODE_HOOKS` / 伪人场景各自判断），核心不为任何单个角色或场景留专属入口。
        self._emit_node("sanity.restored", tenant=tenant, overflow=overflow)
        tenant_hook = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get("sanity.restored")
        if tenant_hook is not None:
            tenant_hook(self, tenant=tenant, overflow=overflow)
        return tenant.sanity - before

    def _after_health_decrease(self, tenant: Tenant, amount: float) -> None:
        """生命下降后结算内容层登记的角色连锁（`CHARACTER_VALUE_HOOKS`）。"""
        if amount <= 0:
            return
        hooks = CHARACTER_VALUE_HOOKS.get(tenant.character_id)
        if hooks:
            after_hook = hooks.get("after_health_decrease")
            if after_hook is not None:
                after_hook(self, tenant)

    def _after_health_changed(self) -> None:
        """生命数值变动后的角色光环统一入口（按注册表执行）。"""
        from weiren_game.data import HEALTH_CHANGED_HOOKS

        for hook in HEALTH_CHANGED_HOOKS:
            hook(self)

    def _natural_high_health_recovery(self, tenant: Tenant) -> None:
        """高生命房客在回合末按概率自然恢复创伤/紊乱。"""
        if tenant.health < 80:
            return
        intensity_chance = min(.50, max(0, (tenant.health * 2 - 140) / 100))
        repeats = max(1, math.floor((tenant.health - 65) / 15))
        maximum = min(9, max(0, 3 * math.floor(tenant.health / 5 - 15)))
        guaranteed_maximum = max(0, 3 * math.floor(tenant.health / 5 - 16))
        from weiren_game.probability import resolve

        layer_chance = resolve((tenant.health * 2 - 175) / 100)
        for condition in (tenant.trauma, tenant.disorder):
            for index in range(repeats):
                if condition.active and condition.intensity <= maximum:
                    chance = 1.0 if condition.intensity <= guaranteed_maximum else intensity_chance
                    if self._rng(EVENT_IDS["health.recover.intensity"], tenant.id, index).random() < chance:
                        self._recover_condition(condition, 0, 1)
                if condition.active and self._rng(EVENT_IDS["health.recover.layer"], tenant.id, index).random() < layer_chance:
                    self._recover_condition(condition, 1, 0)


def _difficulty_health_damage_modifier(context: object):
    """难度：生命伤害的最终百分比乘算。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    mult = float(DIFFICULTIES[engine.state.meta.difficulty]["damage_multiplier"])
    if mult != 1.0:
        yield spec("healthDamage").path("damage").final().mul(mult).source("difficulty")


def _difficulty_sanity_damage_modifier(context: object):
    """难度：理智伤害的最终百分比乘算。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    mult = float(DIFFICULTIES[engine.state.meta.difficulty]["damage_multiplier"])
    if mult != 1.0:
        yield spec("sanityDamage").path("damage").final().mul(mult).source("difficulty")


from weiren_game.modifier_rules import register_modifier_provider as _regdd
_regdd("healthDamage", _difficulty_health_damage_modifier)
_regdd("sanityDamage", _difficulty_sanity_damage_modifier)

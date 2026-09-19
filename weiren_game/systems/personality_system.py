"""人格权重折算、羁绊等级/激活与性格相关判定。"""

from __future__ import annotations

from weiren_game.probability import resolve


import math
from collections import Counter

from weiren_game.content import CONTENT
from weiren_game.data import (
    PERSONALITIES,
    PERSONALITY_LABELS,
)
from weiren_game.data.lang import TEXT
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.tenant import TenantState as Tenant

from weiren_game.exceptions import RuleViolation

class PersonalitySystemMixin:
    # ---------------------------------------------------------- personality/bonds
    def _tenant_personalities(self, tenant: Tenant) -> tuple[str, str]:
        """返回房客当前的主/副性格（按权重表顺序，缺省回退到角色默认值）。"""
        definition = self.character(tenant)
        slots = list(tenant.personalities)[:2]
        return (
            slots[0] if slots else definition.primary,
            slots[1] if len(slots) > 1 else definition.secondary,
        )
#性格只保存权重，因此不再需要 primary / secondary 这种角色字段。
    def _is_personality(self, tenant: Tenant, personality: str) -> bool:
        """判断房客是否具备指定性格：需存活、未休克且消沉值低于 1001。"""
        # Shock and very high depression explicitly disable both personality
        # base effects.  Bond weights are calculated separately below.
        return (
            tenant.alive and not tenant.shock and tenant.depression < 1001
            and personality in self._tenant_personalities(tenant)
        )
#上述情况可以把直接定义为将权重设定为0。且性格的基础效果尽在权重＞0时生效。这样子设定就可以解决问题了。
    def _personality_weights(self) -> dict[str, float]:
        """汇总各房客主/副性格的羁绊权重（跳过休克与高消沉房客）。"""
        weights: Counter[str] = Counter()
        for tenant in self.home_tenants():
            if tenant.shock or tenant.depression >= 1001:
                continue
            primary, secondary = self._tenant_personalities(tenant)
            if primary not in PERSONALITIES or secondary not in PERSONALITIES:
                continue
            from weiren_game.data import NODE_HOOKS

            locked = None
            for hook in NODE_HOOKS.get("personality.weights", ()):
                locked = hook(self, tenant)
                if locked:
                    break
            if locked:
                primary_weight, secondary_weight = locked
            elif tenant.depression <= -500:
                primary_weight, secondary_weight = 2.0, 1.5
            elif tenant.depression > 500:
                primary_weight, secondary_weight = 1.0, .5
            else:
                primary_weight, secondary_weight = 1.5, 1.0
            weights[primary] += primary_weight
            weights[secondary] += secondary_weight
        return dict(weights)
    def bond_levels(self) -> dict[str, int]:
        """将性格权重折算为羁绊等级：由各人格模块声明取整规则。"""
        from weiren_game.data.personalities import PERSONALITY_MODULES

        round_up = {
            key
            for key, module in PERSONALITY_MODULES.items()
            if getattr(module, "ROUND_UP", False)
        }
        return {
            key: (math.ceil(value) if key in round_up else math.floor(value))
            for key, value in self._personality_weights().items()
        }
    def _bond_tier(self, personality: str, level: int | None = None) -> int:
        """根据羁绊等级返回该性格达到的最高档位（默认由当前羁绊等级换算）。"""
        from weiren_game.data.personalities import PERSONALITY_MODULES

        value = self.bond_levels().get(personality, 0) if level is None else level
        module = PERSONALITY_MODULES.get(personality)
        if module is None:
            return 0
        tier_at = getattr(module, "TIER_AT", None)
        if tier_at is not None:
            return tier_at(value)
        thresholds = tuple(getattr(module, "TIERS", ()))
        return max((t for t in thresholds if value >= t), default=0)
    def _activate_new_bonds(self, *, initial: bool = False) -> None:
        """激活达到门槛的新羁绊：档位与激活奖励由各人格模块声明。"""
        from weiren_game.data.personalities import PERSONALITY_MODULES

        levels = self.bond_levels()
        activated = self.state.house.bonds.activated_bonds
        for personality, module in PERSONALITY_MODULES.items():
            active_tiers = getattr(module, "ACTIVE_TIERS", None)
            if active_tiers is not None:
                tiers = active_tiers(levels.get(personality, 0))
            else:
                reached = [
                    tier
                    for tier in getattr(module, "TIERS", ())
                    if levels.get(personality, 0) >= tier
                ]
                tiers = [max(reached)] if reached else []
            for tier in tiers:
                key = f"{personality}:{tier}"
                if key in activated:
                    continue
                activated.append(key)
                self._emit_node(
                    "bond.activated", personality=personality, tier=tier
                )
                on_activate = getattr(module, "ON_ACTIVATE", None)
                if on_activate is not None:
                    on_activate(self, tier)
                if not initial:
                    self._log(TEXT["systems.personality_system._activate_new_bonds.1"].format(p1=PERSONALITY_LABELS[personality], p2=tier))
        if initial:
            for module in PERSONALITY_MODULES.values():
                on_initial = getattr(module, "ON_INITIAL", None)
                if on_initial is not None:
                    on_initial(self)

    def _passive_available(self, tenant: Tenant, event_id: str = "passive") -> bool:
        """判定被动本回合是否可用：休克直接禁用，创伤/紊乱与高消沉增加失效概率。"""
        if tenant.shock or tenant.passives_disabled:
            return False
        chance = .50 if tenant.depression > 1000 else 0.0
        # The source tables deliberately alternate which condition suppresses
        # active and passive powers at each tier.
        if self._condition_extra_effect_active(tenant, "disorder") and 3 <= tenant.disorder.intensity <= 5:
            chance += {3: .25, 4: .30, 5: .35}[tenant.disorder.intensity]
        if self._condition_extra_effect_active(tenant, "trauma") and 6 <= tenant.trauma.intensity <= 8:
            chance += {6: .25, 7: .30, 8: .35}[tenant.trauma.intensity]
        if self._condition_extra_effect_active(tenant, "disorder") and tenant.disorder.intensity == 9:
            chance += .10
        if self._condition_extra_effect_active(tenant, "trauma") and tenant.trauma.intensity == 10:
            chance += .10
        guarantees: list[float] = []
        if chance <= 0:
            guarantees.append(0.0)
        if chance >= 1.0:
            guarantees.append(1.0)
        return self._rng(f"{event_id}.{tenant.id}").random() >= resolve(
            chance, guarantees
        )

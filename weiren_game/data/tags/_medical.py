"""医药/手术 tag 共用实现：成功率与耐久修正。

规则（原稿）：
- 治疗强度 ≤ 可治疗最大强度：成功率固定 100%，且每低 1 级耐久消耗 -10%
  （最低 1）；
- 治疗强度 > 可治疗最大强度：成功率 = 2 / ((目标强度 - 最大强度) + 2)
  （最低 5%），且每高 1 级耐久消耗 +25%。
- 生命 ≤ 50 时成功率额外降低；
- 其它修正（如 BLS 被动 +10 个百分点）由修饰器注册表在 `chance.medical`
  调用点提供，本函数只负责收集与编译；非必中结果收敛到 5%~95%。
"""

from __future__ import annotations

from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers
from weiren_game.probability import resolve

import math

from weiren_game.types import EngineProtocol


def treatment_params(item: object, target: object) -> tuple[float, int]:
    """按目标状态强度返回 (成功率, 本次耐久/消耗数)。"""
    difference = target.intensity - item.medical_max_intensity
    if difference <= 0:
        success = 1.0
        discount = max(0, item.medical_max_intensity - target.intensity)
        cost = max(1, math.ceil(item.use_cost * max(.1, 1 - .1 * discount)))
    else:
        success = 2 / (difference + 2)
        cost = max(1, math.ceil(item.use_cost * (1.25 ** difference)))
    return success, cost


def use_medical(
    engine: EngineProtocol, item: object, tenant: object,
    inventory: object = None, spot: object = None,
) -> None:
    """执行一次医疗物资治疗：判成功、结算耐久并按结果削减状态。"""
    from weiren_game.exceptions import RuleViolation
    from weiren_game.data import EVENT_IDS

    target = tenant.trauma if item.medical_target == "trauma" else tenant.disorder
    if not target.active:
        raise RuleViolation(
            f"目标没有{('创伤' if item.medical_target == 'trauma' else '紊乱')}。"
        )
    base_success, cost = treatment_params(item, target)
    # 目标已在药物可处理范围内且未被低生命惩罚时，本次治疗为“必定成功”。
    guaranteed = base_success >= 1.0 and tenant.health > 50
    if guaranteed:
        success = 1.0
    else:
        success = base_success
        if tenant.health <= 50:
            success -= (50 - tenant.health) / 100
        kind = "手术包" if item.medical_target == "trauma" else "药箱"
        target_kind = "创伤" if item.medical_target == "trauma" else "紊乱"
        event_source = ("医疗", "治疗", "医疗物资", kind, item.name, target_kind)
        context = {"engine": engine, "tenant": tenant, "item": item}
        modifiers = collect_modifiers("chance", event_source, context)
        success = resolve(calculate_modified_amount(success, modifiers))
    engine._spend_item_use(
        item.item_id, item, tenant, cost, inventory=inventory, spot=spot
    )
    if engine._rng(EVENT_IDS["medical"], item.item_id, tenant.id).random() < success:
        engine._recover_condition(target, item.reduce_layers, item.reduce_intensity)
        engine._log(
            f"{engine.character(tenant).name}使用{item.name}成功，"
            f"目标状态-{item.reduce_intensity}/-{item.reduce_layers}。"
        )
    else:
        engine._log(
            f"{engine.character(tenant).name}使用{item.name}失败"
            f"（成功率{success:.0%}）。"
        )

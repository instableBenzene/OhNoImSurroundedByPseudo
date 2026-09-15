"""生命周期节点与引擎回合主流程阶段表。

蓝图见 docs/GUIDE.md。``Node`` 是节点名常量集；``START_TURN_PHASES`` /
``END_TURN_PHASES`` 声明引擎回合主流程的当前实际执行顺序；``AbilityLaunch``
是 A→B 能力发动的组合与阶段常量。
"""

from __future__ import annotations


# --------------------------------------------------------------------- nodes
class Node:
    """回合级与动作级节点的统一常量。"""

    GAME_START = "game_start"
    TURN_START_DEPRESSION = "turn_start.depression_effect"
    TURN_START_SEARCH_RETURN = "turn_start.search_return"
    TURN_START_SEARCH_SUMMARY = "turn_start.search_summary"
    TURN_START_DEPARTED_RETURN = "turn_start.departed_return"
    TURN_START_VISITOR_HUMAN = "turn_start.visitor_human"
    TURN_START_VISITOR_PSEUDO = "turn_start.visitor_pseudo"
    TURN_START_VISITOR_SUPPLY = "turn_start.visitor_supply"
    TURN_START_VISITOR_QUEUE = "turn_start.visitor_queue"
    TURN_START_BONDS = "turn_start.bonds"
    TURN_START_INSTANCES = "turn_start.instances"
    TURN_START_STATUS_EFFECTS = "turn_start.status_effects"
    TURN_START_INFORMATION = "turn_start.information"
    TURN_START_INFO_INVALIDATE = "turn_start.information_invalidate"
    TURN_END_BASE_CONSUME = "turn_end.base_consume"
    TURN_END_STATUS_EFFECTS = "turn_end.status_effects"
    TURN_END_PSEUDO_ATTACK = "turn_end.pseudo_attack"
    TURN_END_STATUS = "turn_end.status_end"
    TURN_END_INFORMATION = "turn_end.information"
    TURN_END_EQUIPMENT = "turn_end.equipment_books"
    TURN_END_INSTANCES = "turn_end.instances"
    TURN_END_OTHER = "turn_end.other_end_effects"
    TURN_END_SURVIVAL = "turn_end.survival_check"
    TURN_END_VICTORY = "turn_end.victory"
    DOOR_EVENT = "door_event"
    DOOR_ACCEPT = "door.accept"
    DOOR_REJECT = "door.reject"
    ITEM_USE = "item_use"
    ITEM_EQUIP = "item_equip"
    ITEM_CONSUMED = "item.consumed"
    ITEM_BROKEN = "item.broken"
    SEARCH_START = "search_start"
    ABILITY_ACTIVATE = "ability.activate"
    ABILITY_USED = "ability.used"
    ABILITY_FAILED = "ability.failed"
    STATUS_APPLIED_ALLOW = "status_applied.before.allow"
    STATUS_APPLIED_MODIFY = "status_applied.before.modify"
    STATUS_APPLIED_AFTER = "status_applied.after"
    MARK_GAINED = "mark.gained"
    MARK_CONSUMED = "mark.consumed"
    MARK_REACHED = "mark.reached"
    TENANT_DEATH = "tenant.death"
    TENANT_EXPELLED = "tenant.expelled"
    TENANT_LEFT = "tenant.left"
    TENANT_RETURNED = "tenant.returned"
    BOND_ACTIVATED = "bond.activated"
    PSEUDO_INSTANCE_CREATED = "pseudo.instance.created"
    PSEUDO_INSTANCE_REMOVED = "pseudo.instance.removed"
    INFORMATION_CREATED = "information.created"
    BEFORE_BREAKTHROUGH = "before_breakthrough"


# 引擎回合主流程的当前实际顺序（保持行为，仅把顺序的归属交给 lifecycle）。
# 每项为 (节点名, GameEngine 方法名)。
START_TURN_PHASES = (
    (Node.TURN_START_DEPRESSION, "_settle_emotion_values"),
    (Node.TURN_START_SEARCH_RETURN, "_advance_searches_and_returns"),
    (Node.TURN_START_SEARCH_SUMMARY, "_log_searching_summary"),
    (Node.TURN_START_DEPARTED_RETURN, "_return_departed_tenants"),
    (Node.TURN_START_VISITOR_QUEUE, "_queue_scheduled_visitors"),
    (Node.TURN_START_INSTANCES, "_start_of_turn_effects"),
    (Node.TURN_START_INFORMATION, "_expire_information"),
    (Node.TURN_START_INFO_INVALIDATE, "_invalidate_target_information"),
    (Node.TURN_START_BONDS, "_activate_new_bonds"),
)

END_TURN_PHASES = (
    (Node.TURN_END_BASE_CONSUME, "_settle_base_end_effects"),
    (Node.TURN_END_STATUS_EFFECTS, "_settle_turn_end_status_effects"),
    (Node.TURN_END_PSEUDO_ATTACK, "_pseudo_attack_searchers"),
    (Node.TURN_END_STATUS, "_settle_buff_debuff_effects"),
    (Node.TURN_END_INFORMATION, "_apply_pending_information_effects"),
    (Node.TURN_END_EQUIPMENT, "_settle_books_and_equipment"),
    (Node.TURN_END_INSTANCES, "_run_pseudo_end_effects"),
    (Node.TURN_END_INSTANCES, "_settle_other_end_effects"),
    (Node.TURN_END_INFORMATION, "_expire_information"),
    (Node.TURN_START_INFO_INVALIDATE, "_invalidate_target_information"),
    (Node.TURN_END_SURVIVAL, "_check_survival"),
)

class AbilityLaunch:
    """A 对 B 发动能力的分类与阶段。

    ``TARGET_NONE`` 为将来"无需选择目标"的技能预留：此类技能可跳过
    ``SELECT_TARGET``/``BEFORE_EFFECT``（无目标可抵抗），只走
    ``APPLY_EFFECT``（必要时 ``AFTER_EFFECT``）。
    """

    TARGET_NONE = "target_none"

    HUMAN_HUMAN = "human_human"
    HUMAN_PSEUDO = "human_pseudo"
    PSEUDO_HUMAN = "pseudo_human"
    PSEUDO_PSEUDO = "pseudo_pseudo"

    SELECT_TARGET = "select_target"
    BEFORE_EFFECT = "before_effect"
    APPLY_EFFECT = "apply_effect"
    AFTER_EFFECT = "after_effect"


__all__ = [
    "END_TURN_PHASES",
    "START_TURN_PHASES",
    "AbilityLaunch",
    "Node",
]

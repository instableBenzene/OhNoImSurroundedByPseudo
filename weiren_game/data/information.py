"""动态信息模板与地点信息修正表。"""

from .types import InformationTemplate
from weiren_game.data.lang import TEXT

INFORMATION_TEMPLATES = {
    "discarded_briefcase": InformationTemplate("discarded_briefcase", TEXT["info.discarded_briefcase.name"], "material_reward", TEXT["info.discarded_briefcase.description"], reward_ids=("meteor_plan",)),
    "secret_raid": InformationTemplate("secret_raid", TEXT["info.secret_raid.name"], "material_reward", TEXT["info.secret_raid.description"], reward_ids=("fiji_chocolate",)),
    "lost_return": InformationTemplate("lost_return", TEXT["info.lost_return.name"], "material_reward", TEXT["info.lost_return.description"], reward_ids=("polar_jacket",)),
    "security_backup": InformationTemplate("security_backup", TEXT["info.security_backup.name"], "material_reward", TEXT["info.security_backup.description"], reward_ids=("video_tape",)),
    "good_talk": InformationTemplate("good_talk", TEXT["info.good_talk.name"], "state", TEXT["info.good_talk.description"], TEXT["data.information.module.1"], TEXT["data.information.module.2"], TEXT["data.information.module.3"]),
    "odd_smile": InformationTemplate("odd_smile", TEXT["info.odd_smile.name"], "state", TEXT["info.odd_smile.description"], TEXT["data.information.module.4"], TEXT["data.information.module.5"], TEXT["data.information.module.6"]),
    "tense_nerves": InformationTemplate("tense_nerves", TEXT["info.tense_nerves.name"], "state", TEXT["info.tense_nerves.description"], TEXT["data.information.module.7"], TEXT["data.information.module.8"], TEXT["data.information.module.9"]),
    "suppressed_sobbing": InformationTemplate("suppressed_sobbing", TEXT["info.suppressed_sobbing.name"], "state", TEXT["info.suppressed_sobbing.description"], TEXT["data.information.module.10"], TEXT["data.information.module.11"], TEXT["data.information.module.12"]),
    "moment_peace": InformationTemplate("moment_peace", TEXT["info.moment_peace.name"], "state", TEXT["info.moment_peace.description"], TEXT["data.information.module.13"], TEXT["data.information.module.14"], TEXT["data.information.module.15"]),
    "supply_dispute": InformationTemplate("supply_dispute", TEXT["info.supply_dispute.name"], "state", TEXT["info.supply_dispute.description"], TEXT["data.information.module.16"], TEXT["data.information.module.17"], TEXT["data.information.module.18"]),
    "courier_absent": InformationTemplate("courier_absent", TEXT["info.courier_absent.name"], "location_modifier", TEXT["info.courier_absent.description"], location_id="courier_station"),
    "double_eleven": InformationTemplate("double_eleven", TEXT["info.double_eleven.name"], "location_modifier", TEXT["info.double_eleven.description"], location_id="courier_station"),
    "medical_samples": InformationTemplate("medical_samples", TEXT["info.medical_samples.name"], "location_modifier", TEXT["info.medical_samples.description"], location_id="county_hospital"),
    "er_disturbance": InformationTemplate("er_disturbance", TEXT["info.er_disturbance.name"], "location_modifier", TEXT["info.er_disturbance.description"], location_id="county_hospital"),
    "clerk_gaming": InformationTemplate("clerk_gaming", TEXT["info.clerk_gaming.name"], "location_modifier", TEXT["info.clerk_gaming.description"], location_id="convenience_store"),
    "cold_chain": InformationTemplate("cold_chain", TEXT["info.cold_chain.name"], "location_modifier", TEXT["info.cold_chain.description"], location_id="convenience_store"),
    "shelf_collapse": InformationTemplate("shelf_collapse", TEXT["info.shelf_collapse.name"], "location_modifier", TEXT["info.shelf_collapse.description"], location_id="supermarket"),
    "late_inventory": InformationTemplate("late_inventory", TEXT["info.late_inventory.name"], "location_modifier", TEXT["info.late_inventory.description"], location_id="supermarket"),
    "lost_nebula_kit": InformationTemplate("lost_nebula_kit", TEXT["info.lost_nebula_kit.name"], "material_reward", TEXT["info.lost_nebula_kit.description"], location_id="county_hospital", reward_ids=("nebula_surgery", "rescue_cart")),
    "unclaimed_phone": InformationTemplate("unclaimed_phone", TEXT["info.unclaimed_phone.name"], "material_reward", TEXT["info.unclaimed_phone.description"], location_id="convenience_store", reward_ids=("smartphone",)),
    "disturbing_picture_book": InformationTemplate("disturbing_picture_book", TEXT["info.disturbing_picture_book.name"], "material_reward", TEXT["info.disturbing_picture_book.description"], location_id="supermarket", reward_ids=("nebula_legend",)),
    "valuable_package": InformationTemplate("valuable_package", TEXT["info.valuable_package.name"], "material_reward", TEXT["info.valuable_package.description"], location_id="courier_station", reward_ids=("gramophone",)),
}

LOCATION_INFORMATION_MODIFIERS = {
    "courier_absent": {"tag:fragile": 4.0, "quality:high": 2.0, "uses": 5},
    "double_eleven": {"quality:purple": 2.0, "quality:gold": 3.0, "quality:red": 6.0, "uses": 3},
    "medical_samples": {"tag:medicine_kit": 2.5, "quality:gold_plus": 3.0, "uses": 3},
    "er_disturbance": {"tag:surgery_kit": 3.0, "quality:high": 6.0, "turns": 2},
    "clerk_gaming": {"tag:snack": 2.5, "quality:blue_plus": 6.0, "uses": 4},
    "cold_chain": {"tag:food": 2.0, "quality:high": 3.0, "uses": 2},
    "shelf_collapse": {"tag:tool": 4.0, "quality:low": 2.5, "tag:fragile": 2.0, "turns": 3},
    "late_inventory": {"tag:tool": 3.0, "quality:blue_plus": 2.5, "uses": 5},
}


# ---------------------------------------------------- state template effects
def _resolve_good_talk(engine: object, info: object, targets: list[object]) -> None:
    if info.status == "confirmed":
        for target in targets:
            engine._restore_sanity(target, 10, info.title)


def _resolve_odd_smile(engine: object, info: object, targets: list[object]) -> None:
    if info.status == "refuted":
        engine._restore_sanity(targets[0], 10, info.title)
        engine._strengthen_named_emotion(targets[0], "focus", 2, 2, info.title)


def _resolve_tense_nerves(engine: object, info: object, targets: list[object]) -> None:
    if info.status == "confirmed":
        engine._strengthen_named_emotion(targets[0], "panic", 1, 2, info.title)
        if len(targets) > 1:
            engine._damage_health(targets[1], 5, info.title)
    elif info.status == "refuted":
        for target in targets:
            engine._restore_sanity(target, 5, info.title)
            engine._adjust_emotion_set(target, "awakening", 2, 2, info.title)


def _resolve_suppressed_sobbing(
    engine: object, info: object, targets: list[object]
) -> None:
    if info.status == "confirmed":
        engine._damage_sanity(targets[0], 10, info.title)
        engine._strengthen_emotion_set(targets[0], "erosion", 2, 3, info.title)
    elif info.status == "refuted":
        engine._restore_sanity(targets[0], 15, info.title)
        engine._strengthen_emotion_set(targets[0], "awakening", 2, 3, info.title)


def _resolve_moment_peace(engine: object, info: object, targets: list[object]) -> None:
    if info.status == "confirmed":
        engine._restore_sanity(targets[0], 15, info.title)
        if len(targets) > 1:
            engine._restore_health(targets[1], 5, info.title)
            engine._restore_sanity(targets[1], 10, info.title)
            # 原稿「宽慰 2/3」未定义效果，改用已有的觉醒情绪「满足」承载。
            targets[1].set_status("satisfaction", intensity=2, layers=3)


def _resolve_supply_dispute(
    engine: object, info: object, targets: list[object]
) -> None:
    if info.status == "confirmed":
        for target in targets:
            engine._consume_sanity(target, 10, info.title)
    elif info.status == "refuted":
        for target in targets:
            engine._restore_sanity(target, 15, info.title)
            engine._set_condition(target, target.condition("trust"), 2, 3, info.title)


def _pending_good_talk(engine: object, info: object, targets: list[object]) -> None:
    for target in targets:
        engine._restore_sanity(target, 2, info.title)


def _pending_odd_smile(engine: object, info: object, targets: list[object]) -> None:
    if targets:
        engine._consume_sanity(targets[0], 2, info.title)


def _pending_tense_nerves(engine: object, info: object, targets: list[object]) -> None:
    if targets:
        engine._extend_condition(
            targets[0], targets[0].condition("panic"), 2, info.title
        )


def _pending_moment_peace(engine: object, info: object, targets: list[object]) -> None:
    for target in targets:
        engine._reduce_emotion_set(target, "erosion", 1, 1)


def _pending_supply_dispute(
    engine: object, info: object, targets: list[object]
) -> None:
    for target in targets:
        engine._consume_sanity(target, 3, info.title)


# 状态类信息模板：声明「核验结算」与「待验证持续影响」两类效果函数。
INFORMATION_STATE_EFFECTS: dict[str, dict[str, object]] = {
    "good_talk": {
        "resolve": _resolve_good_talk,
        "pending": _pending_good_talk,
    },
    "odd_smile": {
        "resolve": _resolve_odd_smile,
        "pending": _pending_odd_smile,
    },
    "tense_nerves": {
        "resolve": _resolve_tense_nerves,
        "pending": _pending_tense_nerves,
    },
    "suppressed_sobbing": {
        "resolve": _resolve_suppressed_sobbing,
        "pending": None,
    },
    "moment_peace": {
        "resolve": _resolve_moment_peace,
        "pending": _pending_moment_peace,
    },
    "supply_dispute": {
        "resolve": _resolve_supply_dispute,
        "pending": _pending_supply_dispute,
    },
}


def register_state_effect(
    template_id: str, resolve: object, pending: object
) -> None:
    """登记某信息模板的核验/待验证效果（供内容模块就近声明）。"""
    INFORMATION_STATE_EFFECTS[template_id] = {"resolve": resolve, "pending": pending}


def register_information_template(
    template: InformationTemplate, *, replace: bool = False
) -> None:
    """登记一条动态信息模板；``replace=True`` 时覆盖同 id（内容包优先级用）。"""
    if template.id in INFORMATION_TEMPLATES and not replace:
        raise ValueError(TEXT["data.information.register_information_template.1"].format(p1=template.id))
    INFORMATION_TEMPLATES[template.id] = template


def register_location_modifier(template_id: str, modifier: dict[str, float]) -> None:
    """登记一条地点信息修正（须先有对应模板）。"""
    if template_id not in INFORMATION_TEMPLATES:
        raise ValueError(TEXT["data.information.register_location_modifier.1"].format(p1=template_id))
    LOCATION_INFORMATION_MODIFIERS[template_id] = dict(modifier)

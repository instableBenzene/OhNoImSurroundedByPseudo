"""动态信息模板与地点信息修正表。"""

from .types import InformationTemplate

INFORMATION_TEMPLATES = {
    "discarded_briefcase": InformationTemplate("discarded_briefcase", "被丢弃的公文包", "material_reward", "医药代表的急救展示公文包被丢在[地点]。", reward_ids=("meteor_plan",)),
    "secret_raid": InformationTemplate("secret_raid", "绝密小镇跑刀之旅", "material_reward", "一盒奢华进口巧克力被丢在[地点]。", reward_ids=("fiji_chocolate",)),
    "lost_return": InformationTemplate("lost_return", "退货途中的遗失物", "material_reward", "物流员在[地点]弄丢了一件特种防寒服。", reward_ids=("polar_jacket",)),
    "security_backup": InformationTemplate("security_backup", "私拷的安防备份", "material_reward", "安保人员在[地点]藏了监控备份。", reward_ids=("video_tape",)),
    "good_talk": InformationTemplate("good_talk", "投缘的交谈", "state", "A和B聊得很投缘。", "A、B回合末各回复2理智。", "A、B立即各回复10理智。", "无。"),
    "odd_smile": InformationTemplate("odd_smile", "深夜的诡异微笑", "state", "A在镜子前练习自然地微笑。", "A回合末额外消耗2理智。", "无。", "A回复10理智，专注强化2、延长2。"),
    "tense_nerves": InformationTemplate("tense_nerves", "紧绷的神经", "state", "A死死盯着B并攥着尖锐工具。", "A回合末恐慌延长2。", "A恐慌+1/+2，B受到5生命伤害。", "A、B各回复5理智且觉醒情绪+2/+2。"),
    "suppressed_sobbing": InformationTemplate("suppressed_sobbing", "压抑的抽泣", "state", "A反锁房门后传来抽泣。", "无。", "A受到10理智伤害，侵蚀情绪恶化2、延长3。", "A回复15理智，觉醒情绪强化2、延长3。"),
    "moment_peace": InformationTemplate("moment_peace", "片刻的宁静", "state", "A帮助B处理伤口。", "A、B回合末侵蚀情绪-1/-1。", "A回复15理智；B回复5生命、10理智并获得宽慰2/3。", "无。"),
    "supply_dispute": InformationTemplate("supply_dispute", "物资分配争端", "state", "A和B因罐头分配争吵。", "A、B回合末理智消耗+3。", "A、B立即消耗10理智。", "A、B各回复15理智并获得信任2/3。"),
    "courier_absent": InformationTemplate("courier_absent", "驿站老板旷工事件", "location_modifier", "县快递驿站无人看管。", location_id="courier_station"),
    "double_eleven": InformationTemplate("double_eleven", "“双11”驿站爆仓", "location_modifier", "贵重快递被放在无人照看的篮子里。", location_id="courier_station"),
    "medical_samples": InformationTemplate("medical_samples", "集采药物样品推广", "location_modifier", "医院展示柜有高级试用品。", location_id="county_hospital"),
    "er_disturbance": InformationTemplate("er_disturbance", "急诊科夜间医闹", "location_modifier", "急诊清创室和药房防线空虚。", location_id="county_hospital"),
    "clerk_gaming": InformationTemplate("clerk_gaming", "夜班店员沉迷游戏", "location_modifier", "便利店店员沉迷手游。", location_id="convenience_store"),
    "cold_chain": InformationTemplate("cold_chain", "冷链运输车卸货失误", "location_modifier", "高档巧克力和便当被留在店外。", location_id="convenience_store"),
    "shelf_collapse": InformationTemplate("shelf_collapse", "五金区货架倒塌", "location_modifier", "超市五金区暂时无人看守。", location_id="supermarket"),
    "late_inventory": InformationTemplate("late_inventory", "深夜闭店盘点", "location_modifier", "备用工具被随意放在推车里。", location_id="supermarket"),
    "lost_nebula_kit": InformationTemplate("lost_nebula_kit", "遗落的星云手术包", "material_reward", "医院VIP病房遗落最高级医疗物资。", location_id="county_hospital", reward_ids=("nebula_surgery", "rescue_cart")),
    "unclaimed_phone": InformationTemplate("unclaimed_phone", "无主失物招领", "material_reward", "便利店冰柜顶有一台无主手机。", location_id="convenience_store", reward_ids=("smartphone",)),
    "disturbing_picture_book": InformationTemplate("disturbing_picture_book", "令人不安的绘本", "material_reward", "超市儿童区有一本无条码旧书。", location_id="supermarket", reward_ids=("nebula_legend",)),
    "valuable_package": InformationTemplate("valuable_package", "贵重的包裹", "material_reward", "驿站深处有无单号木箱。", location_id="courier_station", reward_ids=("gramophone",)),
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


# 状态类信息模板：声明“核验结算”与“待验证持续影响”两类效果函数。
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
        raise ValueError(f"信息模板 ID 重复：{template.id}")
    INFORMATION_TEMPLATES[template.id] = template


def register_location_modifier(template_id: str, modifier: dict[str, float]) -> None:
    """登记一条地点信息修正（须先有对应模板）。"""
    if template_id not in INFORMATION_TEMPLATES:
        raise ValueError(f"未知信息模板：{template_id}")
    LOCATION_INFORMATION_MODIFIERS[template_id] = dict(modifier)

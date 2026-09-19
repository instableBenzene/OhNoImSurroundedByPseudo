"""伪人档案与场景运行时：深潜者祭司-洋葱（人类形态：葱头）。

definition：静态档案；modifier/function：见后续场景迁移。
"""

from weiren_game.probability import resolve

from dataclasses import dataclass

from ..types import PseudoDefinition
from weiren_game.lifecycle import AbilityLaunch
from weiren_game.data.lang import TEXT

DEFINITION = PseudoDefinition(
    "pseudo_onion",
    TEXT["pseudo.pseudo_onion.name"],
    "onion",
    TEXT["pseudo.pseudo_onion.description"],
    TEXT["pseudo.pseudo_onion.breakthrough"],
    TEXT["pseudo.pseudo_onion.liberation"],
    mark_field="whisper_marks",
    mark_label=TEXT["pseudo.pseudo_onion.mark_label"],
)


@dataclass
class OnionState:
    """洋葱场景专属状态：低语印记与安全低语计数。"""

    whisper_marks: int = 0
    whisper_count: int = 0
    safe_irritation_whispers: int = 0
    safe_health_whispers: int = 0
    resolving_skill: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "OnionState":
        """从字典还原 OnionState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "whisper_marks": self.whisper_marks,
            "whisper_count": self.whisper_count,
            "safe_irritation_whispers": self.safe_irritation_whispers,
            "safe_health_whispers": self.safe_health_whispers,
            "resolving_skill": self.resolving_skill,
        }


def visit(engine: object) -> None:
    """洋葱到访：按烦躁占比判定「狂喜的邀约」突破。"""
    pseudo = engine.state.pseudo_state
    irritated = sum(1 for t in engine.home_tenants() if t.irritation.active)
    total = max(1, len(engine.home_tenants()))
    ratio = irritated / total
    adjustment = engine._global_event_value("breakthrough.adjust", 0.0)
    engine._consume_global_event("breakthrough.adjust")
    # 越打越难：突破线随来访次数上升，15%/次、上限 75%。
    threshold = min(.75, .15 * pseudo.visit_count) + adjustment * .10
    threshold = min(.95, max(0.0, threshold))
    engine._log(TEXT["data.pseudos.pseudo_onion.visit.1"].format(p1=ratio, p2=threshold))
    if ratio >= threshold:
        if engine._attempt_breakthrough(
            TEXT["data.pseudos.pseudo_onion.visit.2"]
        ):
            return
    engine._log(TEXT["data.pseudos.pseudo_onion.visit.3"])


def cast_whisper(engine: object) -> None:
    """发动洋葱「不可名状的低语」：向 ceil(印记/4) 名房客施加烦躁并推进解放。"""
    import math

    pseudo = engine.state.pseudo_state
    pseudo.resolving_skill = True
    pseudo.whisper_count += 1
    marks = pseudo.whisper_marks
    pseudo.whisper_marks = 0
    engine._observe_pseudo_skill("whisper")
    targets = sorted(
        engine.home_tenants(), key=lambda value: (value.sanity, value.id)
    )
    targets = targets[: max(1, math.ceil(marks / 4))]
    irritation_gained = False
    health_lost = False
    blocked = engine._skill_respond_skill(
        TEXT["data.pseudos.pseudo_onion.cast_whisper.1"], "cast",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
    )
    if blocked:
        targets = []
    # AOE 收成一条：明细由 log 层按形状自动归并（weiren_game/log_shape.py），这里只包一层。
    engine._collect_start()
    for target in targets:
        if engine._skill_respond_skill(
            TEXT["data.pseudos.pseudo_onion.cast_whisper.2"], "lock",
            mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
            target=target, event="onion.whisper",
        ):
            continue
        before_i = target.irritation.intensity + target.irritation.layers
        before_h = target.health
        engine._apply_emotion(target, "irritation", 2, 5, TEXT["data.pseudos.pseudo_onion.cast_whisper.3"])
        irritation_gained |= target.irritation.intensity + target.irritation.layers > before_i
        if target.irritation.intensity >= 5:
            engine._damage_health(target, 10, "deep_whisper")
        health_lost |= target.health < before_h
    engine._collect_flush(title=TEXT["data.pseudos.pseudo_onion.cast_whisper.5"])
    pseudo.safe_irritation_whispers = (
        0 if irritation_gained else pseudo.safe_irritation_whispers + 1
    )
    pseudo.safe_health_whispers = (
        0 if health_lost else pseudo.safe_health_whispers + 1
    )
    pseudo.resolving_skill = False
    engine._log(TEXT["data.pseudos.pseudo_onion.cast_whisper.6"])
    engine._log(
        TEXT["data.pseudos.pseudo_onion.cast_whisper.7"].format(p1=pseudo.safe_irritation_whispers, p2=pseudo.safe_health_whispers)
    )
    if pseudo.safe_irritation_whispers >= 2 or pseudo.safe_health_whispers >= 4:
        pseudo.liberated = True
        # 洋葱解放：结束「情绪显现」的全局揭示。
        engine._consume_global_event(REVEAL_IRRITATION_EVENT)
        engine._finish(
            True,
            TEXT["data.pseudos.pseudo_onion.cast_whisper.8"],
        )


def maybe_whisper(engine: object) -> None:
    """低语印记达阈值且未被压制时自动发动低语。"""
    pseudo = engine.state.pseudo_state
    if pseudo.scenario_id != DEFINITION.id or not pseudo.revealed or pseudo.resolving_skill:
        return
    threshold = max(4, 12 - min(pseudo.visit_count, 8))
    if pseudo.whisper_marks >= threshold and not engine._pseudo_actions_suppressed():
        cast_whisper(engine)


def start_passive(engine: object) -> None:
    """回合初被动：低理智房客可能先兆性地被施加/加重烦躁。"""
    from weiren_game.data import EVENT_IDS

    for tenant in engine.home_tenants():
        if tenant.sanity <= 30 and engine._rng(
            EVENT_IDS["onion.low_sanity"], tenant.id
        ).random() < .20:
            if tenant.irritation.active:
                others = [
                    value for value in engine.home_tenants()
                    if value.id != tenant.id
                ]
                if others:
                    target = engine._rng(
                        EVENT_IDS["onion.low_sanity.target"], tenant.id
                    ).choice(others)
                    engine._worsen_condition(target, target.irritation, 1, TEXT["data.pseudos.pseudo_onion.start_passive.1"])
            else:
                engine._extend_condition(tenant, tenant.irritation, 1, TEXT["data.pseudos.pseudo_onion.start_passive.2"])


def attack_searcher(engine: object, mission: object, tenant: object) -> None:
    """搜索袭击：洋葱「潮汐的诱惑」（烦躁层数与低生命伤害）。"""
    engine._observe_pseudo_skill("tide")
    already = tenant.irritation.active
    engine._apply_emotion(tenant, "irritation", 0, 1, TEXT["data.pseudos.pseudo_onion.attack_searcher.1"])
    if already:
        engine._damage_health(tenant, 5, "tidal_lure")
        engine._worsen_condition(tenant, tenant.irritation, 1, TEXT["data.pseudos.pseudo_onion.attack_searcher.3"])
    engine.defer_search_report(mission, TEXT["data.pseudos.pseudo_onion.attack_searcher.4"].format(p1=engine.character(tenant).name))


# 场景处理器注册表（供伪人协调器查表调用）。
def encounter_chance(engine: object, mission: object, tenant: object) -> float:
    """洋葱场景的基础遭遇率：必中。"""
    return 1.0


def end_sanity_multiplier(engine: object) -> float:
    """洋葱场景的回合末理智倍率：烦躁占比越高消耗越大。"""
    if engine._pseudo_actions_suppressed():
        return 1.0
    return 1.0 + .05 * sum(
        1 for tenant in engine.home_tenants() if tenant.irritation.active
    )


def on_sanity_lost(engine: object, *, tenant: object = None, lost: float = 0.0,
                   change_type: str = "") -> None:
    """理智变化节点：房客流失/消耗/损失理智后累计低语印记并可能发动低语。"""
    pseudo = engine.state.pseudo_state
    if pseudo.scenario_id != DEFINITION.id or lost <= 0:
        return
    if engine._pseudo_actions_suppressed():
        return
    pseudo.whisper_marks += 1
    maybe_whisper(engine)


NODE_HOOKS = {"sanity.lost": on_sanity_lost}


def emotion_end_extra(
    engine: object, tenant: object, condition: object, key: str
) -> None:
    """洋葱场景：回合末烦躁自演化时的追加恶化/延长。"""
    from weiren_game.data import EVENT_IDS

    if (
        key != "irritation"
        or not engine._global_event_active(REVEAL_IRRITATION_EVENT)
        or engine._pseudo_actions_suppressed()
    ):
        return
    chance = resolve(condition.intensity * .05)
    if engine._rng(EVENT_IDS["onion.irritation.extra"], tenant.id).random() < chance:
        engine._worsen_condition(tenant, condition, 1, TEXT["data.pseudos.pseudo_onion.emotion_end_extra.1"])
        engine._extend_condition(tenant, condition, 1, TEXT["data.pseudos.pseudo_onion.emotion_end_extra.2"])


def observed_skills(engine: object) -> tuple[str, ...]:
    """洋葱场景对外可见的技能（id, 展示名），供信息文本与核验使用。"""
    return (("whisper", TEXT["data.pseudos.pseudo_onion.observed_skills.1"]), ("tide", TEXT["data.pseudos.pseudo_onion.observed_skills.2"]))


def progress_text(engine: object) -> str:
    """洋葱场景的进度摘要文本。"""
    pseudo = engine.state.pseudo_state
    return (
        TEXT["data.pseudos.pseudo_onion.progress_text.1"].format(p1=pseudo.whisper_marks, p2=pseudo.safe_irritation_whispers, p3=pseudo.safe_health_whispers)
    )


# 情绪显现-烦躁：以**全局事件**表达"烦躁对屋主可见"（通用键 emotion.reveal.<情绪>），
# 由 engine.emotion_visible 通用读取，因此对之后新接纳的房客同样生效。
from weiren_game.global_event import emotion_reveal_event

REVEAL_IRRITATION_EVENT = emotion_reveal_event("irritation")


def on_emotion_increase(engine: object, tenant: object, key: str) -> None:
    """情绪显现 modifier：烦躁增加时打断「理智的裂隙」的无烦躁安全进度。"""
    pseudo = engine.state.pseudo_state
    if key != "irritation" or engine._pseudo_actions_suppressed():
        return
    # 烦躁打断「理智的裂隙」：有人获得烦躁即重置无烦躁安全进度。
    pseudo.safe_irritation_whispers = 0


def on_first_reveal(engine: object) -> None:
    """情绪显现（揭示部分）：洋葱初访后，烦躁对屋主可见（全局事件，固定 99 回合）。"""
    if engine._pseudo_actions_suppressed():
        return
    engine._set_global_event(REVEAL_IRRITATION_EVENT, 1.0, 99)


def _onion_reveal_gate(context: object) -> object:
    """情绪显现-烦躁（闸门 provider）：初访后烦躁对**所有**房客可见（含新接纳者）。"""
    if not isinstance(context, dict):
        return
    engine = context.get("engine")
    key = context.get("key")
    if engine is None or key != "irritation":
        return
    if not engine._global_event_active(REVEAL_IRRITATION_EVENT):
        return
    yield (
        gate("emotion.visible").path("emotion_visible", "irritation").match("all")
        .source("pseudo_scene", "pseudo_onion", "emotion_reveal").any()
    )


from weiren_game.modifier_rules import gate, register_gate_provider

register_gate_provider("emotion.visible", _onion_reveal_gate)




def card_info(engine: object) -> dict:
    """伪人卡：解放/突破进度 + 技能 + 印记阈值。"""
    ps = engine.state.pseudo_state
    visits = int(getattr(ps, "visit_count", 0))
    home = engine.home_tenants()
    irritated = sum(1 for t in home if t.irritation.active)
    pct = round(100 * irritated / len(home)) if home else 0
    need_pct = min(75, 15 * visits)
    need_marks = max(4, 12 - visits)
    return {
        "liberation": TEXT["data.pseudos.pseudo_onion.card_info.1"].format(p1=getattr(ps,'safe_irritation_whispers',0), p2=getattr(ps,'safe_health_whispers',0)),
        "breakthrough": TEXT["data.pseudos.pseudo_onion.card_info.2"].format(p1=pct, p2=need_pct, p3=visits),
        "mark_need": int(need_marks),
        "skills": [
            {"name": TEXT["data.pseudos.pseudo_onion.card_info.3"], "text": TEXT["data.pseudos.pseudo_onion.card_info.4"],
             "mark": {"label": TEXT["data.pseudos.pseudo_onion.card_info.5"], "current": int(getattr(ps, "whisper_marks", 0)), "need": int(need_marks)}},
            {"name": TEXT["data.pseudos.pseudo_onion.card_info.6"], "text": TEXT["data.pseudos.pseudo_onion.card_info.7"]},
            {"name": TEXT["data.pseudos.pseudo_onion.card_info.8"], "text": TEXT["data.pseudos.pseudo_onion.card_info.9"]},
            {"name": TEXT["data.pseudos.pseudo_onion.card_info.10"], "text": TEXT["data.pseudos.pseudo_onion.card_info.11"]},
            {"name": TEXT["data.pseudos.pseudo_onion.card_info.12"], "text": TEXT["data.pseudos.pseudo_onion.card_info.13"]},
        ],
    }

HANDLERS: dict[str, object] = {
    "visit": visit,
    "cast_whisper": cast_whisper,
    "maybe_whisper": maybe_whisper,
    "start_passive": start_passive,
    "attack_searcher": attack_searcher,
    "encounter_chance": encounter_chance,
    "end_sanity_multiplier": end_sanity_multiplier,
    "emotion_end_extra": emotion_end_extra,
    "observed_skills": observed_skills,
    "progress_text": progress_text,
    "card_info": card_info,
    "on_emotion_increase": on_emotion_increase,
    "on_first_reveal": on_first_reveal,
}


State = OnionState


def _old_echo_sanity_modifier(context: object):
    """旧日的回声：每拥有 1 名烦躁房客，回合末理智消耗 +5%。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    irritated = sum(1 for value in engine.home_tenants() if value.irritation.active)
    if irritated:
        yield spec("sanityConsume").path("turn_end_consume").percent(0.05 * irritated).source("pseudo_ability", "pseudo_onion", "echo_of_the_past")


from weiren_game.modifier_rules import register_modifier_provider as _rego
_rego("sanityConsume", _old_echo_sanity_modifier)

"""伪人档案与场景运行时：深潜者祭司-洋葱（人类形态：葱头）。

definition：静态档案；modifier/function：见后续场景迁移。
"""

from weiren_game.probability import resolve

from dataclasses import dataclass

from ..types import PseudoDefinition
from weiren_game.lifecycle import AbilityLaunch

DEFINITION = PseudoDefinition(
    "pseudo_onion",
    "深潜者祭司-洋葱",
    "onion",
    "绿发遮眼，笑容不自然，低语仿佛来自深海。",
    "来访时屋内烦躁房客占比≥15%×来访次数（上限75%）。",
    "连续两次低语无人获得烦躁，或连续四次低语无人因技能损失生命。",
    mark_field="whisper_marks",
    mark_label="低语印记-洋葱",
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
    engine._log(f"狂喜的邀约：烦躁房客占比{ratio:.0%}，突破线{threshold:.0%}。")
    if ratio >= threshold:
        if engine._attempt_breakthrough(
            "烦躁情绪达到邀约条件，深潜者祭司完成突破。"
        ):
            return
    engine._log("洋葱本次到访未突破；低语仍只会在低语印记达到阈值时发动。")


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
        "不可名状的低语", "cast",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
    )
    if blocked:
        targets = []
    # AOE 收成一条：逐人播报会刷屏，这里只播一条汇总 + 可点开的三列明细。
    engine._collect_start()
    rows: list[dict] = []
    for target in targets:
        if engine._skill_respond_skill(
            "不可名状的低语", "lock",
            mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
            target=target, event="onion.whisper",
        ):
            continue
        before_i = target.irritation.intensity + target.irritation.layers
        before_h = target.health
        engine._apply_emotion(target, "irritation", 2, 5, "深潜低语")
        irritation_gained |= target.irritation.intensity + target.irritation.layers > before_i
        gained = target.irritation.intensity + target.irritation.layers - before_i
        if gained > 0:
            rows.append({"label": engine.character(target).name,
                         "value": "+%d 烦躁" % gained, "note": "不可名状的低语"})
        if target.irritation.intensity >= 5:
            engine._damage_health(target, 10, "深潜低语")
        health_lost |= target.health < before_h
        if target.health < before_h:
            rows.append({"label": engine.character(target).name,
                         "value": "−%g 生命" % (before_h - target.health),
                         "note": "不可名状的低语"})
    engine._collect_flush(f"不可名状的低语：{len(rows)} 项变化。", rows=rows)
    pseudo.safe_irritation_whispers = (
        0 if irritation_gained else pseudo.safe_irritation_whispers + 1
    )
    pseudo.safe_health_whispers = (
        0 if health_lost else pseudo.safe_health_whispers + 1
    )
    pseudo.resolving_skill = False
    engine._log("洋葱发动「不可名状的低语」。")
    engine._log(
        f"理智的裂隙：连续无烦躁{pseudo.safe_irritation_whispers}/2，"
        f"连续无生命损失{pseudo.safe_health_whispers}/4。"
    )
    if pseudo.safe_irritation_whispers >= 2 or pseudo.safe_health_whispers >= 4:
        pseudo.liberated = True
        # 洋葱解放：结束「情绪显现」的全局揭示。
        engine._consume_global_event(REVEAL_IRRITATION_EVENT)
        engine._finish(
            True,
            "房客们守住心智，来自深海的低语失去回响；理智的裂隙闭合，洋葱得到解放。",
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
                    engine._worsen_condition(target, target.irritation, 1, "先兆低语")
            else:
                engine._extend_condition(tenant, tenant.irritation, 1, "先兆低语")


def attack_searcher(engine: object, mission: object, tenant: object) -> None:
    """搜索袭击：洋葱「潮汐的诱惑」（烦躁层数与低生命伤害）。"""
    engine._observe_pseudo_skill("tide")
    already = tenant.irritation.active
    engine._apply_emotion(tenant, "irritation", 0, 1, "潮汐的诱惑")
    if already:
        engine._damage_health(tenant, 5, "潮汐的诱惑")
        engine._worsen_condition(tenant, tenant.irritation, 1, "潮汐的诱惑")
    engine.defer_search_report(mission, f"伪人袭击：{engine.character(tenant).name}听见了海潮般的诱惑。")


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
        engine._worsen_condition(tenant, condition, 1, "情绪显现-烦躁")
        engine._extend_condition(tenant, condition, 1, "情绪显现-烦躁")


def observed_skills(engine: object) -> tuple[str, ...]:
    """洋葱场景对外可见的技能（id, 展示名），供信息文本与核验使用。"""
    return (("whisper", "不可名状的低语"), ("tide", "潮汐的诱惑"))


def progress_text(engine: object) -> str:
    """洋葱场景的进度摘要文本。"""
    pseudo = engine.state.pseudo_state
    return (
        f"低语印记{pseudo.whisper_marks}，安全路线"
        f"{pseudo.safe_irritation_whispers}/2或{pseudo.safe_health_whispers}/4"
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
        gate("emotion.visible").path("显示情绪", "irritation").match("all")
        .source("伪人场景", "洋葱", "情绪显现").any()
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
        "liberation": f"理智的裂隙：连续无烦躁 {getattr(ps,'safe_irritation_whispers',0)}/2 · 连续无生命损失 {getattr(ps,'safe_health_whispers',0)}/4",
        "breakthrough": f"狂喜的邀约：烦躁占比 {pct}%/{need_pct}%（已到访 {visits} 次）",
        "mark_need": int(need_marks),
        "skills": [
            {"name": "不可名状的低语", "text": "消耗低语印记：向约 ceil(印记/4) 名房客施加烦躁并推进解放。",
             "mark": {"label": "低语印记", "current": int(getattr(ps, "whisper_marks", 0)), "need": int(need_marks)}},
            {"name": "潮汐的诱惑", "text": "搜索袭击：施加烦躁层数并造成少量生命伤害。"},
            {"name": "情绪显现-烦躁", "text": "初访后屋主可见所有房客的烦躁；烦躁每回合可能恶化/延长。"},
            {"name": "旧日的回声", "text": "每有 1 名烦躁房客，全员回合末理智消耗 +5%。"},
            {"name": "先兆低语", "text": "回合初，理智 ≤30 的房客可能被先兆性施加/加重烦躁。"},
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
        yield spec("sanityConsume").path("回合末消耗").percent(0.05 * irritated).source("伪人技能", "伪人洋葱", "旧日的回声")


from weiren_game.modifier_rules import register_modifier_provider as _rego
_rego("sanityConsume", _old_echo_sanity_modifier)

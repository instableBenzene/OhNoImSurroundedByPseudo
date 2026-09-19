"""伪人档案与场景运行时：无眠怪医-苯环（人类形态：苯环）。

definition：静态档案；场景运行时（到访、死亡恐惧、诅咒结算等）均在本文件，
由 SCENARIO_HANDLERS 按 handler 名分发。
"""

from dataclasses import dataclass

from ..types import PseudoDefinition
from weiren_game.lifecycle import AbilityLaunch
from weiren_game.data.lang import TEXT

DEFINITION = PseudoDefinition(
    "pseudo_benzene",
    TEXT["pseudo.pseudo_benzene.name"],
    "benzene",
    TEXT["pseudo.pseudo_benzene.description"],
    TEXT["pseudo.pseudo_benzene.breakthrough"],
    TEXT["pseudo.pseudo_benzene.liberation"],
    mark_field="fear_marks",
    mark_label=TEXT["pseudo.pseudo_benzene.mark_label"],
)


@dataclass
class BenzeneState:
    """苯环场景专属状态：恐惧印记与诅咒相关计数。"""

    fear_marks: int = 0
    curse_count: int = 0
    # 两次来访之间的死亡数（突破判定用；来访时清零）
    deaths_since_last_visit: int = 0
    # 「早交班」解放进度：连续无人休克 / 连续无人死亡
    safe_no_shock_streak: int = 0
    safe_no_death_streak: int = 0
    death_since_last_curse: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "BenzeneState":
        """从字典还原 BenzeneState。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "fear_marks": self.fear_marks,
            "curse_count": self.curse_count,
            "deaths_since_last_visit": self.deaths_since_last_visit,
            "safe_no_shock_streak": self.safe_no_shock_streak,
            "safe_no_death_streak": self.safe_no_death_streak,
            "death_since_last_curse": self.death_since_last_curse,
        }


def death_fear_sanity_bonus(engine: object, tenant: object) -> int:
    """死亡恐惧：初访后，生命≤50 房客回合末理智消耗 +2（≤25 则 +5）。

    使用处：round_effects 的回合末基础理智消耗计算。
    """
    pseudo = engine.state.pseudo_state
    if pseudo.scenario_id != DEFINITION.id or not pseudo.revealed:
        return 0
    if not engine._pseudo_capability("cast"):
        return 0
    if tenant.health > 50:
        return 0
    return 5 if tenant.health <= 25 else 2


def curse_threshold_value(engine: object) -> int:
    """当前恐惧印记达到多少层时自动释放诅咒。"""
    pseudo = engine.state.pseudo_state
    return max(2, 6 - min(pseudo.visit_count, 4))


def maybe_curse(engine: object) -> bool:
    """恐惧印记满即自动释放诅咒（独立于来访）。

    使用处：恐惧印记增加处（如访客到达 visitor_mark）与到访结算。
    """
    pseudo = engine.state.pseudo_state
    if not pseudo.revealed or not engine._pseudo_capability("cast"):
        return False
    if pseudo.fear_marks >= curse_threshold_value(engine):
        cast_curse(engine)
        return True
    return False


def visit(engine: object) -> None:
    """苯环到访：按屋内人数判定「夜间查房」突破，或按恐惧印记决定是否诅咒。

    使用处：pseudo_system._resolve_pseudo_visit 的苯环分发。
    """
    pseudo = engine.state.pseudo_state
    adjustment = engine._global_event_value("breakthrough.adjust", 0.0)
    engine._consume_global_event("breakthrough.adjust")
    threshold = max(0.0, min(5.0, 9.0 - pseudo.visit_count)) + adjustment
    shocked = sum(1 for value in engine.home_tenants() if value.shock)
    interval_deaths = pseudo.deaths_since_last_visit
    score = interval_deaths + shocked
    pseudo.deaths_since_last_visit = 0
    engine._log(
        TEXT["data.pseudos.pseudo_benzene.visit.1"].format(p1=interval_deaths, p2=shocked, p3=threshold)
    )
    if score > threshold:
        engine._attempt_breakthrough(
            TEXT["data.pseudos.pseudo_benzene.visit.2"]
        )
        return
    if not maybe_curse(engine):
        engine._log(
            TEXT["data.pseudos.pseudo_benzene.visit.3"].format(p1=pseudo.fear_marks, p2=curse_threshold_value(engine))
        )


def cast_curse(engine: object) -> None:
    """发动苯环「希波克拉底诅咒」：消耗恐惧印记伤害房客，推进解放。

    使用处：pseudo_system 的到访与强制主动能力分发。
    """
    from weiren_game.data import EVENT_IDS

    pseudo = engine.state.pseudo_state
    spent = pseudo.fear_marks
    pseudo.fear_marks = 0
    pseudo.curse_count += 1
    engine._observe_pseudo_skill("curse")
    engine._log(TEXT["data.pseudos.pseudo_benzene.cast_curse.1"].format(p1=spent))
    blocked = engine._skill_respond_skill(
        TEXT["data.pseudos.pseudo_benzene.cast_curse.2"], "cast",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
    )
    resistant_ids: set[str] = set()
    # AOE 收成一条：明细由 log 层按形状自动归并（weiren_game/log_shape.py），这里只包一层。
    engine._collect_start()
    if not blocked:
        for tenant in list(engine.home_tenants()):
            if engine._skill_respond_skill(
                TEXT["data.pseudos.pseudo_benzene.cast_curse.3"], "lock",
                mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
                target=tenant, event="benzene.curse",
            ):
                resistant_ids.add(tenant.id)
                continue
            engine._damage_health(tenant, 15, "hippocratic_curse")
        repeats = max(0, 10 - spent) * len(engine.home_tenants())
        for index in range(repeats):
            targets = [
                value for value in engine.home_tenants()
                if value.id not in resistant_ids
            ]
            if not targets:
                break
            # 每次重复随机选人；一次效果：50% 强度+1 / 50% 层数+1（强度已满则层数+1）。
            picker = engine._rng(EVENT_IDS["benzene.curse.target"], index).random()
            target = targets[min(len(targets) - 1, int(picker * len(targets)))]
            condition = (
                target.trauma
                if engine._rng(EVENT_IDS["benzene.curse.status"], index).random() < .5
                else target.disorder
            )
            if condition.intensity < 10 and engine._rng(
                EVENT_IDS["benzene.curse.layer"], index
            ).random() < .5:
                condition.intensity = min(10, condition.intensity + 1)
                if condition.layers == 0:
                    condition.layers = 1
            else:
                condition.layers = min(99, condition.layers + 1)
                if condition.intensity == 0:
                    condition.intensity = 1
    engine._collect_flush(title=TEXT["data.pseudos.pseudo_benzene.cast_curse.5"])
    home = engine.home_tenants()
    if any(value.shock for value in home):
        pseudo.safe_no_shock_streak = 0
    else:
        pseudo.safe_no_shock_streak += 1
    if pseudo.death_since_last_curse:
        pseudo.safe_no_death_streak = 0
    else:
        pseudo.safe_no_death_streak += 1
    pseudo.death_since_last_curse = False
    engine._log(
        TEXT["data.pseudos.pseudo_benzene.cast_curse.6"].format(p1=pseudo.safe_no_shock_streak, p2=pseudo.safe_no_death_streak)
    )
    if pseudo.safe_no_shock_streak >= 5 or pseudo.safe_no_death_streak >= 7:
        pseudo.liberated = True
        engine._finish(
            True,
            TEXT["data.pseudos.pseudo_benzene.cast_curse.7"],
        )


def attack_searcher(engine: object, mission: object, tenant: object) -> None:
    """搜索袭击：苯环「精湛刀艺」（创伤+2/+2 与 15 生命伤害）。"""
    engine._observe_pseudo_skill("precision")
    engine._worsen_condition(tenant, tenant.trauma, 2, TEXT["data.pseudos.pseudo_benzene.attack_searcher.1"])
    engine._extend_condition(tenant, tenant.trauma, 2, TEXT["data.pseudos.pseudo_benzene.attack_searcher.2"])
    engine._damage_health(tenant, 15, "master_blade")
    engine.defer_search_report(mission, TEXT["data.pseudos.pseudo_benzene.attack_searcher.4"].format(p1=engine.character(tenant).name))


# 场景处理器注册表（供伪人协调器查表调用）。
def visitor_mark(engine: object) -> None:
    """苯环场景：访客到达时若已揭示且未压制，累加恐惧印记。"""
    pseudo = engine.state.pseudo_state
    if pseudo.revealed and not engine._pseudo_actions_suppressed():
        pseudo.fear_marks += 1
        maybe_curse(engine)


def tenant_death(engine: object) -> None:
    """苯环场景：房客死亡累计「区间死亡数」并打断「早交班」进度。"""
    if engine.state.pseudo_state.revealed:
        engine.state.pseudo_state.deaths_since_last_visit += 1
        engine.state.pseudo_state.death_since_last_curse = True


def encounter_chance(engine: object, mission: object, tenant: object) -> float:
    """苯环场景的基础遭遇率：易危者必中，否则按地点加成。"""
    from weiren_game.data import LOCATIONS

    vulnerable = (
        tenant.health <= 50
        or tenant.trauma.active
        or tenant.disorder.active
    )
    if vulnerable:
        return 1.0
    return .15 + LOCATIONS[mission.location_id].encounter_bonus


def observed_skills(engine: object) -> tuple[str, ...]:
    """苯环场景对外可见的技能（id, 展示名），供信息文本与核验使用。"""
    return (("curse", TEXT["data.pseudos.pseudo_benzene.observed_skills.1"]), ("precision", TEXT["data.pseudos.pseudo_benzene.observed_skills.2"]))


def progress_text(engine: object) -> str:
    """苯环场景的进度摘要文本。"""
    pseudo = engine.state.pseudo_state
    return (
        TEXT["data.pseudos.pseudo_benzene.progress_text.1"].format(p1=pseudo.fear_marks, p2=pseudo.safe_no_shock_streak, p3=pseudo.safe_no_death_streak)
    )




def card_info(engine: object) -> dict:
    """伪人卡：解放/突破进度 + 技能 + 印记阈值（供界面显示）。"""
    ps = engine.state.pseudo_state
    visits = int(getattr(ps, "visit_count", 0))
    threshold = curse_threshold_value(engine)
    shock = sum(1 for t in engine.home_tenants() if getattr(t, "shock", 0))
    need = max(0, min(5, 9 - visits))
    return {
        "liberation": TEXT["data.pseudos.pseudo_benzene.card_info.1"].format(p1=getattr(ps,'safe_no_shock_streak',0), p2=getattr(ps,'safe_no_death_streak',0)),
        "breakthrough": TEXT["data.pseudos.pseudo_benzene.card_info.2"].format(p1=getattr(ps,'deaths_since_last_visit',0)+shock, p2=need, p3=visits),
        "mark_need": int(threshold),
        "skills": [
            {"name": TEXT["data.pseudos.pseudo_benzene.card_info.3"], "text": TEXT["data.pseudos.pseudo_benzene.card_info.4"],
             "mark": {"label": TEXT["data.pseudos.pseudo_benzene.card_info.5"], "current": int(getattr(ps, "fear_marks", 0)), "need": int(threshold)}},
            {"name": TEXT["data.pseudos.pseudo_benzene.card_info.6"], "text": TEXT["data.pseudos.pseudo_benzene.card_info.7"]},
            {"name": TEXT["data.pseudos.pseudo_benzene.card_info.8"], "text": TEXT["data.pseudos.pseudo_benzene.card_info.9"]},
        ],
    }

HANDLERS: dict[str, object] = {
    "visit": visit,
    "cast_curse": cast_curse,
    "attack_searcher": attack_searcher,
    "visitor_mark": visitor_mark,
    "tenant_death": tenant_death,
    "encounter_chance": encounter_chance,
    "observed_skills": observed_skills,
    "progress_text": progress_text,
    "card_info": card_info,
    "end_turn_sanity_bonus": death_fear_sanity_bonus,
}


State = BenzeneState

# 默认伪人（内容自声明，核心不写死 id）。
DEFAULT_PSEUDO = True

"""伪人档案与场景运行时：无法收敛的漏洞体-STAR（人类形态：STAR）。

主题：**漏洞 / AI 幻觉**——它不伤你，它让你的系统出错。
它只有一个度量：**焦虑**（本体现成侵蚀情绪）。不新增状态、不新增计数器体系。

"""

from dataclasses import dataclass

from weiren_game.data.types import PseudoDefinition
from weiren_game.lifecycle import AbilityLaunch


# ---------------------------------------------------------------- 可调数值
# 调参方向见 DESIGN.md §9。

BREAKTHROUGH_LINE = 6        # 突破：某房客焦虑强度 >= 此值即突破。调低=更容易输
INTERRUPT_LINE = 5           # 打断：峰值 >= 此值即清空解放进度（但不突破）。必须 < BREAKTHROUGH_LINE
SAFE_BASE_LINE = 5           # 解放进度 0 时的安全线。实际安全线 = max(SAFE_MIN_LINE, 此值 - streak)
SAFE_MIN_LINE = 3            # 安全线下限（进度满时用）。必须 < INTERRUPT_LINE
SAFE_VISITS_NEEDED = 3       # 连续达标几次即解放。调低=更容易赢

VISIT_LOW_INTENSITY = 2      # 到访：给非峰值房客的强度。调高=压力更大（也更容易触发开枪）
VISIT_LOW_LAYERS = 3         # 到访：给非峰值房客的层数。需 ≥ 到访间隔，否则会被回合末衰减抹掉
VISIT_LOW_TARGETS = 2        # 到访：最多给几人

SHOT_TRIGGER_INTENSITY = 3   # 恐吓射击：峰值 >= 此值时开枪
SHOT_ADD_INTENSITY = 2       # 恐吓射击：给峰值的强度
SHOT_BLOCK_TURNS = 2         # 恐吓射击：令接下来几回合没有人类访客

ENCOUNTER_BASE = 0.30        # 搜索遭遇率基数
ENCOUNTER_PER_VISIT = 0.10   # 搜索遭遇率：每次到访递增
ENCOUNTER_ADD_INTENSITY = 2  # 搜索遭遇：给搜索者的强度
ENCOUNTER_ADD_LAYERS = 1     # 搜索遭遇：给搜索者的层数
ENCOUNTER_LOOT_LOSS_CHANCE = 0.50  # 搜索遭遇：丢失 1 件携带物资的概率

# 文案（计算机故障语汇：注入 / 泄漏 / 堆栈 / 执行 / 回滚）
NAME_PSEUDO = "无法收敛的漏洞体-STAR"
NAME_BREAKTHROUGH = "任意代码执行"
NAME_LIBERATION = "强制回滚"
NAME_SHOT = "恐吓射击"
NAME_VISIT = "提示词污染"
NAME_SEARCH = "上下文泄漏"
MARK_LABEL = "异常堆栈-漏洞体"
# ⚠️ 本模块的**玩家可见文案不得引用人类形态的任何机制**
# （复合生化电池 / 流星信标 / 掩护射击 / 压制射击……）。
# 原因：**同一原型的人类与伪人在同一局里不会同时出现**——这是本体机制，
# `engine.py` 用 `{v.human_character_id for v in PSEUDOS.values()}` 把伪人的人类形态
# 从开局池里排除。所以玩家读伪人图鉴时手里不可能有 STAR，
# 写"可被【掩护射击】挡下"这种交叉说明是**对着空集说话**。
# 这条同样适用于「印记保留当写法」之外的任何互指。见 DESIGN.md §7.1。

# 焦虑：本场景唯一使用的情绪
EMOTION = "anxiety"
# 本伪人的事件命名空间（决定论随机的流名）
_EVENT = "dlc.STAR.pseudo"


DEFINITION = PseudoDefinition(
    "pseudo_STAR",
    NAME_PSEUDO,
    "STAR",                  # 人类形态：本 DLC 房客的 tenant_id
    # 外貌/氛围描写。**只在图鉴出现**（`web_ui.codex_state()['pseudos'][i]['desc']`；
    # 对局内的伪人卡不带 desc），所以可以用多行——`mdText` 会把 `\n` 换成 `<br>`。
    #
    # 写法遵循 docs/PRINCIPLES.md：**恐怖来自"不对劲"，不是形容词**。
    # 四行全是可观察的具体偏差，不用「诡异 / 恐怖 / 阴森」这类词：
    #   ① 整体过于整齐  ② 语言层面的不收敛（「漏洞体」）
    #   ③ 有人的形状却没有人的生理痕迹  ④ 记得"是什么"、不记得"是谁"（曾是人类的某物）
    #
    # 引号写法见 docs/STYLE.md §12：指称具体存在（物资名 / 技能名 / 状态名 / 机制名）用「」；
    # 对话与引语才用「「…」」。（旧版的 `mdText` 会在弯引号前硬插换行，那条规则已删。）
    "轮廓比常人更整齐，动作没有多余的停顿，开口的间隔像被校准过。",
    f"来访时屋内最高焦虑强度≥{BREAKTHROUGH_LINE}。",
    f"连续{SAFE_VISITS_NEEDED}次到访，最高焦虑强度依次低于"
    f"{SAFE_BASE_LINE}/{SAFE_BASE_LINE - 1}/{SAFE_MIN_LINE}；"
    f"期间最高焦虑强度≥{INTERRUPT_LINE}则进度重置。",
    mark_field="seed",
    mark_label=MARK_LABEL,
)


# ---------------------------------------------------------------- state
@dataclass
class StarPseudoState:
    """场景专属状态：解放进度。其余计量直接用本体情绪与 visit_count。"""

    streak: int = 0              # 连续"峰值低于安全线"的到访次数
    total_safe_visits: int = 0   # 累计达标次数（仅供卡片展示）

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "StarPseudoState":
        """从字典还原。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {"streak": self.streak, "total_safe_visits": self.total_safe_visits}


# ---------------------------------------------------------------- 内部工具
def _safe_line(streak: int) -> int:
    """当前安全线：进度越高越宽松（递减）。"""
    return max(SAFE_MIN_LINE, SAFE_BASE_LINE - streak)


def _seed(engine: object) -> StarPseudoState:
    """取（必要时补建）场景状态。"""
    return engine.state.pseudo_state.scenario()


def _anxiety(tenant: object) -> int:
    """某房客的焦虑强度。"""
    return int(tenant.condition(EMOTION).intensity)


def _peak(engine: object) -> tuple[object | None, int]:
    """返回（焦虑强度最高的房客，其强度）。无人焦虑时返回 (None, 0)。"""
    best, value = None, 0
    for tenant in engine.home_tenants():
        current = _anxiety(tenant)
        if current > value:
            best, value = tenant, current
    return best, value


def _add_anxiety(engine: object, tenant: object, intensity: int, layers: int) -> bool:
    """给单个房客叠加焦虑。"""
    return bool(engine._apply_emotion(tenant, EMOTION, intensity, layers, NAME_PSEUDO))


def _block_visitors(engine: object) -> None:
    """令接下来若干回合没有人类访客（不影响伪人自己）。"""
    engine._set_global_event("visitor.suppress", 1.0, SHOT_BLOCK_TURNS)


# ---------------------------------------------------------------- handlers
def visit(engine: object) -> None:
    """到访：施加焦虑 → 可能开枪 → 判定突破 → 结算解放进度。"""
    pseudo = engine.state.pseudo_state
    state = _seed(engine)

    _apply_visit_anxiety(engine)
    _maybe_shoot(engine)

    _, value = _peak(engine)
    if value >= BREAKTHROUGH_LINE:
        if engine._attempt_breakthrough(
            f"屋内焦虑失控（峰值 {value}/{BREAKTHROUGH_LINE}），伪人完成突破。"
        ):
            return

    line = _safe_line(state.streak)
    if value >= INTERRUPT_LINE:
        state.streak = 0
        engine._log(f"焦虑峰值 {value} 越过中断线 {INTERRUPT_LINE}，解放进度重置。")
        return
    if value < line:
        state.streak += 1
        state.total_safe_visits += 1
        engine._log(
            f"峰值 {value} 低于安全线 {line}，解放进度 {state.streak}/{SAFE_VISITS_NEEDED}。"
        )
        if state.streak >= SAFE_VISITS_NEEDED:
            pseudo.liberated = True
            engine._finish(
                True,
                "焦虑始终没有失控，伪人的漏洞被彻底摸清；它归于平静，得到解放。",
            )
        return
    engine._log(f"峰值 {value} 未达安全线 {line}，本次到访不推进解放进度。")


def _apply_visit_anxiety(engine: object) -> None:
    """给焦虑最低的若干房客施加轻度焦虑，让多个候选峰值同时生长。

    注意：不能用「焦虑 < 峰值」筛选——首次到访时峰值为 0，会把所有人都排除掉。
    直接取"最不焦虑的几个人"即可（首次到访时即全体最不焦虑）。
    """
    targets = sorted(
        engine.home_tenants(), key=lambda t: (_anxiety(t), t.id)
    )[:VISIT_LOW_TARGETS]
    for tenant in targets:
        if _add_anxiety(engine, tenant, VISIT_LOW_INTENSITY, VISIT_LOW_LAYERS):
            engine._log(
                f"{engine.character(tenant).name}的焦虑被推高"
                f"（+{VISIT_LOW_INTENSITY}/+{VISIT_LOW_LAYERS}）。"
            )


def _maybe_shoot(engine: object) -> None:
    """峰值达到开枪线时发动恐吓射击：推高峰值，并让门外安静下来。"""
    pseudo = engine.state.pseudo_state
    target, value = _peak(engine)
    if target is None or value < SHOT_TRIGGER_INTENSITY:
        return
    engine._observe_pseudo_skill("fright")
    # 施法位压制：伪人被压制时打不出这一枪
    if engine._skill_respond_skill(
        NAME_SHOT, "cast", mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
    ):
        return
    # 目标侧锁定：该房客可能免疫/抵挡
    if engine._skill_respond_skill(
        NAME_SHOT, "lock",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
        target=target, event=f"{_EVENT}.fright",
    ):
        return
    _add_anxiety(engine, target, SHOT_ADD_INTENSITY, 0)
    _block_visitors(engine)
    engine._log(
        f"门外传来一声枪响；{engine.character(target).name}的焦虑骤然升高"
        f"（+{SHOT_ADD_INTENSITY}），一时不会有人敢来敲门。"
    )


def attack_searcher(engine: object, mission: object, tenant: object) -> None:
    """搜索遭遇：对搜索者施加较重焦虑，并可能震落其携带的物资。"""
    pseudo = engine.state.pseudo_state
    engine._observe_pseudo_skill("search_fright")
    if engine._skill_respond_skill(
        NAME_SEARCH, "cast", mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
    ):
        return
    if engine._skill_respond_skill(
        NAME_SEARCH, "lock",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
        target=tenant, event=f"{_EVENT}.search",
    ):
        return
    # 返程抵御：携带物（燧发枪/撬棍等）与角色被动在此生效
    if engine._skill_respond_skill(
        NAME_SEARCH, "resist",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=pseudo,
        target=tenant, mission=mission, event=f"{_EVENT}.search",
    ):
        return

    _add_anxiety(engine, tenant, ENCOUNTER_ADD_INTENSITY, ENCOUNTER_ADD_LAYERS)
    loss = ""
    if mission.rewards and engine._rng(
        f"{_EVENT}.loot", tenant.id
    ).random() < ENCOUNTER_LOOT_LOSS_CHANCE:
        mission.rewards.pop()
        loss = "，并震落了携带的物资"
    engine.defer_search_report(
        mission,
        f"伪人袭击：{engine.character(tenant).name}在暗处听见一声枪响，心神不宁"
        f"（焦虑 +{ENCOUNTER_ADD_INTENSITY}）{loss}。",
    )


def encounter_chance(engine: object, mission: object, tenant: object) -> float:
    """搜索遭遇率：随到访次数上升。"""
    visits = int(getattr(engine.state.pseudo_state, "visit_count", 0))
    return min(0.95, ENCOUNTER_BASE + ENCOUNTER_PER_VISIT * visits)


def observed_skills(engine: object) -> tuple[tuple[str, str], ...]:
    """对外可见的技能（id, 展示名），供信息核验使用。"""
    return (("fright", NAME_SHOT), ("search_fright", NAME_SEARCH))


def progress_text(engine: object) -> str:
    """伪人进度摘要（命令行/日志用）。"""
    state = _seed(engine)
    _, value = _peak(engine)
    return (
        f"焦虑峰值{value}，解放进度{state.streak}/{SAFE_VISITS_NEEDED}"
        f"（安全线{_safe_line(state.streak)}）"
    )


def card_info(engine: object) -> dict:
    """伪人卡：突破/解放进度 + 技能列表。

    卡片正文比图鉴**更短**——面板空间小，只留判据与数字。
    体例：`判据名：当前值/门槛（补充）`。
    """
    pseudo = engine.state.pseudo_state
    state = _seed(engine)
    _, value = _peak(engine)
    return {
        "liberation": (
            f"{NAME_LIBERATION}：连续达标 {state.streak}/{SAFE_VISITS_NEEDED}"
            f"（安全线 {_safe_line(state.streak)}）"
        ),
        "breakthrough": (
            f"{NAME_BREAKTHROUGH}：焦虑峰值 {value}/{BREAKTHROUGH_LINE}"
            f"（已到访 {int(getattr(pseudo, 'visit_count', 0))} 次）"
        ),
        "mark_need": int(INTERRUPT_LINE),
        "skills": [
            {
                "name": NAME_SHOT,
                "text": f"到访时峰值 ≥{SHOT_TRIGGER_INTENSITY} 即发动："
                        f"该房客焦虑 +{SHOT_ADD_INTENSITY}，"
                        f"且 {SHOT_BLOCK_TURNS} 回合内无访客来访。",
                "mark": {
                    "label": "焦虑峰值",
                    "current": value,
                    "need": int(BREAKTHROUGH_LINE),
                },
            },
            {
                "name": NAME_VISIT,
                "text": f"每次到访令 {VISIT_LOW_TARGETS} 名焦虑最低的房客 "
                        f"焦虑 +{VISIT_LOW_INTENSITY}/+{VISIT_LOW_LAYERS}。",
            },
            {
                "name": NAME_SEARCH,
                "text": f"搜索遭遇率 {ENCOUNTER_BASE:.0%} + {ENCOUNTER_PER_VISIT:.0%} × 到访次数；"
                        f"遭遇者焦虑 +{ENCOUNTER_ADD_INTENSITY}/+{ENCOUNTER_ADD_LAYERS}，"
                        f"并有 {ENCOUNTER_LOOT_LOSS_CHANCE:.0%} 概率丢失 1 件携带物资。",
            },
        ],
    }


HANDLERS: dict[str, object] = {
    "visit": visit,
    "attack_searcher": attack_searcher,
    "encounter_chance": encounter_chance,
    "observed_skills": observed_skills,
    "progress_text": progress_text,
    "card_info": card_info,
}

# 图鉴「伪人」页的技能文案。DLC 伪人自带（优先于内置静态表 PSEUDO_SKILLS）。
# 体例对照本体 PSEUDO_SKILLS：`突破 · X` / `解放 · X` / `主动能力① · X` / `被动能力① · X`，
# 正文写成有时间线的长叙述（「……后，每当……便……。当……时立刻……」），
# 专有名词用 `【】`，数值两侧留空格，减号用 `−`。
CODEX_SKILLS: tuple[tuple[str, str], ...] = (
    (
        f"突破 · {NAME_BREAKTHROUGH}",
        f"漏洞体来访时，若屋内任一房客的焦虑强度 ≥ {BREAKTHROUGH_LINE}，则触发突破。",
    ),
    (
        f"解放 · {NAME_LIBERATION}",
        f"连续 {SAFE_VISITS_NEEDED} 次到访期间，屋内最高焦虑强度需依次低于 "
        f"{SAFE_BASE_LINE} / {SAFE_BASE_LINE - 1} / {SAFE_MIN_LINE}（要求逐次收紧）；"
        f"期间最高焦虑强度 ≥ {INTERRUPT_LINE} 则进度清零，从下一次到访重新计算。",
    ),
    (
        f"主动能力① · {NAME_SHOT}",
        f"漏洞体到访时，若屋内最高焦虑强度 ≥ {SHOT_TRIGGER_INTENSITY}，立刻对"
        f"最高焦虑的房客发动：令其焦虑强度 +{SHOT_ADD_INTENSITY}，"
        f"并令接下来 {SHOT_BLOCK_TURNS} 回合内没有访客来访。"
        f"该效果只封锁人类访客，对漏洞体自身无效。",
    ),
    (
        f"被动能力① · {NAME_VISIT}",
        f"漏洞体每次到访时，取屋内焦虑强度最低的 {VISIT_LOW_TARGETS} 名房客，"
        f"令其焦虑强度 +{VISIT_LOW_INTENSITY}、层数 +{VISIT_LOW_LAYERS}。"
        f"该效果不经过抵御判定。",
    ),
    (
        f"被动能力② · {NAME_SEARCH}",
        f"对局开始后，所有房客搜索时遭遇漏洞体的概率为 "
        f"{ENCOUNTER_BASE:.0%} + {ENCOUNTER_PER_VISIT:.0%} × 漏洞体到访次数。"
        f"遭遇时令该房客焦虑强度 +{ENCOUNTER_ADD_INTENSITY}、层数 +{ENCOUNTER_ADD_LAYERS}，"
        f"并有 {ENCOUNTER_LOOT_LOSS_CHANCE:.0%} 概率令其丢失 1 件携带物资。",
    ),
)


# PseudoRuntime 通过这个属性构造场景子状态；名字必须是 State。
State = StarPseudoState

"""伪人档案与场景运行时：藏于人群之中的黑手-薯条（无固定外部形态）。

definition：静态档案；modifier/function：见后续场景迁移。
"""

from dataclasses import dataclass, field
from typing import Any

from ..types import PseudoDefinition
from weiren_game.lifecycle import AbilityLaunch

DEFINITION = PseudoDefinition(
    "pseudo_fries",
    "藏于人群之中的黑手-薯条",
    "fries",
    "没有固定形态，会绑架搜索者并以完美替身回屋。",
    "累计潜伏10回合，或单次潜伏5回合；或释放炼狱扳机时屋内房客少于3人。",
    "累计将替身驱逐三次。",
    enters_house=False,
    mark_field="exposure",
    mark_label="暴露值",
    # 暴露值即“暴露印记-薯条”：由理智溢出体系转化而来，禁止被外界改写。
    mark_externally_locked=True,
)


@dataclass
class FriesState:
    """薯条场景专属状态：潜入、暴露度与驱逐相关计数。"""

    infiltrator_id: int | None = None
    # Snapshot of the kidnapped tenant（TenantState 字典）。
    kidnapped_snapshot: dict[str, Any] | None = None
    infiltration_turns: int = 0
    total_infiltration_turns: int = 0
    exposure: float = 0.0
    cumulative_exposure: float = 0.0
    exposure_five_milestone: int = 0
    exposure_ten_milestone: int = 0
    # 仅用于“每累计 5/10 层产生指认”的计数池：不含「虚假信息被识破」的回敬暴露，
    # 否则「识破→+15→再生 3 条假指认→再被识破」会自我放大（见 add_exposure 注释）。
    milestone_pool: float = 0.0
    performance_count: int = 0
    expelled_count: int = 0
    # 替身未结算的理智溢出累积（按房客实例 ID）。
    overflow: dict[int, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "FriesState":
        """从字典还原 FriesState。"""
        data = dict(raw)
        data["overflow"] = {
            int(key): float(value)
            for key, value in dict(data.get("overflow", {})).items()
        }
        return cls(**data)

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典。"""
        return {
            "infiltrator_id": self.infiltrator_id,
            "kidnapped_snapshot": self.kidnapped_snapshot,
            "infiltration_turns": self.infiltration_turns,
            "total_infiltration_turns": self.total_infiltration_turns,
            "exposure": self.exposure,
            "cumulative_exposure": self.cumulative_exposure,
            "exposure_five_milestone": self.exposure_five_milestone,
            "exposure_ten_milestone": self.exposure_ten_milestone,
            "milestone_pool": self.milestone_pool,
            "performance_count": self.performance_count,
            "expelled_count": self.expelled_count,
            "overflow": {
                int(key): float(value) for key, value in self.overflow.items()
            },
        }


def add_exposure(
    engine: object, amount: float, source: str, *, spawn: bool = True
) -> None:
    """为薯条替身累计暴露值，并在跨 5/10 里程碑时生成指认信息。

    ``spawn=False`` 只把暴露值计入总量（推进炼狱扳机/心机判定），**不**参与里程碑产信息。
    「虚假信息被识破 +15」必须用 ``spawn=False``：否则单次识破就回敬 15 点、按每 5 层再产
    3 条假指认，配合多疑的每回合自动识破会形成复利式暴增（实测一局可堆到数百条信息）。
    """
    pseudo = engine.state.pseudo_state
    if pseudo.scenario_id != DEFINITION.id or not pseudo.infiltrator_id:
        return
    pseudo.exposure += amount
    pseudo.cumulative_exposure += amount
    engine._log(f"替身因{source}获得{amount:g}暴露值（当前{pseudo.exposure:g}）。")
    if not spawn:
        return
    pseudo.milestone_pool += amount
    five = int(pseudo.milestone_pool // 5)
    while pseudo.exposure_five_milestone < five:
        pseudo.exposure_five_milestone += 1
        create_accusation(engine, False)
    ten = int(pseudo.milestone_pool // 10)
    while pseudo.exposure_ten_milestone < ten:
        pseudo.exposure_ten_milestone += 1
        create_accusation(engine, True)


def create_accusation(engine: object, true_accusation: bool) -> object:
    """生成一条指认伪人信息：真实指认替身或随机嫁祸屋内房客。"""
    from weiren_game.data import EVENT_IDS
    from weiren_game.models import Information

    targets = engine.home_tenants()
    if not targets:
        return None
    infiltrator = engine.state.pseudo_state.infiltrator_id
    if true_accusation and infiltrator and infiltrator in engine.state.house.tenants:
        target = engine.state.house.tenants[infiltrator]
    else:
        humans = [tenant for tenant in targets if not tenant.is_pseudo]
        target = engine._rng(EVENT_IDS["fries.accusation.false"]).choice(humans or targets)
    info_id = engine.state.ids.allocate_information()
    info = Information(
        info_instance_id=info_id, title="指认房间内的伪人",
        text=f"一条线索指向{engine.character(target).name}：此人可能是伪装者。",
        status="pending", gained_turn=engine.state.flow.turn,
        expires_turn=engine.state.flow.turn + 5,
        truth=true_accusation and target.is_pseudo, kind="pseudo_inhome",
        source="未知", target_ids=[target.id],
        data={"fries_exposure_generated": True},
    )
    engine.state.house.information.append(info)
    return info


def capture_searcher(engine: object, mission: object, tenant: object) -> None:
    """薯条绑架搜索房客：保存状态快照、标记捕获并完成替身顶替。"""
    from dataclasses import asdict

    pseudo = engine.state.pseudo_state
    if pseudo.infiltrator_id:
        return
    pseudo.kidnapped_snapshot = asdict(tenant)
    pseudo.infiltrator_id = tenant.id
    engine._emit_node(
        "pseudo.instance.created", pseudo=pseudo, tenant=tenant
    )
    mission.captured = True
    mission.fortune = max(-10, mission.fortune - 5)
    engine._recalculate_search(mission)
    pseudo.revealed = True


def expel_infiltrator(
    engine: object, source: str, *, self_infernal: bool = False
) -> None:
    """驱逐薯条替身并归还被绑架房客。

    识破驱逐推进解放进度；炼狱扳机为自我驱逐，重置进度。
    """
    from weiren_game.tenant import TenantState

    pseudo = engine.state.pseudo_state
    tenant_id = pseudo.infiltrator_id
    snapshot = pseudo.kidnapped_snapshot
    if not tenant_id or not snapshot:
        return
    original = TenantState.from_dict(snapshot)
    original.at_home = True
    original.is_pseudo = False
    original.pseudo_source = None
    penalty = pseudo.infiltration_turns * 10
    original.health = max(-100, original.health - penalty)
    original.sanity = max(-100, original.sanity - penalty)
    engine.state.house.tenants[tenant_id] = original
    if self_infernal:
        pseudo.expelled_count = 0
        # 重后果（红色）：替身自己走了，玩家的解放进度被清零。
        engine._log("炼狱扳机自我驱逐：解放进度已重置。", kind="danger")
    else:
        pseudo.expelled_count += 1
    pseudo.infiltrator_id = None
    engine._emit_node(
        "pseudo.instance.removed", pseudo=pseudo, tenant=original
    )
    pseudo.kidnapped_snapshot = None
    pseudo.infiltration_turns = 0
    pseudo.exposure = 0
    pseudo.performance_count = 0
    pseudo.cumulative_exposure = 0
    pseudo.exposure_five_milestone = 0
    pseudo.exposure_ten_milestone = 0
    pseudo.milestone_pool = 0
    engine._log(
        f"{source}驱逐了替身；被绑架的{engine.character(original).name}归来"
        f"并损失{penalty}生命、理智。"
        f"解放进度{pseudo.expelled_count}/3。", kind="danger",
    )
    engine._after_health_changed()
    if original.health < 0:
        engine._kill_tenant(original, "被绑架期间伤重")
    if pseudo.expelled_count >= 3:
        pseudo.liberated = True
        engine._finish(True, "三名替身先后被识破驱逐，藏于人群中的黑手无处可藏。")


def performance(engine: object) -> None:
    """伪装表演：概率点名两名屋内房客制造互相怀疑的假信息。"""
    from weiren_game.data import EVENT_IDS
    from weiren_game.models import Information

    pseudo = engine.state.pseudo_state
    infiltrator = engine.state.house.tenants.get(pseudo.infiltrator_id or "")
    if not infiltrator or not infiltrator.at_home or engine._pseudo_actions_suppressed():
        return
    if pseudo.performance_count >= 2 or engine._rng(
        EVENT_IDS["fries.performance"]
    ).random() >= .75:
        return
    candidates = engine.home_tenants()
    if len(candidates) < 2:
        return
    engine._observe_pseudo_skill("performance")
    if engine._skill_respond_skill(
        "伪装表演", "cast",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
    ):
        return
    a, b = engine._rng(EVENT_IDS["fries.performance.targets"]).sample(candidates, 2)
    info_id = engine.state.ids.allocate_information()
    engine.state.house.information.append(Information(
        info_instance_id=info_id, title="伪装表演-互相怀疑",
        text=f"{engine.character(a).name}与{engine.character(b).name}都指责对方像伪人。",
        status="pending", gained_turn=engine.state.flow.turn,
        expires_turn=engine.state.flow.turn
        + engine._rng(EVENT_IDS["fries.performance.duration"]).randint(3, 5),
        truth=False, kind="state", source="伪装", template_id="fries_performance",
        target_ids=[a.id, b.id],
    ))
    pseudo.performance_count += 1


def mind_play(engine: object) -> None:
    """玩弄人心：随机强化房客侵蚀情绪并累计暴露值。"""
    from weiren_game.data import EVENT_IDS

    pseudo = engine.state.pseudo_state
    engine._observe_pseudo_skill("mind")
    if engine._skill_respond_skill(
        "玩弄人心", "cast",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
    ):
        return
    targets = [
        tenant for tenant in engine.home_tenants()
        if tenant.id != pseudo.infiltrator_id
    ]
    if not targets:
        return
    engine._rng(EVENT_IDS["fries.mind.targets"]).shuffle(targets)
    for target in targets[:3]:
        if engine._skill_respond_skill(
            "玩弄人心", "lock",
            mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
            target=target, event="fries.mind",
        ):
            continue
        engine._strengthen_emotion_set(target, "erosion", 1, 2, "玩弄人心")
    add_exposure(engine, 3, "玩弄人心")


def settle_end(engine: object) -> None:
    """回合末：累计潜伏/暴露并视情况发动心机、炼狱扳机或藏身突破。"""
    from weiren_game.data import EVENT_IDS

    pseudo = engine.state.pseudo_state
    if pseudo.scenario_id != DEFINITION.id or not pseudo.infiltrator_id or engine._pseudo_actions_suppressed():
        return
    infiltrator = engine.state.house.tenants.get(pseudo.infiltrator_id)
    if not infiltrator or not infiltrator.alive or not infiltrator.at_home:
        return
    pseudo.infiltration_turns += 1
    pseudo.total_infiltration_turns += 1
    pending_overflow = engine.state.pseudo_state.scenario().overflow.pop(
        infiltrator.id, 0.0
    )
    if pending_overflow:
        add_exposure(engine, pending_overflow, "理智回复溢出")
    add_exposure(engine, 1, "回合结束")
    if engine._rng(EVENT_IDS["fries.mind_play"]).random() < min(
        1.0, (.35 + pseudo.exposure / 100)
    ):
        mind_play(engine)
    if pseudo.exposure >= 25:
        infernal_trigger(engine)
        return
    if pseudo.infiltration_turns >= 5 or pseudo.total_infiltration_turns >= 10:
        engine._attempt_breakthrough(
            "薯条的替身已潜伏足够久，“藏身”突破完成。"
        )


def infernal_trigger(engine: object) -> None:
    """炼狱扳机：替身自我驱逐并重置解放进度。"""
    from weiren_game.data import EVENT_IDS

    pseudo = engine.state.pseudo_state
    engine._observe_pseudo_skill("trigger")
    engine._log("替身暴露值达到25，发动“炼狱扳机”！")
    blocked = engine._skill_respond_skill(
        "炼狱扳机", "cast",
        mode=AbilityLaunch.PSEUDO_HUMAN, caster=engine.state.pseudo_state,
    )
    if not blocked:
        for repeat in range(9):
            targets = [
                tenant for tenant in engine.home_tenants()
                if tenant.id != pseudo.infiltrator_id
            ]
            engine._rng(EVENT_IDS["fries.trigger"], repeat).shuffle(targets)
            for target in targets[:3]:
                if not engine._skill_respond_skill(
                    "炼狱扳机", "lock",
                    mode=AbilityLaunch.PSEUDO_HUMAN,
                    caster=engine.state.pseudo_state,
                    target=target, event=f"fries.trigger.{repeat}",
                ):
                    engine._damage_health(target, 5, "炼狱扳机")
    # 突破条件：释放炼狱扳机时屋内房客人数小于 3。
    if len(engine.home_tenants()) < 3:
        if engine._attempt_breakthrough(
            "炼狱扳机引爆时屋内房客不足三人，薯条完成“黑手”突破。"
        ):
            return
    expel_infiltrator(engine, "炼狱扳机自我驱逐", self_infernal=True)


def attack_searcher(engine: object, mission: object, tenant: object) -> None:
    """搜索袭击：薯条绑架外出房客（替身顶替）。"""
    engine._observe_pseudo_skill("infiltrate")
    capture_searcher(engine, mission, tenant)


# 场景处理器注册表（供伪人协调器查表调用）。
def encounter_chance(engine: object, mission: object, tenant: object) -> float:
    """薯条场景的基础遭遇率：驱逐越多越高，空背包再乘 1.5。"""
    chance = .50 + .15 * engine.state.pseudo_state.expelled_count
    if not engine._tenant_item_ids(tenant):
        chance *= 1.5
    return chance


def blocks_search_dispatch(engine: object, tenant: object) -> bool:
    """薯条场景：派遣替身外出会立刻触发炼狱扳机并取消本次搜索。"""
    pseudo = engine.state.pseudo_state
    if pseudo.infiltrator_id != tenant.id or not tenant.is_pseudo:
        return False
    engine._log("派遣替身外出搜索令薯条发动“炼狱扳机”。")
    infernal_trigger(engine)
    return True


def captured_return(engine: object, mission: object, tenant: object) -> None:
    """薯条场景：搜索返程时若曾被绑架，房客被替身顶替。"""
    pseudo = engine.state.pseudo_state
    tenant.is_pseudo = True
    tenant.pseudo_source = "fries"
    pseudo.infiltrator_id = tenant.id
    engine._emit_node(
        "pseudo.instance.created", pseudo=pseudo, tenant=tenant
    )
    # 通用节点：把「一名屋内房客被伪人替身顶替」这一事实广播出去，
    # 由各角色/性格自行决定是否响应（不在此处直连任何具体角色）。
    engine._emit_node("pseudo.tenant_replaced", pseudo=pseudo, tenant=tenant)
    pseudo.revealed = True
    pseudo.infiltration_turns = 0


def search_resist_penalty(engine: object) -> float:
    """薯条场景：其搜索袭击的锁定/抵御成功率惩罚。"""
    return .50


def infiltrator_search_penalty(engine: object, tenant: object) -> float:
    """替身（被模仿房客）外出搜索时的时运惩罚。"""
    return 5.0


def on_information_verified(engine: object, *, info: object) -> None:
    """由暴露值产生的虚假信息被验证时，追加暴露值。"""
    if info.truth or not info.data.get("fries_exposure_generated"):
        return
    # 回敬暴露值只推进炼狱扳机，不再触发新的里程碑指认（打断自我放大循环）。
    add_exposure(engine, 15, "虚假信息被识破", spawn=False)


NODE_HOOKS = {"information.verified": on_information_verified}


def observed_skills(engine: object) -> tuple[str, ...]:
    """薯条场景对外可见的技能（id, 展示名），供信息文本与核验使用。"""
    return (
        ("infiltrate", "潜伏"),
        ("mind", "玩弄人心"),
        ("performance", "表演"),
        ("trigger", "炼狱扳机"),
    )


def progress_text(engine: object) -> str:
    """薯条场景的进度摘要文本。"""
    pseudo = engine.state.pseudo_state
    return (
        f"驱逐{pseudo.expelled_count}/3，潜伏{pseudo.infiltration_turns}/5，"
        f"暴露{pseudo.exposure:g}/25"
    )


def ability_fail_modifier(
    engine: object, actor: object, chance: float
) -> float:
    """替身模仿他人主动能力时额外失败 +25%。"""
    if actor.is_pseudo and actor.pseudo_source == "fries":
        return chance + .25
    return chance


def ability_fail_resolved(
    engine: object, actor: object, ability_id: str, failed: bool
) -> None:
    """替身模仿能力的暴露结算：失败 7、成功 3。"""
    if actor.is_pseudo and actor.pseudo_source == "fries":
        add_exposure(engine, 7 if failed else 3, "模仿主动能力")


def sanity_overflow_share(
    engine: object, tenant: object, overflow: float
) -> None:
    """理智溢出转化：与比格小星同属“溢出转化”体系的一次性版本。

    比格小星把回复理智超过 100 的部分按 100% 转为【星之印记】；
    替身则把同样的溢出部分按 50% 累积，在该回合末结算为【暴露印记-薯条】
    （对外描述仍是“暴露值”）。
    """
    if tenant.is_pseudo and tenant.pseudo_source == "fries" and overflow:
        engine.state.pseudo_state.scenario().overflow[tenant.id] = (
            engine.state.pseudo_state.scenario().overflow.get(tenant.id, 0.0)
            + overflow * .5
        )


# 薯条专属信息效果：就近声明“伪装表演”信息的核验/待验证结算。
def resolve_performance_information(
    engine: object, info: object, targets: list[object]
) -> None:
    """核验“伪装表演”：确认为真时生成指认，并把目标侵蚀-5/-5。"""
    if info.status == "confirmed":
        create_accusation(engine, True)
        for target in targets:
            engine._reduce_emotion_set(target, "erosion", 5, 5)


def pending_performance_information(
    engine: object, info: object, targets: list[object]
) -> None:
    """待验证的“伪装表演”：降低暴露，并使目标侵蚀+1/+1。"""
    from weiren_game.lifecycle import AbilityLaunch

    engine.state.pseudo_state.exposure = max(
        0, engine.state.pseudo_state.exposure - 2
    )
    for target in targets:
        if engine._skill_respond_skill(
            "薯条表演", "lock",
            mode=AbilityLaunch.PSEUDO_HUMAN,
            caster=engine.state.pseudo_state,
            target=target, event=f"fries.performance.pending.{info.info_instance_id}",
        ):
            continue
        engine._strengthen_emotion_set(target, "erosion", 1, 1, "伪装表演")


from ..information import register_state_effect

register_state_effect(
    "fries_performance",
    resolve_performance_information,
    pending_performance_information,
)




def card_info(engine: object) -> dict:
    """伪人卡：解放/突破进度 + 技能 + 印记阈值。"""
    ps = engine.state.pseudo_state
    exposure = int(getattr(ps, "exposure", 0))
    return {
        "liberation": f"无可奈何：累计驱逐替身 {getattr(ps,'expelled_count',0)}/3",
        # 暴露值只在「印记（顶栏）」与「潜伏」技能行显示，避免同一数值在多处堆叠。
        "breakthrough": "黑手：潜伏累计 10 / 单次 5 回合即突破；暴露值满 25 会自我驱逐",
        "mark_need": 25,
        "skills": [
            {"name": "潜伏", "text": "搜索袭击：绑架外出房客，并以「替身」冒名归队。",
             "mark": {"label": "暴露值", "current": exposure, "need": 25}},
            {"name": "玩弄人心", "text": "回合末概率强化至多 3 名房客的侵蚀情绪，并累计暴露值。"},
            {"name": "表演", "text": "回合初概率生成一条虚假的房客状态信息。"},
            {"name": "炼狱扳机", "text": "随机至多 3 名房客各受 5 点伤害，重复 9 次；替身自我驱逐。"},
        ],
    }

HANDLERS: dict[str, object] = {
    "add_exposure": add_exposure,
    "create_accusation": create_accusation,
    "capture_searcher": capture_searcher,
    "expel_infiltrator": expel_infiltrator,
    "performance": performance,
    "mind_play": mind_play,
    "settle_end": settle_end,
    "infernal_trigger": infernal_trigger,
    "attack_searcher": attack_searcher,
    "blocks_search_dispatch": blocks_search_dispatch,
    "encounter_chance": encounter_chance,
    "captured_return": captured_return,
    "search_resist_penalty": search_resist_penalty,
    "infiltrator_search_penalty": infiltrator_search_penalty,
    "observed_skills": observed_skills,
    "progress_text": progress_text,
    "card_info": card_info,
    "ability_fail_modifier": ability_fail_modifier,
    "ability_fail_resolved": ability_fail_resolved,
    "sanity_overflow_share": sanity_overflow_share,
}


State = FriesState

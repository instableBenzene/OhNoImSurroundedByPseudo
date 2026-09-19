"""房客档案：火龙（1 号）。

本文件按「定义 / 修饰器 / 技能函数」三节组织，角色的静态档案、可用性判定
与效果实现全部集中于此；每项函数都标注由哪个系统在何处调用。
"""

from ..types import A, CharacterDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "dragon", 1, TEXT["character.dragon.name"], TEXT["character.dragon.description"],
    "cheerful", "steady", 4, (TEXT["character.dragon.tag.0"], TEXT["character.dragon.tag.1"], TEXT["character.dragon.tag.2"]),
    (A("party_focus", TEXT["ability.party_focus.name"], TEXT["ability.party_focus.description"]),),
    (A("call_friends", TEXT["ability.call_friends.name"], TEXT["ability.call_friends.description"], chips=(TEXT["ability.call_friends.chip.0"], TEXT["ability.call_friends.chip.1"])),),
)

# ---------------------------------------------------------------- modifier
def requirements_call_friends(
    engine: EngineProtocol, actor: object, *, bypass: bool
) -> str | None:
    """呼朋引伴的使用条件（入住 3 回合解锁）；不满足返回错误文案。

    使用处：ability_system 的公共技能门槛判定。
    """
    if getattr(actor, "home_turns") < 3 and not bypass:
        return TEXT["data.characters.dragon.requirements_call_friends.1"]
    return None


def costs_call_friends(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """呼朋引伴本次的 cost 项（25 理智），交给公共消耗流程。"""
    return [T("sanity", 25)]


# ---------------------------------------------------------------- function
def use_call_friends(engine: EngineProtocol, actor: object, ability_id: str, *, bypass: bool = False) -> None:
    """呼朋引伴：立即增加两名访客并设置 4 回合冷却（成本由公共流程处理）。

    使用处：ability_system.use_ability 的火龙分发分支。
    """
    engine._queue_human_visitor(TEXT["data.characters.dragon.use_call_friends.1"], force_supply=True)
    engine._queue_human_visitor(TEXT["data.characters.dragon.use_call_friends.2"], force_supply=True)
    engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 4)


def party_focus(engine: EngineProtocol, tenant: object) -> None:
    """派对的焦点：回合开始时理智高于 85 时以 15% 概率增加一名访客。

    使用处：round_effects 回合初实例节点经 TURN_START_HOOKS 查表调用。
    """
    if (
        getattr(tenant, "sanity") > 85
        and engine._passive_available(tenant, "dragon")
    ):
        success = engine._rng(_event_id("dragon.visitor"), tenant.id).random() < .15
        engine._skill_outcome(tenant, "dragon.party_focus", success)
        if success:
            engine._queue_human_visitor(TEXT["data.characters.dragon.party_focus.1"])


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "call_friends": (
        lambda engine, actor, *, bypass=False, **kwargs:
        use_call_friends(engine, actor, "call_friends", bypass=bypass)
    ),
}

def turn_start(engine, tenant):
    """回合初实例钩子：委托给「派对的焦点」。"""
    party_focus(engine, tenant)

TURN_START = turn_start

# 开局核心角色：不可被禁用（内容自声明，核心不写死名单）。
PROTECTED_STARTER = True

# 界面头像图标（内容自声明）。
AVATAR = "i-av5"

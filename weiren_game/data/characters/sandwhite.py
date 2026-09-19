"""房客档案：沙白（24 号）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件，
系统侧只保留调用点。
"""

from ..types import A, CharacterDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "sandwhite", 24, TEXT["character.sandwhite.name"], TEXT["character.sandwhite.description"], "loner", "gentle", 4,
    (TEXT["character.sandwhite.tag.0"], TEXT["character.sandwhite.tag.1"], TEXT["character.sandwhite.tag.2"]),
    # 排版与去重（STYLE §12）：数值加粗、条件分行；冷却只留在 chips 里，不在正文重复。
    (A("ordinary", TEXT["ability.ordinary.name"],
       TEXT["ability.ordinary.description"],
       chips=(TEXT["ability.ordinary.chip.0"],)),
     A("slow_perception", TEXT["ability.slow_perception.name"],
       TEXT["ability.slow_perception.description"])),
    (A("encourage", TEXT["ability.encourage.name"], TEXT["ability.encourage.description"], chips=(TEXT["ability.encourage.chip.0"],)),),
)

# ---------------------------------------------------------------- modifier
def initial_setup(engine: EngineProtocol, tenant: object) -> None:
    """感知迟钝：沙白入住时理智固定为 50。

    使用处：engine._add_tenant 的新房客登记。
    """
    if tenant.character_id == "sandwhite":
        tenant.sanity = 50.0


def sanity_reduce_multiplier(
    engine: EngineProtocol, tenant: object, *, change_type: str
) -> float:
    """感知迟钝：仅沙白的「消耗」型理智削减减半（被动一次判定）。

    使用处：value_system._reduce_sanity 经 CHARACTER_VALUE_HOOKS 查表调用。
    """
    if change_type != "consume":
        return 1.0
    if not engine._passive_available(tenant, "sandwhite.slow_perception.consume"):
        return 1.0
    return .5


def sanity_restore_multiplier(engine: EngineProtocol, tenant: object) -> float:
    """感知迟钝：沙白获得的理智回复减半（被动一次判定）。

    使用处：value_system._restore_sanity 经 CHARACTER_VALUE_HOOKS 查表调用。
    """
    if not engine._passive_available(tenant, "sandwhite.slow_perception.restore"):
        return 1.0
    return .5


VALUE_HOOKS = {
    "reduce_sanity": sanity_reduce_multiplier,
    "restore_sanity": sanity_restore_multiplier,
}


# ---------------------------------------------------------------- function
def use_encourage(engine: EngineProtocol, actor: object, ability_id: str) -> None:
    """鼓舞：为所有屋内房客附加 3 回合的理智回复效果并设置冷却。

    使用处：ability_system.use_ability 的沙白分发分支。
    """
    for tenant in engine.home_tenants():
        vitality = tenant.condition("vitality_boost")
        if not (vitality.active and vitality.layers >= 3):
            tenant.set_status("vitality_boost", intensity=1, layers=3)
    engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 2)


def costs_encourage(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """鼓舞无资源消耗（仅冷却），无 cost 项。"""
    return []


def vitality_boost(engine: EngineProtocol, tenant: object) -> None:
    """活力焕发：鼓舞的 condition 回合末效果，每次 -1 层、归 0 消失。"""
    condition = tenant.condition("vitality_boost")
    if not condition.active:
        return
    engine._restore_sanity(tenant, 2, "sandwhite_inspire")
    remaining = condition.layers - 1
    if remaining <= 0:
        tenant.clear_status("vitality_boost")
    else:
        tenant.set_status("vitality_boost", intensity=1, layers=remaining)


from weiren_game.condition import StatusDefinition, register_status_definition

register_status_definition(
    StatusDefinition(
        "vitality_boost",
        TEXT["status.vitality_boost.label"],
        "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="ability:encourage@sandwhite",
        nodes=frozenset({"turn_end.status_effects"}),
        auto_decay=False,
        hook=vitality_boost,
     description=TEXT["status.vitality_boost.description"])
)


def passive_heal(engine: EngineProtocol, tenant: object) -> None:
    """万事通：回合开始时以 20% 概率减轻一名轻度创伤房客。

    使用处：round_effects 回合初实例节点经 TURN_START_HOOKS 查表调用。
    """
    heal_state = tenant.ability_state("ordinary")
    if heal_state and heal_state.cooldown_until > engine.state.flow.turn:
        return
    candidates = [
        value for value in engine.home_tenants()
        if value.trauma.active and value.trauma.intensity <= 3
    ]
    if candidates and engine._passive_available(tenant, "sandwhite.ordinary.heal"):
        success = engine._rng(_event_id("sandwhite.heal"), tenant.id).random() < .20
        engine._skill_outcome(tenant, "sandwhite.mastermind.heal", success)
        if success:
            target = max(candidates, key=lambda value: (value.trauma.intensity, value.trauma.layers))
            engine._recover_condition(target.trauma, 0, 3)
            engine._set_ability_cooldown(tenant, "ordinary", engine.state.flow.turn + 3)
            engine._log(TEXT["data.characters.sandwhite.passive_heal.1"].format(p1=engine.character(target).name))


def search_reward(engine: EngineProtocol, tenant: object, guaranteed: list[str]) -> None:
    """万事通：搜索返回时有 30% 概率多获得一件随机物资。

    使用处：search_system._collect_guaranteed_rewards（沙白行）。
    """
    if engine._passive_available(tenant, "sandwhite.ordinary.search_reward"):
        success = (
            engine._rng(_event_id("sandwhite.ordinary.search_reward"), tenant.id).random()
            < .30
        )
        engine._skill_outcome(tenant, "sandwhite.mastermind.search_reward", success)
        if success:
            guaranteed.append(engine._random_item(event_id=_event_id("sandwhite.extra"), event_suffix=(tenant.id,)))


SEARCH_REWARD = search_reward


def search_rest(engine: EngineProtocol, tenant: object) -> None:
    """感知迟钝／疲倦：搜索返回后休息至下下回合，期间不能再被派出。

    使用处：search_system._process_search_returns（返回结算尾部）。
    """
    if tenant.character_id != "sandwhite":
        return
    if engine._passive_available(tenant, "sandwhite.slow_perception.search_rest"):
        tenant.search_locked_until = engine.state.flow.turn + 2


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "encourage": (
        lambda engine, actor, *, ability_id=None, **kwargs:
        use_encourage(engine, actor, ability_id or "encourage")
    ),
}

def turn_start(engine, tenant):
    """回合初实例钩子：委托给「万事通」。"""
    passive_heal(engine, tenant)

TURN_START = turn_start


HOOKS = {"search.return.rest": search_rest}


def _sandwhite_consume_modifier(context: object):
    """沙白：理智消耗减半。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "sandwhite":
        return
    if engine._passive_available(tenant, "sandwhite.slow_perception.consume"):
        yield spec("sanityConsume").path("consume").mul(0.5).source("ability", "sandwhite", "slow_perception")


def _sandwhite_restore_modifier(context: object):
    """沙白：理智回复减半。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "sandwhite":
        return
    if engine._passive_available(tenant, "sandwhite.slow_perception.restore"):
        yield spec("sanityRestore").path("restore").mul(0.5).source("ability", "sandwhite", "slow_perception")


from weiren_game.modifier_rules import register_modifier_provider as _regsw
_regsw("sanityConsume", _sandwhite_consume_modifier)
_regsw("sanityRestore", _sandwhite_restore_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av5"

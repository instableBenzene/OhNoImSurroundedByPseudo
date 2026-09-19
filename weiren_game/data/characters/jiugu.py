"""房客档案：久孤（9 号，忍术防御）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from weiren_game.probability import resolve

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "jiugu", 9, TEXT["character.jiugu.name"], TEXT["character.jiugu.description"],
    "cheerful", "impatient", 3, (TEXT["character.jiugu.tag.0"], TEXT["character.jiugu.tag.1"], TEXT["character.jiugu.tag.2"], TEXT["character.jiugu.tag.3"]),
    (A("ninjutsu", TEXT["ability.ninjutsu.name"], TEXT["ability.ninjutsu.description"]),
     A("storm_blade", TEXT["ability.storm_blade.name"], TEXT["ability.storm_blade.description"])),
)

# ---------------------------------------------------------------- function
def resists_pseudo_active(
    engine: EngineProtocol, tenant: object, event_id: str, *, success_penalty: float
) -> bool:
    """吓我一跳，我释放忍术：45% 概率免疫伪人主动技能。

    使用处：pseudo_system._skill_respond_skill 的 lock 阶段。
    """
    if engine._passive_available(tenant, f"{event_id}.jiugu.passive"):
        from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers

        source = (TEXT["data.characters.jiugu.resists_pseudo_active.1"], TEXT["data.characters.jiugu.resists_pseudo_active.2"], TEXT["data.characters.jiugu.resists_pseudo_active.3"], TEXT["data.characters.jiugu.resists_pseudo_active.4"])
        ctx = {"engine": engine, "tenant": tenant, "event_id": event_id}
        value = calculate_modified_amount(
            0.0, collect_modifiers("chance", source, ctx)
        )
        success = (
            engine._rng(f"{event_id}.jiugu.resist.{tenant.id}").random()
            < resolve(value - success_penalty)
        )
        engine._skill_outcome(tenant, f"{event_id}.jiugu", success)
        if success:
            engine._log(TEXT["data.characters.jiugu.resists_pseudo_active.5"])
            return True
        return False
    return False


def search_reward(engine: EngineProtocol, tenant: object, guaranteed: list[str]) -> None:
    """岚刀一直切：搜索返回必得一件紫色及以上物资。

    使用处：search_system 的保底战利品收集。
    """
    if not engine._passive_available(tenant, "jiugu.reward"):
        return
    guaranteed.append(
        engine._random_item(minimum_quality=3, event_id=_event_id("jiugu.reward"), event_suffix=(tenant.id,))
    )


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

SEARCH_REWARD = search_reward


def _jiugu_resist_modifier(context: object):
    """忍术：45% 抵御伪人主动能力。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]; event_id = context.get("event_id", "")  # type: ignore[index]
    if not engine._passive_available(tenant, f"{event_id}.jiugu.passive"):
        return
    yield (
        spec("chance").flat(0.45).match("all")
        .path("resist", "pseudo_active").source("ability", "jiugu", "ninjutsu")
    )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _jiugu_resist_modifier)

NODE_HOOKS = {"target_lock": resists_pseudo_active}

# 界面头像图标（内容自声明）。
AVATAR = "i-av12"

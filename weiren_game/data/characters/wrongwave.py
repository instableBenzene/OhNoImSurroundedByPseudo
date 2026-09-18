"""房客档案：错潮（6 号，饮品抵御搜索技能）。

按“定义 / 修饰器 / 技能函数”组织；角色专属逻辑集中在本文件。
"""

from weiren_game.probability import resolve

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "wrongwave", 6, "错潮", "自称是笨蛋，但真打起架来有惊人的直觉。",
    "loner", "impatient", 4, ("无业游民", "18-24岁", "男性", "便利店店员"),
    (A("water_thrower", "矿泉水瓶投掷爱好者", "错潮搜索返回时，必定获得一瓶矿泉水。"),
     A("there_you_go", "走你！", "搜索中受到伪人主动能力影响时，可消耗一个【饮料】或【罐头】：有 **70%** 可能不受影响。\n*若抵御成功，伪人会在错潮搜索返回后的下一个回合来访。*")),
)

# ---------------------------------------------------------------- function
def search_reward(engine: EngineProtocol, tenant: object, guaranteed: list[str]) -> None:
    """矿泉水瓶投掷爱好者：错潮搜索返回时，必定获得一瓶矿泉水。

    使用处：search_system 的保底战利品收集。
    """
    if not engine._passive_available(tenant, "wrongwave.reward"):
        return
    guaranteed.append("water")


def try_resist(
    engine: EngineProtocol,
    mission: object,
    tenant: object,
    event: str,
    *,
    penalty: float,
) -> bool:
    """走你！：消耗随身饮料/罐头，以 70% 概率抵御搜索中的伪人技能。

    返回是否成功抵御；成功时还会顺延下一次伪人到访。
    使用处：pseudo_system._skill_respond_skill 的 resist 阶段（搜索袭击）。
    """
    from ..items import ITEMS

    if (
        tenant.character_id != "wrongwave"
        or not engine._passive_available(tenant, event + ".wrongwave.passive")
    ):
        return False
    drink = next(
        (
            value for value in tenant.inventory.items
            if "drink" in ITEMS[value.item_id].tags or "can" in ITEMS[value.item_id].tags
        ),
        None,
    )
    if drink is None:
        return False
    engine._take_tenant_item(tenant, drink.item_id)
    engine._recalculate_search(mission)
    from weiren_game.modifier_rules import calculate_modified_amount, collect_modifiers

    source = ("抵御", "伪人使用主动能力", "伪人技能", "搜索")
    ctx = {"engine": engine, "tenant": tenant}
    value = calculate_modified_amount(
        0.0, collect_modifiers("chance", source, ctx)
    )
    if engine._rng(event + ".wrongwave").random() < resolve(value - penalty):
        engine.state.world.visitors.next_pseudo_turn = max(
            engine.state.world.visitors.next_pseudo_turn,
            engine.state.flow.turn + mission.remain_search_turns + 1,
        )
        engine._skill_outcome(tenant, "wrongwave.try_resist", True)
        return True
    engine._skill_outcome(tenant, "wrongwave.try_resist", False)
    return False

SEARCH_REWARD = search_reward


def _wrongwave_resist_modifier(context: object):
    """走你！：70% 抵御伪人主动能力（消耗饮料触发）。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "wrongwave":
        return
    yield (
        spec("chance").flat(0.70).match("all")
        .path("抵御", "伪人使用主动能力").source("角色技能", "错潮", "走你")
    )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _wrongwave_resist_modifier)

NODE_HOOKS = {"pseudo_search_resist": try_resist}

# 界面头像图标（内容自声明）。
AVATAR = "i-av11"

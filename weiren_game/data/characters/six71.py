"""房客档案：柳七鱼（8 号，社恐转物资者）。

按“定义 / 修饰器 / 技能函数”组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "six71", 8, "柳七鱼", "不擅长与人相处、喜欢独处的男大学生。",
    "suspicious", "loner", 3, ("大学生", "18-24岁", "男性"),
    (A("suspension_bridge", "吊桥效应", "当屋内人数＞4人时，柳七鱼回合末理智消耗+30%。"),),
    (A("cannot_stand", "不行，我要受不了了", "驱逐1名房客，立即获得10份随机物资，并根据目标已损失的生命值获得时运修正（基础 +5，目标每损失 10 点生命值则时运 -1，最低 -5）。*柳七鱼不会因自己驱逐房客受到理智惩罚。", "other_tenant"),),
)

# ---------------------------------------------------------------- modifier
def crowd_sanity_multiplier(engine: EngineProtocol, tenant: object) -> float:
    """吊桥效应：屋内超过 4 人时回合末理智消耗 ×1.3。

    使用处：round_effects 的回合末理智消耗计算。
    """
    if (
        len(engine.home_tenants()) > 4
        and engine._passive_available(tenant, "six71.crowd")
    ):
        return 1.30
    return 1.0


# ---------------------------------------------------------------- function
def use_cannot_stand(engine: EngineProtocol, actor: object, target_id: str | None) -> None:
    """不行，我要受不了了：驱逐一名房客，按目标损失生命获得时运并产出物资。

    使用处：ability_system.use_ability 的柳七鱼分发分支。
    """
    from weiren_game.exceptions import RuleViolation
    from ..items import ITEMS

    target = engine._require_home_tenant(target_id)
    if target.id == actor.id:
        raise RuleViolation("柳七鱼不能驱逐自己。")
    # 目标损失生命越多，时运越低（基础 +5，每损失 10 点 -1，最低 -5）。
    lost = max(0, int(target.max_health) - int(target.health))
    fortune = max(-5, 5 - lost // 10)
    occupants_before = len(engine.home_tenants())
    engine._expel_tenant(target, "柳七鱼", sanity_exempt_ids={actor.id})
    rewards = 10
    gained = []
    for index in range(rewards):
        item_id = engine._random_item(
            event_id=_event_id("liu.reward"), event_suffix=(index,), fortune=fortune,
        )
        gained.append(item_id)
        engine._gain_item(item_id)
    engine._log(
        f"柳七鱼找出物资（时运{fortune:+d}）：" + "、".join(ITEMS[key].name for key in gained) + "。"
    )


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "cannot_stand": (
        lambda engine, actor, *, target_id=None, **kwargs:
        use_cannot_stand(engine, actor, target_id)
    ),
}


def end_of_turn_sanity_cost(
    engine: EngineProtocol, tenant: object, cost: float
) -> float:
    """柳七鱼的回合末理智消耗修正：屋内超 4 人时 ×1.3。

    使用处：round_effects 回合末 base_consume 经 CHARACTER_VALUE_HOOKS 查表调用。
    """
    return cost * crowd_sanity_multiplier(engine, tenant)


VALUE_HOOKS = {"end_sanity_cost": end_of_turn_sanity_cost}


def _six71_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "six71":
        return
    mult = crowd_sanity_multiplier(engine, tenant)
    if mult != 1.0:
        yield spec("sanityConsume").path("回合末消耗").mul(mult).source("角色技能", "陆柒壹", "喧嚣")


from weiren_game.modifier_rules import register_modifier_provider as _reg6
_reg6("sanityConsume", _six71_sanity_modifier)

# 界面头像图标（内容自声明）。
AVATAR = "i-av6"

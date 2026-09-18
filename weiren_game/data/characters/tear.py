"""房客档案：ED Tear（3 号，沃尔玛购物袋依赖）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from weiren_game.probability import resolve

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "tear", 3, "ED Tear", "14岁的小男孩，自称是一个「沃尔玛购物袋」。",
    "keen", "gentle", 2, ("小学生", "12-14岁", "男性", "沃尔玛购物袋"),
    (A("walmart_bag", "我是一个沃尔玛购物袋", "ED Tear 入住时带来一个「沃尔玛购物袋」（金色）【工具】【易损品】：\n· 持有者可携带物资数 **+5**。\n· 搜索返回后有 **25%** 可能被消耗；携带者为 ED Tear 时概率 **−10%**。\n*一个普通的超市购物袋，但对 ED 来说，他即是塑料袋，塑料袋即是他。*"),
     A("needs_bag", "我不能没有购物袋", "若ED Tear自身不携带「沃尔玛购物袋」， 回合末理智消耗*3，且消耗理智+5。")),
)

# ---------------------------------------------------------------- function
def on_arrival(engine: EngineProtocol, tenant: object) -> None:
    """我是一个沃尔玛购物袋：入住时给屋主带来购物袋。

    使用处：visitor_system._on_tenant_accepted。
    """
    if tenant.character_id != "tear":
        return
    if not engine._passive_available(tenant, "tear.arrival"):
        return
    engine._gain_item("walmart_bag")
    engine._log("ED Tear带来了沃尔玛购物袋。")


def missing_bag_cost(engine: EngineProtocol, tenant: object, cost: float) -> float:
    """我不能没有购物袋：未携带购物袋时回合末理智消耗 ×3 并额外 +5。

    使用处：round_effects 的回合末理智消耗计算。
    """
    missing = not any(
        held.item_id == "walmart_bag" for held in tenant.inventory.items
    )
    if (
        tenant.character_id == "tear"
        and missing
        and engine._passive_available(tenant, "tear.missing_bag")
    ):
        return cost * 3 + 5
    return cost




VALUE_HOOKS = {"end_sanity_cost": missing_bag_cost}


def _tear_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "tear":
        return
    missing = not any(v.item_id == "walmart_bag" for v in tenant.inventory.items)
    if missing and engine._passive_available(tenant, "tear.missing_bag"):
        yield spec("sanityConsume").path("回合末消耗").mul(3).source("角色技能", "ED Tear", "我不能没有购物袋")
        yield spec("sanityConsume").path("回合末消耗").final().flat(5).source("角色技能", "ED Tear", "我不能没有购物袋")


from weiren_game.modifier_rules import register_modifier_provider as _regt
_regt("sanityConsume", _tear_sanity_modifier)

NODE_HOOKS = {"on_arrival": on_arrival}

# 开局核心角色：不可被禁用（内容自声明，核心不写死名单）。
PROTECTED_STARTER = True

# 界面头像图标（内容自声明）。
AVATAR = "i-av9"

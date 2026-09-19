"""房客档案：ED Tear（3 号，沃尔玛购物袋依赖）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from weiren_game.probability import resolve

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "tear", 3, TEXT["character.tear.name"], TEXT["character.tear.description"],
    "keen", "gentle", 2, (TEXT["character.tear.tag.0"], TEXT["character.tear.tag.1"], TEXT["character.tear.tag.2"], TEXT["character.tear.tag.3"]),
    (A("walmart_bag", TEXT["ability.walmart_bag.name"],
       TEXT["ability.walmart_bag.description"]),
     # 排版：中英之间加空格、标点后不留空格；倍率写 `×`（`*` 是 mdText 的斜体标记，会被吃掉）。
     A("needs_bag", TEXT["ability.needs_bag.name"],
       TEXT["ability.needs_bag.description"])),
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
    engine._log(TEXT["data.characters.tear.on_arrival.1"])


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
        yield spec("sanityConsume").path("turn_end_consume").mul(3).source("ability", "tear", "needs_bag")
        yield spec("sanityConsume").path("turn_end_consume").final().flat(5).source("ability", "tear", "needs_bag")


from weiren_game.modifier_rules import register_modifier_provider as _regt
_regt("sanityConsume", _tear_sanity_modifier)

NODE_HOOKS = {"on_arrival": on_arrival}

# 开局核心角色：不可被禁用（内容自声明，核心不写死名单）。
PROTECTED_STARTER = True

# 界面头像图标（内容自声明）。
AVATAR = "i-av9"

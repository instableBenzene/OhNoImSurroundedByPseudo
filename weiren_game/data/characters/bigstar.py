"""房客档案：比格小星（2 号）。"""

# 按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。

from ..types import A, CharacterDefinition, MarkDefinition
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "bigstar", 2, TEXT["character.bigstar.name"], TEXT["character.bigstar.description"],
    "cheerful", "gentle", 3, (TEXT["character.bigstar.tag.0"], TEXT["character.bigstar.tag.1"], TEXT["character.bigstar.tag.2"], TEXT["character.bigstar.tag.3"], TEXT["character.bigstar.tag.4"], TEXT["character.bigstar.tag.5"]),
    (A("hell_gift", TEXT["ability.hell_gift.name"],
       TEXT["ability.hell_gift.description"]),
     A("everyone_star", TEXT["ability.everyone_star.name"], TEXT["ability.everyone_star.description"])),
)

# ---------------------------------------------------------------- modifier
def star_doll_pool_weight(engine: EngineProtocol, item_id: str) -> float | None:
    """地狱的赠礼：修改搜索池中玩偶的权重（未禁用时 ×15，禁用则为 0）。

    使用处：search_system 的物资抽取加权循环。
    """
    if item_id != "star_doll":
        return None
    if "bigstar" in engine.state.world.disabled_characters:
        return 0.0
    return 15.0


# ---------------------------------------------------------------- function
def use_star_doll(engine: EngineProtocol, tenant: object, item: object) -> None:
    """可爱的玩偶：仅比格小星可使用的角色专属回复物。

    使用处：item_system.use_item 的 star_doll 分支。
    """
    from weiren_game.exceptions import RuleViolation

    if tenant.character_id != "bigstar":
        raise RuleViolation(TEXT["data.characters.bigstar.use_star_doll.1"])
    engine._restore_sanity(tenant, 25, item.name)


def collect_star_overflow(engine: EngineProtocol, *, tenant: object, overflow: float) -> None:
    """大家的星星：理智回复溢出时按 **100%** 累计为星之印记。

    使用处：`value_system._restore_sanity` 发出的 `sanity.restored` 节点
    （核心只发事件；"怎么用溢出"是各自的事——伪人薯条的替身按 50% 累计，另见其模块）。
    """
    if overflow <= 0 or tenant.character_id != "bigstar":
        return
    if not engine._passive_available(tenant, "bigstar.star_overflow"):
        return
    engine._gain_mark(tenant, "star", overflow)


def everyone_star(engine: EngineProtocol, tenant: object) -> None:
    """大家的星星：回合开始时消耗印记为最低理智的房客回复理智。

    使用处：round_effects 回合初实例节点经 TURN_START_HOOKS 查表调用。
    """
    if (
        engine._mark_count(tenant, "star") > 0
        and engine._passive_available(tenant, "bigstar.everyone_star")
    ):
        amount = min(10.0, engine._mark_count(tenant, "star"))
        target = min(engine.home_tenants(), key=lambda value: (value.sanity, value.id))
        engine._consume_mark(tenant, "star", amount)
        engine._restore_sanity(target, amount * .5, "everyone_star")

def turn_start(engine, tenant):
    """回合初实例钩子：委托给「大家的星星」。"""
    everyone_star(engine, tenant)

TURN_START = turn_start


NODE_HOOKS = {"sanity.restored": collect_star_overflow}


# ---------------------------------------------------------------- runtime


MARKS = (
    MarkDefinition(
        id="star",
        label=TEXT["mark.star.label"],
        acquisition=TEXT["mark.star.acquisition"],
        minimum=0,
        maximum=None,
        # 无上限：以「每回合最多消耗 10 枚」当满槽参照，攒够就换高位配色。
        bar_tiers=((10, TEXT["data.characters.bigstar.module.1"], "warn"),),
        triggers=("sanity.restore.overflow",),
        hooks=(collect_star_overflow,),
     description=TEXT["mark.star.description"]),
)


HOOKS = {"search.pool_weight": star_doll_pool_weight}

# 开局核心角色：不可被禁用（内容自声明，核心不写死名单）。
PROTECTED_STARTER = True

# 界面头像图标（内容自声明）。
AVATAR = "i-av2"

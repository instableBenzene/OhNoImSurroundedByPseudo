"""房客档案：比格小星（2 号）。"""

# 按“定义 / 修饰器 / 技能函数”组织；角色专属逻辑集中在本文件。

from ..types import A, CharacterDefinition, MarkDefinition
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "bigstar", 2, "比格小星", "看起来呆呆的社牛学生，最喜欢吃松饼。",
    "cheerful", "gentle", 3, ("大学生", "留学生", "日语掌握者", "18-24岁", "未知的性别", "星星"),
    (A("hell_gift", "地狱的赠礼", "比格小星未被禁用时，房客在外出搜索时可能获得“可爱的玩偶”。可爱的玩偶（紫色）【工具】【工艺品】【消耗品】·仅可用于比格小星，使用后回复25理智。一个“快乐恶魂”玩偶，比格小星总喜欢带着她，为她拍摄不同的照片。"),
     A("everyone_star", "大家的星星", "比格小星回复的理智中超过100的部分将转化为等量【星之印记-比格小星】。每回合开始时，消耗至多10个【星之印记-比格小星】，为当前理智值最低的1名房客回复等同于消耗印记数*0.5的理智。")),
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
        raise RuleViolation("可爱的玩偶只能由比格小星使用。")
    engine._restore_sanity(tenant, 25, item.name)


def collect_star_overflow(engine: EngineProtocol, tenant: object, overflow: float) -> bool:
    """大家的星星：理智回复溢出时累计为星之印记。

    与伪人薯条的“暴露值”同属“理智溢出转化”体系：小星按 100% 转为星之印记，
    薯条的替身按 50% 转为暴露印记（对外称暴露值）。

    使用处：value_system._restore_sanity 的溢出结算段。
    """
    if (
        tenant.character_id == "bigstar" and overflow
        and engine._passive_available(tenant, "bigstar.star_overflow")
    ):
        engine._gain_mark(tenant, "star", overflow)
        return True
    return False


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
        engine._restore_sanity(target, amount * .5, "大家的星星")

def turn_start(engine, tenant):
    """回合初实例钩子：委托给「大家的星星」。"""
    everyone_star(engine, tenant)

TURN_START = turn_start


VALUE_HOOKS = {"restore_overflow": collect_star_overflow}


# ---------------------------------------------------------------- runtime


MARKS = (
    MarkDefinition(
        id="star",
        label="星之印记-比格小星",
        acquisition="比格小星回复理智超过 100 的部分，转为等量星之印记。",
        minimum=0,
        maximum=None,
        # 无上限：以「每回合最多消耗 10 枚」当满槽参照，攒够就换高位配色。
        bar_tiers=((10, "满档", "warn"),),
        triggers=("sanity.restore.overflow",),
        hooks=(collect_star_overflow,),
     description="从溢出的理智里析出的微光，一颗一颗攒着。"),
)


HOOKS = {"search.pool_weight": star_doll_pool_weight}

# 开局核心角色：不可被禁用（内容自声明，核心不写死名单）。
PROTECTED_STARTER = True

# 界面头像图标（内容自声明）。
AVATAR = "i-av2"

"""房客档案：清桃（12 号，正义执行／持之以恒）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "peach", 12, "青桃", "助人为乐的小道士，带着糯米与符纸。",
    "gentle", "keen", 3, ("道士", "16-18岁", "女性", "神秘学研究者"),
    # 限制交给 chips（STYLE §12 规则 3）：实现是给**该房客**打一次性状态——即"每人每局一次"，
    # 不是"全场一次"（口径以代码为准）。
    (A("slow_guard", "持之以缓",
       "需屋内有青桃。\n房客理智从 **≥50** 跌破 **50** 时：拉回 **50**，并在本回合结束前使其不低于 **50**。",
       chips=("每名房客每局 1 次",)),
     A("justice_execution", "正义执行", "当伪人即将突破时，避免这次突破，且该伪人接下来两个回合不会来访。触发后该能力失效。")),
)

register_status_definition(
    StatusDefinition(
        "peach_slow_guard",
        "持之以恒",
        "other",
        shown=frozenset({"layers"}),
        source_id="passive:peach.slow_guard",
     description="在它真正出手前，先把伤害一点点拖慢、拖散。")
)
register_status_definition(
    StatusDefinition(
        "peach_slow_guard_used",
        "已被持之以恒保护",
        "other",
        shown=frozenset(),
        source_id="passive:peach.slow_guard",
        permanent=True,
     description="那份从容已经用掉，剩下的只能硬接。")
)

# ---------------------------------------------------------------- modifier
def slow_guard_floor(
    engine: EngineProtocol, tenant: object, before: float, target: float
):
    """持之以恒：理智削减时的 50 下限与首次跌破触发。

    返回要使用的理智下限（None 表示不拦截）。首次触发会挂上保护 condition；
    使用处：value_system._reduce_sanity。
    """
    guard = tenant.condition("peach_slow_guard")
    if guard.active:
        return 50.0
    if tenant.condition("peach_slow_guard_used").active:
        return None
    if not (before >= 50 and target < 50):
        return None
    if not any(
        value.character_id == "peach" for value in engine.home_tenants()
    ):
        return None
    tenant.set_status(
        "peach_slow_guard", intensity=1, layers=2
    )
    tenant.set_status("peach_slow_guard_used", intensity=1, layers=99)
    engine._log(
        f"青桃的「持之以恒」保护了{engine.character(tenant).name}："
        f"理智被拉回50且到下一回合结束前不低于50。"
    )
    return 50.0


def justice_execution_guard(engine: EngineProtocol) -> bool:
    """正义执行（justice_execution）：阻止一次伪人突破并压制伪人两回合。

    使用处：pseudo_system._attempt_breakthrough。
    """
    guardian = next(
        (value for value in engine.home_tenants() if value.character_id == "peach"),
        None,
    )
    ability = guardian.ability_state("justice_execution") if guardian else None
    if (
        guardian
        and ability is not None
        and not ability.disabled
        and engine._passive_available(guardian, "peach.guard")
    ):
        ability.disabled = True
        engine._suppress_pseudo(2, ("visit",))
        engine._log("青桃发动「正义执行」，阻止突破；伪人被压制两回合。")
        return True
    return False


HOOKS = {
    "sanity.floor": slow_guard_floor,
    "breakthrough.guard": justice_execution_guard,
}

# 界面头像图标（内容自声明）。
AVATAR = "i-av3"

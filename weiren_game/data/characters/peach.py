"""房客档案：清桃（12 号，正义执行／持之以恒）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "peach", 12, TEXT["character.peach.name"], TEXT["character.peach.description"],
    "gentle", "keen", 3, (TEXT["character.peach.tag.0"], TEXT["character.peach.tag.1"], TEXT["character.peach.tag.2"], TEXT["character.peach.tag.3"]),
    # 限制交给 chips（STYLE §12 规则 3）：实现是给**该房客**打一次性状态——即"每人每局一次"，
    # 不是"全场一次"（口径以代码为准）。
    (A("slow_guard", TEXT["ability.slow_guard.name"],
       TEXT["ability.slow_guard.description"],
       chips=(TEXT["ability.slow_guard.chip.0"],)),
     A("justice_execution", TEXT["ability.justice_execution.name"], TEXT["ability.justice_execution.description"])),
)

register_status_definition(
    StatusDefinition(
        "peach_slow_guard",
        TEXT["status.peach_slow_guard.label"],
        "other",
        shown=frozenset({"layers"}),
        source_id="passive:peach.slow_guard",
     description=TEXT["status.peach_slow_guard.description"])
)
register_status_definition(
    StatusDefinition(
        "peach_slow_guard_used",
        TEXT["status.peach_slow_guard_used.label"],
        "other",
        shown=frozenset(),
        source_id="passive:peach.slow_guard",
        permanent=True,
     description=TEXT["status.peach_slow_guard_used.description"])
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
        TEXT["data.characters.peach.slow_guard_floor.1"].format(p1=engine.character(tenant).name)
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
        engine._log(TEXT["data.characters.peach.justice_execution_guard.1"])
        return True
    return False


HOOKS = {
    "sanity.floor": slow_guard_floor,
    "breakthrough.guard": justice_execution_guard,
}

# 界面头像图标（内容自声明）。
AVATAR = "i-av3"

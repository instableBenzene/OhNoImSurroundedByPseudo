"""测试 DLC 角色：老楷（likai）。

人物：稳重/机敏双主性格、携带 4，常年流浪、生存力极强。
被动：死亡后 75%-15%×死亡次数（最低 5%）重生成新访客回到访客池，
并累计死亡次数（每次重生时最大生命值 +10×死亡次数）。
"""

from weiren_game.data.types import AbilityDefinition, CharacterDefinition
from weiren_game.global_event import GlobalEventDefinition, register_global_event

register_global_event(
    GlobalEventDefinition(
        id="likai.deaths",
        label="老楷·死亡次数",
        source_id="dlc:likai_test",
    )
)


def _rebirth_ability() -> AbilityDefinition:
    """流浪者的重生（被动描述）。"""
    return AbilityDefinition(
        "likai_rebirth",
        "老楷的重生",
        "死亡后有 x% 可能以全新访客的身份回到访客池；"
        "概率 = 75% - 15%×死亡次数（最低 5%）。每次死亡后，"
        "老楷再次入住时最大生命值 +10×死亡次数。",
    )


CHARACTER = CharacterDefinition(
    "likai",
    900,
    "老楷",
    "常年流浪的中年人，具有极强的生存能力。",
    "steady",
    "keen",
    4,
    ("25岁-30岁", "男性", "无业游民"),
    passives=(_rebirth_ability(),),
    available=True,
    source_note="测试 DLC：likai_test",
)

# 头像：从 12 个形状里挑一个（不声明会回退通用头像、`validate_content` 也会提醒）。
# 更贴题的做法是给整张头像：`likai_test/avatars/characters/likai.svg`（或放内容层
# `data/avatars/characters/likai.svg`）—— 那样连配件一起定死，不再受哈希派生影响。
AVATAR = "i-av9"


def initial_setup(engine: object, tenant: object) -> None:
    """老楷入住时按累计死亡次数提升最大生命值。"""
    deaths = int(engine.state.world.global_events.value_of("likai.deaths", 0.0))
    if deaths:
        tenant.max_health += 10 * deaths


def tenant_death(engine: object) -> None:
    """老楷死亡：累计死亡次数并按概率把 likai 放回访客候选池。"""
    for tenant in engine.state.house.tenants.values():
        if tenant.character_id != "likai" or tenant.alive:
            continue
        deaths = (
            int(engine.state.world.global_events.value_of("likai.deaths", 0.0)) + 1
        )
        engine.state.world.global_events.set("likai.deaths", float(deaths), 99)
        chance = max(.05, .75 - .15 * deaths)
        if engine._rng("dlc.likai.rebirth", tenant.id).random() < chance:
            pool = engine.state.world.visitors.visitor_pool
            if "likai" not in pool:
                pool.append("likai")
        return


TENANT_DEATH = tenant_death

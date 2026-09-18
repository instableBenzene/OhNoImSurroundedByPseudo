"""房客档案：罗丁（14 号，分享型旅行家）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "looting", 14, "罗丁", "去过许多地方的旅行者，乐意分享背包中的必需品。",
    "cheerful", "steady", 5, ("旅行家", "18-24岁", "男性"),
    (A("sharing", "分享的乐趣", "罗丁在入住时，获得1份随机【食物】与1份矿泉水。"),
     A("travel_experience", "旅游的经验", "罗丁搜索时，遭遇伪人概率-10%；搜索返回时额外获得1份矿泉水与1份随机【食物】。")),
)

# ---------------------------------------------------------------- function
def on_arrival(engine: EngineProtocol, tenant: object) -> None:
    """分享的乐趣：入住时带来随机食物与矿泉水。

    使用处：visitor_system._on_tenant_accepted。
    """
    if tenant.character_id != "looting":
        return
    if not engine._passive_available(tenant, "looting.arrival"):
        return
    from ..items import ITEMS

    food = engine._random_item(required_tags=("food",), event_id="looting.arrival")
    engine._gain_item(food)
    engine._gain_item("water")
    engine._log(f"罗丁分享了{ITEMS[food].name}和矿泉水。")


def encounter_penalty(engine: EngineProtocol, tenant: object) -> float:
    """旅游的经验：遭遇伪人概率 -10%。

    使用处：pseudo_system 的搜索遭遇率计算。
    """
    if engine._passive_available(tenant, "looting.encounter"):
        return .10
    return 0.0


def search_reward(engine: EngineProtocol, tenant: object, guaranteed: list[str]) -> None:
    """旅游的经验：搜索返回额外获得水与随机食物。

    使用处：search_system 的保底战利品收集。
    """
    if not engine._passive_available(tenant, "looting.reward"):
        return
    guaranteed.extend((
        "water",
        engine._random_item(required_tags=("food",), event_id=_event_id("looting.food"), event_suffix=(tenant.id,)),
    ))


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

SEARCH_REWARD = search_reward

NODE_HOOKS = {
    "pseudo_encounter_penalty": encounter_penalty,
    "on_arrival": on_arrival,
}

# 界面头像图标（内容自声明）。
AVATAR = "i-av1"

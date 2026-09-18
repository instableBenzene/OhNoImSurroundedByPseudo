"""房客档案：薯条（10 号，人设机制；也是伪人薯条的人类形态）。

按“定义 / 修饰器 / 技能函数”组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition

PERSONA_LABELS = {
    "lucky": "幸运", "unlucky": "不幸", "focused": "专注", "distracted": "分心",
    "vitality": "活力", "fatigued": "疲惫", "alert": "警觉", "dull": "迟钝",
    "inspired": "灵感", "confused": "混乱",
}
PERSONA_OPPOSITES = {
    "lucky": "unlucky", "unlucky": "lucky",
    "focused": "distracted", "distracted": "focused",
    "vitality": "fatigued", "fatigued": "vitality",
    "alert": "dull", "dull": "alert",
    "inspired": "confused", "confused": "inspired",
}
PERSONA_FLAVOR = {
    "lucky": "今天似乎格外顺利，连巧合都站在自己这边。",
    "unlucky": "做什么都差一口气，坏事像是约好了找上门。",
    "focused": "心无旁骛，把注意力拧成一根绳。",
    "distracted": "注意力总被别处牵走，手边的事频频出错。",
    "vitality": "精神头很足，身体像是比平时更经得起折腾。",
    "fatigued": "倦意压着眼皮，每一步都比平时更沉。",
    "alert": "神经紧绷，一点风吹草动都逃不过耳朵。",
    "dull": "感官像蒙了层布，危险的信号总慢半拍。",
    "inspired": "灵感忽然通了，脑子转得飞快。",
    "confused": "思路打结，连自己刚想做什么都记不清。",
}
PERSONAS = tuple(PERSONA_LABELS)
for _persona in PERSONAS:
    register_status_definition(StatusDefinition(
        f"persona_{_persona}", f"人设-{_persona}", "other",
        shown=frozenset(), source_id="character:fries",
        permanent=True,
        # 人设不进状态栏：它在详情页头像右侧的小面板里连同风味一起展示。
        chip_hidden=True,
        description=PERSONA_FLAVOR[_persona],
    ))


def detail_slot(engine: EngineProtocol, tenant: object) -> list[dict]:
    """详情页小面板：当前持有的「人设」逐条列出（名称 + 风味），不占状态栏。

    声明为模块级 ``DETAIL_SLOT``；未持有任何人设时返回空列表（面板就不显示）。
    """
    rows: list[dict] = []
    for key in engine._personas_of(tenant):
        rows.append({
            "kind": "text",
            "label": "人设",
            "text": f"{PERSONA_LABELS.get(key, key)}——{PERSONA_FLAVOR.get(key, '')}",
        })
    return rows


DETAIL_SLOT = detail_slot

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "fries", 10, "薯条", "一位随波逐流的旅人，总是看上去充满活力。",
    "stubborn", "cheerful", 4, ("无业游民", "16-18岁", "男性"),
    (A("odd_belongings", "莫名带点东西", "入住时带来一把“燧发枪”和两枚“弹药-燧发枪”。\n“燧发枪”（金色）【工具】【易损品】\n· 搜索中受到伪人主动能力影响时，有 **25%** 可能免疫；消耗一个【弹药-燧发枪】可把概率提升为 **100%**。\n· 触发后有 **25%** 可能被消耗；若消耗了弹药则改为 **5%**。\n“弹药-燧发枪”（紫色）【工具】【消耗品】【可堆叠】\n· 可被燧发枪消耗。\n*一个较为古典的燧发枪；不到必要关头，薯条不会浪费他的子弹。薯条制作的子弹尽管逊色于机器制造的，威力仍不容小觑。*"),
     A("odd_luck", "莫名的幸运B", "薯条搜索时遭遇伪人概率-6%；有40%可能额外获得1件随机物资；有15%可能获得一个【人设-薯条】。")),
    (A("deep_thought", "深度思考", "获得一个【人设-薯条】：\n· **最多同时持有 2 个**；获得第 **3 个**时随机移除其中 1 个（优先移除互斥的）。\n*各人设的机制与描述见下方「人设」一栏。*", chips=("每次对局 1 次",)),),
)

# ---------------------------------------------------------------- modifier
def encounter_penalty(engine: EngineProtocol, tenant: object) -> float:
    """搜索遭遇伪人概率的角色修正：幸运 B -6%，人设警觉 -10%、迟钝 +10%。

    使用处：pseudo_system 的搜索遭遇率计算。
    """
    penalty = 0.0
    if engine._passive_available(tenant, "fries.human.encounter"):
        penalty += .06
    if engine._has_persona(tenant, "alert"):
        penalty += .10
    if engine._has_persona(tenant, "dull"):
        penalty -= .10
    return penalty


def search_fortune(engine: EngineProtocol, tenant: object) -> int:
    """人设对搜索时运的修正：幸运 +1、不幸 -1。

    使用处：search_system 的时运计算。
    """
    fortune = 0
    if engine._has_persona(tenant, "lucky"):
        fortune += 1
    if engine._has_persona(tenant, "unlucky"):
        fortune -= 1
    return fortune


def item_fragility(engine: EngineProtocol, tenant: object) -> float:
    """人设对易损品消耗概率的修正：灵感 -20%、混乱 +20%。

    使用处：item_system 的易损概率计算。
    """
    value = 0.0
    if engine._has_persona(tenant, "inspired"):
        value -= .20
    if engine._has_persona(tenant, "confused"):
        value += .20
    return value


# ---------------------------------------------------------------- function
def grant_persona(engine: EngineProtocol, tenant: object) -> str:
    """获得一项随机人设（先移除对立人设），记录日志并返回人设名。

    使用处：深度思考主动技能与“莫名的幸运 B”搜索额外触发。
    """
    rng = engine._rng(_event_id("fries.persona"), tenant.id)
    candidate = rng.choice(list(PERSONA_OPPOSITES))
    opposite = PERSONA_OPPOSITES[candidate]
    current = [
        value for value in engine._personas_of(tenant)
        if value != opposite
    ]
    if candidate not in current:
        current.append(candidate)
    removed = None
    while len(current) > 2:
        removed = rng.choice(current)
        current.remove(removed)
    engine._set_personas(tenant, current)
    suffix = f"；随机移除{PERSONA_LABELS[removed]}" if removed else ""
    engine._log(f"薯条获得人设：{PERSONA_LABELS[candidate]}{suffix}。")
    return candidate


def use_deep_thought(engine: EngineProtocol, actor: object) -> None:
    """深度思考：获得一项随机人设，每局一次。

    使用处：ability_system.use_ability 的薯条分发分支。
    """
    grant_persona(engine, actor)


def costs_deep_thought(
    engine: EngineProtocol, actor: object, *, option: object
) -> list[T]:
    """深度思考：每局一次（game 资源）。"""
    return [T("game", 1, key="deep_thought_once")]


def on_arrival(engine: EngineProtocol, tenant: object) -> None:
    """莫名带点东西：薯条在入住时会带来一把“燧发枪”和两枚“弹药-燧发枪”。燧发枪（金色）【工具】【易损品】·在搜索中受到伪人主动能力影响时，有25%可能免疫该能力影响，消耗一个【弹药-燧发枪】，将概率提升为100%·触发后有25%可能被消耗，若消耗了弹药-燧发枪则改为5%一个较为古典的燧发枪，不到必要关头，薯条不会浪费他的子弹。弹药-燧发枪（紫色）【工具】【消耗品】【可堆叠】·可被燧发枪消耗。薯条制作的燧发枪子弹，尽管逊色于机器制造的子弹，威力仍不容小觑。

    使用处：visitor_system._on_tenant_accepted。
    """
    if tenant.character_id != "fries":
        return
    if not engine._passive_available(tenant, "fries.human.arrival"):
        return
    engine._gain_item("flintlock")
    engine._gain_item("flintlock_ammo", 2)
    engine._log("薯条带来了燧发枪和两枚弹药。")


def search_reward(engine: EngineProtocol, tenant: object, guaranteed: list[str]) -> None:
    """莫名的幸运 B：40% 额外物资、15% 获得一项人设。

    使用处：search_system 的保底战利品收集。
    """
    if not engine._passive_available(tenant, "fries.human.search"):
        return
    extra_success = (
        engine._rng(_event_id("fries.human.extra"), tenant.id).random() < .40
    )
    engine._skill_outcome(tenant, "fries.odd_luck.extra", extra_success)
    if extra_success:
        guaranteed.append(engine._random_item(event_id=_event_id("fries.human.reward"), event_suffix=(tenant.id,)))
    persona_success = (
        engine._rng(_event_id("fries.human.persona"), tenant.id).random() < .15
    )
    engine._skill_outcome(tenant, "fries.odd_luck.persona", persona_success)
    if persona_success:
        grant_persona(engine, tenant)


def _event_id(name):
    """返回事件名对应的 EVENT_IDS 编号。"""
    from weiren_game.data import EVENT_IDS
    return EVENT_IDS[name]

ACTIVE_DISPATCH = {
    "deep_thought": (
        lambda engine, actor, **kwargs: use_deep_thought(engine, actor)
    ),
}

SEARCH_REWARD = search_reward


def end_of_turn_sanity_cost(
    engine: EngineProtocol, tenant: object, cost: float
) -> float:
    """人设对回合末理智消耗的修正：专注减半、心不在焉翻倍。"""
    if engine._has_persona(tenant, "focused"):
        cost *= .50
    if engine._has_persona(tenant, "distracted"):
        cost *= 2.0
    return cost


def end_of_turn_health_loss(
    engine: EngineProtocol, tenant: object, amount: float
) -> float:
    """人设对回合末生命流失的修正：活力减半、疲惫翻倍。"""
    if engine.state.flow.phase == "turn_end":
        if engine._has_persona(tenant, "vitality"):
            amount *= .5
        if engine._has_persona(tenant, "fatigued"):
            amount *= 2
    return amount


VALUE_HOOKS = {
    "end_sanity_cost": end_of_turn_sanity_cost,
    "health_loss": end_of_turn_health_loss,
}


def _fries_fragile_modifier(context: object):
    """薯条人设：灵感/混乱对易损概率的修正。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant is None:
        return
    delta = item_fragility(engine, tenant)
    if delta:
        yield (
            spec("chance").path("易损").flat(float(delta))
            .source("角色技能", "薯条", "人设")
        )


from weiren_game.modifier_rules import register_modifier_provider
register_modifier_provider("chance", _fries_fragile_modifier)


def _fries_fortune_modifier(context: object):
    """薯条人设：幸运/不幸的搜索时运修正。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant is None:
        return
    value = search_fortune(engine, tenant)
    if value:
        yield spec("search").path("时运").flat(value).source("角色技能", "薯条", "人设")


from weiren_game.modifier_rules import register_modifier_provider as _regf
_regf("search", _fries_fortune_modifier)


def _fries_loss_modifier(context: object):
    """薯条人设：活力 ×0.5 / 疲惫 ×2（回合末生命流失）。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "fries" or engine.state.flow.phase != "turn_end":
        return
    if engine._has_persona(tenant, "vitality"):
        yield spec("healthLoss").path("生命流失").mul(0.5).source("角色技能", "薯条", "人设")
    if engine._has_persona(tenant, "fatigued"):
        yield spec("healthLoss").path("生命流失").mul(2.0).source("角色技能", "薯条", "人设")


from weiren_game.modifier_rules import register_modifier_provider as _regfl
_regfl("healthLoss", _fries_loss_modifier)


def _fries_end_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "fries":
        return
    if engine._has_persona(tenant, "focused"):
        yield spec("sanityConsume").path("回合末消耗").mul(0.5).source("角色技能", "薯条", "人设")
    if engine._has_persona(tenant, "distracted"):
        yield spec("sanityConsume").path("回合末消耗").mul(2.0).source("角色技能", "薯条", "人设")


from weiren_game.modifier_rules import register_modifier_provider as _regfe
_regfe("sanityConsume", _fries_end_sanity_modifier)

NODE_HOOKS = {
    "pseudo_encounter_penalty": encounter_penalty,
    "item_fragility": item_fragility,
    "on_arrival": on_arrival,
}

# 界面头像图标（内容自声明）。
AVATAR = "i-av10"


PERSONA_TEXT = {
    "lucky": "搜索时获得时运 +1（与不幸互斥）。",
    "unlucky": "搜索时获得时运 -1（与幸运互斥）。",
    "focused": "回合末理智消耗 -50%（与分心互斥）。",
    "distracted": "回合末理智消耗 +100%（与专注互斥）。",
    "vitality": "回合末生命流失 -50%（与疲惫互斥）。",
    "fatigued": "回合末生命流失 +100%（与活力互斥）。",
    "alert": "搜索时遭遇伪人技能概率 -10%（与迟钝互斥）。",
    "dull": "搜索时遭遇伪人技能概率 +10%（与警觉互斥）。",
    "inspired": "易损品消耗概率 -20%（与混乱互斥）。",
    "confused": "易损品消耗概率 +20%（与灵感互斥）。",
}


def CODEX_EXTRA() -> list:
    """图鉴补充：薯条的 persona（人格）机制与描述。"""
    labels = globals().get("PERSONA_LABELS", {})
    flavor = globals().get("PERSONA_FLAVOR", {})
    entries = []
    for key in globals().get("PERSONAS", ()):
        mech = PERSONA_TEXT.get(key, "")
        flo = flavor.get(key, "") if isinstance(flavor, dict) else ""
        text = mech + ("　" + flo if flo else "")
        entries.append((labels.get(key, key), text or "—"))
    return [{"title": "人设（persona）", "entries": entries}]

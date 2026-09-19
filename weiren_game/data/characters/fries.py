"""房客档案：薯条（10 号，人设机制；也是伪人薯条的人类形态）。

按「定义 / 修饰器 / 技能函数」组织；角色专属逻辑集中在本文件。
"""

from ..types import A, CharacterDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.data.lang import TEXT

PERSONA_LABELS = {
    "lucky": TEXT["data.characters.fries.PERSONA_LABELS.lucky"], "unlucky": TEXT["data.characters.fries.PERSONA_LABELS.unlucky"], "focused": TEXT["data.characters.fries.PERSONA_LABELS.focused"], "distracted": TEXT["data.characters.fries.PERSONA_LABELS.distracted"],
    "vitality": TEXT["data.characters.fries.PERSONA_LABELS.vitality"], "fatigued": TEXT["data.characters.fries.PERSONA_LABELS.fatigued"], "alert": TEXT["data.characters.fries.PERSONA_LABELS.alert"], "dull": TEXT["data.characters.fries.PERSONA_LABELS.dull"],
    "inspired": TEXT["data.characters.fries.PERSONA_LABELS.inspired"], "confused": TEXT["data.characters.fries.PERSONA_LABELS.confused"],
}
PERSONA_OPPOSITES = {
    "lucky": "unlucky", "unlucky": "lucky",
    "focused": "distracted", "distracted": "focused",
    "vitality": "fatigued", "fatigued": "vitality",
    "alert": "dull", "dull": "alert",
    "inspired": "confused", "confused": "inspired",
}
PERSONA_FLAVOR = {
    "lucky": TEXT["data.characters.fries.PERSONA_FLAVOR.lucky"],
    "unlucky": TEXT["data.characters.fries.PERSONA_FLAVOR.unlucky"],
    "focused": TEXT["data.characters.fries.PERSONA_FLAVOR.focused"],
    "distracted": TEXT["data.characters.fries.PERSONA_FLAVOR.distracted"],
    "vitality": TEXT["data.characters.fries.PERSONA_FLAVOR.vitality"],
    "fatigued": TEXT["data.characters.fries.PERSONA_FLAVOR.fatigued"],
    "alert": TEXT["data.characters.fries.PERSONA_FLAVOR.alert"],
    "dull": TEXT["data.characters.fries.PERSONA_FLAVOR.dull"],
    "inspired": TEXT["data.characters.fries.PERSONA_FLAVOR.inspired"],
    "confused": TEXT["data.characters.fries.PERSONA_FLAVOR.confused"],
}
PERSONAS = tuple(PERSONA_LABELS)
for _persona in PERSONAS:
    register_status_definition(StatusDefinition(
        f"persona_{_persona}", TEXT["data.characters.fries.module.1"].format(p1=_persona), "other",
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
            "label": TEXT["data.characters.fries.detail_slot.1"],
            "text": f"{PERSONA_LABELS.get(key, key)}——{PERSONA_FLAVOR.get(key, '')}",
        })
    return rows


DETAIL_SLOT = detail_slot

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "fries", 10, TEXT["character.fries.name"], TEXT["character.fries.description"],
    "stubborn", "cheerful", 4, (TEXT["character.fries.tag.0"], TEXT["character.fries.tag.1"], TEXT["character.fries.tag.2"]),
    (A("odd_belongings", TEXT["ability.odd_belongings.name"], TEXT["ability.odd_belongings.description"]),
     A("odd_luck", TEXT["ability.odd_luck.name"], TEXT["ability.odd_luck.description"])),
    (A("deep_thought", TEXT["ability.deep_thought.name"], TEXT["ability.deep_thought.description"], chips=(TEXT["ability.deep_thought.chip.0"],)),),
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

    使用处：深度思考主动技能与「莫名的幸运 B」搜索额外触发。
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
    suffix = TEXT["data.characters.fries.grant_persona.1"].format(p1=PERSONA_LABELS[removed]) if removed else ""
    engine._log(TEXT["data.characters.fries.grant_persona.2"].format(p1=PERSONA_LABELS[candidate], p2=suffix))
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
    """莫名带点东西：薯条在入住时会带来一把「燧发枪」和两枚「弹药-燧发枪」。燧发枪（金色）【工具】【易损品】·在搜索中受到伪人主动能力影响时，有25%可能免疫该能力影响，消耗一个【弹药-燧发枪】，将概率提升为100%·触发后有25%可能被消耗，若消耗了弹药-燧发枪则改为5%一个较为古典的燧发枪，不到必要关头，薯条不会浪费他的子弹。弹药-燧发枪（紫色）【工具】【消耗品】【可堆叠】·可被燧发枪消耗。薯条制作的燧发枪子弹，尽管逊色于机器制造的子弹，威力仍不容小觑。

    使用处：visitor_system._on_tenant_accepted。
    """
    if tenant.character_id != "fries":
        return
    if not engine._passive_available(tenant, "fries.human.arrival"):
        return
    engine._gain_item("flintlock")
    engine._gain_item("flintlock_ammo", 2)
    engine._log(TEXT["data.characters.fries.on_arrival.1"])


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
            spec("chance").path("fragile").flat(float(delta))
            .source("ability", "fries", "persona")
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
        yield spec("search").path("luck").flat(value).source("ability", "fries", "persona")


from weiren_game.modifier_rules import register_modifier_provider as _regf
_regf("search", _fries_fortune_modifier)


def _fries_loss_modifier(context: object):
    """薯条人设：活力 ×0.5 / 疲惫 ×2（回合末生命流失）。"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "fries" or engine.state.flow.phase != "turn_end":
        return
    if engine._has_persona(tenant, "vitality"):
        yield spec("healthLoss").path("health_loss").mul(0.5).source("ability", "fries", "persona")
    if engine._has_persona(tenant, "fatigued"):
        yield spec("healthLoss").path("health_loss").mul(2.0).source("ability", "fries", "persona")


from weiren_game.modifier_rules import register_modifier_provider as _regfl
_regfl("healthLoss", _fries_loss_modifier)


def _fries_end_sanity_modifier(context: object):
    from weiren_game.modifier_rules import spec
    engine = context["engine"]; tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != "fries":
        return
    if engine._has_persona(tenant, "focused"):
        yield spec("sanityConsume").path("turn_end_consume").mul(0.5).source("ability", "fries", "persona")
    if engine._has_persona(tenant, "distracted"):
        yield spec("sanityConsume").path("turn_end_consume").mul(2.0).source("ability", "fries", "persona")


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
    "lucky": TEXT["data.characters.fries.PERSONA_TEXT.lucky"],
    "unlucky": TEXT["data.characters.fries.PERSONA_TEXT.unlucky"],
    "focused": TEXT["data.characters.fries.PERSONA_TEXT.focused"],
    "distracted": TEXT["data.characters.fries.PERSONA_TEXT.distracted"],
    "vitality": TEXT["data.characters.fries.PERSONA_TEXT.vitality"],
    "fatigued": TEXT["data.characters.fries.PERSONA_TEXT.fatigued"],
    "alert": TEXT["data.characters.fries.PERSONA_TEXT.alert"],
    "dull": TEXT["data.characters.fries.PERSONA_TEXT.dull"],
    "inspired": TEXT["data.characters.fries.PERSONA_TEXT.inspired"],
    "confused": TEXT["data.characters.fries.PERSONA_TEXT.confused"],
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
    return [{"title": TEXT["data.characters.fries.CODEX_EXTRA.1"], "entries": entries}]

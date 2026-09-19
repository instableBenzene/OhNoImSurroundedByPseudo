"""房客档案：STAR（DLC_Character_STAR）。

"""

from weiren_game.data.types import A, CharacterDefinition, MarkDefinition, T
from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.modifier_rules import register_modifier_provider
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import pack_text_from_file
TEXT = pack_text_from_file(__file__)

# ---------------------------------------------------------------- 可调数值

TENANT_ID = "STAR"

ENERGY_MARK = "energy"
# 上限 5：收入每回合 2~3，若上限只有 3，电量永远停在顶格，
# 玩家只能看到「满」和「被开火清空」两种状态——中间档位根本不存在。
ENERGY_MAX = 5               # 能量上限。调高=存量层次更细；调低=更容易被"用光"惩罚
ENERGY_PER_TURN = 2          # 回合初充能。调高=更宽裕；调低=更紧
ENERGY_FULL_HEALTH_BONUS = 1 # 满生命额外充能。0 = 关闭该机制

# 供能代扣：回合末自动扣 1 点，买回"身体不必自己硬撑"。
# 这是电量的**每回合常规支出**，也是整个能源经济能"流动"起来的原因。
# 设 0 则关闭代扣（电量又会退回只涨不跌的顶格状态）。
ENERGY_UPKEEP = 1
UPKEEP_SANITY_FACTOR = 0.50  # 代扣成功：回合末理智消耗 ×此值
UPKEEP_HEALTH_FACTOR = 0.50  # 代扣成功：高生命值自然流失 ×此值

LOW_POWER_PENALTY = 3        # 低功耗（能量为 0）：回合末理智消耗与生命流失各 +此值。调高=更痛

SANITY_DAMAGE_REDUCTION = 0.30  # 情感淡漠④：受理智伤害减免。调高=更耐打
DEPRESSION_FACTOR = 0.50     # ①消沉变动倍率（双向，好的坏的都慢）
SANITY_RESTORE_FACTOR = 0.50 # ②理智回复倍率
AWAKENING_FACTOR = 0.50      # ③觉醒情绪获取倍率（主要对冲「开朗」的正加成）

COVER_RESIST = 0.50          # 掩护射击：为队友提供的抵御率
# 佩枪自带的基础抵御率。**已定为 0**：掩护射击只有"开"与"关"两个状态，
# 关掉就是完全不支援（不再有"枪在屋里就白送一点抵御"的常驻档）。
# 设成 >0 即可把那一档加回来（`_cover_fire_modifier` 的基础档分支仍在，见 §4.3）。
COVER_BASE_RESIST = 0.0
COVER_COST = 1               # 掩护射击：每次实际抵御扣的电量

# 「掩护射击」开关的状态 id（不衰减的常驻状态，由玩家主动开合）
ST_COVER = "star_cover"

GUN_ID = "star_sidearm"      # 佩枪 id（在 items/ 中定义）
# 开火：**放空全部电量**，而且**必须攒满**才能扣扳机。
# 为什么要求满格：既然消耗是"全部"，4 格和 5 格打出去的效果**完全一样**，
# 玩家就会一到 3 格（旧门槛）随手打掉——电池上半段永远没人看。
# 改成"满格才能打"之后，攒满本身变成明确目标，"还差一格"是有意义的状态。
# 「过载 → 取消冷却」的接入方案见 DESIGN.md §3.4 / §11 TODO-3。
FIRE_MIN_ENERGY = ENERGY_MAX  # 开火门槛 = 满电量；调小即变成"够 N 点就能打"
FIRE_COOLDOWN = 3            # 开火冷却回合数；0 = 无冷却。调高=更难靠开枪锁死伪人
FIRE_SUPPRESS_TURNS = 1      # 开火对伪人的压制回合数。必须 < FIRE_COOLDOWN，否则可锁死伪人
FIRE_MAX_PER_GAME = 0        # >0 时限制每局开火次数（0 = 不限制）

# 文案（术语层：资源 / 系统 / 方案）
#
# 描写体例**对齐本体 24 人的写法**（对照 rose / dragon / onion / bigstar / sandwhite / zero329）：
#   · 主语写**角色名**，不写"自身"：本体是「洋葱在屋内时…」「沙白的理智消耗…」
#   · 专有名词用 `【】` 包起来：本体是「【恶魔印记-罗兹】」「【人设-薯条】」「【共情印记-洋葱】」
#     （`index.html::linkTags` 只给**物品 tag** 加悬浮，印记/状态名同样只是视觉约定）
#   · 限定条件**另起 `*` 句**，不揉进正文：本体是「*该能力有4回合冷却时间。」「*每个回合仅能使用1次。」
#   · 数值紧贴符号、不加空格：本体是「-25%」「+10%」「最多6层」
#   · **不用 `**加粗**`**（本体几乎不用；且 `*` 在 `mdText` 里是斜体标记，混用会串味）
NAME_CHARACTER = "STAR"
NAME_GUN = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_GUN"]
NAME_MARK = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_MARK"]
NAME_PASSIVE_ENERGY = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_PASSIVE_ENERGY"]
NAME_PASSIVE_APATHY = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.1"]
NAME_PASSIVE_COVER = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_PASSIVE_COVER"]
NAME_TOGGLE_COVER = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_TOGGLE_COVER"]
NAME_STATUS_COVER = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_STATUS_COVER"]
NAME_FIRE = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_FIRE"]
NAME_FIRE_DESC = (
    TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_FIRE_DESC"].format(p1=FIRE_SUPPRESS_TURNS, p2=NAME_MARK, p3=ENERGY_MAX, p4=ENERGY_MAX, p5=FIRE_COOLDOWN)
)
NAME_PASSIVE_ENERGY_DESC = (
    TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_PASSIVE_ENERGY_DESC"].format(p1=NAME_MARK, p2=ENERGY_MAX, p3=ENERGY_PER_TURN, p4=ENERGY_FULL_HEALTH_BONUS, p5=ENERGY_UPKEEP, p6=1 - UPKEEP_HEALTH_FACTOR, p7=ENERGY_UPKEEP, p8=LOW_POWER_PENALTY)
)
NAME_PASSIVE_APATHY_DESC = (
    TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.2"].format(p1=SANITY_DAMAGE_REDUCTION, p2=DEPRESSION_FACTOR)
)
NAME_PASSIVE_COVER_DESC = (
    TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_PASSIVE_COVER_DESC"].format(p1=NAME_GUN, p2=NAME_TOGGLE_COVER, p3=COVER_RESIST)
)
NAME_TOGGLE_COVER_DESC = (
    TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.NAME_TOGGLE_COVER_DESC"].format(p1=COVER_RESIST, p2=COVER_COST, p3=NAME_MARK, p4=COVER_COST)
)

# 事件命名空间（决定论随机的流名）
_EVENT = "dlc.STAR"


# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    TENANT_ID,
    9001,
    NAME_CHARACTER,
    TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.3"],
    "steady", "keen", 3,
    (TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.4"], TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.5"], TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.6"],  TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.7"]),
    passives=(
        A("energy_cycle", NAME_PASSIVE_ENERGY, NAME_PASSIVE_ENERGY_DESC),
        A("apathy", NAME_PASSIVE_APATHY, NAME_PASSIVE_APATHY_DESC),
    ),
    actives=(
        A("toggle_cover", NAME_TOGGLE_COVER, NAME_TOGGLE_COVER_DESC),
        A(
            "fire", NAME_FIRE, NAME_FIRE_DESC, "none",
            chips=(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.8"].format(p1=FIRE_COOLDOWN),) if FIRE_COOLDOWN else (),
        ),
    ),
    available=True,
    source_note="DLC_Character_STAR",
)

MARKS = (
    MarkDefinition(
        id=ENERGY_MARK,
        label=NAME_MARK,
        acquisition=(
            TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.9"].format(p1=ENERGY_PER_TURN, p2=ENERGY_FULL_HEALTH_BONUS, p3=ENERGY_MAX, p4=ENERGY_UPKEEP)
        ),
        minimum=0,
        maximum=ENERGY_MAX,
        # 第 1 档处画一条红线：低于它即低功耗。刻度会同时出现在状态栏与详情页。
        bar_tiers=((1, TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.10"], "danger"),),
        description=TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.11"],
    ),
)

# 12 个形状里的通用"人 + 轮廓"款。
AVATAR = "i-av4"


# ---------------------------------------------------------------- 内部工具
def _energy(engine: object, tenant: object) -> float:
    """当前能量。"""
    return engine._mark_count(tenant, ENERGY_MARK)


def _gain_energy(engine: object, tenant: object, amount: int) -> None:
    """获得能量（印记自带上限钳制）。"""
    if amount > 0:
        engine._gain_mark(tenant, ENERGY_MARK, amount)


def _has_gun(tenant: object) -> bool:
    """是否持有佩枪。"""
    return any(held.item_id == GUN_ID for held in tenant.inventory.items)


def _low_power(tenant: object) -> bool:
    """低功耗：能量已用完（自动，不是开关）。"""
    return tenant.marks.count(ENERGY_MARK) <= 0


def _upkeep_affordable(engine: object, tenant: object) -> bool:
    """回合末电量够不够付供能代扣。

    **纯查询**：`_sanity_consume_modifier` / `_health_loss_modifier` 用它判断该走折扣还是走
    低功耗；真正扣电与写日志在结算点 `end_turn_settle` 里做（见下方 §modifier 段的注释）。
    """
    return ENERGY_UPKEEP > 0 and _energy(engine, tenant) >= ENERGY_UPKEEP


# ---------------------------------------------------------------- 约定回调
def turn_start(engine: EngineProtocol, tenant: object) -> None:
    """回合初：充能（基础 + 满生命额外），并**如实播报充了多少**。

    没有开关：能量有没有剩，自动决定是常规还是低功耗。

    为什么要写日志：充能原本是**静默**的——玩家只看到电量条悄悄变长，
    既不知道每回合回多少，也分不清"满血多给 1 点"到底有没有生效。
    这里报的是**实际增加量**（印记自带上限钳制，满了就是 0），不是名义值。
    """
    if tenant.character_id != TENANT_ID:
        return
    name = engine.character(tenant).name
    bonus = tenant.health >= tenant.max_health and ENERGY_FULL_HEALTH_BONUS > 0
    gain = ENERGY_PER_TURN + (ENERGY_FULL_HEALTH_BONUS if bonus else 0)

    before = int(_energy(engine, tenant))
    _gain_energy(engine, tenant, gain)
    actual = int(_energy(engine, tenant)) - before
    now = int(_energy(engine, tenant))

    if actual <= 0:
        engine._log(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.turn_start.1"].format(p1=name, p2=NAME_MARK, p3=now, p4=ENERGY_MAX))
        return
    note = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.turn_start.2"].format(p1=ENERGY_FULL_HEALTH_BONUS) if bonus else ""
    engine._log(
        TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.turn_start.3"].format(p1=name, p2=NAME_MARK, p3=actual, p4=before, p5=ENERGY_MAX, p6=now, p7=ENERGY_MAX, p8=note)
    )


TURN_START = turn_start


def initial_setup(engine: EngineProtocol, tenant: object) -> None:
    """入住：把个人佩枪直接配发进背包，并给一点起始能量。
    """
    if tenant.character_id != TENANT_ID:
        return
    from weiren_game.items import ItemInstance

    tenant.inventory.add(
        ItemInstance(engine.state.ids.allocate_item(), GUN_ID, count=1)
    )
    _gain_energy(engine, tenant, ENERGY_PER_TURN)


# ---------------------------------------------------------------- 详情页小面板
def detail_slot(engine: EngineProtocol, tenant: object) -> list[dict]:
    """房客详情页小面板：能量条 + **掩护射击开关指示器** + 状态 + 持有物。

    能量条本身由「未声明 DETAIL_SLOT 时的回退」自动列出（读 `CHARACTER_MARKS`），
    低功耗红线则由印记的 `bar_tiers` 声明——这里只加开关、状态与持有物。
    条目形状见 `web_ui._project_slot`：`bar` / `text` / `tags` / `mark`。
    """
    rows: list[dict] = [{"kind": "mark", "id": ENERGY_MARK}]

    # 开关指示器：0/1 的进度条——开着满格、关着空条。
    # 用 `bar` 而不是 `text`，是为了让**两个状态都看得见**：
    # 只写"掩护中"的话，玩家分不清"没开"和"根本没这个能力"。
    cover_on = tenant.condition(ST_COVER).active
    rows.append({
        "kind": "bar",
        "label": f'{NAME_TOGGLE_COVER} · {"开启" if cover_on else "关闭"}',
        "value": 1 if cover_on else 0,
        "max": 1,
        # 刻度线兼悬停说明：只在开启时打绿点，关着就留空条。
        "tiers": (
            (1, TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.detail_slot.1"].format(p1=COVER_COST, p2=COVER_RESIST), "ok"),
        ) if cover_on else (),
    })

    status = TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.detail_slot.2"].format(p1=ENERGY_PER_TURN)
    if tenant.health >= tenant.max_health:
        status += TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.detail_slot.3"].format(p1=ENERGY_FULL_HEALTH_BONUS)
    if _low_power(tenant):
        status += TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.detail_slot.4"].format(p1=LOW_POWER_PENALTY)
    elif _energy(engine, tenant) >= ENERGY_UPKEEP:
        status += (
            TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.detail_slot.5"].format(p1=ENERGY_UPKEEP, p2=UPKEEP_HEALTH_FACTOR)
        )
    rows.append({"kind": "text", "label": TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.detail_slot.6"], "text": status})
    if _has_gun(tenant):
        rows.append({"kind": "tags", "items": [NAME_GUN]})
    return rows


DETAIL_SLOT = detail_slot

# ---------------------------------------------------------------- modifier
# ⚠️ **provider 必须是纯查询**（`docs/ARCH.md` 硬规则：掷骰与消耗只发生在结算点）。
# 它们会被**每一次**该通道的收集问到——`collect_modifiers` 无条件调用 provider，
# 之后才用 `path` 过滤它 yield 出来的 spec。所以在 provider 里扣电/写日志，
# 会在"根本没命中"的调用上照样执行：
#   实测一回合内 `sanityConsume` 被问了 8 次，其中只有 1 次是回合末结算。
# 因此：**判断只读状态，花钱全部放到 `end_turn_settle`（真正的结算点）。**
def _sanity_consume_modifier(context: object):
    """回合末理智消耗：电量够 → 折扣；电量见底 → 低功耗加罚。**纯查询，不写状态。**"""
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != TENANT_ID:
        return
    source = (TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._sanity_consume_modifier.1"], NAME_CHARACTER, NAME_PASSIVE_ENERGY)
    if _low_power(tenant):
        yield spec("sanityConsume").path("turn_end_consume").flat(LOW_POWER_PENALTY).source(*source)
    elif _upkeep_affordable(engine, tenant):
        yield (
            spec("sanityConsume")
            .path("turn_end_consume")
            .percent(-(1.0 - UPKEEP_SANITY_FACTOR))
            .source(*source)
        )


def _health_loss_modifier(context: object):
    """高生命值自然流失：同上（折扣 / 加罚）。**纯查询，不写状态。**

    `path` 里带上来源名，只作用回合末这一处流失；搜索中遭遇等其它流失不受影响。
    """
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != TENANT_ID:
        return
    source = (TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._health_loss_modifier.1"], NAME_CHARACTER, NAME_PASSIVE_ENERGY)
    path = (TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._health_loss_modifier.2"], TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._health_loss_modifier.3"])
    if _low_power(tenant):
        yield spec("healthLoss").path(*path).flat(LOW_POWER_PENALTY).source(*source)
    elif _upkeep_affordable(engine, tenant):
        yield (
            spec("healthLoss")
            .path(*path)
            .percent(-(1.0 - UPKEEP_HEALTH_FACTOR))
            .source(*source)
        )


def end_turn_settle(engine: EngineProtocol, tenant: object) -> None:
    """回合末**结算点**：真正扣掉供能的那 1 点电，并把结果说出来。

    挂在 `NODE_HOOKS["end_turn_instance"]`——它在回合末基础消耗**之后**、
    任何可能改动电量的东西之前执行，所以这里读到的电量与刚才判定折扣时一致。

    为什么要专门写日志：代扣是**看不见的**（电量少 1、消耗数字变小），
    不写清楚玩家会以为机制没生效（实测反馈：「似乎没有发生代扣」）。
    """
    if tenant.character_id != TENANT_ID:
        return
    name = engine.character(tenant).name
    if _upkeep_affordable(engine, tenant):
        engine._consume_mark(tenant, ENERGY_MARK, ENERGY_UPKEEP)
        engine._log(
            TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.end_turn_settle.1"].format(p1=name, p2=ENERGY_UPKEEP, p3=NAME_MARK)
        )
        return
    engine._log(
        TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.end_turn_settle.2"].format(p1=name, p2=NAME_MARK, p3=NAME_PASSIVE_ENERGY)
    )


NODE_HOOKS = {"end_turn_instance": end_turn_settle}


def _apathy_modifiers(context: object):
    """情感淡漠：消沉变动 / 理智回复 / 觉醒获取 三处乘算。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != TENANT_ID:
        return
    source = (TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._apathy_modifiers.1"], NAME_CHARACTER, NAME_PASSIVE_APATHY)
    yield spec("depressionChange").path("depression").mul(DEPRESSION_FACTOR).source(*source)
    yield spec("sanityRestore").path("restore").mul(SANITY_RESTORE_FACTOR).source(*source)
    yield spec("awakeningGain").path("awakening").mul(AWAKENING_FACTOR).source(*source)


def _sanity_damage_modifier(context: object):
    """情感淡漠④：受到的理智伤害降低。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != TENANT_ID:
        return
    yield (
        spec("sanityDamage")
        .path("damage")
        .percent(-SANITY_DAMAGE_REDUCTION)
        .source("ability_passive", NAME_CHARACTER, NAME_PASSIVE_APATHY)
    )


def _cover_fire_modifier(context: object):
    """掩护射击：为正在搜索的队友提供抵御，每次实际抵御扣 1 能量。

    只在「搜索遭遇」的抵御判定里被收集，因此天然只对外出者生效。
    枪主必须在屋内且持有佩枪；**掩护开关**开启；能量不足时不再生成。
    """
    from weiren_game.modifier_rules import spec

    engine = context["engine"]  # type: ignore[index]
    if getattr(engine, "state", None) is None:
        return
    owner = next(
        (
            value
            for value in engine.home_tenants()
            if value.character_id == TENANT_ID and _has_gun(value)
        ),
        None,
    )
    if owner is None:
        return
    source = (TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._cover_fire_modifier.1"], NAME_CHARACTER, NAME_PASSIVE_COVER)
    # 基础档：只要枪主在屋并且拿着枪，就自带一点抵御（不花电量）。
    if COVER_BASE_RESIST > 0:
        yield (
            spec("chance").flat(COVER_BASE_RESIST).match("all")
            .path("resist", "pseudo_active").source(*source)
        )
    # 掩护档：开关开着 + 有电量 → 额外补足到 COVER_RESIST。
    extra = COVER_RESIST - COVER_BASE_RESIST
    if not owner.condition(ST_COVER).active or extra <= 0:
        return
    if _energy(engine, owner) < COVER_COST:
        return
    # 扣费必须**每回合最多一次**：provider 会被每一次 chance 收集问到，
    # 而搜索抵御是"按携带的抵御道具逐个收集"的，同一次遭遇就可能问好几次。
    # 不加这道闸，一次遭遇能把电量整条抽干（实测一次收集扣 4 点）。
    turn = int(engine.state.flow.turn)
    if int(owner.turn_counters.get("star_cover_turn", -1)) != turn:
        owner.turn_counters["star_cover_turn"] = turn
        engine._consume_mark(owner, ENERGY_MARK, COVER_COST)
        engine._log(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._cover_fire_modifier.2"].format(p1=engine.character(owner).name))
    yield (
        spec("chance").flat(extra).match("all")
        .path("resist", "pseudo_active").source(*source)
    )


# ---------------------------------------------------------------- provider 登记
# 纯登记即可：这四张效果表（修饰器 / 闸门的静态项与 provider）都已纳入
# `content.py::_BASE_CONTAINERS` 的快照 —— 每次「应用」先还原 base 再按包优先级
# 重装，所以重载任意次都只有一份，卸载也随快照回滚，包自己不需要去重或认领。
register_modifier_provider("sanityConsume", _sanity_consume_modifier)
register_modifier_provider("healthLoss", _health_loss_modifier)
register_modifier_provider("depressionChange", _apathy_modifiers)
register_modifier_provider("sanityRestore", _apathy_modifiers)
register_modifier_provider("awakeningGain", _apathy_modifiers)
register_modifier_provider("sanityDamage", _sanity_damage_modifier)
register_modifier_provider("chance", _cover_fire_modifier)


# ---------------------------------------------------------------- 技能函数
def _shots_fired(actor: object) -> int:
    """本局已开火次数。"""
    return int(actor.turn_counters.get("star_shots", 0))


def requirements_fire(
    engine: EngineProtocol, actor: object, *, bypass: bool = False
) -> str | None:
    """开火条件：持有佩枪 + 门外有事件 + **电量充满** + 未超每局次数。"""
    if not _has_gun(actor):
        return TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.requirements_fire.1"].format(p1=NAME_GUN)
    if not engine.state.world.events.door_events:
        return TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.requirements_fire.2"]
    energy = int(_energy(engine, actor))
    if energy < FIRE_MIN_ENERGY:
        return (
            TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.requirements_fire.3"].format(p1=NAME_MARK, p2=energy, p3=ENERGY_MAX)
        )
    if FIRE_MAX_PER_GAME and _shots_fired(actor) >= FIRE_MAX_PER_GAME:
        return TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.requirements_fire.4"].format(p1=FIRE_MAX_PER_GAME)
    return None


def _resolve_door(engine: object, actor: object, spent_note: str) -> None:
    """开火结算：清事件 + 对伪人压制 + 记次数与冷却。

    · 人类访客 → 惊退（等同拒绝，不记入"连续拒绝两次"）
    · 伪人到访 → 清除事件并压制它 FIRE_SUPPRESS_TURNS 回合不再来访

    播报按「可观察的结果」区分，不按目标身份区分。
    """
    name = engine.character(actor).name
    outcome = engine.state.world.events.door_events[0]
    engine.state.world.events.door_events.pop(0)
    actor.turn_counters["star_shots"] = _shots_fired(actor) + 1
    if FIRE_COOLDOWN:
        engine._set_ability_cooldown(
            actor, "fire", engine.state.flow.turn + FIRE_COOLDOWN
        )
    if outcome.kind != "pseudo":
        engine._log(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._resolve_door.1"].format(p1=name))
        return
    engine._suppress_pseudo(FIRE_SUPPRESS_TURNS, ("visit",))
    engine._log(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR._resolve_door.2"].format(p1=name, p2=spent_note))


# ---------------------------------------------------------------- 开关技能
def use_toggle(
    engine: EngineProtocol, actor: object, *, ability_id: str = "", **kwargs: object
) -> None:
    """切换「掩护射击」开关。

    它是玩家唯一的**主动节能手段**：关掉即停止为队友抵御，把电量留给开火。
    电量用完后自动进入低功耗，所以"不该花的时候别花"本身就是权衡。
    """
    if ability_id != "toggle_cover":
        return
    name = engine.character(actor).name
    if actor.condition(ST_COVER).active:
        actor.clear_status(ST_COVER)
        engine._log(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.use_toggle.1"].format(p1=name, p2=NAME_TOGGLE_COVER))
        return
    actor.set_status(ST_COVER, intensity=1, layers=1)
    engine._log(TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.use_toggle.2"].format(p1=name, p2=NAME_TOGGLE_COVER))


def use_fire(engine: EngineProtocol, actor: object, **kwargs: object) -> None:
    """压制射击：**放空全部电量**打出这一枪。

    门槛是"电量必须充满"——既然消耗是全部，4 格和 5 格效果一样，
    不要求满格的话电池上半段就没人看（见 §1.3）。
    放空之后必然进入低功耗，这就是"攒满再打"的价格。
    """
    energy = int(_energy(engine, actor))
    actor.marks.consume(ENERGY_MARK, energy)
    _resolve_door(engine, actor, TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.use_fire.1"].format(p1=energy, p2=NAME_MARK))


ACTIVE_DISPATCH = {
    "toggle_cover": use_toggle,
    "fire": use_fire,
}


# ---------------------------------------------------------------- 状态注册
# 「掩护射击」开关：不衰减的常驻状态，由玩家主动开合。
# 开着时会在房客卡的 chip 栏出现——图标用准星、配色用 info（冷蓝），
# 与创伤/紊乱那种"红色警告"区分开：这是**玩家自己开的装置**，不是负面状态。
register_status_definition(
    StatusDefinition(
        ST_COVER, NAME_STATUS_COVER, "other",
        shown=frozenset({"icon"}),
        chip_icon="i-target",
        chip_css="info",
        source_id="ability:toggle_cover@STAR",
        auto_decay=False,
        description=TEXT["dlc.DLC_Character_STAR_V1.0.0.characters.STAR.module.12"],
    )
)

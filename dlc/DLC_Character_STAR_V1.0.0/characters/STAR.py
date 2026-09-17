"""房客档案：STAR（DLC_Character_STAR）。

"""

from weiren_game.data.types import A, CharacterDefinition, MarkDefinition, T
from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.modifier_rules import register_modifier_provider
from weiren_game.types import EngineProtocol

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
NAME_GUN = "流星信标"
NAME_MARK = "复合生化电池"
NAME_PASSIVE_ENERGY = "半永久能源动力炉"
NAME_PASSIVE_APATHY = "有机计算机稳定化方案"
NAME_PASSIVE_COVER = "掩护射击"
NAME_TOGGLE_COVER = "掩护射击"
NAME_STATUS_COVER = "掩护射击"
NAME_FIRE = "压制射击"
NAME_FIRE_DESC = (
    f"处理门外当前的事件：人类访客被惊退；伪人到访则清除该事件，"
    f"并令其 {FIRE_SUPPRESS_TURNS} 回合内不再来访。"
    f"发动时放空全部【{NAME_MARK}】电量；仅在电量充满（{ENERGY_MAX}/{ENERGY_MAX}）"
    f"时可发动，放空后必然进入低功耗。"
    f"*该能力有 {FIRE_COOLDOWN} 回合冷却时间。"
)
NAME_PASSIVE_ENERGY_DESC = (
    f"STAR 搭载【{NAME_MARK}】，上限 {ENERGY_MAX} 点；每回合开始时充能 "
    f"{ENERGY_PER_TURN} 点，若生命值为上限则额外充能 {ENERGY_FULL_HEALTH_BONUS} 点。"
    f"每回合结束时扣除 {ENERGY_UPKEEP} 点供能，"
    f"使当回合的理智消耗量与高生命值自然流失量各-{1 - UPKEEP_HEALTH_FACTOR:.0%}。"
    f"若电量不足 {ENERGY_UPKEEP} 点则无法供能，进入低功耗："
    f"当回合的理智消耗量与生命流失量各+{LOW_POWER_PENALTY}。"
)
NAME_PASSIVE_APATHY_DESC = (
    f"STAR 受到的理智伤害-{SANITY_DAMAGE_REDUCTION:.0%}；"
    f"消沉值变化量、理智回复量与觉醒情绪获取量均×{DEPRESSION_FACTOR:.0%}。"
)
NAME_PASSIVE_COVER_DESC = (
    f"STAR 在屋内且持有【{NAME_GUN}】时，可开启【{NAME_TOGGLE_COVER}】为在外搜索的同伴"
    f"提供火力掩护：同伴受到伪人主动能力影响时，有 {COVER_RESIST:.0%} 概率免疫该影响。"
    f"未开启时不提供任何掩护。"
)
NAME_TOGGLE_COVER_DESC = (
    f"开启后：为在外搜索的同伴提供火力掩护——同伴受到伪人主动能力影响时"
    f"有 {COVER_RESIST:.0%} 概率免疫该影响；每次实际抵御消耗 {COVER_COST} 点"
    f"【{NAME_MARK}】（每回合至多 {COVER_COST} 点）。"
    f"关闭后：不提供掩护，也不消耗电量。"
)

# 事件命名空间（决定论随机的流名）
_EVENT = "dlc.STAR"


# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    TENANT_ID,
    9001,
    NAME_CHARACTER,
    "特殊作战部队Freesia的指挥官直属通用型特殊支援单元，感情平淡但意外的喜欢交流。喜欢吃松饼。",
    "steady", "keen", 3,
    ("改造人", "18-24岁", "未知的性别",  "星星"),
    passives=(
        A("energy_cycle", NAME_PASSIVE_ENERGY, NAME_PASSIVE_ENERGY_DESC),
        A("apathy", NAME_PASSIVE_APATHY, NAME_PASSIVE_APATHY_DESC),
    ),
    actives=(
        A("toggle_cover", NAME_TOGGLE_COVER, NAME_TOGGLE_COVER_DESC),
        A(
            "fire", NAME_FIRE, NAME_FIRE_DESC, "none",
            chips=(f"冷却 {FIRE_COOLDOWN} 回合",) if FIRE_COOLDOWN else (),
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
            f"每回合开始时充能 {ENERGY_PER_TURN} 点；若生命值为上限则额外充能 "
            f"{ENERGY_FULL_HEALTH_BONUS} 点，上限 {ENERGY_MAX} 点。"
            f"每回合结束时扣除 {ENERGY_UPKEEP} 点供能，抵消当回合的部分自然消耗。"
        ),
        minimum=0,
        maximum=ENERGY_MAX,
        # 第 1 档处画一条红线：低于它即低功耗。刻度会同时出现在状态栏与详情页。
        bar_tiers=((1, "低于此处即低功耗", "danger"),),
        description="它知道自己还剩多少电。低于一格时，身体会替它硬撑。",
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
        engine._log(f"{name}的{NAME_MARK}已经充能完毕（{now}/{ENERGY_MAX}）。")
        return
    note = f"，动力炉状态良好 +{ENERGY_FULL_HEALTH_BONUS}" if bonus else ""
    engine._log(
        f"{name}的{NAME_MARK}充能 {actual} 点"
        f"（{before}/{ENERGY_MAX} → {now}/{ENERGY_MAX}{note}）。"
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
            (1, f"每次实际抵御消耗 {COVER_COST} 电量，抵御 {COVER_RESIST:.0%}", "ok"),
        ) if cover_on else (),
    })

    status = f"每回合 +{ENERGY_PER_TURN}"
    if tenant.health >= tenant.max_health:
        status += f"（动力炉状态良好 +{ENERGY_FULL_HEALTH_BONUS}）"
    if _low_power(tenant):
        status += f" · **低功耗**：回合末消耗 +{LOW_POWER_PENALTY}"
    elif _energy(engine, tenant) >= ENERGY_UPKEEP:
        status += (
            f" · 供能中：回合末扣 {ENERGY_UPKEEP}，"
            f"自然消耗降至 {UPKEEP_HEALTH_FACTOR:.0%}"
        )
    rows.append({"kind": "text", "label": "状态", "text": status})
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
    source = ("角色被动", NAME_CHARACTER, NAME_PASSIVE_ENERGY)
    if _low_power(tenant):
        yield spec("sanityConsume").path("回合末消耗").flat(LOW_POWER_PENALTY).source(*source)
    elif _upkeep_affordable(engine, tenant):
        yield (
            spec("sanityConsume")
            .path("回合末消耗")
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
    source = ("角色被动", NAME_CHARACTER, NAME_PASSIVE_ENERGY)
    path = ("生命流失", "高生命值自然流失")
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
            f"{name}消耗 {ENERGY_UPKEEP} 点{NAME_MARK}，"
            f"回合末的自然消耗减轻了。"
        )
        return
    engine._log(
        f"{name}的{NAME_MARK}已经见底，{NAME_PASSIVE_ENERGY}进入低功耗状态。"
    )


NODE_HOOKS = {"end_turn_instance": end_turn_settle}


def _apathy_modifiers(context: object):
    """情感淡漠：消沉变动 / 理智回复 / 觉醒获取 三处乘算。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != TENANT_ID:
        return
    source = ("角色被动", NAME_CHARACTER, NAME_PASSIVE_APATHY)
    yield spec("depressionChange").path("消沉").mul(DEPRESSION_FACTOR).source(*source)
    yield spec("sanityRestore").path("回复").mul(SANITY_RESTORE_FACTOR).source(*source)
    yield spec("awakeningGain").path("觉醒").mul(AWAKENING_FACTOR).source(*source)


def _sanity_damage_modifier(context: object):
    """情感淡漠④：受到的理智伤害降低。"""
    from weiren_game.modifier_rules import spec

    tenant = context["tenant"]  # type: ignore[index]
    if tenant.character_id != TENANT_ID:
        return
    yield (
        spec("sanityDamage")
        .path("伤害")
        .percent(-SANITY_DAMAGE_REDUCTION)
        .source("角色被动", NAME_CHARACTER, NAME_PASSIVE_APATHY)
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
    source = ("角色技能", NAME_CHARACTER, NAME_PASSIVE_COVER)
    # 基础档：只要枪主在屋并且拿着枪，就自带一点抵御（不花电量）。
    if COVER_BASE_RESIST > 0:
        yield (
            spec("chance").flat(COVER_BASE_RESIST).match("all")
            .path("抵御", "伪人使用主动能力").source(*source)
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
        engine._log(f"{engine.character(owner).name}为外出的同伴提供掩护射击。")
    yield (
        spec("chance").flat(extra).match("all")
        .path("抵御", "伪人使用主动能力").source(*source)
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
        return f"需要{NAME_GUN}才能开火。"
    if not engine.state.world.events.door_events:
        return "门外没有值得开枪的目标。"
    energy = int(_energy(engine, actor))
    if energy < FIRE_MIN_ENERGY:
        return (
            f"{NAME_MARK}没有充满（{energy}/{ENERGY_MAX}），无法开火。"
        )
    if FIRE_MAX_PER_GAME and _shots_fired(actor) >= FIRE_MAX_PER_GAME:
        return f"本次对局至多开火 {FIRE_MAX_PER_GAME} 次。"
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
        engine._log(f"{name}朝天放了一枪，门外的人退开了。")
        return
    engine._suppress_pseudo(FIRE_SUPPRESS_TURNS, ("visit",))
    engine._log(f"{name}{spent_note}，门外的东西暂时退去了。")


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
        engine._log(f"{name}关闭了{NAME_TOGGLE_COVER}。")
        return
    actor.set_status(ST_COVER, intensity=1, layers=1)
    engine._log(f"{name}开启了{NAME_TOGGLE_COVER}。")


def use_fire(engine: EngineProtocol, actor: object, **kwargs: object) -> None:
    """压制射击：**放空全部电量**打出这一枪。

    门槛是"电量必须充满"——既然消耗是全部，4 格和 5 格效果一样，
    不要求满格的话电池上半段就没人看（见 §1.3）。
    放空之后必然进入低功耗，这就是"攒满再打"的价格。
    """
    energy = int(_energy(engine, actor))
    actor.marks.consume(ENERGY_MARK, energy)
    _resolve_door(engine, actor, f"把 {energy} 点{NAME_MARK}一次放空")


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
        description="STAR把枪口对着门外，不是为了打中谁；是为了让外面知道这里有枪。",
    )
)

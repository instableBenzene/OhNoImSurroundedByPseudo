"""游戏内容的数据类型与简写工厂。

角色、物资、地点等纯内容文件只需要依赖这里的类型与工厂，不依赖运行时。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    """技能里的一个资源条目；side 决定它是「cost」还是「effect」。

    即使两者都写 sanity，语义也由 side 区分：
    - side="cost"：发动前置代价（发动前要支付）；
    - side="effect"：技能效果结算（发动成功后的资源变化）。

    修饰词：
    - optional=True：可选项。cost 表示玩家可放弃该项；effect 表示可选择
      是否结算。强制发动时可选视为必选。
    - maximum=True：「至多」。cost 表示至多支付 N（实际可少付）；effect
      表示效果至多作用 N（如回复至多 N）。强制时取最大档。

    payer：actor=发动者，target=被作用方/被强制方。
    tag：本分支内的标识（可选），供 links 建立 cost→effect 的关联。
    """

    tag: str = ""
    side: str = "cost"
    resource: str = "sanity"
    amount: float | None = None
    key: str = ""
    optional: bool = False
    maximum: bool = False
    payer: str = "actor"


@dataclass(frozen=True)
class CostEffectLink:
    """cost → effect 的多对多关联。

    - costs：触发本条效果的若干 cost tag（多个 cost 可以共同对应同一效果）；
    - effects：这些 cost 引发的全部 effect tag（一个 cost 也可以引发多条
      效果，因此用元组而不是单一 id）。
    """

    costs: tuple[str, ...] = ()
    effects: tuple[str, ...] = ()


@dataclass(frozen=True)
class CostExpr:
    """cost 侧的逻辑表达式节点。

    - op="and"：全部子项都必须支付（默认）；
    - op="or"：任意一个子项可支付即可（如洋葱「1 共情印记 或 15 理智」）。
    refs 的每一项可以是字符串（Branch 内 cost Term 的 tag）或嵌套 CostExpr。
    """

    op: str = "and"
    refs: tuple[object, ...] = ()


@dataclass(frozen=True)
class Branch:
    """技能的一个可选分支：cost（前置代价）与 effect（效果）成对声明。

    - option：与发动时传入的 option 参数对应，"" 为默认分支；
    - terms：该分支的全部条目（cost 与 effect 按 side 区分）；
    - forced_terms：被强制发动时，用于整体取代本分支 cost 侧条目的
      替代代价（side 仍为 cost、payer 常为 target）；
    - max_on_force：被强制发动时优先选择该分支。
    - links：cost 与 effect 的关联表（多对多，非一一对应）。links 只描述
      「哪几笔代价引发哪几条效果」，不要求 1:1；没有 links 时表示效果由
      角色模块函数直接实现。
    - cost_expr：cost 侧的逻辑组合；None 表示把全部 cost Term 按 AND 处理。
    """

    option: str = ""
    terms: tuple[Term, ...] = ()
    links: tuple[CostEffectLink, ...] = ()
    cost_expr: CostExpr | None = None
    forced_terms: tuple[Term, ...] = ()
    max_on_force: bool = False


@dataclass(frozen=True)
class AbilityDefinition:
    """主动或被动能力的静态定义。

    技能 = 一个或多个 Branch；每个 Branch 内部以
    ``{cost: Term, effect: Term, ...}`` 的成对结构声明，cost 与 effect
    只是 Term.side 的两种取值，不再是两种不同的类。
    解锁条件（如入住满 3 回合）单独放在 unlock_home_turns，不参与支付。
    """

    id: str
    name: str
    description: str
    target: str = "none"
    branches: tuple[Branch, ...] = ()
    unlock_home_turns: int = 0
    # 目标选择的界面提示与候选（由内容自描述，核心/前端不写死内容文案）。
    prompt: str = ""
    # ``(value, label)``；可选第 3 项 = 图标 id（``i-*``）、第 4 项 = 一句说明 ——
    # 界面有就用、没有就回退中性图标（所以旧的两元组照样能跑）。
    options: tuple[tuple[str, str], ...] = ()
    amount_label: str = ""
    amount_mark: str = ""
    # 限定条件 chip（如"冷却 3 回合""每回合 1 次""对局仅 1 次"），供界面展示。
    chips: tuple[str, ...] = ()
    # 是否每回合只能使用 1 次（由内容显式声明；未声明即无此限制）。
    per_turn: bool = False
    # 触发"嵌套调用"的选项值（如模仿：选定后需再选一个被调用能力）。
    nested_option: str = ""
    # True：这条"主动技能"不结算效果，只负责**打开本角色的专属面板**（`PANEL`）。
    # 前端把它渲染成开/关；引擎侧不掷失败、不付代价、不记冷却。
    opens_panel: bool = False
    # 不可撤销的动作：选定目标后先弹一次确认，文案由内容给（前端不写死）。
    # `danger=True` 时界面用危险色（语义色 token）；空字符串＝不需要确认。
    confirm: str = ""
    danger: bool = False


@dataclass(frozen=True)
class CharacterDefinition:
    """一名房客的静态档案（身份、性格、携带量与能力）。"""

    tenant_id: str
    source_id: int
    name: str
    description: str
    primary: str
    secondary: str
    carry: int
    tags: tuple[str, ...] = ()
    passives: tuple[AbilityDefinition, ...] = ()
    actives: tuple[AbilityDefinition, ...] = ()
    available: bool = True
    source_note: str = ""

    @property
    def active_name(self) -> str | None:
        """以「／」连接全部主动能力名称，无则返回 None。"""
        return "／".join(a.name for a in self.actives) or None

    @property
    def active_description(self) -> str | None:
        """以「；」连接全部主动能力描述，无则返回 None。"""
        return "；".join(a.description for a in self.actives) or None


@dataclass(frozen=True)
class MarkDefinition:
    """角色专属「印记」的静态定义（存放于该角色的档案文件）。

    - ``acquisition``：获得条件（文字描述；具体触发在角色技能/机制处实现）；
    - ``minimum`` / ``maximum``：层数上下限（maximum 为 None 表示无上限）；
    - ``special``：不属于其它技能的特殊用法说明（无则留空）。
    """

    id: str
    label: str
    acquisition: str
    # 风味描述（面向屋主的「这是什么感觉」，与机制无关）。
    description: str = ""
    minimum: int = 0
    maximum: int | None = None
    # 进度条换档阈值（升序，最多 4 档，与羁绊位阶同一套配色）。
    # 每档可写 `at`，或 `(at, 标注, 刻度配色)`——标注与配色只为"提示"服务
    # （例：`(1, "可发动", "danger")` 就是在第 1 档画一条红线并写明用途）。
    # 有上限的印记按 maximum 铺满；无上限的印记以最后一个阈值作为"满槽"参照；
    # 留空且无上限 = 不画条（只显示数字）。
    bar_tiers: tuple = ()
    special: str = ""
    # 由哪些 lifecycle 节点驱动获得/变化，以及对应实现函数（贴角色文件）。
    triggers: tuple[str, ...] = ()
    hooks: tuple[object, ...] = ()
    # True 时该印记是「特殊牌库」等内部结构，禁止被外界直接改写。
    externally_locked: bool = False


@dataclass(frozen=True)
class ItemDefinition:
    """一种物资的静态定义。"""

    item_id: str
    name: str
    category: str
    quality: int
    description: str
    tags: tuple[str, ...]
    consumable: bool = False
    fragile_chance: float = 0.0
    max_durability: int = 0
    use_cost: int = 0
    medical_target: str | None = None
    medical_max_intensity: int = 0
    reduce_intensity: int = 0
    reduce_layers: int = 0
    stack_size: int = 1
    searchable: bool = True
    source_note: str = ""
    # 使用普通消耗品效果时，指向 weiren_game.systems.item_system 中
    # ITEM_EFFECTS 注册表里的效果函数名；None 表示使用通用效果逻辑。
    on_use: str | None = None
    # 使用的目标模式：tenant=必须指定屋内房客；optional/none=可不指定目标
    # （由 on_use 效果自行处理 target=None 的情形）。
    target_mode: str = "tenant"
    # 风味文本（面向屋主的描写/台词，与机制无关）；flavor_shown 控制是否展示。
    flavor: str = ""
    flavor_shown: bool = True
    # 单次获得数量区间（可堆叠品用）；None=默认 stack_size/4 ± 1（下限 ≥1，上限 ≤stack_size）。
    obtain_range: tuple[int, int] | None = None

    @property
    def durable(self) -> bool:
        """是否有耐久属性（最大耐久大于 0）。"""
        return self.max_durability > 0


@dataclass(frozen=True)
class MapDefinition:
    """一张**地图**（区域包）：一组搜索地点 + 屋子的名字。

    内置的默认地图是 ``base``（显示名「城郊小镇」，屋子叫「城郊小屋」）。
    ``locations`` 是**显式名单**：地点要出现在这张图上就必须列进来 ——
    DLC 自带的地点默认不进任何地图，想加入城郊小镇得登记（``register_map_location``）
    或者自带一张地图。
    """

    id: str
    name: str
    shelter: str
    locations: tuple[str, ...] = ()
    # 开局从本图里抽多少个地点（``fixed`` 的地点必定入选）。
    draw_count: int = 10
    description: str = ""


@dataclass(frozen=True)
class LocationDefinition:
    """一个搜索地点的静态定义。"""

    id: str
    name: str
    description: str
    group: str
    tag_distribution: tuple[tuple[tuple[str, ...], float], ...]
    # 物资点的档位：1=低 / 2=中 / 3=高。只影响展示（图标特征色 + 档位 chip），不影响掉落。
    tier: int = 2
    turn_delta: int = 0
    behavior_delta: int = 0
    encounter_bonus: float = 0.0
    quality_modifiers: tuple[tuple[str, float], ...] = ()
    item_tag_modifiers: tuple[tuple[str, float], ...] = ()
    fixed: bool = False

    @property
    def turns(self) -> int:
        """实际搜索回合数（基础 4 加修正，至少为 1）。"""
        return max(1, 4 + self.turn_delta)

    @property
    def attempts(self) -> int:
        """实际行为次数（基础 4 加修正，至少为 0）。"""
        return max(0, 4 + self.behavior_delta)

    @property
    def loot(self) -> tuple[tuple[str, int], ...]:
        """地点固定战利品表（当前恒为空元组）。"""
        return ()


@dataclass(frozen=True)
class InformationTemplate:
    """一条可生成的动态信息模板。"""

    id: str
    name: str
    kind: str
    description: str
    pending: str = ""
    confirmed: str = ""
    refuted: str = ""
    location_id: str | None = None
    reward_ids: tuple[str, ...] = ()
    duration: int = 5


@dataclass(frozen=True)
class PseudoDefinition:
    """一类伪人的静态定义。"""

    id: str
    name: str
    human_character_id: str
    description: str
    breakthrough: str
    liberation: str
    enters_house: bool = True
    # 场景状态中充当「印记」的字段名（无则留空），供外界统一改写。
    mark_field: str = ""
    # 该印记对外的称呼（内部结算名与外部描述可能不同）。
    mark_label: str = ""
    # True 时该伪人的印记同样禁止被外界直接改写。
    mark_externally_locked: bool = False


def A(
    id_: str,
    name: str,
    description: str,
    target: str = "none",
    *,
    branches: tuple[Branch, ...] = (),
    unlock_home_turns: int = 0,
    prompt: str = "",
    options: tuple[tuple[str, str], ...] = (),
    amount_label: str = "",
    amount_mark: str = "",
    chips: tuple[str, ...] = (),
    nested_option: str = "",
    per_turn: bool = False,
    opens_panel: bool = False,
    confirm: str = "",
    danger: bool = False,
) -> AbilityDefinition:
    """构造 AbilityDefinition 的简写工厂函数。"""
    return AbilityDefinition(
        id_,
        name,
        description,
        target,
        branches=branches,
        unlock_home_turns=unlock_home_turns,
        prompt=prompt,
        options=options,
        amount_label=amount_label,
        amount_mark=amount_mark,
        chips=chips,
        nested_option=nested_option,
        per_turn=per_turn,
        opens_panel=opens_panel,
        confirm=confirm,
        danger=danger,
    )


def T(
    resource: str,
    amount: float | None = None,
    *,
    tag: str = "",
    side: str = "cost",
    key: str = "",
    optional: bool = False,
    maximum: bool = False,
    payer: str = "actor",
) -> Term:
    """构造 Term（cost/effect 资源条目）的简写工厂。"""
    return Term(
        tag=tag,
        side=side,
        resource=resource,
        amount=amount,
        key=key,
        optional=optional,
        maximum=maximum,
        payer=payer,
    )


def B(
    *,
    option: str = "",
    terms: tuple[Term, ...] = (),
    links: tuple[CostEffectLink, ...] = (),
    cost_expr: CostExpr | None = None,
    forced_terms: tuple[Term, ...] = (),
    max_on_force: bool = False,
) -> Branch:
    """构造 Branch（一个 cost→effect 成对分支）的简写工厂。"""
    return Branch(
        option=option,
        terms=terms,
        links=links,
        cost_expr=cost_expr,
        forced_terms=forced_terms,
        max_on_force=max_on_force,
    )


def CE(op: str = "and", *refs: object) -> CostExpr:
    """构造 cost 逻辑表达式（and/or）的简写工厂。"""
    return CostExpr(op=op, refs=refs)


def I(id_: str, name: str, category: str, quality: int, description: str,
      tags: tuple[str, ...], **kwargs: object) -> ItemDefinition:
    """构造 ItemDefinition 的简写工厂函数。"""
    return ItemDefinition(id_, name, category, quality, description, tags, **kwargs)


def L(id_: str, name: str, description: str, group: str,
      distribution: tuple[tuple[tuple[str, ...], float], ...], **kwargs: object) -> LocationDefinition:
    """构造 LocationDefinition 的简写工厂函数。"""
    return LocationDefinition(id_, name, description, group, distribution, **kwargs)

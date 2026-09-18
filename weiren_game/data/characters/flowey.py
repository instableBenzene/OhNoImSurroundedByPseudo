"""房客档案：花尔维纳（22 号）。

专属技能「园艺达人」：他有一块**田**（两块地），在专属面板里打理。

规则（玩家视角的账在 `docs/BALANCE.md`，为什么这么定在 `docs/DECISIONS.md`）：
- 每块地各有一份**水分**（0..MOISTURE_MAX，浇水回满，每回合初 −1）
  与**生长进度**（0..RIPE_PROGRESS 即成熟）。
- 水分 > 0 才长：本回合与上回合（都在回合初取样）都是满水 → 本回合 +2，否则 +1。
- 水分 = 0：连续 2 回合 → 最大产物量 −1；连续 3 回合 → 枯萎；
  最大产物量被扣到 0 同样等于枯萎。
- 种下之后**取不出来**（只能等）；一熟就自动落到"产物格"，再从产物格拖进仓库。

核心不认识"田 / 水 / 成熟"里的任何一个词：规则全在这个文件里，删掉本文件即整块消失。
"""

from dataclasses import dataclass, field

from ..types import A, CharacterDefinition
from weiren_game.types import EngineProtocol

CHARACTER = CharacterDefinition(
    "flowey", 22, "花尔维纳", "总是带着笑容的乐观派，相信事情总会好起来。", "gentle", "steady", 4, ("花店店员", "打工人", "25-30岁", "男性"),
    actives=(
        A(
            "gardener",
            "园艺达人",
            "打理他的田：把【食物】种下、用【矿泉水】浇水，成熟后收成。",
            opens_panel=True,
        ),
    ),
    source_note="原稿无专属技能；「园艺达人」与田为本项目新增（见 docs/BALANCE.md）",
)

# 界面头像图标（内容自声明）。
AVATAR = "i-av9"

TENANT_ID = "flowey"
FIELD_KEY = "field"

# ---------------------------------------------------------------- 可调数值
PLOT_COUNT = 2          # 几块地
MOISTURE_MAX = 3        # 水分上限；浇水回满
RIPE_PROGRESS = 7       # 成熟所需进度
BASE_YIELD = 3          # 一次采收的产物量（会被干旱扣减）
DROUGHT_YIELD_LOSS = 2  # 连续几回合没水 → 最大产物量 −1
DROUGHT_WITHER = 3      # 连续几回合没水 → 枯萎
FAST_GROWTH_BONUS = 1   # 连续两回合满水时，本回合额外涨的进度
WATER_ITEM = "water"    # 【矿泉水】

# 显示名：原始叫法"干燥度"，但满格 = 刚浇过水，所以标签按语义用"湿润度"。
NAME_MOISTURE = "湿润度"
NAME_FIELD = "田"


# ---------------------------------------------------------------- 专属状态
def _empty_plot() -> dict:
    """一块地刚翻开时的样子（键固定；缺字段一律按这里回落）。"""
    return {
        "seed": "",           # 种下的物品 id；空 = 荒地
        "progress": 0,
        "moisture": 0,
        "last_moisture": 0,   # 上回合初取样的水分（用于"连续两回合满水"）
        "drought": 0,         # 连续多少回合没水
        "yield_max": BASE_YIELD,
        "product": "",        # 已成熟、还没拖走的产物 id
        "pending": 0,         # 产物件数
    }


@dataclass
class FieldState:
    """一块田：每块地一份生长记录（内容自有状态，随存档走）。"""

    plots: list = field(default_factory=list)

    def plot(self, index: int) -> dict:
        """取第 index 块地的记录（不足就补齐）。"""
        while len(self.plots) <= index:
            self.plots.append(_empty_plot())
        return self.plots[index]

    def to_dict(self) -> dict:
        """序列化；顺手按当前规则补齐字段，老存档也能读回来。"""
        plots = []
        for index in range(PLOT_COUNT):
            merged = _empty_plot()
            merged.update(self.plot(index))
            plots.append(merged)
        return {"plots": plots}

    @classmethod
    def from_dict(cls, raw: dict) -> "FieldState":
        """从存档还原；未知字段丢弃、缺字段走默认（玩家侧宽容）。"""
        plots = []
        for item in raw.get("plots", ()):
            merged = _empty_plot()
            if isinstance(item, dict):
                merged.update({key: item[key] for key in merged if key in item})
            plots.append(merged)
        return cls(plots)


CONTAINERS = {FIELD_KEY: FieldState}


# ---------------------------------------------------------------- 小工具
def _item_name(item_id: str) -> str:
    """物品显示名（内容侧查目录；查不到就回落到 id）。"""
    from weiren_game.data import ITEMS

    definition = ITEMS.get(item_id)
    return definition.name if definition is not None else item_id


def _is_food(item_id: str) -> bool:
    """能不能种：带 `food` tag 的都算【食物】（矿泉水也是 food，但它优先当水用）。"""
    from weiren_game.data import ITEMS

    definition = ITEMS.get(item_id)
    return definition is not None and "food" in definition.tags


def _field(engine: EngineProtocol, tenant: object):
    """本角色的田（不是本角色就返回 None）。"""
    if getattr(tenant, "character_id", "") != TENANT_ID:
        return None
    return engine.container(tenant, FIELD_KEY)


def _consume(engine: EngineProtocol, tenant: object, item_id: str) -> bool:
    """取走 1 件物资：先看本人背包，再看屋主仓库；都没有返回 False。

    用 `Inventory.consume` 按"单位"扣（可堆叠品减 count、归零才移除实例），
    不能用 `remove_first` —— 那会把整摞一起拿走。
    """
    if tenant.inventory.consume(item_id, 1) >= 1:
        return True
    return engine.state.house.inventory.consume(item_id, 1) >= 1


def _plot_index(value: object) -> int:
    """把外部传来的格号夹进合法范围（越界按第 0 块处理）。"""
    try:
        index = int(value)
    except (TypeError, ValueError):
        return 0
    return index if 0 <= index < PLOT_COUNT else 0


def _reset_growth(plot: dict) -> None:
    """只清生长相关的字段；产物（product / pending）留着 —— 收成可以压在地里等地收。"""
    for key, value in _empty_plot().items():
        if key not in ("product", "pending"):
            plot[key] = value


# ---------------------------------------------------------------- 回合结算
def turn_start(engine: EngineProtocol, tenant: object) -> None:
    """回合初：每块地变干、生长（一熟就落到产物格），以及干旱的代价。"""
    state = _field(engine, tenant)
    if state is None:
        return
    for index in range(PLOT_COUNT):
        _tick_plot(engine, tenant, state.plot(index))


TURN_START = turn_start


def _tick_plot(engine: EngineProtocol, tenant: object, plot: dict) -> None:
    """单块地的一回合：满水判定 → 生长 / 干旱 → 变干。"""
    if not plot["seed"]:
        return
    full_last = plot["last_moisture"] >= MOISTURE_MAX
    full_now = plot["moisture"] >= MOISTURE_MAX
    if plot["moisture"] > 0:
        plot["progress"] += 1 + (FAST_GROWTH_BONUS if (full_last and full_now) else 0)
        plot["drought"] = 0
    else:
        plot["drought"] += 1
        if plot["drought"] >= DROUGHT_WITHER:
            _wither(engine, tenant, plot, "连着三回合没浇水")
            return
        if plot["drought"] == DROUGHT_YIELD_LOSS:
            plot["yield_max"] = max(0, plot["yield_max"] - 1)
            if plot["yield_max"] <= 0:
                _wither(engine, tenant, plot, "收成被旱没了")
                return
    plot["last_moisture"] = plot["moisture"]
    plot["moisture"] = max(0, plot["moisture"] - 1)
    if plot["progress"] >= RIPE_PROGRESS:
        _ripen(engine, tenant, plot)


def _ripen(engine: EngineProtocol, tenant: object, plot: dict) -> None:
    """成熟：产物落到产物格，地腾出来可以接着种。"""
    seed = plot["seed"]
    count = int(plot["yield_max"])
    plot.update(_empty_plot())
    plot["product"] = seed
    plot["pending"] = count
    engine._log(f"{engine.character(tenant).name}的{NAME_FIELD}熟了：{_item_name(seed)} ×{count}。")


def _wither(engine: EngineProtocol, tenant: object, plot: dict, why: str) -> None:
    """枯死：种下的东西没了，地重新变回荒地（产物也跟着没了）。"""
    name = _item_name(plot["seed"])
    plot.update(_empty_plot())
    # 真警告（少用）：作物枯死是不可逆的损失，值得让玩家一眼看到。
    engine._log(f"{engine.character(tenant).name}的{NAME_FIELD}里，{name}{why}，枯了。", kind="warn")


# ---------------------------------------------------------------- 面板
def build_view(engine: EngineProtocol, tenant: object) -> dict | None:
    """田的面板视图：两块地，各一个"地格"和一个"产物格"。

    条目词表与 `DETAIL_SLOT` 同一套；`item` 只给 id/数量，前端按目录补图标与品质。
    `backdrop` 是内容自带的底板图形（不借资源包贴图），内坐标固定 0..100、核心负责拉满面板。
    """
    state = _field(engine, tenant)
    if state is None:
        return None
    slots: list = []
    for index in range(PLOT_COUNT):
        plot = state.plot(index)
        slots.append(_seed_slot(plot, index))
        slots.append(_product_slot(plot, index))
    return {
        "title": NAME_FIELD,
        "prompt": f"把【食物】拖进空地种下，把【矿泉水】拖进去浇水。",
        "slots": slots,
        "rows": [],
        "actions": [],
        "backdrop": _backdrop(),
    }


def _backdrop() -> str:
    """底板：一圈内框 + 一条地脚线（内坐标固定 0..100；颜色走主题色，随资源包变）。

    刻意做得尽量安静 —— 田地的"型"交给每块地自己的框（`.pf-plot`），底板只压个调子。
    想换成别的纹理只改这里；想完全不要，`build_view` 里去掉 `backdrop` 即可。
    """
    return (
        '<g fill="none" stroke="currentColor" stroke-width=".5">'
        '<rect x="1.6" y="1.6" width="96.8" height="96.8" opacity=".18"/>'
        '<path d="M0 97.5h100" opacity=".1"/>'
        "</g>"
    )


def _seed_slot(plot: dict, index: int) -> dict:
    """地格：种着东西时显示它 + 进度条 + 状态；空着时是个可拖入的空格。"""
    label = f"{index + 1} 号地"
    if not plot["seed"]:
        return {
            "group": index, "role": "seed", "label": label, "item": None,
            "locked": False, "on_drop": "drop", "on_take": "",
            "rows": [{"kind": "text", "label": "", "text": "空地。"}],
        }
    rows = [
        {
            "kind": "bar",
            "label": "生长",
            "value": plot["progress"],
            "max": RIPE_PROGRESS,
            "hint": f"每回合涨 1；连着两回合满水涨 2。到 {RIPE_PROGRESS} 成熟。",
        },
        {
            "kind": "bar",
            "label": NAME_MOISTURE,
            "value": plot["moisture"],
            "max": MOISTURE_MAX,
            "hint": "浇水回满，每回合 −1；干着会减产，干满三回合会枯。",
        },
    ]
    rows.append({"kind": "text", "label": "状态", "text": _plot_status(plot)})
    return {
        "group": index, "role": "seed", "label": label,
        "item": {"item_id": plot["seed"], "count": 1},
        "locked": True,           # 种下之后取不出来
        "on_drop": "drop",        # 还能往里浇水
        "on_take": "",
        "rows": rows,
    }


def _product_slot(plot: dict, index: int) -> dict:
    """产物格：成熟后产物落在这里，拖进仓库即收下。"""
    label = f"{index + 1} 号地产物"
    if not plot["pending"]:
        return {
            "group": index, "role": "product", "label": label, "item": None,
            "locked": True, "on_drop": "", "on_take": "",
            "rows": [{"kind": "text", "label": "", "text": "还没有收成。"}],
        }
    return {
        "group": index, "role": "product", "label": label,
        "item": {"item_id": plot["product"], "count": plot["pending"]},
        "locked": False,          # 可以拖走
        "on_drop": "",
        "on_take": "take",
        "rows": [{"kind": "text", "label": "收成", "text": "拖进仓库即可收下。"}],
    }


def _plot_status(plot: dict) -> str:
    """一句话状态：还差几回合熟 / 旱情。"""
    left = max(0, RIPE_PROGRESS - plot["progress"])
    text = f"还差 {left} 点进度成熟（预计收 {plot['yield_max']} 份）。"
    if plot["moisture"] <= 0:
        text += f" 已经断了 {plot['drought']} 回合水。"
    elif plot["moisture"] < MOISTURE_MAX:
        text += f" {NAME_MOISTURE} {plot['moisture']}/{MOISTURE_MAX}。"
    return text


def resolve_action(
    engine: EngineProtocol,
    tenant: object,
    action: str,
    *,
    slot: int | None = None,
    item_id: str | None = None,
    source: object = None,
) -> None:
    """面板动作：`drop`（拖东西进地格）与 `take`（把产物拖走）。"""
    from weiren_game.exceptions import RuleViolation

    state = _field(engine, tenant)
    if state is None:
        raise RuleViolation("这位房客没有田。")
    plot = state.plot(_plot_index(slot))
    if action == "drop":
        _action_drop(engine, tenant, plot, item_id, RuleViolation)
    elif action == "take":
        _action_take(engine, tenant, plot, RuleViolation)
    else:
        raise RuleViolation("田里没有这种操作。")
    _ = source


def _action_drop(engine: EngineProtocol, tenant: object, plot: dict, item_id, error) -> None:
    """拖入：矿泉水 → 浇水；其它【食物】→ 种下。"""
    if not item_id:
        raise error("没有认出拖进来的是什么。")
    if item_id == WATER_ITEM:
        if not plot["seed"]:
            raise error("这块地还空着，先种点什么再浇水。")
        if plot["moisture"] >= MOISTURE_MAX:
            raise error(f"这块地的{NAME_MOISTURE}已经满了。")
        if not _consume(engine, tenant, WATER_ITEM):
            raise error(f"没有{_item_name(WATER_ITEM)}可用。")
        plot["moisture"] = MOISTURE_MAX
        plot["drought"] = 0
        return
    if not _is_food(item_id):
        raise error(f"{_item_name(item_id)}种不下去，只能种【食物】。")
    if plot["seed"]:
        raise error("这块地已经种着东西了。")
    if plot["pending"]:
        raise error("这一格的收成还没拿走，先把地腾干净。")
    if not _consume(engine, tenant, item_id):
        raise error(f"没有{_item_name(item_id)}可种。")
    _reset_growth(plot)
    plot["seed"] = item_id
    plot["moisture"] = MOISTURE_MAX          # 种下就算浇过一遍水
    plot["last_moisture"] = MOISTURE_MAX
    engine._log(f"{engine.character(tenant).name}在{NAME_FIELD}里种下了{_item_name(item_id)}。")


def _action_take(engine: EngineProtocol, tenant: object, plot: dict, error) -> None:
    """拖走产物：并进屋主仓库。"""
    if not plot["pending"]:
        raise error("这一格没有可以收下的东西。")
    item_id, count = plot["product"], int(plot["pending"])
    for _ in range(count):
        engine._merge_house_item(item_id, 1)
    engine._log(f"{engine.character(tenant).name}收下了{_item_name(item_id)} ×{count}。")
    plot["product"] = ""
    plot["pending"] = 0


PANEL = (build_view, resolve_action)


# ---------------------------------------------------------------- 详情页小角落
def detail_slot(engine: EngineProtocol, tenant: object) -> list[dict]:
    """详情页小面板：一句话说明田里现在什么情况。"""
    state = _field(engine, tenant)
    if state is None:
        return []
    rows: list = []
    for index in range(PLOT_COUNT):
        plot = state.plot(index)
        label = f"{index + 1} 号地"
        if plot["seed"]:
            rows.append({
                "kind": "bar", "label": label,
                "value": plot["progress"], "max": RIPE_PROGRESS,
                "hint": f"{_item_name(plot['seed'])}·{NAME_MOISTURE}{plot['moisture']}/{MOISTURE_MAX}",
            })
        elif plot["pending"]:
            rows.append({"kind": "text", "label": label,
                         "text": f"有收成没收：{_item_name(plot['product'])} ×{plot['pending']}"})
    if not rows:
        return []
    return rows


DETAIL_SLOT = detail_slot

# 创作样例集（照着改就能用）

> 面向**内容作者**：这里给的是"最小可用、可以直接抄改"的样例，重点是把
> **需求 → 落哪个文件 → 哪几行是你要改的**讲清楚。
>
> 规则与字段的唯一来源：`docs/ADD_CONTENT.md`（能加什么 / 放哪 / DLC 目录）、
> `docs/GUIDE.md`（数据模型）、`docs/ARCH.md`（效果字段：通道 / 概率 / 闸门）、
> `docs/PRINCIPLES.md`（为什么这样做）。**样例只示范结构，字段以代码为准。**
>
> 本页样例已实测：把 §1–§6 的代码块按标注的文件位置放进一个临时 DLC，能正常装载、
> 各项都注册成功、卸载后无残留（见 §8 自检）。
>
> ⚠️ **样例里的文字为了短，直接写在定义里**；真实写法必须**先把文本放进 lang 表**
> （base = `weiren_game/data/lang.py`；DLC = `dlc/<包>/lang.py`），定义里只写
> `TEXT["item.<id>.name"]` 这类 key。键名约定见 `docs/ADD_CONTENT.md`「文本（lang）」。

---

## 0. 先把需求说清楚（六项）

写任何内容前，先把下面六项写下来（缺项就写"默认 / 沿用现有"）：

1. **是什么、放哪**：类型、放 `data/`（基础包）还是 `dlc/<包>/`、`id`（ascii）与中文名
2. **风味与语气**：一句话定位 / 用途；参考哪条既有内容
3. **机制意图**：解决什么玩法问题；在什么时机生效
4. **数值与概率**：具体数字；概率 5%~95%（**必定**用 0/100）；是否每回合限次
5. **交互与文案**：要不要玩家选（目标/数量/物资）；提示语、标题、选项名（都属内容层）
6. **约束**：是否影响按种子的随机（搜索池/访客池/地点池）、是否触碰平衡、跨内容引用关系

> 完整模板见 `docs/ADD_CONTENT.md`「内容需求描述模板」。

---

## 1. 一件消耗品 + 附着状态

**需求**：`我的小零食`（ascii `my_snack`，食物类，绿色品质）——使用后回复 8 生命，
之后 **3 回合**每回合开始额外回复 2 理智。

**放哪**：基础包 → `weiren_game/data/items/my_snack.py`（文件名随意，新分类才需要新文件）；
DLC → `dlc/<包>/items/my_snack.py`。

```python
"""物资：我的小零食（样例）。"""

from weiren_game.condition import StatusDefinition, register_status_definition
from weiren_game.data.types import I          # 基础包里写 from ..types import I

CATEGORY = "food"

ITEMS = {
    "my_snack": I(
        "my_snack", "我的小零食", CATEGORY, 1,
        "回复 8 生命；之后 3 回合每回合开始额外回复 2 理智。",
        ("food", "consumable"),               # tag 决定通用行为与图标
        consumable=True, stack_size=16,
        on_use="my_snack",                    # ↳ 指向本文件 ITEM_EFFECTS 里的键
    ),
}


def _effect_my_snack(engine, tenant, item):
    """使用效果：签名固定为 (engine, tenant, item)。"""
    engine._restore_health(tenant, 8, item.name)
    tenant.set_status("my_snack_aftertaste", intensity=1, layers=3)


ITEM_EFFECTS = {"my_snack": _effect_my_snack}


def my_snack_aftertaste(engine, tenant):
    """状态每回合开始时结算。"""
    if tenant.condition("my_snack_aftertaste").active:
        engine._restore_sanity(tenant, 2, "小零食余味")


register_status_definition(
    StatusDefinition(
        "my_snack_aftertaste", "小零食余味", "other",
        source_id="item:my_snack",
        nodes=frozenset({"turn_start.status_effects"}),   # ↳ 声明在哪个节点被调用
        hook=my_snack_aftertaste,
        description="嘴里还留着一点甜。",
    )
)
```

**你要改的**：`I(...)` 里的名字/品质/描述/tag、`_effect_my_snack` 的数值、状态名与 `layers`。
**要点**：① 消耗品用 `consumable + stack_size`，耐久品用 `max_durability + use_cost`（二选一）；
② "后续回合的效果"= 挂一个**状态**，状态自己声明 `nodes` + `hook`；
③ 概率/数值别手写随机，走通道（见 §8）。

---

## 2. 一个主动技能（解锁 / 代价 / 效果 / 冷却）

**需求**：`召集邻人`（ascii `my_summon`）——在屋存活 3 回合后解锁；消耗 25 理智；
立刻多 1 名访客；冷却 4 回合。

**放哪**：写在角色文件 `weiren_game/data/characters/<id>.py` 里（与 `CHARACTER` 同一个文件）。

| 需求 | 落点 |
| --- | --- |
| 名称 / 描述 / 限定标记 | `A("my_summon", "召集邻人", "…", chips=("入住 3 回合后解锁", "冷却 4 回合"))` |
| 解锁条件 | `requirements_my_summon(engine, actor, *, bypass)` → 不满足**返回给玩家看的文案** |
| 代价 | `costs_my_summon(engine, actor, *, option)` → `[T("sanity", 25)]`（**别在效果里手扣**） |
| 效果 | `use_my_summon(engine, actor, ability_id, *, bypass=False)` |
| 冷却 | `engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 4)` |
| 让前端能点到 | `ACTIVE_DISPATCH = {"my_summon": lambda engine, actor, *, bypass=False, **kwargs: …}` |

```python
from weiren_game.data.types import A, CharacterDefinition, T

CHARACTER = CharacterDefinition(
    "my_hero", 9001, "我的角色", "一句话人设。", "cheerful", "steady", 3, ("大学生",),
    actives=(A("my_summon", "召集邻人",
               "消耗 25 理智，本回合立即额外增加 1 名访客。"
               "*在屋内存活 3 回合后解锁。*冷却 4 回合。",
               chips=("入住 3 回合后解锁", "冷却 4 回合")),),
)


def requirements_my_summon(engine, actor, *, bypass):
    if getattr(actor, "home_turns") < 3 and not bypass:
        return "需在屋内存活 3 回合后才能使用。"
    return None


def costs_my_summon(engine, actor, *, option):
    return [T("sanity", 25)]


def use_my_summon(engine, actor, ability_id, *, bypass=False):
    engine._queue_human_visitor("邻人应声而来。", force_supply=True)
    engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 4)


ACTIVE_DISPATCH = {
    "my_summon": lambda engine, actor, *, bypass=False, **kwargs:
    use_my_summon(engine, actor, "my_summon", bypass=bypass),
}
```

**真实对照**：`weiren_game/data/characters/dragon.py` 的「呼朋引伴」就是这个结构
（`requirements_/costs_/use_call_friends` + `ACTIVE_DISPATCH`），可以逐行对照着抄。

**变的写法**：需要玩家选目标时给 `A(..., target="tenant"/"information"/"resource"/"amount"/"fate")`
（取值以 `AbilityDefinition.target` 为准），候选由内容自描述：
`TARGET_OPTIONS = {ability_id: lambda engine, actor: [{"value":…, "label":…, "desc":…}]}`。

### 2.1 印记（计数）与进度条

房客可以有专属「印记」：详情页显示成徽记，悬停给出获得条件。想让它有**进度条并在达到阈值时换色**，
就在自己的文件里声明 `bar_tiers`：

```python
from weiren_game.data.types import MarkDefinition

MARKS = (
    MarkDefinition(
        id="my_mark", label="我的印记-我的角色",
        acquisition="每次受伤时获得 1 层。",
        minimum=0, maximum=6,        # 有上限 → 进度条按 6 铺满
        bar_tiers=(3, 6),            # 达到 3 换一档配色，6 为满档
    ),
)
# 无上限（maximum=None）时用最后一个阈值当"满槽"参照，例如 bar_tiers=(10,)；
# 上限与阈值都不写 → 只显示数字，不画条。
```

获得/消耗/读取都用引擎方法：`engine._gain_mark(tenant, "my_mark", n)` /
`engine._consume_mark(tenant, "my_mark", n)` / `engine._mark_count(tenant, "my_mark")`。

### 2.2 头像右侧那片小空间：内容自己说了算

详情页头像右侧（伪人则是门口那张袖珍卡）是一块**公共面板**：谁都可以声明放什么，
系统只提供几种通用条目，排版由框架统一（整行占满，所以多条进度条长度/高度是齐的）。

```python
def detail_slot(engine, tenant):
    """放在头像右侧的条目（按顺序渲染）；不声明就默认列出自己的印记。"""
    return [
        {"kind": "mark", "id": "my_mark"},                  # 引用自己的印记（含进度条）
        {"kind": "bar", "label": "暴露值", "value": 12, "max": 25,
         "tiers": [(5, "线索"), (10, "实锤"), (25, "触发", "danger")]},   # 自定义进度条 + 刻度
        {"kind": "text", "label": "人设", "text": "今天的运气格外好。"},     # 一段说明
        {"kind": "tags", "items": ["崇敬", "3 层"]},                        # 一排小标签
        {"kind": "glyph", "icon": "i-taiji", "label": "混沌",               # 装饰图形（彩蛋）
         "hint": "方向与速度都不由人。", "spin": "random"},                 #   spin: random / cw / 省略
    ]


DETAIL_SLOT = detail_slot           # 模块级声明即可（自动发现）
```

- 档位写法：`at`，或 `(at, 标注, 刻度配色)`——配色可写 `danger`（红线）/`warn`（黄线）/`ok`；
  标注与配色只是**提示**（悬停可见），不改机制。
- 想让某个状态**不进状态栏**（例如人设改到面板里显示），在该状态上声明
  `chip_hidden=True`——见 `weiren_game/data/characters/fries.py` 的实例。
- 伪人同理，声明 `CARD_SLOT(engine)`（同一套条目形状）。
- **独立资源包**（不改资料包也能换外观）：放 `resourcepacks/<名字>/`，`theme.py` 写 `THEME`，
  素材放 `<名字>/assets/` 并在 `theme.py` 里声明：
  ```python
  ASSETS = {"background": "background.svg", "title": "title.svg"}   # 封面背景 / 大标题
  ```
  在「设置 → 资源包」里启用并用 ▲▼ 排位次（越靠上越优先）。现成例子：`resourcepacks/blood_moon/`
  （血月·黑红：只覆盖色调 token + 自带血月背景与血红标题）。
- `glyph` 是"装饰性图形"：给自己挑一个图标 id（`i-moon` / `i-taiji` / 现有 80+ 个，
  见 `webui/index.html` 的 `<symbol id=...>`），`spin="random"` 每次渲染随机方向与速度、
  `spin="cw"` 稳定顺时针、不写就不转；`hint` 悬停可见。
  两个现成彩蛋：厄瑞玻斯在「伟大的封印」期间多一轮明月（悬停：厄瑞玻斯-正在杀出月球）；
  混的太极图在固定「纯真的自我」后由乱转变为稳定顺时针。

---

## 3. 一个概率被动（回合初）

**需求**：`专注`（`my_focus`）——理智 > 85 时，每回合开始 15% 概率回 3 理智。

```python
from weiren_game.data import EVENT_IDS


def my_focus(engine, tenant):
    if getattr(tenant, "sanity") <= 85:
        return
    if not engine._passive_available(tenant, "my_hero.focus"):   # 创伤/紊乱/消沉导致的失效
        return
    success = engine._rng(EVENT_IDS["passive.roll"], tenant.id).random() < .15
    engine._skill_outcome(tenant, "my_hero.focus", success)      # 记录成败（供成就/统计/图鉴）
    if success:
        engine._restore_sanity(tenant, 3, "专注")


TURN_START = my_focus        # ↳ 回合初，每名房客各调一次
```

**要点**：随机用 `engine._rng(EVENT_IDS["…"], salt)`（**按种子的确定性**）；`EVENT_IDS` 里没有的键
要先去 `weiren_game/data/__init__.py` 登记编号（样例借用了已有的 `passive.roll`，
想和其他内容分开随机流就登记一个自己的编号）。

---

## 4. 一类伪人（最小可玩）

**需求**：`我的伪人`（`pseudo_my`）——原型是某位现有房客；每次来访留 1 个印记；
印记满 3 触发突破提示；连续 5 次无印记则解放。

**放哪**：`weiren_game/data/pseudos/pseudo_my.py` 或 `dlc/<包>/pseudos/pseudo_my.py`。
文件名必须是 `pseudo_<id>`（去掉前缀就是状态的桶名）。

```python
from dataclasses import dataclass

from weiren_game.data.types import PseudoDefinition


@dataclass
class MyState:
    """场景状态（必需；`state.pseudo_state.<字段>` 可直读直写）。"""
    marks: int = 0
    safe_streak: int = 0


DEFINITION = PseudoDefinition(
    "pseudo_my", "我的伪人", "my_hero",       # ↳ 人类原型：必须是已存在的角色 id
    "一句话设定。",
    "突破：印记达到 3 时，下一次来访变得危险。",
    "解放：连续 5 次来访不留下印记。",
    mark_field="marks", mark_label="印记-我的伪人",
)


def visit(engine):
    """每次来访结算。"""
    ps = engine.state.pseudo_state
    ps.marks += 1
    engine._log(f"{ps.name}又靠近了一步。")


def observed_skills(engine):
    """对外可见的技能：(内部 id, 展示名)。"""
    return (("mark", "留下印记"),)


def progress_text(engine):
    ps = engine.state.pseudo_state
    return f"印记 {ps.marks}/3，安全 {ps.safe_streak}/5"


def card_info(engine):
    ps = engine.state.pseudo_state
    return {
        "liberation": f"连续 {ps.safe_streak}/5 次无恙则解放。",
        "breakthrough": f"印记 {ps.marks}/3。",
        "mark_need": max(0, 3 - ps.marks),
        "skills": [{"name": "留下印记", "text": "每次来访印记 +1。"}],
    }


HANDLERS = {
    "visit": visit,
    "observed_skills": observed_skills,
    "progress_text": progress_text,
    "card_info": card_info,
}
State = MyState
```

**要点**：① `State` **必需**（没有会在装载时报错）；② 通用进度字段 `revealed` / `visit_count` /
`liberated` 由核心维护，直接读写即可；③ 其余可挂的点（`attack_searcher` / `encounter_chance` /
`tenant_death` / `expel_infiltrator`…）的**签名与时机**用
`python tools/dump_effects.py` + `rg "SCENARIO_HANDLERS.get" weiren_game` 查，别背；
④ 人类原型会自动被排除出访客池、也不能列入禁用角色。

---

## 5. 一条信息

### 5.1 状态类（房客身上的传闻）

**需求**：`投缘的交谈`——待验证时"A、B 回合末各回复 2 理智"；证实后各回复 10；
证伪后无事发生。

```python
from weiren_game.data.types import InformationTemplate

INFORMATION_TEMPLATES = {
    "my_talk": InformationTemplate(
        "my_talk", "投缘的交谈", "state",
        "A与B的日常，相当投缘。",        # 待验证正文（A/B 会换成房客姓名）
        "A 与 B 回合末各回复 2 理智。",   # 待验证期间的持续效果（pending）
        "A 与 B 各回复 10 理智。",        # 证实结算（confirmed）
        "无。",                           # 证伪结算（refuted）
    ),
}


def _resolve_my_talk(engine, info, targets):
    """证实/证伪那一刻的结算；用 info.status 分支。"""
    if info.status == "confirmed":
        for target in targets:
            engine._restore_sanity(target, 10, info.title)


INFORMATION_STATE_EFFECTS = {"my_talk": {"resolve": _resolve_my_talk, "pending": None}}
```

### 5.2 地点修正类（去哪搜更值）

**需求**：`我常去的那家店`——指向便利店，搜这里更容易出易损品和高级货。

```python
from weiren_game.data.types import InformationTemplate

INFORMATION_TEMPLATES = {
    "my_shop": InformationTemplate(
        "my_shop", "我常去的那家店", "location_modifier",
        "便利店的货架后面还有东西。", location_id="convenience_store",
    ),
}

LOCATION_INFORMATION_MODIFIERS = {
    "my_shop": {"tag:fragile": 4.0, "quality:high": 2.0, "uses": 5},
}
```

**要点**：占位符只有 `[地点]` 与 `A` / `B`；修正键是 `tag:<tag>` / `quality:<段位>` /
`uses`（次数）/ `turns`（回合）；`reward_ids` 里的物品必须已存在。

---

## 6. 一个全局事件（跨内容开关）

**需求**：`我的事件`（`my.event`）——生效期间搜索更容易出好货；持续 5 回合。

```python
from weiren_game.global_event import GlobalEventDefinition, register_global_event

register_global_event(GlobalEventDefinition(
    id="my.event", label="我的事件",
    icon="i-clock",                 # 游戏内「全局事件」页第一行的图标
    description="这段时间里，搜索更容易遇到好东西。",   # 点开看到的内容
))
```

下面两段是**片段**，分别写在"触发它的地方"和"读它的地方"：

```python
# 谁让它生效：在触发点（技能 / 信息结算 / 物品效果）写
engine._set_global_event("my.event", 1.0, 5)          # (id, 数值, 持续回合)

# 谁读它：在相关系统/内容里判断
if engine._global_event_active("my.event"):
    fortune = engine._global_event_value("my.event", 1.0)
```

**要点**：事件只是"通用键 + 数值/布尔"，**它本身不做判定**——读取方决定效果；
命名用 `<域>.<作用>`（别塞角色名）；持续回合约定：下回合初兑现 ≥2 / 本回合内 1 / 长期 99。

---

## 6.5 换个材质 / 字体 / 加一个贴图零件（资源包）

材质（颜色 token、字体栈）与贴图零件（SVG）都在**内容层**：`weiren_game/data/resourcepack/`
是默认材质（**前端 `:root` 留着一份同样的兜底值**，所以资源包坏了也不掉材质），
DLC 放个同名目录就能**覆盖/追加**：

```python
# dlc/我的包/resourcepack/skin.py
THEME = {
    "tokens": {                                  # 同名 token 覆盖内置（只能改"色调/字体"）
        "--bg": "#0d1214", "--panel": "#19221f", "--panel2": "#1f2b28",   # 底/面板
        "--edge": "#0a1416",                                              # 描边
        "--btn-1": "#22383a", "--btn-2": "#131f21",                       # 普通按钮面
        "--pri-1": "#2f6f78", "--pri-2": "#1d474e",                       # 主按钮面
        "--amber": "#4fd1c5",                                             # 强调色
        "--amber-rgb": "79,209,197",     # 强调色的 rgb 分量：hover/选中态用它做透明叠加，改 --amber 时要一起改
        "--sans": '"Cascadia Mono",monospace',   # 换字体就覆盖字体 token（--mono/--sans/--serif/--hei/--comic/--px-font）
    },
    "css": ".tenant{border-radius:6px}",         # 可选：追加自己的规则（含 @font-face）
}

SYMBOLS = {                                      # 新贴图零件（viewBox 统一 24×24）
    "i-av13": '<path d="M12 3l3 6 6 .8-4.4 4.2 1.1 6-5.7-3-5.7 3 1.1-6L3 9.8 9 9z"/>',
}
```

- 用法：零件按 id 被内容引用 —— 角色声明 `AVATAR = "i-av13"`、小面板 `{"kind":"glyph","icon":"i-av13"}`。
- **只能改"色调"**：语义提示色（好/危险/警告/信息）、品质色、羁绊位阶、以及尺寸
  （`--slot` 格子边长、`--w` 描边）都被**锁定**，资源包写了也会被忽略（服务端会打一行提示）。
  这样换皮肤不会改变颜色含义、也不会让布局跑版。
- **头像零件可以组合**：角色可声明「形状 × 专属特征」（点缀色/点缀环已废弃）
  ```python
  AVATAR = "i-av9"              # 形状
  AVATAR_FEATURE = "i-ft-crown" # 专属特征（可由资源包提供新零件）
  AVATAR_COLORS = {"a": "#ffcc66"}  # 可选：给零件的色槽 var(--a) 填色
  ```
  不声明就按 id 哈希派生（保持既有观感）；有整张头像（`data/avatars/characters/<角色id>.svg`
  或包内 `avatars/characters/`）时整张优先，包声明 `avatar_mode="parts"` 可让 base 层立绘让位。
- **装载/卸载即生效回滚**：界面 DLC 页「应用」即可；同名零件/token 由包优先级决定谁赢。
- 内置材质清单见 `data/resourcepack/theme.py`（颜色 token 与字体栈都在那），参数速查见 `docs/STYLE.md` §9。

---

## 7. 打包成 DLC

```
dlc/我的内容包/
  dlc.json                 # {"name": "我的内容包", "version": "1.0.0", "min_game_version": "2.1.0"}
  __init__.py              # 可选：def register(ctx): ...
  characters/  items/  tags/  locations/  information/  pseudos/  codex/
```

| 场景 | 怎么做 |
| --- | --- |
| 只加新东西（扩展包） | 按上面目录放文件 → 界面 DLC 页「▶ 安装」→ 应用 |
| **替换**内置内容（如"更强的某角色"） | 用**同样的 id** 写一遍，然后在 DLC 页用 **▲** 把包调到 `base` **上面** → 应用 |

- 卸载即回滚：装/卸都在 DLC 页完成，无需重启。
- 起步可直接复制 `dlc/_template/`；失败先看 `python tools/validate_content.py`。

---

## 8. 自检与常见坑

```
python tools/validate_content.py        # 编号/头像/性格/技能派发/引用完整性
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_separation.py        # 内容层不许被系统/前端按名字引用
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
python game_ui.py                       # 进游戏看一眼
```

- **数值与随机**：走通道与收敛（`engine._apply_modifiers`；概率见 `docs/GUIDE.md` §4.3）；
  **必定**用 0/1；"能不能 / 是否免疫"用**闸门**（纯查询）。见 `docs/ARCH.md`。
- **确定性**：新增**可搜索物品**、`available=True` 的角色、新地点会改变按种子的随机序列——
  可能牵动固定种子的测试/素材，先跑单测。
- **别改核心**：文案、数值、判定都写在内容文件里；系统层与前端**不得出现具体内容名/id**。
- **平衡**：数值改动请单独列出、等确认，不要顺手调（仓库约定）。

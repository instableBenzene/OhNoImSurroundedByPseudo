# 内容创作：能加什么、放哪、怎么加

> 本文由原 `CONTENT_TYPES.md` / `ADD_CHARACTER.md` / `ADD_DLC.md` 合并，**内容原样保留**。
> 不变量见 `AGENTS.md` §3；架构与数据模型细节见 `docs/GUIDE.md`；风格见 `docs/STYLE.md`。

---

## 内容类型全景：base 扩展 vs DLC

> 本文件回答「到底能加哪些东西、放在哪、怎么生效」。细节见 `docs/GUIDE.md`，规范见 `AGENTS.md`。

### 两种创作方式

| | base 扩展 | DLC |
| --- | --- | --- |
| 放哪 | `weiren_game/data/**` | `dlc/<name>/**` |
| 生效 | 随游戏一起、**自动发现** | 装载后生效；界面可**热安装/卸载** |
| 定位 | 基础内容包（影响固定种子的随机序列） | 可选内容包（存档记录 `meta.packs`） |
| 版本 | 随 `GAME_VERSION` | `dlc.json.min_game_version` 门槛 |
| 约束 | 不得让系统/前端引用其名（不变量 1） | 同左；且不得 import 具体内置内容 |

新增内容后统一验证：`python tools/validate_content.py` + 单测 + `python tools/audit_separation.py`。

### 内容类型一览

| 类型 | 位置 / 文件 | 声明方式 | 自动发现 | 备注 |
| --- | --- | --- | --- | --- |
| **房客（人类角色）** | `data/characters/<id>.py` | 暴露 `CHARACTER`（`CharacterDefinition`） | ✅ | 一个文件一名角色；`source_id` 唯一；建议声明 `AVATAR` |
| **角色行为** | 同上 | `ACTIVE_DISPATCH`、`INTERACTIONS`、`PENDING_VIEW`、`TARGET_OPTIONS`、`CODEX_EXTRA/SECTION/SUMMARY`、`SEARCH_REWARD`、`TURN_START`、`VALUE_HOOKS`、`NODE_HOOKS`、`HOOKS`、`MARKS`、`HEALTH_CHANGED`、`ON_ABILITY_USED/FAILED`、`ON_MARK_GAINED/CONSUMED/REACHED`、`TENANT_DEATH`、`INFORMATION_CREATED`、`PROTECTED_STARTER`、`DEFAULT_PSEUDO` | ✅（随角色模块） | 角色专属的状态/事件/搜索修正/能力全写在自己文件里 |
| **性格（羁绊）** | `data/personalities/<key>.py`；DLC `personalities/<key>.py` | `TIERS`（或 `TIER_AT`/`ACTIVE_TIERS`/`ROUND_UP`）、`HOOKS`、`BOND_*`、modifier providers；可选 `LABEL`（中文名） | ✅ | 文件名即性格键；DLC 的中文名由 `LABEL` 登记（缺省回退为键名） |
| **物品** | `data/items/<file>.py` | `CATEGORY` + `ITEMS`（`I(...)`）；可选 `ITEM_HOOKS`、`ITEM_EFFECTS` | ✅（按 `CATEGORY_ORDER`） | 风味见 `items/flavor.py`；图鉴全文见 `items/codex_text.py` |
| **物资标签** | `data/tags/<tag>.json`（条目）或 `data/tags/<tag>.py`（行为）；DLC 同名两路 | JSON 为 `item_id`/物品名列表；`.py` 暴露 `after_*` 等 → `TAG_BEHAVIORS` | ✅（与内置同名 tag 合并/覆盖） | 中文名/图标经 `data/labels.py` 的登记函数（或 `register(ctx)` 调用） |
| **地点** | `data/locations.py`（内置）/ DLC `locations/<file>.py` | `LOCATIONS`（`L(...)`，可选 `tier=1/2/3` 标档位）；可选 `MAP_GROUPS`（新分组纳入开局抽取） | DLC ✅ | 图鉴图标/文案在 `data/codex_pack.py` 的 `LOCATION_ICONS`/`LOCATION_TEXT`；图标是「白底 + 档位特征色」，见 `data/icon/locations/` |
| **地图（区域包）** | `data/maps/<地图id>/map.py`；DLC `maps/<地图id>/map.py` | 暴露 `MAP = MapDefinition(id, name, shelter, locations=(...), draw_count=10)` | ✅（文件夹即发现） | `locations` 是**显式名单**：地点要出现在这张图里就必须列进来。DLC 想让自己的地点进「城郊小镇」→ `ctx.register_map_location("base", "<地点id>")`。屋子显示名 = 所选地图的 `shelter` |
| **信息模板** | `data/information.py` / DLC `information/<file>.py` | `INFORMATION_TEMPLATES`、`LOCATION_INFORMATION_MODIFIERS`、`INFORMATION_STATE_EFFECTS` | DLC ✅ | 图鉴全文见 `data/information_text.py` |
| **伪人** | `data/pseudos/<id>.py` | 暴露 `DEFINITION` + `HANDLERS`（+ 可选 `State`、`NODE_HOOKS`） | ✅ | 建议提供 `HANDLERS["observed_skills"]`、`["progress_text"]`；人类原型须存在 |
| **主动/被动能力** | 写在角色/伪人模块内 | `A(id, name, desc, target=..., prompt=..., options=..., amount_label/amount_mark, chips, nested_option, branches)` | 随模块 | 声明式；前端/CLI 通用渲染；处理函数进 `ACTIVE_DISPATCH`。`options` 每项是 `(value, label)`，**可选第 3、4 项** `(value, label, icon, desc)`：`icon` 取贴图零件 id（`i-*`）、`desc` 是一句说明 —— 界面有就用、没有就回退中性图标，旧写法不受影响 |
| **状态 / 情绪** | 内置写在 `weiren_game/condition.py`；DLC `statuses/<file>.py` | 暴露 `STATUSES` / `EMOTIONS`（`StatusDefinition` / `EmotionDefinition`）；`chip_hidden=True` 表示不进状态栏（改用小面板等展示） | DLC ✅ | 情绪会顺带登记「情绪显现」**全局事件**定义（`emotion.reveal.<情绪>`）并同步 data 层标签表 |
| **印记** | 角色模块 | `MARKS = (MarkDefinition(...),)`；可选 `bar_tiers`（进度条换档；可写 `(at, 标注, 刻度配色)` 做提示，如 `(4, "可驱逐", "danger")`；无上限时当"满槽"参照） | ✅（随角色模块） | 获得/消耗走 `engine._gain_mark/_consume_mark/_mark_count`；伪人印记的对外称呼见 `PseudoDefinition.mark_label` |
| **详情页小面板 / 袖珍卡面板** | 角色模块 `DETAIL_SLOT`、伪人模块 `CARD_SLOT` | 返回条目列表：`mark`（引用自己的印记）/ `bar`（自定义进度条，可带档位刻度）/ `text`（一段说明，如人设）/ `tags`（小标签）/ `glyph`（装饰图形，可 `spin` 旋转，悬停给文案） | ✅（随模块） | 头像右侧与门口伪人卡里的**公共区域**；不声明 `DETAIL_SLOT` 时回退为"列出自己的印记" |
| **资源包（材质 / 字体 / 贴图零件）** | 内置 `data/resourcepack/*.py`；DLC `resourcepack/*.py` | 暴露 `THEME = {"tokens": {"--bg": …, "--btn-1": …, "--amber": …}, "css": "…"}` 与 `SYMBOLS = {"i-xxx": "<path …/>"}`（viewBox 统一 24×24） | ✅ | **覆盖/追加**语义：同名 token / 零件 id 由包优先级决定谁赢；**只能改色调/字体**——语义色、品质色、羁绊位阶、尺寸（`--slot`/`--w`）锁定；前端自带默认材质，资源包缺失时观感不变 |
| **专属状态容器** | 角色模块 `CONTAINERS` | `CONTAINERS = {"<key>": <类>}`；类自己实现 `to_dict` / `from_dict` | ✅（随模块） | 房客专属状态，随存档走；引擎入口 `engine.container(tenant, key)`；存档里没声明过的 key / 坏数据一律丢弃（对玩家宽容） |
| **专属面板（自定义 UI）** | 角色模块 `PANEL` | `PANEL = (build_view, resolve_action)`；`build_view` 返回 `{title, prompt, slots, rows, actions, backdrop?}`（`rows` 与 `DETAIL_SLOT` 同词表；`slots` 只给 `item_id`/数量）；`resolve_action(engine, tenant, action, *, slot, item_id, source)` | ✅（随模块） | 入口是 `opens_panel=True` 的技能（点击**不结算**能力）；面板**不参与回合流程**，开合是纯展示；详见 `docs/GUIDE.md` §14.11 |
| **资源包（独立一层）** | `resourcepacks/<name>/`（`pack.json` + `theme.py` / `symbols*.py` / `assets/*`） | 同上的 `THEME` / `SYMBOLS`（零件 id 通用，内容引用即生效）；另有 **`ASSETS`**：`background`（启动器封面）、`title`（大标题**整块**，含副标题那行） | ✅ | 与资料包并列、**各自有序**（设置 → 资源包，可 ▲▼ 调位次）；高者覆盖低者；独立资源包总在资料包之后套用，故能盖过资料包自带的外观 |
| **头像零件**（每件一个文件） | `data/avatars/shapes/<id>.svg`、`data/avatars/features/<id>.svg`、`data/avatars/characters/<角色id>.svg`（24 张兜底立绘就在这里，属 base 层）；资料包/资源包可放同名 `avatars/...` 覆盖 | 角色 `.py` 可声明 `AVATAR`（形状 id）/`AVATAR_FEATURE`/`AVATAR_COLORS`（零件色槽 a–e 填色；点缀色/点缀环已废弃） | ✅ | 优先级 base → 资料包（位次）→ 资源包（位次）；`characters/<id>.svg` 是"整张头像"，直接替换该角色（人/伪人通用）；包的 `pack.json::avatar_mode="parts"` 可让 base 层立绘让位、全员改用零件（包自己放的整图仍优先）。零件声明过颜色就内联（色槽可被创作者替换），只用 `currentColor` 的走蒙版+主题色。**纯显示，不进存档** |
| **物品图标**（每件一个文件） | `data/item/item/<物品id>.svg`（专属）、`data/item/tag/<tag>.svg`（按标签兜底）；资料包/资源包可放同名 `item/...` 覆盖 | 纯 SVG 文件，无需登记：有专属图就用专属图，否则按物品标签顺序找 tag 图（`ITEM_TAG_ICON_PRIORITY`） | ✅（放文件即生效） | 优先级 base → 资料包（位次）→ 资源包（位次）。**两色规则**：`#d7ddd2`/`currentColor` = 底色（→ 主题 `--ink`），其余颜色 = 特征色（→ 该物品的**品质色**）；后端内联下发，尺寸走 `.art-inline`。没图标文件就回退内置 `i-*` 零件。**纯显示，不进存档** |
| **全局事件** | 任意内容模块 | `weiren_game/global_event.py` 的 `register_global_event(...)`；定义带 `label` / `icon` / `description`（后者是游戏内「全局事件」页点开看到的内容） | ✖（需显式注册；无目录约定） | DLC 可在 `register(ctx)` 或模块导入时注册 |
| **图鉴补充 / 机制 / 羁绊文案** | `data/codex_pack.py`、`data/labels.py` | `MECHANICS`、`PERSONALITY_*`、`PSEUDO_SKILLS`、`register_section(...)` | 内置；DLC 经 `codex/` | 见 `docs/STYLE.md` §7；改这些静态表卸载时会整体回滚 |
| **地点 / 信息 / 伪人图标**（每件一个文件） | `data/icon/locations/<location_id>.<ext>`、`data/icon/information/<template_id>.<ext>`、`data/icon/pseudos/<pseudo_id>.<ext>`；资料包/资源包可放同名 `icon/<section>/...` 覆盖 | 纯图片文件，**无需登记**（按 id 命名即可；`.svg/.png/.jpg/.jpeg/.webp`） | ✅（放文件即生效） | 优先级 base → 资料包（位次）→ 资源包（位次），经 `GET /api/icon/<section>/<id>` 提供。这些是**彩色插画**（不参与配色 token）；没图就回退内置单线图标。**纯显示，不进存档** |

### 快速上手

- 加房客：`python tools/new_character.py <id> <名>` → 填内容 → `validate_content` → 单测。
  （脚手架**同时**把名字/描述等文本写进 `data/lang.py`，你只要去 lang 表填 TODO 文案。）
- 打包 DLC：复制 `dlc/_template/` → 按上表填各目录 → 界面"应用"热装卸。
- 换美术（**按 id 命名放文件即可，不用清单**）：地点/信息/伪人图标放 `data/icon/<section>/<id>.<ext>`；
  某角色的**整张头像**放 `data/avatars/characters/<角色id>.svg`；物品图标放 `data/item/item/<id>.svg`；
  要能"随包开关"就放包内同名路径（`dlc/<包>/...` 或 `resourcepacks/<包>/...`）。
- **不知道怎么下手 → 抄样例**：`docs/COOKBOOK.md` 有"照着改就能用"的最小样例
  （物品+状态 / 主动技能 / 概率被动 / 伪人 / 信息 / 全局事件 / DLC 打包）。

### 内容需求描述模板（开工前先对齐）

给 AI / 内容作者提需求时按下面六项说清；缺项就明确写「默认 / 沿用现有」，别边做边猜：

1. **是什么、放哪**：类型（房客 / 物品 / 伪人 / 信息·事件 / 地点 / 性格 / 状态…）、
   放 `data/`（base 扩展）还是 `dlc/<包>/`、`id`（ascii）与中文名。
2. **风味与语气**：一句话定位 / 用途；参考哪条既有内容；是否要同步设计稿（差异记「附录 A」）。
3. **机制意图**：解决什么玩法问题；在什么时机生效（回合初 / 回合末 / 搜索 / 来访 / 使用 / 被识破…）。
4. **数值与概率**：具体数字，或「照某某条目」；概率一律 5%~95%（**必定**用 0/100）；
   是否每回合限次（`per_turn`）——**没写就是没限制**。
5. **交互与文案**：要不要玩家选（目标 / 数量 / 提交物资）；提示语、标题、选项名（属内容层，随视图下发）。
6. **约束**：是否影响按种子的确定性（搜索掉落池 / 访客池 / 地点池）、是否触碰平衡
   （数值改动单列、待评审）、与其它内容的引用关系（跨内容引用要**成组增删**）。

> 各内容类型还有自己的一组字段：见对应 skill（`weiren-new-character` / `weiren-new-item` /
> `weiren-new-pseudo` / `weiren-new-information` / `weiren-new-dlc`）。

### 文本（lang）：加一条就能用，没有注册动作

- **表在哪**：base = `weiren_game/data/lang.py::TEXT`；每个 DLC = `dlc/<包>/lang.py`
  （模块顶部 `TEXT = pack_text_from_file(__file__)`）。
- **键名用既有 id 拼**：`character.<id>.name|description|tag.N`、`ability.<id>.name|description`、
  `item.<id>.name|description|flavor`、`pseudo.<id>.*`、`info.<id>.*`、`mark.<id>.*`；
  系统层与前端的键按位置生成（`<模块>.<函数>.<n>`、`ui.js.<n>`、`ui.markup.<n>`）。
- **怎么用**：定义里写 `TEXT["item.my_item.name"]`；带占位符的模板写 `{名字}`、调用点 `.format(...)`；
  前端 chrome 用 `TXT("ui.x")` 或槽位 `data-t="ui.x"`。
  ```python
  # lang.py
  "item.my_item.name": "我的物品",
  "item.my_item.description": "使用后回复 {amount} 点生命。",
  # 使用点
  I("my_item", TEXT["item.my_item.name"], "consumable", 2,
    TEXT["item.my_item.description"], ("consumable",), on_use="my_item")
  ```
- **打错 key**：Python 侧当场 `KeyError`；前端原样显示 key（肉眼可见）。核对/盘点用
  `python tools/dump_text.py --out <目录>`。
- **不进 lang 的**：`path` / `source` / tag / 性别 / 年龄 / 兴趣——它们参与规则命中，**禁止翻译**。
- 详细约定（含 DLC）见 `.opencode/skills/weiren-dev/SKILL.md` §2.1 与 `weiren-new-dlc`。

### 已知限制（诚实说明）

- **全局事件** 不是"放文件即生效"，需要在模块里调用注册函数（角色模块导入时执行，或用 DLC 的 `register(ctx)`）。
- **新增注册表**必须登记进 `weiren_game/content.py` 的 `_BASE_CONTAINERS`，否则卸载 DLC 后仍会残留（历史踩坑：目标候选、图鉴补充、状态/情绪、图鉴静态表、效果内核的修饰器·闸门表）。
- 头像/图标默认是**程序化单线 SVG**；要高质感需按"外置美术资源"提供图片。

---

## 新增一名房客（零改核心）

### 0. 原则
- 只新增 `weiren_game/data/characters/<id>.py`；自动发现会登记它，**不要**改注册表。
- 不写任何 `id` 特判到 `systems/` 或前端；交互/选择用声明式规格。

### 1. 文件骨架

```python
"""房客档案：<姓名>（<编号>号，<机制一句话>）。"""
from ..types import A, B, CharacterDefinition, MarkDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT          # 文本都住 lang 表

CHARACTER = CharacterDefinition(
    "my_id", 25, TEXT["character.my_id.name"], TEXT["character.my_id.description"],
    "primary_key", "secondary_key", 3,
    (TEXT["character.my_id.tag.0"], TEXT["character.my_id.tag.1"]),
    actives=(A("active_id", TEXT["ability.active_id.name"],
               TEXT["ability.active_id.description"]),),   # 需要目标时给 target="tenant"/...
    passives=(A("passive_id", TEXT["ability.passive_id.name"],
                TEXT["ability.passive_id.description"]),),
    available=True,
)

# 主动技能结算：用能力 id → 处理函数
def use_active(engine: EngineProtocol, actor, **kwargs) -> None:
    """<主动名> 的结算。"""
    ...

ACTIVE_DISPATCH = {"active_id": use_active}

# 需要玩家选择的候选（供前端/CLI 通用渲染）
# def candidates(engine, actor): return [{"value": ..., "label": ..., "desc": ...}]
# TARGET_OPTIONS = {"active_id": candidates}

# 图鉴补充（可选）
# def CODEX_EXTRA(): return [{"title": "...", "entries": [("名", "说明"), ...]}]

# 头像（内容自声明；形状 1~12，可与专属特征组合）
AVATAR = "i-av5"
```

### 2. 可选的模块级自描述（按需）
`INTERACTIONS`、`PENDING_VIEW`、`TARGET_OPTIONS`、`CODEX_EXTRA`、`CODEX_SECTION`、`CODEX_SUMMARY`、
`SEARCH_REWARD`、`TURN_START`、`VALUE_HOOKS`、`NODE_HOOKS`、`HOOKS`、`MARKS`、
`HEALTH_CHANGED`、`ON_ABILITY_USED`、`ON_ABILITY_FAILED`、`ON_MARK_GAINED/CONSUMED/REACHED`、
`TENANT_DEATH`、`INFORMATION_CREATED`。

### 3. 能力声明式字段
`A(id, name, desc, target="none", branches=..., prompt="", options=((值,显示名),...), amount_label="", amount_mark="", chips=("冷却 3 回合",), nested_option="")`。
- `target` 决定前端/CLI 弹什么：`tenant / other_tenant / tenant_condition / resource / amount / information / fate / none`。
- 限定条件写进 `chips`，**不要**再在描述里重复。

### 4. 检查清单
- [ ] `source_id` 唯一；`primary/secondary` 用现有性格键。
- [ ] 主动能力都有 `ACTIVE_DISPATCH` 处理函数（签名含 `**kwargs`）。
- [ ] 需要选择的能力给了 `target`（及 `options`/`TARGET_OPTIONS`/`amount_*`）。
- [ ] 给了 `AVATAR`。
- [ ] 运行验证：`compileall`、`unittest discover`、`smoke`、`audit_separation`。
- [ ] 若与设计稿有差异，更新设计稿 md 的「附录 A」。

---

## 编写一个 DLC 内容包

### 1. 目录结构

```
dlc/<dlc_name>/
  dlc.json                # {"name": "...", "version": "1.0.0", "min_game_version": "2.1.0"}
  lang.py                 # **本包全部文案**：TEXT = {"item.my_item.name": "我的物品", ...}
  __init__.py             # 可选：def register(ctx): ...（ctx 即 ContentManager）
  characters/<id>.py      # 每个文件暴露 CHARACTER（或 CHARACTERS）
  personalities/<key>.py  # 每文件一类性格（TIERS/TIER_AT/HOOKS/BOND_* + 可选 LABEL）
  items/<name>.py         # 暴露 CATEGORY 与 ITEMS；可选 ITEM_HOOKS / ITEM_EFFECTS
  tags/<tag>.json         # 文件名即 tag；内容为 item_id 或物品名列表（与内置同名 tag 合并）
  tags/<tag>.py           # 文件名即 tag 的行为模块（进 TAG_BEHAVIORS）
  statuses/<name>.py      # 暴露 STATUSES / EMOTIONS（状态与情绪定义）
  resourcepack/<name>.py  # 暴露 THEME（CSS 变量/字体/追加 css）与 SYMBOLS（贴图零件）
  avatars/<section>/<id>.svg  # 头像零件/整张头像（shapes/features/characters，按位次覆盖 base）
  item/item/<物品id>.svg  # 自带物品的专属图标
  item/tag/<tag>.svg      # 按标签兜底（没有专属图标的物品用）
  icon/<section>/<id>.<ext>  # 地点/信息/伪人图标（section = locations/information/pseudos）
  maps/<id>/map.py        # 自带一张地图（MAP = MapDefinition，含显式地点名单）
  locations/<name>.py     # 暴露 LOCATIONS
                          #   可选 MAP_GROUPS：把新分组纳入开局抽取
  information/<name>.py   # 暴露 INFORMATION_TEMPLATES（可选 LOCATION_INFORMATION_MODIFIERS）
  pseudos/<id>.py         # 暴露 DEFINITION / State / HANDLERS（可选 NODE_HOOKS）
  codex/*.py              # 可选：def register(ctx): ctx.register_section({...}) 追加图鉴分节
```

### 2. 行为
- 装载：`weiren_game/dlc.py` 的 `load_single_dlc(name)`；界面"应用"时 `reload_dlc(names)` 热切换（回滚 base 再重装）。
- 版本：`dlc.json.min_game_version` 高于当前 `GAME_VERSION` 会被拒绝。
- 存档记录 `meta.packs`；与当前启用包不一致时拒绝读档。
- 依赖提示：跨内容引用（角色发放某物品、伪人与其人类形态、tag 引用物品）应成组增删；核心对缺失内容一律容忍。
- **DLC 伪人的图鉴技能**：本体图鉴「伪人」页的技能来自 `codex_pack.PSEUDO_SKILLS`（内置静态表）。
  DLC 伪人在自己的模块里声明 `CODEX_SKILLS = ((名称, 文案), ...)`，图鉴页会自动回退读它；
  突破 / 解放来自 `DEFINITION`，无需额外处理。
- **人类形态互斥**：`DEFINITION.human_character_id` 指向的角色会被自动排除出访客池，且不能被列入禁用角色
  （运行时从 `PSEUDOS` 计算，DLC 同样生效）。
- **限定 chip 由技能自声明**：`A(..., chips=("冷却 2 回合",))`；内置已无静态 chip 表。
- **性格 / 状态·情绪 / tag 行为 / 地点分组** 都是"放文件即生效"（`personalities/`、
  `statuses/`、`tags/<tag>.py`、`locations/` 的 `MAP_GROUPS`）；**全局事件**仍需在
  `register(ctx)` 或模块导入时显式注册。
- **热切换回滚**：装载器能回滚的注册表以 `weiren_game/content.py` 的 `_BASE_CONTAINERS` 为准；
  卸载后不残留 id、不串味（若新增注册表，必须加进那张表）。
- **内容包优先级 = 替换内置内容**：启用包是一份**有序**清单（`game_config.json::pack_order`，
  高 → 低，含 `base`）。装载从最低优先级开始，因此**高位包覆盖低位包的同 id 内容**；
  轮到 `base` 时执行一次"base 覆盖"，于是排在 base **下方**的包改不动内置内容，
  把包调到 base **上方**即可替换它（例：一个替换某位房客的更新包）。

### 2.1 哪些能被覆盖

| 可覆盖（同 id 取高位包） | 只增不换（钩子序列等） |
| --- | --- |
| 房客（`CHARACTERS`/行为模块）、物资、地点、信息模板、伪人（定义与处理器）、性格（同键）、状态·情绪（同 id）、tag 行为（同名）、图鉴/标签静态表 | 各类节点 hook 列表、`PENDING_VIEWS`、`CODEX_*` 追加段、全局事件 |

- 覆盖只针对**按 id 索引的定义**；钩子是"叠加"语义，卸载时整体回滚。
- 存档记录的是**包清单**（不含顺序）；对局中途改顺序不会被存档校验拦下，请在新开局前调整。

### 3. 用 `dlc/_template/` 起步
复制模板目录改名，按上面结构填写；`codex/` 可让 DLC 贡献图鉴内容。

### 4. 检查清单
- [ ] `dlc.json` 完整，`min_game_version` 与当前版本匹配。
- [ ] 新内容 id 不与内置冲突（冲突会报错或覆盖，视类型而定）。
- [ ] 不 import 具体内置内容；只用通用协议与注册表。
- [ ] 新性格给了 `LABEL`（中文名）；新地点分组给了 `MAP_GROUPS` 的中文名/图标。
- [ ] 安装/卸载（界面"应用"）能正确生效与回滚；跑 `audit_separation` 与单测
      （可参照 `tests/test_architecture.test_dlc_content_channels_and_rollback`）。

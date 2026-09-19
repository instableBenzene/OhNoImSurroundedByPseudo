---
name: weiren-new-information
description: Use when adding information/信息 or global events/事件 to OhNoImSurroundedByPseudo — "加信息 / 新信息 / 做事件 / 全局事件 / information". Covers InformationTemplate fields, placeholders and kinds, location modifiers, state effects, global event registration/keys, and verification.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# 新增信息模板 / 全局事件

先读 `.opencode/skills/weiren-dev/SKILL.md` 与 `docs/ADD_CONTENT.md`；效果细则见 `docs/ARCH.md`。
**给人读的完整样例**：`docs/COOKBOOK.md` §5（状态类 / 地点修正）/ §6（全局事件）。

## 1. 信息模板放哪

- base：`weiren_game/data/information.py`；DLC：`dlc/<包>/information/<文件>.py`。
- 暴露 `INFORMATION_TEMPLATES = {id: InformationTemplate(...)}`，
  可选 `LOCATION_INFORMATION_MODIFIERS`、`INFORMATION_STATE_EFFECTS`。

```python
from ..types import InformationTemplate       # DLC：from weiren_game.data.types import ...
from weiren_game.data.lang import TEXT         # DLC 里用 pack_text_from_file(__file__)
INFORMATION_TEMPLATES = {
    # 物资线索：说明被 [地点] 替换；奖励物品必须已存在
    "my_reward": InformationTemplate("my_reward", TEXT["info.my_reward.name"], "material_reward",
                                     TEXT["info.my_reward.description"], reward_ids=("my_item",)),
    # 房客状态：A / B 会被替换成两名房客姓名；三段 = 待验证 / 已证实 / 已证伪
    "my_state": InformationTemplate("my_state", TEXT["info.my_state.name"], "state",
                                    TEXT["info.my_state.description"],
                                    TEXT["info.my_state.pending"],
                                    TEXT["info.my_state.confirmed"],
                                    TEXT["info.my_state.refuted"]),
}
```

文案写进 lang 表：`info.<id>.name|description|pending|confirmed|refuted`
（加一条就能用，没有注册动作；`kind` / `location_id` / `reward_ids` 是数据键，不进 lang）。

- `InformationTemplate` 字段以 `weiren_game/types.py` 为准：
  `id / name / kind / description / pending / confirmed / refuted / location_id / reward_ids / duration`。
- `kind` 取现有值（见 `data/labels.py::INFORMATION_KIND_LABELS`）；**新 kind 要登记中文名**。
- 占位符（由 `information_system` 替换，**只有这两个**，见调用点）：`[地点]`、`A` / `B`。
- 地点修正：`LOCATION_INFORMATION_MODIFIERS[template_id] = {"tag:food": 2.0, "quality:high": 2.0, "uses": 3, "turns": 2}`
  （键为 `tag:<tag>` / `quality:<段位>`，`uses` / `turns` 控制生效次数或回合）。
- 状态类信息的实际结算：`register_state_effect(...)` 挂到 `INFORMATION_STATE_EFFECTS`。
- 图鉴全文：`data/information_text.py`。

## 2. 字段速查

| 字段 | 用途 |
| --- | --- |
| `kind` | 信息类型（`material_reward` / `location_modifier` / `state`；取值与中文名见 `data/labels.py::INFORMATION_KIND_LABELS`） |
| `description` | **待验证时**显示的正文（物资/地点类只用这一段） |
| `pending` / `confirmed` / `refuted` | 状态类信息的三段：待验证**持续效果** / **证实**结算 / **证伪**结算（不需要就写 `"无。"`） |
| `location_id` | 指向的地点（`[地点]` 会替换成它的名字；也是"去哪能核实"的依据） |
| `reward_ids` | 核实后给的物品（**必须已存在**） |
| `duration` | 存活回合数（过期即"已失效"） |

**占位符只有两个**（`information_system` 替换，见调用点）：`[地点]`、`A` / `B`（房客姓名）。

## 3. 拆解 A：状态类信息（good_talk）

```python
# ① 模板：三段 = 待验证 / 已证实 / 已证伪
INFORMATION_TEMPLATES = {
    "good_talk": InformationTemplate(
        "good_talk", "投缘的交谈", "state",
        "A与B的日常，相当投缘。",
        "A 与 B 回合末各回复 2 理智。",
        "A 与 B 各回复 10 理智。",
        "无。",
    ),
}

# ② 结算：按 info.status 决定做什么（targets 是 A/B 的实例）
def _resolve_good_talk(engine, info, targets):
    if info.status == "confirmed":
        for target in targets:
            engine._restore_sanity(target, 10, info.title)

# ③ 挂上去（同文件；DLC 可用 register_state_effect）
INFORMATION_STATE_EFFECTS = {"good_talk": {"resolve": _resolve_good_talk, "pending": _pending_good_talk}}
# 等价写法：register_state_effect("good_talk", _resolve_good_talk, _pending_good_talk)
```

- `pending` = 待验证期间的每回合效果（`odd_smile` 的 `pending` 就是"A 回合末额外消耗 2 理智"）；
  `resolve` = 证实/证伪那一刻的结算，函数里用 `info.status` 分支。
- 三段文案里的房客用 `A`/`B` 占位，**别写死角色名**。

## 4. 拆解 B：地点修正类（courier_absent）

```python
INFORMATION_TEMPLATES = {
    "courier_absent": InformationTemplate(
        "courier_absent", "驿站老板旷工事件", "location_modifier",
        "县快递驿站无人看管。", location_id="courier_station",
    ),
}
LOCATION_INFORMATION_MODIFIERS = {
    "courier_absent": {"tag:fragile": 4.0, "quality:high": 2.0, "uses": 5},
}
```

- 键的写法：`tag:<tag>` 提高该 tag 物品的掉落权重；`quality:<段位>` 提高品质权重；
  `uses` 生效次数；`turns` 持续回合。

## 5. 全局事件

全局事件是**通用键 + 数值/布尔**的机制开关，需显式注册（**没有目录约定**）：

```python
from weiren_game.global_event import GlobalEventDefinition, register_global_event

register_global_event(GlobalEventDefinition(
    id="my.event",            # 通用键命名：<域>.<作用>
    label="我的事件",
    icon="i-clock",           # 游戏内「全局事件」页的图标（缺省 i-clock）
    description="……",         # 点开看到的内容（玩家向说明）
    nodes=frozenset(),        # 需要回合初/末效果时声明节点 + hook
    hook=my_hook,             # 可选
))
```

- 读写用引擎既有入口（`_set_global_event(id, value, layers)` / `_global_event_active` /
  `_global_event_value` / `_consume_global_event`，见 `systems/marks_system.py`）；
  **持续回合约定**：下回合初兑现 ≥2 / 本回合内 1 / 长期 99 / 限时写具体数。
- "是否允许"这类判断用**闸门**（纯查询，不掷骰不写状态），见 `docs/ARCH.md`。
- DLC 可在 `__init__.register(ctx)` 或模块导入时注册。

**拆解 C：一个真实事件（`information.false_lock`）**

```python
# 定义（内容层，可只声明 id/label/出处；erebus.py 就是批量注册命运牌事件）
register_global_event(GlobalEventDefinition(
    id="information.false_lock", label="太阳牌·假信息锁定",
    source_id="ability:draw_fate@erebus",
))

# 读取（事件本身不做判定，读它的地方决定效果）
truth_chance = .45 if self.state.world.global_events.active("information.false_lock") else .70

# 数值型事件示例：倍率默认 1.0，读出来直接乘
value *= max(0.0, self._global_event_value("item.fragile.multiplier", 1.0))

# 写入（内容在结算点设置它）
engine._set_global_event("my.event", 1.0, 99)      # (id, 数值, 持续回合)
```

- 事件是**跨内容的通用开关**：命名用 `<域>.<作用>`，别塞具体角色名。
- 需要回合级效果时给 `nodes=frozenset({Node.…})` + `hook`（节点见 `weiren_game/lifecycle.py`）。

## 6. 需求描述清单（把这段给 AI / 作者）

1. 信息名 + `id` + **类型**（现有 kind，或新 kind + 中文名）
2. 正文三段（待验证 / 已证实 / 已证伪）**逐段**给出，或说明「无」
3. 触发来源与频率（搜索返程 / 来访 / 伪人技能 / 每回合…）；**不要擅自改频率**
4. 是否指向某房客（`A`/`B`）或某地点（`[地点]` / `location_id`）
5. 持续时间（回合）；奖励物品 id（必须已存在）
6. 状态类信息的实际结算：确认/证伪时对谁做什么
7. 事件键名 + 作用（数值修正 / 布尔开关）+ 持续回合 + 在哪个节点生效
8. 约束：是否触碰平衡（数值单列、待评审）；是否影响按种子的随机序列

## 7. 验证

```
python tools/validate_content.py     # 地点/奖励引用必须已存在
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_separation.py
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
```

- **坑**：信息条数过多会淹没玩家（信息面板有"隐藏已失效"）；`duration` 决定过期回合；
  三段文案里出现的房客用 `A`/`B` 占位，**别写死角色名**（那是内容耦合、也会被审计拦下）。

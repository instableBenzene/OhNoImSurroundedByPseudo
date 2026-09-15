---
name: weiren-new-item
description: Use when adding items/物资 to OhNoImSurroundedByPseudo — "加物品 / 新增物资 / 做一个道具 / 新 tag / 物资描述 / item". Covers the item file skeleton, I(...) fields, tags and Chinese labels, on_use effects, item hooks, codex text, art, and verification.
---

# 新增一件物资

先读 `.opencode/skills/weiren-dev/SKILL.md`（两条分离、声明式规格）与 `docs/ADD_CONTENT.md`。
**给人读的完整样例**：`docs/COOKBOOK.md` §1（消耗品 + 附着状态）。

## 1. 放哪

- base：`weiren_game/data/items/<文件>.py`（文件名随意）；**新分类 = 新文件**。
- DLC：`dlc/<包>/items/<文件>.py`。两者都靠自动发现，**无需登记**。
- 文件暴露 `CATEGORY`（分类键）与 `ITEMS = {item_id: I(...)}`；可选 `ITEM_HOOKS`、`ITEM_EFFECTS`。

```python
from ..types import I          # DLC 里用 from weiren_game.data.types import I

CATEGORY = "food"
ITEMS = {
    "my_item": I("my_item", "我的物品", CATEGORY, 2,
                 "食用恢复 8 点生命。", ("food", "consumable"),
                 consumable=True, stack_size=16),
}
```

字段以 `ItemDefinition`（`weiren_game/types.py`）为准，常用：
`consumable` / `stack_size` / `max_durability` / `use_cost` / `fragile_chance` /
`medical_target` / `medical_max_intensity` / `reduce_intensity` / `reduce_layers` /
`on_use` / `searchable` / `source_note`。**别在文档里抄字段表**，改字段请对着 `types.py`。

## 2. 机制怎么挂

| 要的效果 | 挂法 |
| --- | --- |
| 通用使用效果（治疗/回理智等） | 走 `medical_*` / `consumable` 等**既有字段**，让 `item_system` 通用结算 |
| 指名物的特殊效果 | 物品上 `on_use="my_effect"`，本文件里 `ITEM_EFFECTS = {"my_effect": fn}`（签名看 `item_system` 调用点） |
| 生命周期（回合初/末背包实例、食用后…） | `ITEM_HOOKS = {item_id: {"<节点>": {名称: fn}}}`；**节点名由消费方定义**，用 `rg "ITEM_HOOKS" weiren_game` 找（如 `systems/round_effects.py` 读实例节点、`data/tags/food.py` 读 `after_food`） |
| 按 tag 的通用行为 | `data/tags/<tag>.py`（`TAG_BEHAVIORS`）＋ `data/tags/<tag>.json` 条目合并 |

数值/概率一律走通道 + 修饰器（`engine._apply_modifiers` / `_apply_chance`），见 `docs/ARCH.md`；
概率 5%~95%，必定用 `.certain(0/1)`。

## 3. 文案与美术（都在内容层）

- 中文名/tag 中文名/分类中文名：`data/labels.py` 的 `ITEM_TAG_LABELS` / `ITEM_CATEGORY_LABELS`
  （DLC 用 `register_item_tag_label` / `register_item_category_label` / `register_item_tag_icon`，
  或在 `__init__.register(ctx)` 里调用）。
- 图鉴全文：`data/items/codex_text.py`；风味：`data/items/flavor.py`。
- 贴图：`assets/art/` + `manifest.json`（有图即覆盖内置图标，**不改代码**）。

## 4. 需求描述清单（把这段给 AI / 作者）

1. 中文名 + `id`（ascii，全局唯一）
2. 分类：用现有 7 类之一，还是新分类（新分类要给**中文名**）
3. 品质 `0~5`（可写「照某某物品」）
4. 一句话用途
5. 机制：可消耗？耐久？堆叠数量？使用代价？对谁生效？数值多少？
6. tag：复用哪些 / 是否新 tag（新 tag 给中文名与图标）
7. 文案：图鉴描述要不要按设计稿原文；是否只要一句风味
8. 约束：是否**可被搜索**（会改掉落池）、是否触碰平衡数值（单列、待评审）

## 5. 字段速查（先想清楚这五个）

| 字段 | 什么时候用 | 注意 |
| --- | --- | --- |
| `quality` `0~5` | 总有 | 品质影响搜索权重（见 `QUALITY_WEIGHTS`），**不是越大越好**；中文名见 `data/__init__.py::QUALITY_NAMES` |
| `consumable=True` + `stack_size=N` | 用完就没的消耗品 | 与"耐久品"二选一 |
| `max_durability=N` + `use_cost=c` | 用 N/c 次才坏的道具 | 与"堆叠消耗品"二选一 |
| `fragile_chance` | 可能损坏 | 判定走通道：`engine._fragile_chance(base, tenant)` + `engine._rng(EVENT_IDS["item.fragile"], salt)` |
| `medical_target` / `medical_max_intensity` / `reduce_intensity` / `reduce_layers` | 治疗/镇痛类 | 走**通用使用逻辑**，不需要写效果函数 |
| `on_use="key"` | 需要特殊使用逻辑 | 解析到本文件 `ITEM_EFFECTS = {"key": fn}`，`fn(engine, tenant, item)` |
| `searchable=False` | 不该出现在搜索池 | 默认 True |

概率/数值一律走通道与收敛（`engine._apply_chance` / `_apply_modifiers`）；**必定** 用 0/1。
生命周期节点 / `source`·`path` / 闸门取舍：见 `docs/ARCH.md` §2/§4/§5，
或以 `.opencode/skills/weiren-new-character/SKILL.md` §5 的三套速查为准。

## 6. 拆解：麦当当（使用效果 + 回合初状态 + 易损/食用后触发）

原文：`weiren_game/data/items/food.py`（物品 + 效果 + 状态 + hook 都在这一个文件里）。

| 需求清单里的项 | 落在哪里 |
| --- | --- |
| 名称 / 分类 / 品质 / 标签 | `I("mcdangdang", "麦当当", "food", 4, "…", ("food","durability_consumable"))` |
| "能用 5 次"，每次消耗 1 | `max_durability=5, use_cost=1`（**耐久品**，不是 `consumable`） |
| "回复 20 生命 / 5 理智" | `_effect_mcdangdang(engine, tenant, item)` 里 `engine._restore_health/_restore_sanity` |
| "之后 3 回合每回合开始 +3 理智" | ① `tenant.set_status("mcdangdang_aftertaste", intensity=1, layers=3)`；② 状态**自带节点 hook**：`register_status_definition(StatusDefinition(..., source_id="item:mcdangdang", nodes=frozenset({"turn_start.status_effects"}), hook=mcdangdang_aftertaste))` |
| 使用入口 | `on_use="mcdangdang"` + 同文件 `ITEM_EFFECTS = {"mcdangdang": _effect_mcdangdang}` |
| 大蒜"食用时全屋调味品强化 / 10% 易损" | `fragile_chance=.10` + `ITEM_HOOKS = {"garlic": {"after_food": {"蒜泥味": _garlic_seasoning}}}`；消费方是 `data/tags/food.py::after_food`（遍历背包里的 `seasoning`） |

```python
ITEMS = {
    "my_item": I("my_item", "我的物品", CATEGORY, 2, "回复 8 生命。",
                 ("food", "consumable"), consumable=True, stack_size=16, on_use="my_item"),
}


def _effect_my_item(engine, tenant, item):
    engine._restore_health(tenant, 8, item.name)
    tenant.set_status("my_aftertaste", intensity=1, layers=3)   # 需要后续回合效果时就挂状态


ITEM_EFFECTS = {"my_item": _effect_my_item}
```

- 状态定义可以写在物品文件里（内容自包含）；**同一个状态 id 只登记一次**（重复登记是覆盖）。
- `ITEM_HOOKS` 的节点名由**消费方**决定：`data/tags/*.py`（如 `after_food`）或
  `systems/round_effects.py`（背包实例节点）；用 `rg "ITEM_HOOKS" weiren_game` 确认。

## 7. 验证

```
python tools/validate_content.py     # 品质范围 / tag 非空 / 引用完整
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_separation.py
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>
```

- **坑**：新增可搜索物品会改变按种子的掉落池（`loot.item` / `loot.quality` 事件）→
  可能需更新依赖固定种子的测试/素材；先跑单测确认。
- 完成标准：`validate_content` 与单测全绿，运行 `python game_ui.py` 能在开局补给/搜索/图鉴里看到它。

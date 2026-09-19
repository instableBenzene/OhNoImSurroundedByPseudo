---
name: weiren-new-character
description: Use when adding a new tenant/character to the OhNoImSurroundedByPseudo game — "加角色 / 新增房客 / 做一个角色 / new character". Covers scaffolding with tools/new_character.py, filling persona/tags/abilities, optional content registries, avatar/icon, and verification.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# 新增一名房客

先读 `AGENTS.md` 与 `.opencode/skills/weiren-dev/SKILL.md`（两条分离、声明式规格）。
**给人读的完整样例**：`docs/COOKBOOK.md` §2（主动技能）/ §3（概率被动）。

## 1. 生成骨架（首选）
```
python tools/new_character.py <ascii_id> <中文名> [--carry N] [--primary KEY] [--secondary KEY]
# 例：python tools/new_character.py sunset 斜阳 --carry 4 --primary suspicious --secondary loner
```
- 自动分配**唯一 `source_id`** 与 `AVATAR`；写入 `weiren_game/data/characters/<id>.py`。
- **同时把文本写进 `weiren_game/data/lang.py`**：`character.<id>.name|description|tag.N`、
  `ability.<id>_skill.name|description`、`data.characters.<id>.use_skill.1`。
  生成的模块里已经是 `TEXT["…"]`，你只需去 lang 表把 TODO 文案填掉。
- **无需登记**：`data/_discovery.py` 会自动发现该文件。
- 性格键以 `PERSONALITY_LABELS` / `PERSONALITIES` 为准（**勿在文档里另存一份**，避免漂移）。

## 2. 填写内容
- **文案一律先写进 lang 表，再在定义里按 key 取**（`TEXT["character.<id>.name"]` 等）：
  键名用既有 id 拼，加文本**只是加一条**、没有注册动作；漏 key 会当场 `KeyError`。
  约定与数据键禁区见 `.opencode/skills/weiren-dev/SKILL.md` §2.1。
- `CharacterDefinition(tenant_id, source_id, TEXT[...], TEXT[...], primary, secondary, carry, (TEXT[...],), ...)`：补人设、标签。
- 技能用 `A(id, TEXT[...], TEXT[...], target=..., prompt=..., options=..., amount_label=..., amount_mark=..., chips=..., nested_option=..., branches=...)`：
  - `target` 取值以 `AbilityDefinition.target`（`weiren_game/types.py`）为准，前端/CLI 据此弹选择。
  - 限定条件写进 `chips`（如 `(TEXT["ability.<id>.chip.0"], …)`），**不要**在描述里重复。
  - 每个主动技能都要在 `ACTIVE_DISPATCH` 里有处理函数，签名用 `def handler(engine, actor, **kwargs)`。
- 需要玩家**选目标**时，内容自描述候选：`TARGET_OPTIONS = {ability_id: lambda engine, actor: [{"value","label","desc"}...]}`。
- 图鉴补充（可选）：`CODEX_EXTRA()`；头像：`AVATAR = "i-avN"`。
- 角色专属的状态/事件/搜索修正/钩子都写在**本文件内**（自动被发现），不要改核心。

## 3. 验证
```
python tools/validate_content.py          # 编号唯一 / 头像 / 性格 / 主动技能派发 / 引用完整
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_separation.py
```
- 若角色 `available=True`，会进入访客池、**改变按种子的随机序列**：可能需同步更新依赖固定种子的测试/素材；先在 `bash` 里跑单测确认。
- 前端无需改动：状态 JSON 会自动带上新角色（头像/技能/标签全走通用机制）。

## 4. 需求描述清单（把这段给 AI / 作者）

1. 中文名 + `id`（ascii）+ 编号（脚手架会自动分配，别与现有 `source_id` 冲突）
2. 一句话人设 + 语气参考（世界观：冷、准、生活流里透诡异）
3. 主性格 / 副性格（现有性格键）与携带量
4. 标签（展示用）
5. 技能表：每个技能给「名称 + 主动/被动 + 触发时机 + 目标 + 效果 + 数值/概率 +
   是否每回合限次（`per_turn`）+ 冷却/解锁条件（写进 `chips`）」
6. 是否需要玩家选择（目标/信息/资源/数量/提交物资）；提示语与选项名（属内容层）。
   `options` 每项 `(value, label)` 可**再加两项** `(value, label, icon, desc)`：`icon` 是贴图零件 id、
   `desc` 是一句说明 —— 选择页会渲染成带图标的卡片，不写就回退中性图标
7. 是否需要**专属印记**（计数）：获得条件、上下限、需要在详情页画进度条时给出换档阈值
   （`MARKS` + `MarkDefinition(..., bar_tiers=...)`；档位可带标注/刻度配色做提示，
   无上限就写阈值当参照）
8. 头像右侧那片**小面板**放什么（`DETAIL_SLOT(engine, tenant)` 返回 `mark`/`bar`/`text`/`tags`/`glyph` 条目；
   `glyph` 是装饰图形（可 `spin="random"/"cw"` 旋转、`hint` 悬停文案），适合彩蛋；
   不声明就默认列印记）；若某个状态不该出现在状态栏（如人设），给它 `chip_hidden=True`
9. 头像（默认按 id 哈希派生的「形状 × 特征」，可用 `AVATAR`/`AVATAR_FEATURE` 指定；
   点缀色/点缀环已废弃）；要**整张头像**就给 `data/avatars/characters/<角色id>.svg`
   （或包内 `avatars/characters/`）——立绘已进内容层，不再往 `assets/art/` 放
10. 约束：`available=True` 会进入访客池、**改变按种子的随机序列**；是否触碰平衡

> 以上每一项文字（名称/描述/chip/提示语/选项名）都会落进 `weiren_game/data/lang.py`；
> **给需求时只要把文字写清楚**，落表与取用由实现方按 §2 的键名约定完成。

## 5. 字段速查（写技能/被动最常用的三套）

### 5.1 生命周期：什么时候生效

- 节点常量集中在 `weiren_game/lifecycle.py::Node`；**回合主流程的真实顺序**是
  `START_TURN_PHASES` / `END_TURN_PHASES`（`(节点, 引擎方法)` 列表）——"钩子会在哪个点被调用"以它为准。
- 挂进内容模块的方式：
  | 挂法 | 何时调用 | 签名 |
  | --- | --- | --- |
  | `TURN_START = fn` | 回合初，**每名房客各一次** | `fn(engine, tenant)` |
  | `HOOKS = {"<节点>": fn \| (fn,...)}` | 该节点（并入通用 `NODE_HOOKS`） | 按节点约定 |
  | `VALUE_HOOKS = {"<节点>": fn}` | 数值结算点（`value_system` 查表） | 按节点约定 |
  | `NODE_HOOKS = {"<节点>": fn}` | 能力/事件级节点（伪人流程、`ability_launch` 等） | 按节点约定 |
  | 状态自带 | `StatusDefinition(nodes=frozenset({"turn_end.status_effects"}), hook=fn)` | `fn(engine, tenant)` |
- 常用节点关键词：回合初 `turn_start.*`、回合末 `turn_end.*`、门口 `door_event` / `door.accept`、
  技能 `ability.used` / `ability.failed`、印记 `mark.gained` / `mark.reached`、死亡 `tenant.death`。
- **别在文档里背节点清单**：要哪个就打开 `lifecycle.py` 或 `rg '"turn_end\.' weiren_game`。

### 5.2 `path` / `source`：对谁生效、由谁触发

- 词表与规则：`docs/ARCH.md` §4 令牌词表（功能词 / 对象 / 出身词 / 物品 tag）。**令牌一律英文**。
- `path` = 这个修饰器**响应哪个功能**（`search` / `damage` / `turn_end_consume`…）；
  `source` = **调用点由什么构成**（`("bond","loner")`、`("ability","zero329","sharp_instinct")`）；
  两者命中取**交**。派生项靠 `source` 区分，**不新增通道**。
- 写法：`spec("<通道>").path(...).source(...)`。
- 令牌**不是文案**：要显示就走 `lang.source_label(令牌)`，别把令牌插进句子。

### 5.3 通道 / 概率 / 闸门：三选一，别用错

| 想干的事 | 用哪个 | 入口 |
| --- | --- | --- |
| 数值加减 / 乘算 / 取上下限 | **通道 + 修饰器** | `engine._apply_modifiers("<通道>", base, source, context)`；`spec(...).flat/.percent/.mul/.final/.max/.min` |
| 掷随机 | **概率收敛** | `calculate_modified_amount(base, collect_modifiers("chance", source, ctx))` → 自调（惩罚/保底）→ `resolve(...)`；或内容自带 `engine._rng(EVENT_IDS["..."], salt)`。非必定收敛 5%~95%，**必定**用 0/1（`spec("chance").certain(1.0)`） |
| "能不能 / 是否免疫 / 目标是否合法" | **闸门（纯查询）** | `engine._eval_gate("<闸门类型>", source, context)`；贡献项 `gate(...).path(...).source(...).any()/.veto()`；**不掷骰、不写状态** |

- 闸门是纯查询，掷骰与消耗只发生在**结算点**；闸门目录见 `docs/ARCH.md` §5。

## 6. 拆解：呼朋引伴（照这个结构写主动技能）

需求 → 代码的对应关系（原文在 `weiren_game/data/characters/dragon.py`）：

| 需求清单里的项 | 落在哪里 |
| --- | --- |
| 名称 + 描述 + 限定 chip | 先落 lang（`ability.call_friends.name|description|chip.0|chip.1`），再用 `A("call_friends", TEXT["ability.call_friends.name"], TEXT["ability.call_friends.description"], chips=(TEXT["ability.call_friends.chip.0"], TEXT["ability.call_friends.chip.1"]))`——**chip 只写一遍**，描述里不重复 |
| "在屋存活 3 回合才可用" | `requirements_call_friends(engine, actor, *, bypass)` → 不满足**返回给玩家看的文案**（`TEXT["ability.call_friends.requirement.0"]`；`bypass` 让内部调用跳过） |
| "消耗 25 理智" | `costs_call_friends(engine, actor, *, option)` → `[T("sanity", 25)]`，交给公共消耗流程；**不要在效果里手扣理智** |
| "立即 +2 名访客" | `use_call_friends`：`engine._queue_human_visitor("…", force_supply=True)` ×2 |
| "冷却 4 回合" | `engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 4)` |
| 前端要能点到 | `ACTIVE_DISPATCH = {"call_friends": lambda engine, actor, *, bypass=False, **kwargs: …}`（**必须带 `**kwargs`**） |
| 被动"理智>85 时 15% 多一位访客" | `party_focus`：`engine._rng(EVENT_IDS["dragon.visitor"], tenant.id).random() < .15` → `engine._skill_outcome(tenant, "...", success)` → `TURN_START = turn_start` 挂回合初 |

```python
# 骨架（照抄结构，换内容）
def requirements_my_active(engine, actor, *, bypass):
    if bypass or actor.home_turns >= 3:
        return None
    return TEXT["ability.my_active.requirement.0"]        # 文案在 lang 表


def costs_my_active(engine, actor, *, option):
    return [T("sanity", 25)]                      # T(资源, 数量)


def use_my_active(engine, actor, ability_id, *, bypass=False):
    engine._queue_human_visitor("supply_run", force_supply=True)
    engine._set_ability_cooldown(actor, ability_id, engine.state.flow.turn + 4)


ACTIVE_DISPATCH = {
    "my_active": lambda engine, actor, *, bypass=False, **kwargs:
    use_my_active(engine, actor, "my_active", bypass=bypass),
}
```

- 需要玩家选目标：`target` 取值见 `AbilityDefinition.target`（`types.py`）；候选用
  `TARGET_OPTIONS = {ability_id: fn(engine, actor) -> [{"value","label","desc"}]}` **由内容自描述**。
- 文案里的角色名/机制名都是内容：**写进 lang 表**（`lang.py` 或 DLC 的 `dlc/<包>/lang.py`），
  本文件只留 key；**数值与判定不要写进系统层**。

## 7. 完成标准

> 这个角色要**自己的界面或自己的状态**（专属面板 / 可拖拽浮窗 / 进存档的专属数据）？
> 那不是一个角色文件能兜住的：先读 `.opencode/skills/weiren-custom-ui`（怎么做），
> 验收再走 `.opencode/skills/weiren-ui-probe`。
- `validate_content` 与单测全绿；运行 `python game_ui.py` 能在候选/访客中看到该角色。

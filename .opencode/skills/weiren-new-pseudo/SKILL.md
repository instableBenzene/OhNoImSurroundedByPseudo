---
name: weiren-new-pseudo
description: Use when adding a pseudo/伪人 (impostor scenario) to OhNoImSurroundedByPseudo — "加伪人 / 新伪人 / 做一个伪人 / pseudo / 潜伏机制". Covers the pseudo module skeleton, PseudoDefinition fields, HANDLERS vocabulary, State/marks, human-form exclusion, codex skills, and verification.
---

# 新增一类伪人

先读 `.opencode/skills/weiren-dev/SKILL.md` 与 `docs/ADD_CONTENT.md`；机制细则见 `docs/GUIDE.md`。
**给人读的完整样例**：`docs/COOKBOOK.md` §4（最小可玩伪人 + 展示三件套）。

## 1. 放哪

- base：`weiren_game/data/pseudos/pseudo_<id>.py`；DLC：`dlc/<包>/pseudos/<id>.py`。
- 暴露 `DEFINITION`（+ 可选 `HANDLERS` / `State` / `NODE_HOOKS` / `CODEX_SKILLS` / `DEFAULT_PSEUDO`）。

```python
from weiren_game.data.types import PseudoDefinition

DEFINITION = PseudoDefinition(
    "pseudo_my", "我的伪人", "my_human",       # id / 名称 / **人类原型角色 id（必须已存在）**
    "一句话设定。", "突破条件文案。", "解放条件文案。",
    mark_field="my_marks", mark_label="印记-我的伪人",
)
```

`PseudoDefinition` 字段以 `weiren_game/types.py` 为准（还有 `enters_house`、
`mark_externally_locked`）。人类原型会被**自动排除出访客池**，也不能列入禁用角色（DLC 同样生效）。

## 2. 处理器（HANDLERS）

核心通过 `SCENARIO_HANDLERS[scenario_id][名]` 按名查表调用。**名与签名以调用点为准**，别照抄文档：

```
python tools/dump_effects.py        # 打印「伪人场景 HANDLERS」目录
rg "SCENARIO_HANDLERS.get" weiren_game        # 找到每个名字的调用点与签名
```

常见挂载点（**仅为速览，以调用点为准**）：`visit`、`on_first_reveal`、`settle_end`、
`attack_searcher`、`encounter_chance`、`progress_text`、`card_info`、`observed_skills`、
`tenant_death`、`expel_infiltrator`、`emotion_end_extra`。
场景状态用模块内 dataclass（挂在 `state.pseudo_state.<字段>`），印记字段由 `mark_field` 指定。

概率同样走通道/修饰器；"能否被识破/是否在场"这类判断优先用**闸门**（纯查询，见 `docs/ARCH.md`）。

## 3. 文案与图鉴

- 图鉴「伪人」页技能：在模块里声明 `CODEX_SKILLS = ((名称, 文案), ...)`（优先于内置静态表）。
- 突破 / 解放文案来自 `DEFINITION`；进度文案来自 `progress_text`；卡片信息来自 `card_info`。
- 若有"默认伪人"语义，声明 `DEFAULT_PSEUDO = True`。

## 4. 字段速查（定义 / 状态 / 印记）

| 字段 | 用途 | 注意 |
| --- | --- | --- |
| `DEFINITION.name` / `.description` | 名称与设定 | 图鉴/卡片直接显示 |
| `.human_character_id` | **人类原型** | 必须已存在；会被自动排除出访客池、不能列入禁用角色 |
| `.enters_house` | 是否进屋 | 替身/绑架类流程用 |
| `.breakthrough` / `.liberation` | 突破 / 解放条件文案 | 图鉴展示，写成可判定的表述 |
| `mark_field` | 场景状态里充当"印记"的字段名（`fear_marks` / `exposure` / `whisper_marks`） | 外界改写走 `engine._set_pseudo_marks(target)` |
| `mark_label` / `mark_externally_locked` | 印记对外称呼 / 是否禁止外界改写 | 薯条 `exposure` 就是 locked |
| `State = MyState`（dataclass） | 场景状态（**必需**，缺了装载即报错） | `state.pseudo_state.<字段>` 可直读直写；通用字段 `revealed` / `visit_count` / `liberated` 由核心维护 |
| `DEFAULT_PSEUDO = True` | 不指定时默认用这一位 | 全局只应有一个 |
| `NODE_HOOKS = {"<节点>": fn}` | 通用节点钩子 | 节点名见 `weiren_game/lifecycle.py::Node` |
| `CARD_SLOT(engine)` | 门口那张**袖珍卡的小面板**：返回 `mark`/`bar`/`text`/`tags` 条目（与房客小面板同一套形状，伪人用 `bar` 画自己的进度与档位刻度） | 只在下发时用；卡里已有的印记条不受影响 |

## 5. HANDLERS 对照表（名 → 签名 → 何时被调用）

> **以 `python tools/dump_effects.py` 的「伪人场景 HANDLERS」与 `rg "SCENARIO_HANDLERS.get" weiren_game` 为准**；
> 下表是常用项的速览（签名摘自现有实现）。

| 名 | 签名 | 何时 |
| --- | --- | --- |
| `visit` | `(engine)` | 伪人来访结算 |
| `on_first_reveal` | `(engine)` | 首次暴露（此后走正常流程） |
| `start_passive` | `(engine)` | 开局被动 |
| `attack_searcher` | `(engine, mission, tenant)` | 回合末袭击在外搜索者 |
| `encounter_chance` | `(engine, mission, tenant) -> float` | 搜索遭遇概率（先 `resolve` 保底，再走 `chance` 通道） |
| `tenant_death` | `(engine)` | 有无死亡/被驱逐 |
| `settle_end` | `(engine)` | 回合末额外结算 |
| `on_emotion_increase` | `(engine, tenant, key)` | 某情绪被强化 |
| `emotion_end_extra` | `(engine, tenant, condition, key)` | 回合末情绪恶化/延长时追加 |
| `expel_infiltrator` | `(engine, source: str, *, self_infernal=False)` | 替身被识破/驱逐 |
| `observed_skills` / `progress_text` / `card_info` | 见下 §6 | 展示三件套 |

## 6. 拆解：展示三件套（照抄这个写法）

原文：`weiren_game/data/pseudos/pseudo_benzene.py`。

```python
def observed_skills(engine):
    # 对外用展示名；内部 id 留给信息文本/核验用
    return (("curse", "希波克拉底诅咒"), ("precision", "精湛刀艺"))


def progress_text(engine):
    ps = engine.state.pseudo_state          # 场景状态（State dataclass）
    return f"恐惧{ps.fear_marks}，无休克{ps.safe_no_shock_streak}/5，无死亡{ps.safe_no_death_streak}/7"


def card_info(engine):
    ps = engine.state.pseudo_state
    threshold = curse_threshold_value(engine)
    return {
        "liberation": "…进度文案…",
        "breakthrough": "…突破文案…",
        "mark_need": int(threshold),         # 印记还差多少
        "skills": [
            {"name": "希波克拉底诅咒", "text": "…效果…",
             "mark": {"label": "恐惧印记", "current": int(ps.fear_marks), "need": int(threshold)}},
        ],
    }
```

- 概率走 `resolve` + `chance` 通道（`encounter_chance` 就是范例）；"能不能/是否免疫"用**闸门**（纯查询）。
- 状态/全局事件/搜索修正都可以在伪人自己文件里注册（模块导入副作用）。
- 生命周期节点 / `source`·`path` / 闸门与通道的取舍：见 `docs/ARCH.md` §2/§4/§5，
  或以 `.opencode/skills/weiren-new-character/SKILL.md` §5 的三套速查为准。

## 7. 需求描述清单（把这段给 AI / 作者）

1. 名称 + `id` + **人类原型**（用哪位现有房客，或先加角色）
2. 伪装方式：进不进屋？替身 / 绑架 / 附身？在屋身份如何表现
3. 识破与证据：靠什么信息被识破（指认需几条）、识破后发生什么
4. 技能表：每个技能给「名称 + 触发时机 + 效果 + 数值/概率 + 是否每回合限次」
5. 推进条件：突破（强化的条件）与解放（胜利/击败它的条件），**写出可判定的表述**
6. 印记：对外称呼、上限、是否禁止被外界改写
7. 图鉴技能文案（`CODEX_SKILLS`）
8. 约束：是否默认伪人、是否改变访客池/随机序列、是否触碰平衡

## 8. 验证

```
python tools/validate_content.py        # 人类原型存在；建议提供 observed_skills / progress_text
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_separation.py
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>   # 每个伪人都要有可玩性
```

- 完成标准：能用该伪人开一局并走完一轮；图鉴「伪人」页显示正确；单测/审计/冒烟全绿。

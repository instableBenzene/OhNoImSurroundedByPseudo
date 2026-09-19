---
name: weiren-new-dlc
description: Use when packaging content as a DLC pack for OhNoImSurroundedByPseudo — "写 DLC / 内容包 / 打包角色 / dlc pack". Covers directory layout, dlc.json, content dirs, codex contributions, hot install/uninstall, and verification.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# 编写一个 DLC 内容包

先读 `docs/ADD_CONTENT.md`（DLC 一节）、`dlc/README.md`、`dlc/_template/`。

## 目录（以 `dlc/_template/` 为准，下面仅为速览）
```
dlc/<dlc_name>/
  dlc.json                # {"name","version","min_game_version": "2.1.0"}
  lang.py                 # **本包全部文案**（TEXT = {...}），模块里 TEXT = pack_text_from_file(__file__)
  __init__.py             # 可选：def register(ctx): ...
  characters/<id>.py      # 暴露 CHARACTER（或 CHARACTERS）
  personalities/<key>.py  # 一类性格：LABEL + TIERS/TIER_AT/HOOKS/BOND_*
  items/<name>.py         # 暴露 CATEGORY 与 ITEMS；可选 ITEM_HOOKS / ITEM_EFFECTS
  tags/<tag>.json         # 文件名即 tag；内容为 item_id 或物品名列表
  tags/<tag>.py           # 文件名即 tag 的行为模块（进 TAG_BEHAVIORS）
  statuses/<name>.py      # 暴露 STATUSES / EMOTIONS
  resourcepack/<name>.py  # 暴露 THEME（CSS 变量/字体/追加 css）与 SYMBOLS（贴图零件）
  avatars/<section>/<id>.svg  # 头像零件/整张头像（shapes/features/characters），按位次覆盖 base
  item/item/<id>.svg      # 自带物品的图标；item/tag/<tag>.svg 按标签兜底
  icon/<section>/<id>.<ext>  # 地点/信息/伪人图标（locations/information/pseudos）
  maps/<id>/map.py        # 自带一张地图（显式地点名单 + 屋子名；或用 ctx.register_map_location）
  locations/<name>.py     # 暴露 LOCATIONS
                          #   可选 MAP_GROUPS：新分组纳入开局抽取
  information/<name>.py   # 暴露 INFORMATION_TEMPLATES
  pseudos/<id>.py         # 暴露 DEFINITION / State / HANDLERS
  codex/*.py              # 可选图鉴分节：def register(ctx): ctx.register_section({...})
```

## 规则
- **零改核心**：DLC 只放内容；不得 import 具体内置内容，只用协议与注册表。
- **文案一律住本包的 `lang.py`**（一个包一个文件，不做回退链、不做多语言）：
  ```python
  # dlc/<包>/lang.py
  TEXT = {"item.my_item.name": "我的物品", "ability.my_skill.description": "……"}
  # dlc/<包>/items/my.py
  from weiren_game.data.lang import pack_text_from_file
  TEXT = pack_text_from_file(__file__)          # 按包目录取表
  ```
  键名沿用既有 id（`character.<id>.*` / `item.<id>.*` / `ability.<id>.*` / `pseudo.<id>.*`）；
  **加文本只是往本包 lang 加一条**，没有注册动作；取错 key 会 `KeyError`。
  DLC 文本随包装载/卸载（表本身不参与注册表快照，包没载就不会被读）。
- **DLC 伪人的图鉴技能**：本体图鉴「伪人」页的技能来自 `codex_pack.PSEUDO_SKILLS`。DLC 伪人优先在
  自己模块里声明 `CODEX_SKILLS = ((name, text), ...)`（图鉴页会自动回退读它）；也可在 `codex/register(ctx)`
  里直接改静态表——**这些表已纳入快照，卸载会回滚**。（突破/解放来自 `DEFINITION`，无需处理。）
- **限定 chip 由技能自声明**：`A(..., chips=(TEXT["ability.<id>.chip.0"],))`；**不要**指望内置的 chip 表（已删除）。
- **人类形态互斥**：`DEFINITION.human_character_id` 指向的角色会被自动排除出访客池，也不能被列入禁用角色。
- **新增性格/状态/情绪/tag 行为/地点分组**都是"放文件即生效"；**全局事件**要在 `register(ctx)` 或模块导入时显式注册。
- **新注册表**必须加进 `weiren_game/content.py` 的 `_BASE_CONTAINERS`，否则卸载后残留。
  效果内核的修饰器 / 闸门表（`register_modifier_provider` / `register_gate_provider`）**已在快照里**：
  装载、卸载都随包回滚，重复「应用」也不累积 —— **不需要**自己写去重或认领。
- 版本：`min_game_version` 高于当前 `GAME_VERSION` 会被拒。
- 热切换：界面 DLC 页"应用"会按包顺序重建注册表（`dlc.apply_pack_order`，见
  `tests/test_architecture.py::test_dlc_content_channels_and_rollback`）。
- **替换包（覆盖内置内容）**：启用清单**有序**（高→低，含 `base`，存 `CONFIG.pack_order`）。
  装载从最低优先级开始，轮到 `base` 时让内置内容赢过它下方的包；**用 ▲ 把包调到 `base` 之上**，
  同 id 的角色/物品/地点/信息/伪人/性格/状态就会覆盖内置。钩子序列只增不换；
  存档只记录包清单、不记录顺序。
- 存档记录 `meta.packs`，与当前启用包不一致会拒读。

## 验证

> 资料包里如果带**专属界面**（角色专属面板 / 可拖拽浮窗 / 进存档的专属状态），
> 先读 `.opencode/skills/weiren-custom-ui`；界面验收走 `.opencode/skills/weiren-ui-probe`。
```
python tools/validate_content.py
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_separation.py      # 系统/前端不得出现 DLC 内容名
# 也可复制 dlc/_template 起步
```
- 建议用 `python game_ui.py` 在 DLC 页安装/卸载一次，确认即时生效与回滚。

## 需求描述清单（把这段给 AI / 作者）

1. 包名（`dlc/<包名>/`，同时是 `dlc.json::name`）与一句话定位
2. **是扩展包还是替换包**：替换包要说明**覆盖哪些内置 id**（角色/物品/地点/信息/伪人…），
   并在界面把它调到 `base` 之上
3. 包含哪些类型的内容（各类型字段见对应的 `weiren-new-*` skill）
4. `min_game_version`（低于等于当前 `GAME_VERSION` 才可装载）
5. 跨内容引用关系（成组增删），以及是否触碰平衡（数值单列、待评审）

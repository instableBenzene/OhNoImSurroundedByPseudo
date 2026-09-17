# DLC 模板

复制 `_template` 目录并改名（`_` 开头的目录会被 `load_dlc()` 跳过）。
字段与规则的唯一来源是 `docs/ADD_CONTENT.md`；各子目录里放了最小可改的示例。

- `characters/<id>.py`：新房客（`CHARACTER` + 可选注册表）
- `personalities/<key>.py`：新性格/羁绊（`LABEL` + `TIERS` + `HOOKS`）
- `items/<名>.py`：`CATEGORY` + `ITEMS`
- `tags/<tag>.json`：tag 条目合并；`tags/<tag>.py`：tag 行为模块
- `statuses/<名>.py`：`STATUSES` / `EMOTIONS`
- `avatars/<section>/<id>.svg`：头像零件 / 整张头像（`shapes` / `features` / `characters`）
- `item/item/<物品id>.svg` / `item/tag/<tag>.svg`：自带物品的图标 / 按标签兜底
- `icon/<section>/<id>.<ext>`：地点 / 信息 / 伪人图标（`locations` / `information` / `pseudos`）
- `maps/<id>/map.py`：自带一张地图（`MAP = MapDefinition(...)`，地点是显式名单）
- `locations/<名>.py`：`LOCATIONS`（可选 `MAP_GROUPS`）
- `information/<名>.py`：`INFORMATION_TEMPLATES`
- `pseudos/<id>.py`：`DEFINITION` + `State` + `HANDLERS`
- `codex/*.py`：`register(ctx)` 追加图鉴分节
- `__init__.py`：可选 `register(ctx)`

装载：`from weiren_game.dlc import load_dlc; load_dlc()`

> 若这个包是**替换包**（要覆盖内置的同 id 角色/物品/地点…），把界面 DLC 页里的它
> 用 ▲ 调到 `base` 之上再「应用」；否则它只会与内置内容并存。

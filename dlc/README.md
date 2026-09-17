# DLC 内容目录

> **只记 DLC 特有规则**；内容能加哪些、字段怎么写，一律以
> `docs/ADD_CONTENT.md`「编写一个 DLC 内容包」为唯一来源（避免两处清单漂移）。

扩展内容放 `dlc/<dlc名>/`，启动时由 `weiren_game.dlc.load_dlc()` 自动注册；
界面「应用」走 `reload_dlc(names)` 热切换（回滚 base 再重装）。把内容直接加进
`weiren_game/data/` 同样有效——两种方式进的是同一套注册表。

## 目录格式总览

```text
dlc/<dlc_name>/
  dlc.json                    # 可选：{"name","version","min_game_version",...}
  __init__.py                 # 可选：def register(ctx): ...（ctx 即 ContentManager）
  characters/<id>.py          # 每文件一个（或多个）新房客
  personalities/<key>.py      # 每文件一类性格（LABEL 即中文名）
  items/any_name.py           # 每文件 CATEGORY + ITEMS（可选 ITEM_HOOKS / ITEM_EFFECTS）
  tags/<tag>.json             # 文件名即 tag，条目合并进物品
  tags/<tag>.py               # 文件名即 tag 的行为模块（进 TAG_BEHAVIORS）
  statuses/any_name.py        # STATUSES / EMOTIONS（状态与情绪定义）
  resourcepack/any_name.py    # THEME（CSS 变量/字体/追加 css）/ SYMBOLS（贴图零件）
  avatars/<section>/<id>.svg  # 头像零件/整张头像（shapes/features/characters，按位次覆盖 base）
  item/item/<id>.svg          # 自带物品的图标；item/tag/<tag>.svg 按标签兜底
  icon/<section>/<id>.<ext>   # 地点/信息/伪人图标（locations/information/pseudos）
  maps/<id>/map.py            # 自带一张地图（显式地点名单 + 屋子名）
  locations/any_name.py       # LOCATIONS；可选 MAP_GROUPS 把新分组纳入开局抽取
  information/any_name.py     # INFORMATION_TEMPLATES（可选 LOCATION_INFORMATION_MODIFIERS）
  pseudos/<id>.py             # DEFINITION / State / HANDLERS（可选 NODE_HOOKS）
  codex/*.py                  # register(ctx) / SECTIONS：追加图鉴分节与文案
```

## 只属于 DLC 的注意事项

- 文件夹名 `dlc_name` 只影响加载顺序与日志，不参与游戏内 ID。
- ID 冲突（物品 / 角色 / 地点 / 信息模板）在装载时**直接报错**，不静默覆盖；
  同名 tag 是**合并/覆盖**语义。
- 指令顺序：先 `register(ctx)`，再按目录装载，最后 `validate_catalogue()` 与登记包名。
- **卸载即回滚**：能回滚的注册表由 `weiren_game/content.py` 的 `_BASE_CONTAINERS` 决定；
  新增注册表必须加进那张表，否则卸载后残留、与后续 DLC 串味。
- **优先级 = 覆盖内置**：启用顺序（`game_config.json::pack_order`，高 → 低，含 `base`）决定
  同 id 内容由谁胜出。包放在 `base` **下方**时不影响内置内容；把它调到 `base` **上方**
  即可替换内置内容（例：一个"替换某位房客"的更新包）。界面在 DLC 页用 ▲▼ 调序。
- 起步：复制 `dlc/_template/`；可运行示例见 `dlc/likai_test/`。

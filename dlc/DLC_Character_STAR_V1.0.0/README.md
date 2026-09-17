# DLC_Character_STAR

一个"角色包"的完整示例：**新角色 + 自带物资 + 对应的伪人形态**。

```text
characters/STAR.py        # 房客 STAR（主动/被动、印记、详情页小面板、搜索修正）
items/sidearm.py          # 物资「流星信标」（角色能力要用到它）
item/item/star_sidearm.svg  # 上面那件物资自己的图标（内容层放文件即生效）
pseudos/pseudo_STAR.py    # 伪人形态
__init__.py               # register(ctx)：登记 tag 的中文名与内置图标兜底
```

## 怎么用

放进 `dlc/` 即可被识别；在启动器「设置 → 资料包」里把它 ▶ 启用，再点「应用」。
想让它**替换**内置的同 id 内容（而不是并存），用 ▲ 把它排到 `base` 上面。

## 注意

- 本包**不进存档的显示层**（头像/图标/材质）都可被别的资源包按位次覆盖。
- 目录名就是包名（会写进 `game_config.json` 的 `pack_order` 与存档的 `meta.packs`），
  改名后旧存档会因包清单不一致而拒读 —— 改名请连带处理存档。

*by. 比格小星*

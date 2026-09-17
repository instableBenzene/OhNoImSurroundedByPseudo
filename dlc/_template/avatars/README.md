# avatars/

头像零件 / 整张头像，**一件一个文件**（`.svg`）。目录名即分区：

```text
avatars/shapes/<id>.svg          # 基础形状（i-av1..12）
avatars/features/<id>.svg        # 专属特征（i-ft-*）
avatars/characters/<角色id>.svg  # 整张头像，直接替换该角色（人/伪人通用）
```

同 id 由**包优先级**决定谁赢（把本包用 ▲ 排到 `base` 之上即可替换内置）；
只改外观、**不进存档**，移除后不影响存档。角色也能在自己 `.py` 里声明
`AVATAR` / `AVATAR_FEATURE` / `AVATAR_COLORS`（点缀色/点缀环已废弃）。

详见 `resourcepacks/README.md`「人物（头像）」与 `docs/ADD_CONTENT.md`。

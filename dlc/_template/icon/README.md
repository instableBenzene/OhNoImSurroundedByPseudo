# icon/

地点 / 信息 / 伪人的图标，**一件一个文件**（`.svg` / `.png` / `.jpg` / `.jpeg` / `.webp`）。目录名即分区：

```text
icon/locations/<location_id>.svg     # 地点
icon/information/<template_id>.svg   # 信息模板
icon/pseudos/<pseudo_id>.svg         # 伪人
```

按 **id 命名**即可，不需要任何清单或登记。同 id 由**包优先级**决定谁赢
（把本包排到 `base` 之上即可替换内置图标）。这些是**彩色插画**，
不参与配色 token（和物品图标不同，换肤不会改它们）。

只改外观、**不进存档**；没图的 id 自动回退内置单线图标。

详见 `resourcepacks/README.md`「地点 / 信息 / 伪人图标 ——`icon/`」与 `docs/ADD_CONTENT.md`。

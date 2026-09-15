# 外置美术资源（assets/art）

**给多模态模型的接口说明：只在本目录内新增图片文件并更新 `manifest.json`，
不要修改 `weiren_game/` 下的任何代码。** 缺图时会自动回退到内置单线图标/程序化头像。

## 目录
```
assets/art/
  manifest.json          # 唯一需要改的清单文件
  characters/<id>.png    # 立绘（推荐 256×256 以上，正方形、透明背景）
  items/<id>.png         # 图标（推荐 64×64 以上）
  locations/<id>.svg     # 图标
  pseudos/<id>.png       # 头像
```

## manifest.json 格式
```json
{
  "characters": { "benzene": "characters/benzene.png" },
  "items":      { "smartphone": "items/smartphone.png" },
  "locations":  { "county_hospital": "locations/county_hospital.svg" },
  "pseudos":    { "pseudo_benzene": "pseudos/benzene.png" }
}
```
- 路径相对于本目录；支持 `.png` / `.svg`（浏览器可直接显示）。
- **id 就是内容 id**：角色用 `tenant_id`（如 `benzene`）、物品用 `item_id`（如 `smartphone`）、
  地点用 `location_id`、伪人用 `pseudo_id`（如 `pseudo_benzene`）。
- 未在清单中、或文件不存在的条目 → 自动回退内置图标，不会报错。

## 生效方式
- 服务端按 `manifest.json` 的修改时间热更新，**放入文件后刷新页面即可**（无需重启）。
- 图片通过 `/assets/art/<相对路径>` 提供（`weiren_game/web_ui.py` 已在启动时挂载）。

## 建议
- 立绘透明背景、方形；图标保持简洁、与暗绿+琥珀整体调性协调（见 `docs/STYLE.md`）。
- 不要把大体积位图直接塞进仓库源码；如需版本管理，可把原图放别处、只提交压缩后的成品。

## 当前覆盖（SVC 线描两色风，已铺满；共 131 个）
- **房客头像 24 个**（`characters/*.svg`，`viewBox 0 0 64 64`）：共用"肩 + 颈 + 头"底，按角色差异换
  发型（短发/长发/马尾/丸子/刺猬/凌乱/兜帽）、配件（眼镜/口罩/耳机/棒球帽/宽檐帽/花/王冠/眼罩/耳饰/
  天线/星星/围巾/创可贴/塔罗牌/购物袋/符纸/角/头带/天眼）与强调色；浅色描边 `#dde3d8` + 深色填充 `#1d2625`。
- **伪人头像 3 个**（`pseudos/*.svg`）：对应房客的"污染版"——红强调色 + 螺旋眼 + 错位线条/多出部件。
- **物资图标 57 个**（`items/*.svg`，`viewBox 0 0 32 32`）：按标签归类到 ~30 个模板（手术包/药箱/抢救车/
  注射器/安瓿/食物/汉堡/松饼/蒜/饮料/罐头/巧克力/饼干/糖/肉干/薯片/手电筒/指南针/撬棍/鞋/防刺服/头盔/
  冲锋衣/随身听/留声机/书/报纸/录像带/手机/玩偶/购物袋/燧发枪/弹药），浅色描边 `#d7ddd2`。
- **地点图标 25 个**（`locations/*.svg`）：按功能分组上色——医疗 `#68b998`、食物 `#e2a84d`、
  工具 `#9fb8c9`、混合 `#c4c9c4`。应用于图鉴（列表 19px / 详情 72px）与"指派搜索 · 选择地点"弹窗。
- **信息图标 22 个**（`information/*.svg`）：按信息类型上色——物资线索 `#e2a84d`、地点修正 `#71a6c4`、
  房客状态 `#a77ad1`。应用于图鉴信息页与**游戏内「现有信息」条目**（行首 19px 小图标）。
- **品质着色**：每个物资 SVG 的强调色**直接写死为该物品的品质色**（`--q0..--q5`），因此"图标上一部分颜色
  随品质"依然成立——只是靠 `manifest` 里逐件烧进去，而不是运行时 `currentColor`。
- **前端配合**：图鉴列表行原先没有给 `img` 尺寸，外置图会按 SVG 固有尺寸撑破行；已补
  `.cv .art-img{width:19px;height:19px}` 与 `.loc-name .art-img{width:19px;height:19px}`（对齐内置 `svg.ic`）。
- **仍然存在的代价**：`<img>` 不参与 `currentColor`，所以**同一张图无法在不同品质语境里改色**；
  如果将来物品品质可动态变化，需要改成可着色渲染（mask / inline SVG）而不是外置 PNG/SVG。

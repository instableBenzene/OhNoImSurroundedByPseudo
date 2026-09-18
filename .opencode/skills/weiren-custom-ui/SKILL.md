---
name: weiren-custom-ui
description: Use when a character needs its own state or its own panel/floating window — 触发场景："园艺达人要打开一块田""这个技能要点进去选人""加一个可拖拽的专属浮窗""专属状态要进存档". Contracts live in docs/GUIDE.md §14.11 and docs/STYLE.md §10; this page is the procedure and the pitfalls.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# 做专属状态 / 专属界面

> 契约先读：`docs/GUIDE.md` **§14.11**（`CONTAINERS` / `PANEL` / `opens_panel` / `confirm`）；
> 界面怎么拼读 `docs/STYLE.md` **§10 UI 范式**（照着用，别另造）。本页只讲**步骤与坑**。
> 验证走 `.opencode/skills/weiren-ui-probe`。

## 三层各放什么

| 层 | 放什么 |
| --- | --- |
| 内容层（角色模块） | 状态类（自己实现 `to_dict`/`from_dict`）、`PANEL = (build_view, resolve_action)`、视图内容、图标 svg、全部文案 |
| `web_ui` | 只做**投影**：内容给的 `{item_id, 数量}` / 行式条目 / 文字 → 前端能画的形状 |
| 前端 | 只画：格子用 `slotInner`、信息行用 `slotHtml`、卡片用 `svgCardHtml` / `tenantChoiceCard` |

## 步骤

1. **状态**：`CONTAINERS = {"<key>": 类}`；**缺字段走默认、坏数据丢弃**（老存档必须读得回来）。
2. **视图**：`build_view` 返回 `{title, prompt, slots, rows, actions, backdrop?}`；`rows` 用 `DETAIL_SLOT` 那套词表。
3. **动作**：`resolve_action(engine, tenant, action, *, slot, item_id, source)`；**动作名由内容定**，前端只转发。
4. **入口**：只负责开面板的技能声明 `opens_panel=True`（引擎会拒绝把它当普通主动技能结算）。
5. **登记**：新注册表进 `weiren_game/content.py::_BASE_CONTAINERS`（类型表 `tenant.CONTAINER_TYPES` 已在其中）。
6. **验证**：单测（规则 + 存档往返 + 卸载回滚）→ `node --check` → 定向探针。

## 坑

- **面板不是待处理交互**：它不进 `PENDING_VIEWS`，"开着没有"是纯展示状态。走那条路会卡住保存 / 开始回合 / 结束回合。
- **前端注释里不许写内容词**：`audit_separation` 扫的是文件文本，注释不豁免（这条踩过三次）。
- **物品条目由后端下发**（`web_ui._item_entry`），前端**不去别处查**物品——否则"引用对象不同"会在每个调用点漏一遍。
- **不可撤销的动作要让玩家看出后果**：内容给逐项说明（`TARGET_OPTIONS.desc`）+ `confirm` 文案 + `danger`；
  危险色一律用锁定语义色 token，**不新造颜色**。
- **别泄露玩家不该知道的**：给目标写"对伪人会如何"等于泄露身份（罗兹那条就故意只给 `confirm`）。

## 相关

- 前端实测：`weiren-ui-probe`；材质 / 渲染约定：`weiren-frontend`。

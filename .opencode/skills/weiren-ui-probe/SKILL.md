---
name: weiren-ui-probe
description: Use when verifying the web UI in a headless browser — frontend changes, UI bug repro, or producing before/after evidence. 触发词："验一下前端/界面""无头实测""CDP""改前改后对照". Random playthroughs belong to tools/browser_playtest.mjs; targeted checks belong here.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# 前端实测（定向探针）

> **改前端必须实机验**（`node --check` + 无头浏览器）。结论要能复述：**哪一局/哪一步/看到什么**。
> 会用到的模板：本目录 `probe.mjs`（照抄，别每次重写）。

## 流程

1. `node --check`：把 `index.html` 里的 `<script>` 抽出来校验（一行 Node/Python 都行）。
2. **备份 `game_config.json`**（探针若会写设置）。
3. 后台起服务：`python game_ui.py --no-browser --port <p>`。
4. 改 `probe.mjs` 的步骤段 → 跑 → 读结论。
5. 收尾：停服务、删临时文件、还原 `game_config.json`。
6. 改完再跑固定动作（单测 / 审计 / 内容校验）。

## 坑（每一条都踩过）

- **别用 Python 侧的种子去推演浏览器**。同一个 seed，`GameEngine.new_game()` 与网页创建路径消耗随机数的顺序不同 → 开局人选、抽到的牌都不一样。**按浏览器实际下发的数据找目标**（例：`STATE.pending.interaction.options[].number`），或遍历种子重试。
- **探针文件必须是真 UTF-8**：经 PowerShell 管道写会把脚本里的中文毁掉（变成 `?`）→ 用 `apply_patch`，或让 Python 写盘。
- **结论输出全用 `\uXXXX` 转义**，并记得 `padStart(4,"0")`（`\u80` 是非法转义）；控制台编码会把中文输出弄坏。
- **`WEIREN_SAVES_DIR` 指到临时目录**，否则探针会写进玩家的 `saves/`。
- **PowerShell 的 `>` 重定向写 UTF-16**：读回时按编码探测，别直接当 UTF-8。
- **`ERR_EMPTY_RESPONSE` 多半是后端未捕获异常**：去读服务端 traceback，别猜。
- **注入状态要说明**：真状态难凑（如"可指认"要先攒证据）时可以注入，但要**照后端的形状**注入，并在结论里写清哪部分是注入的。

## 什么时候别用

- 只关心"随机对局跑通不崩" → `tools/browser_playtest.mjs`。
- 纯后端 / 纯内容 → 单测 + `tools/smoke_simulation.py` 更省。

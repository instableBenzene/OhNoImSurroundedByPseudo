---
name: weiren-release
description: Use before shipping/releasing OhNoImSurroundedByPseudo — "投放 / 发布前检查 / release check / 上线自检". Runs the full pre-release verification: separation audits, unit tests, smoke, content validation, and browser playtest.
---

> **动手前先读**：`AGENTS.md` §7「已知坑」——尤其是**别打转**那六条
> （别猜锚点 / 别手写 `\u` 码点 / 中文别进 here-string / 注释不豁免分离度检查 /
> 提交前显式读退出码 / 探针先自证），以及 `docs/PRINCIPLES.md` §15「先怀疑探针」。

# 发布前自检

按顺序执行并报告结果；任一失败先修复。

## 1. 静态与单测
```
python -m compileall -q weiren_game game.py game_ui.py tools
python -m unittest discover -s tests -p "test_*.py"          # 必须全绿（刻意精简）
python tools/validate_content.py                             # 内容完整性
python tools/audit_separation.py                             # ①系统/前端无内容泄漏 ②data 不依赖 systems
python tools/smoke_simulation.py --seeds 3 --log-dir <tmp>   # 批量对局冒烟
```

## 2. 浏览器对局压测（捕获 UI/接口异常）
```
python game_ui.py --no-browser --port 8775
node tools/browser_playtest.mjs url=http://127.0.0.1:8775/ games=30 turns=12 budget=420
```
- 关注输出里的 `errors` 与 `errorCount`；用 `turns=12` 更易跑完整局。
- 若同时看服务器异常，启动时把 stderr 重定向到文件并检查 `Traceback`。

## 3. 人工抽查（脚本覆盖不到的界面）
开局选人 → 门口接纳/拒绝 → 指派搜索 → 使用/装备物资 → 使用技能（含"提交物资"）→ 结束回合 → 保存/读取/回溯 → ESC 退出 → 图鉴各分页与筛选。

## 4. 判定

## 5. 提交与推送

- 只提交**源码与文档**：`git add -A` 之后 `git reset -- saves`——`saves/` 是玩家的运行期数据，
  **绝不提交**（里面还有玩家自己的增删）。
- 提交信息**走 UTF-8 文件**（`git commit -F <file>`）：PowerShell 直接拼中文 `-m` 会被转坏。
- 提交前 `git status` 复核一遍暂存清单；提交后**再跑一次固定自检**，确认落在提交里的状态是绿的。
- 推送（`git push`）**只在明确要求时做**。
- 单测 / 校验 / 审计全绿；压测无 JS 异常、服务器无 Traceback；人工抽查无阻断问题 → 可投放。
- 收尾：清理 `saves/` 测试存档与后台进程。

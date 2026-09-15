# 《完蛋，我被伪人包围了！？》Python 完整规则终端版

> 开发者 / AI：先读 `docs/PRINCIPLES.md`（品味与手法）与 `AGENTS.md`（入口与硬性约束）；
> 架构细节见 `docs/GUIDE.md`（唯一权威）；内容创作见 `docs/ADD_CONTENT.md`。

把一个设计原稿（`基础设定.docx`、`游戏资源.docx`、`程序详情.docx`）里可以执行的游戏规则，
实装成一套能从开局玩到结局的纯 Python 终端游戏：你扮演屋主，在夜晚接纳/拒绝访客、指派房客
外出搜索、管理物资与状态，并识破、抵御混入其中的“伪人”。

引擎采用“核心与内容分离”：核心系统不引用任何具体角色、物资或地点；内置内容作为**基础内容包**，
并可通过 `dlc/` 声明式扩展。仅使用 Python 标准库（推荐 3.10+）。

## 运行

```powershell
python game.py
```

默认普通难度 `a0`、伪人按种子随机、第 32 回合日出。常用参数：

```powershell
python game.py --pseudo pseudo_benzene              # 指定伪人（benzene / onion / fries）
python game.py --difficulty a1 --seed 固定种子 --max-turns 15
python game.py --load savegame.json                # 读档（存档版本/内容包需与当前一致）
python game.py --disable dragon,bigstar            # 禁用若干房客
python game.py --list-content                      # 不进入游戏，打印全部静态内容
```

相同种子 + 难度 + 伪人 + 操作 ⇒ 相同的世界生成、搜索判定与事件结果。游戏内输入 `help` 查看全部
命令（`status` / `inventory` / `door` / `search` / `item` / `equip` / `ability` / `info` / `accuse` /
`lock` / `locations` / `codex` / `save` / `rewind` / `end` / `quit`）。旧版控制台中文乱码可先 `chcp 65001`。

本地 Web 界面（纯标准库，无需依赖）：

```
启动游戏UI.vbs            # 双击：无任何控制台窗口（推荐；用 pythonw）
启动游戏UI.bat            # 双击：无窗口启动，失败回退到有窗口
启动游戏UI(调试窗口).bat   # 需要看输出/排错时用（保留控制台）
python game_ui.py         # 直接在终端运行（可见日志）
```

启动后会自动打开浏览器（默认 `http://127.0.0.1:8730/`）。用 `pythonw` 启动时输出写入
`logs/web_ui.log`。引擎保持无头；命令行（`game.py`）与 Web 界面（`game_ui.py` → `weiren_game/web_ui.py`）
是同一引擎的前端，前端只消费状态 JSON 与动作 JSON。

## 文档地图

| 文档 | 作用 |
| --- | --- |
| `docs/PRINCIPLES.md` | 品味与手法（灵魂篇）—— **先读** |
| `AGENTS.md` | AI / 开发入口：常用命令、硬性不变量、当前状态 |
| `docs/GUIDE.md` | **唯一权威**架构文档（含 §14 分层、§15 原稿覆盖） |
| `docs/STYLE.md` | 美术与 UI 风格 + §9 参数表 |
| `docs/ADD_CONTENT.md` | 内容创作：类型全景 / 加房客 / 写 DLC |
| `docs/DECISIONS.md` | 决策与修正记录 |
| `dlc/README.md`、`dlc/_template/` | 内容包 / 伪人编写规范与模板 |
| `../完蛋，我被伪人包围了？！/` | 设计原稿（在项目外）：docx、`md/` 转换稿、差异附录 |

## 内容可插拔

- **自动发现**（`weiren_game/data/_discovery.py`）：`characters/`、`personalities/`、`pseudos/`、
  `items/`、`tags/` 下的 `.py` **放入或删除即生效，无需登记**。
- 核心不含具体内容 id；角色专属的状态 / 事件 / 搜索修正 / 图鉴 / 选牌 UI 都写在各自的模块里。
- 外部内容包放 `dlc/<pack>/`，`base` 恒启用；启用集合写入存档并在读取时校验一致。

## 验证

```powershell
python -m unittest discover -s tests -p "test_*.py"    # 50 项确定性单元/回归测试（刻意精简）
python tools/smoke_simulation.py --seeds 200           # 三类伪人的批量完整对局（稳定性）
```

自动玩家只用于稳定性验证，胜率不代表正式平衡结果。

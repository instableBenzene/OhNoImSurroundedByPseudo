# 参与这个项目

先说边界：这个仓库**只开放两类东西**给外部贡献。

| 开放区 | 放什么 | 怎么加 |
| --- | --- | --- |
| `dlc/` | 内容包：角色、性格、伪人、物品、地点、地图、信息模板、图鉴分节…… | 照 `dlc/README.md` + `dlc/_template/` 复制一份改；字段见 `docs/ADD_CONTENT.md` |
| `resourcepacks/` | 资源包：**只改外观**（配色 token、字体、贴图、素材位） | 见 `docs/STYLE.md` §9 与 `AGENTS.md` §6「外观与材质」 |

**其余一切是自留区**：`weiren_game/`（核心与内置内容）、`tools/`、`tests/`、`docs/`、`design/`、
`.github/`、`.opencode/`，以及根目录的入口脚本与配置。这些文件只由仓库作者维护；
改动自留区的 PR 会被 `ownership-guard` 自动打回（规则见 `.github/workflows/ownership-guard.yml`，
本地可跑 `python tools/audit_ownership.py --base origin/main` 自查）。

## 提内容包（推荐路径）

1. Fork 仓库，在你的分支里**只**动 `dlc/` 或 `resourcepacks/`（新增文件为主）。
2. 本地跑一遍：

   ```text
   python -m compileall -q weiren_game
   python -m unittest discover -s tests -p "test_*.py"
   python tools/validate_content.py
   python tools/audit_separation.py
   ```

3. **实际玩一局**，确认内容能出现、机制能生效：`python game_ui.py`（或 `python game.py`）。
4. 提 PR，按模板写清：加了什么、放在哪个目录、怎么验证的；有截图更好。

## 想改核心或内置内容？

**先开 issue 说清楚**：要解决什么问题、为什么现有扩展点（`dlc/`、`resourcepacks/`）不够用。
直接改 `weiren_game/` 的 PR 会被自动检查拦下，白费一轮。作者认可后，改法由作者落地。

## 不接受

- 改自留区（尤其 `weiren_game/` 的核心与内置内容）。
- 动 `.github/`（守卫本身）或绕过 `ownership-guard`。
- 把 `saves/`、`logs/` 等运行期数据提进来。

## 许可

仓库目前**没有 LICENSE**：未经作者许可，不得复制、修改或再分发本仓库的核心代码。
`dlc/` 与 `resourcepacks/` 的提交在合并时视为按同等条款收录。

# 分发：让别人"不用装 Python"也能玩

本项目只用标准库，但默认需要本机有 Python。下面两条路线都能免安装运行。

## 路线 A（推荐）：便携运行时 + 双击 VBS

把 Python 的 **embeddable** 版放进项目里的 `runtime/`，随文件夹一起分发；使用者双击
`启动游戏UI.vbs` 即可（该脚本会**优先**使用 `runtime\pythonw.exe`）。

打包者操作一次：
```
python tools/prepare_portable.py          # 下载并解压 embeddable Python 到 runtime/
# 之后 runtime\pythonw.exe 就位（约 19MB），且 ._pth 已加入项目根
```
- 网络不通时：手动到 <https://www.python.org/ftp/python/> 下载
  `python-<版本>-embed-amd64.zip`，解压到 `runtime/` 即可。
- 验证：`runtime\pythonw.exe game_ui.py --no-browser --port 8786` 应能启动并返回 200。

分发给别人：**打包整个项目文件夹**（含 `runtime/`、`weiren_game/`、`assets/`、`dlc/`）。
对方解压后双击 `启动游戏UI.vbs`。若对方系统缺失 VC 运行库导致 DLL 加载失败，另装
「Visual C++ Redistributable」即可（Windows 常见）。

## 路线 B（可选）：单文件 exe（PyInstaller）

在自己机器上装一次 PyInstaller 后打一个 exe：
```
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name "完蛋我被伪人包围了" ^
  --add-data "weiren_game/webui;weiren_game/webui" ^
  --add-data "weiren_game/data;weiren_game/data" ^
  --add-data "assets;assets" ^
  game_ui.py
```
**注意**：内容目录 `weiren_game/data/**` 是**按文件自动发现**的，PyInstaller 的静态分析**不会**自动收集，
所以必须像上面那样用 `--add-data` 把 `data` 与 `webui` 作为数据文件打进去，否则打包后会"零内容"。
打完后**务必实测**能开局、能看到图鉴。

## 运行期文件位置

打包/便携运行下，可写目录取**可执行文件（或脚本）所在目录**（见 `weiren_game/paths.py` 的 `app_base()`）：
- `saves/`：存档；`assets/art/`：外置美术；`game_config.json`：设置；`dlc/`：内容包；`logs/web_ui.log`：无窗口时的输出。

## 其他
- `runtime/` 是**运行时**，不是源码；不想随仓库携带可删除，需要分发时再 `prepare_portable`。
- 无窗口启动（`pythonw`/VBS）时没有控制台；排查问题请用 `启动游戏UI(调试窗口).bat` 或看 `logs/web_ui.log`。

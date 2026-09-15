"""准备「便携运行时」：把 Python embeddable 解压到 runtime/，之后运行**无需安装 Python**。

用法：
    python tools/prepare_portable.py                 # 用当前 Python 版本
    python tools/prepare_portable.py --version 3.11.0 --arch amd64

做完后分发**整个项目文件夹**即可；使用者双击 启动游戏UI.vbs 就能玩。
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"


def main() -> int:
    """下载并解压 embeddable Python 到 runtime/。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=".".join(str(v) for v in sys.version_info[:3]))
    parser.add_argument("--arch", default="amd64")
    args = parser.parse_args()
    url = (f"https://www.python.org/ftp/python/{args.version}/"
           f"python-{args.version}-embed-{args.arch}.zip")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    print("下载：", url)
    try:
        data = urllib.request.urlopen(url, timeout=60).read()
    except Exception as exc:  # noqa: BLE001 - 网络问题给出人工指引
        print("下载失败：", exc)
        print("请手动下载上面的 zip，并解压到：", RUNTIME)
        return 2
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        archive.extractall(RUNTIME)
    # 让自带解释器能找到项目包（把项目根加入 ._pth 搜索路径）。
    for pth in RUNTIME.glob("python*._pth"):
        text = pth.read_text(encoding="utf-8")
        if ".." not in text.split():
            pth.write_text(text.rstrip() + "\n..\n", encoding="utf-8")
    print("完成：runtime/ 已就绪。双击 启动游戏UI.vbs 即可（无需安装 Python）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
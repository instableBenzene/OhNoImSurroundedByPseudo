"""运行路径：区分"可写根目录"与"只读资源目录"，兼容源码运行与打包/便携运行。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_base() -> Path:
    """可写根目录：打包后 = 可执行文件所在目录；源码运行 = 项目根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def saves_dir() -> Path:
    """存档目录：可用环境变量 WEIREN_SAVES_DIR 隔离（测试/脚本务必用它，勿动用户存档）。"""
    override = os.environ.get("WEIREN_SAVES_DIR")
    return Path(override) if override else app_base() / "saves"


def resource_dir(name: str = "") -> Path:
    """只读资源目录：打包后 = 解包目录(_MEIPASS)；源码运行 = 包内目录。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name if name else base


__all__ = ["app_base", "saves_dir", "resource_dir"]

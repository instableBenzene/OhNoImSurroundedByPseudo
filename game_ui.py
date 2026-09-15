"""图形界面入口：python game_ui.py（本地 Web 界面）。

用 pythonw（无控制台）启动时 stdout/stderr 为 None；这里重定向到 logs/web_ui.log，
避免 print 抛错导致服务起不来。
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_streams() -> None:
    """无控制台启动时，把标准输出/错误重定向到日志文件。"""
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stream = open(log_dir / "web_ui.log", "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


_ensure_streams()

from weiren_game.web_ui import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
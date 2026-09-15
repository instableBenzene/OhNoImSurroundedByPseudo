"""内容模块自动发现：扫描包目录并导入，供各聚合 __init__ 复用。

放入一个满足约定的 .py 文件即自动登记；删除即自动注销，无需手写清单。
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def discover_modules(
    package_name: str,
    directory: Path,
    *,
    require: str | None = None,
) -> dict[str, object]:
    """按文件名字典序导入同目录模块。

    ``require``：仅登记暴露了该属性的模块（如 "CHARACTER" / "DEFINITION"）。
    """
    modules: dict[str, object] = {}
    for info in sorted(pkgutil.iter_modules([str(directory)]), key=lambda item: item.name):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package_name}.{info.name}")
        if require is None or getattr(module, require, None) is not None:
            modules[info.name] = module
    return modules

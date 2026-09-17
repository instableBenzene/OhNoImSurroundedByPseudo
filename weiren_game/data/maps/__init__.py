"""地图（区域包）注册表：一张地图 = 一组搜索地点 + 屋子名。

目录约定（**一张地图一个文件夹**）::

    weiren_game/data/maps/base/map.py      # 默认地图（显示名「城郊小镇」）
    weiren_game/data/maps/<id>/map.py      # 其它地图
    dlc/<包>/maps/<id>/map.py              # 资料包自带的地图

``map.py`` 里暴露 ``MAP = MapDefinition(...)``（内容文件请用**绝对 import**）。
``base`` 这个名字只是为了标明"默认的那张图"，显示名由 ``MapDefinition.name`` 决定。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ..types import MapDefinition

MAPS: dict[str, MapDefinition] = {}
# 默认地图的 id：没选地图时用它（= 城郊小镇）。
BASE_MAP_ID = "base"

_LOAD_COUNTER = [0]


def _load_file(path: Path):
    """按文件路径装载一个内容文件（绝对 import 最稳，和 DLC 的写法一致）。"""
    _LOAD_COUNTER[0] += 1
    name = "weiren_data_map_%d" % _LOAD_COUNTER[0]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def register_map(definition: MapDefinition, *, replace: bool = False) -> None:
    """登记一张地图（同 id 需要 ``replace=True`` 才覆盖，供内容包优先级用）。"""
    if definition.id in MAPS and not replace:
        raise ValueError(f"地图 ID 重复：{definition.id}")
    MAPS[definition.id] = definition


def register_map_location(map_id: str, location_id: str) -> None:
    """把某个地点**加进**已有地图的名单（DLC 想让自己的地点进"城郊小镇"时用）。"""
    current = MAPS.get(map_id)
    if current is None or location_id in current.locations:
        return
    from dataclasses import replace as _replace

    MAPS[map_id] = _replace(current, locations=tuple(current.locations) + (str(location_id),))


def load_map_dirs(directory: "Path | str") -> None:
    """扫描 ``<目录>/<id>/map.py`` 并登记（资料包用）。"""
    base = Path(directory)
    if not base.is_dir():
        return
    for entry in sorted(base.iterdir(), key=lambda item: item.name):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name == "__pycache__":
            continue
        target = entry / "map.py"
        if not target.is_file():
            continue
        module = _load_file(target)
        definition = getattr(module, "MAP", None)
        if isinstance(definition, MapDefinition):
            register_map(definition, replace=definition.id in MAPS)


load_map_dirs(Path(__file__).parent)

__all__ = [
    "MAPS", "BASE_MAP_ID", "MapDefinition", "load_map_dirs",
    "register_map", "register_map_location",
]

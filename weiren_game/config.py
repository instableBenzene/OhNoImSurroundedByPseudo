"""对局外的全局配置（总设计 config）。
保存“启动即定、对局期间不变”的设定：默认难度、默认回合数、是否随机伪人、
默认伪人，以及启用内容包及其**优先级顺序**（``pack_order``，高 → 低，含 ``base``）。
可通过游戏根目录的 ``game_config.json`` 覆盖；不存任何对局内状态。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path


from .paths import app_base

CONFIG_PATH = app_base() / "game_config.json"


@dataclass
class GameConfig:
    """对局外设定（不随存档变化）。"""

    difficulty: str = "a0"
    max_turns: int = 32
    random_pseudo: bool = False
    default_pseudo: str | None = None
    enabled_dlc: list[str] = field(default_factory=list)
    # 内容包优先级（**高 → 低**，可含 "base"）：靠上的包覆盖靠下的同 id 内容。
    # 空 = 尚未设置；装载时按 ``["base", *enabled_dlc]`` 回落（base 优先级最高）。
    pack_order: list[str] = field(default_factory=list)
    # 资源包优先级（**高 → 低**）：含 `base`（= 内置材质 weiren_game/data/resourcepack/），
    # 位次可调 —— 排在 base 上方的外观包覆盖内置材质，排在下方则被内置材质覆盖。
    # 与内容包分开：整个外观层在内容包之后套用，故包总能盖过 DLC 内嵌的 resourcepack/。
    resourcepack_order: list[str] = field(default_factory=lambda: ["base"])
    # 显示偏好：房客卡详情页是否直接展开完整技能文本（否则折叠成一行、悬浮查看）。
    show_full_skills: bool = True
    # 专属面板能不能拖着走（默认开启）。位置按**视口比例**记住：面板 key（角色 id）→ [左, 上]。
    panel_draggable: bool = True
    panel_pos: dict = field(default_factory=dict)


def load_config(path: str | Path = CONFIG_PATH) -> GameConfig:
    """读取 config 文件并覆盖默认值；文件缺失/损坏时返回默认配置。"""
    config = GameConfig()
    source = Path(path)
    if not source.is_file():
        return config
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return config
    if not isinstance(raw, dict):
        return config
    known = {item.name for item in fields(GameConfig)}
    for key, value in raw.items():
        if key in known:
            setattr(config, key, value)
    if not config.pack_order:
        config.pack_order = ["base", *config.enabled_dlc]
    # enabled_dlc 恒为"额外包"（去掉 base），与 pack_order 保持一致。
    config.enabled_dlc = [name for name in config.pack_order if name != "base"]
    # 资源包清单里的 `base` = 内置材质，恒存在（缺失则垫底）；其位次可调。
    if not isinstance(config.resourcepack_order, list):
        config.resourcepack_order = []
    config.resourcepack_order = [str(name) for name in config.resourcepack_order]
    if "base" not in config.resourcepack_order:
        config.resourcepack_order.append("base")
    if not isinstance(config.panel_pos, dict):
        config.panel_pos = {}
    return config


# 模块级当前配置：默认从根目录 game_config.json 读取。
CONFIG = load_config()


def save_config(config: GameConfig, path: str | Path = CONFIG_PATH) -> Path:
    """把配置原子写回文件。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "difficulty": config.difficulty,
        "max_turns": config.max_turns,
        "random_pseudo": config.random_pseudo,
        "default_pseudo": config.default_pseudo,
        "enabled_dlc": [name for name in config.pack_order if name != "base"] or list(config.enabled_dlc),
        "pack_order": list(config.pack_order),
        "resourcepack_order": list(config.resourcepack_order),
        "show_full_skills": config.show_full_skills,
        "panel_draggable": bool(config.panel_draggable),
        "panel_pos": dict(config.panel_pos or {}),
    }
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return target


__all__ = ["CONFIG", "CONFIG_PATH", "GameConfig", "load_config", "save_config"]

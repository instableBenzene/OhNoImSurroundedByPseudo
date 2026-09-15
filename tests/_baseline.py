"""测试基准：把可变全局配置钉在 a0 / 32 回合 / 不装内容包。

玩家可在界面里改难度等设置并写入 ``game_config.json``；
测试断言的是基准下的引擎行为，故在导入时显式覆盖，保证结果与玩家设置无关。
"""

from __future__ import annotations

from weiren_game.config import CONFIG


def pin() -> None:
    CONFIG.difficulty = "a0"
    CONFIG.max_turns = 32
    CONFIG.random_pseudo = False
    CONFIG.default_pseudo = None
    CONFIG.enabled_dlc = []


pin()

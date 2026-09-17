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
    # 装载看的是 ``pack_order``（``load_configured_dlc``），所以只清 ``enabled_dlc`` 不够：
    # 玩家在界面里启用的包仍会被 ``GameEngine.new_game()`` 装进来，后面的目录统计就偏了。
    CONFIG.pack_order = ["base"]
    CONFIG.resourcepack_order = ["base"]


pin()

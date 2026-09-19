"""likai_test 的文字总表（lang）：本包面向玩家的文字都住这里，别处只引用。

包自己的模块这样取：`TEXT = pack_text_from_file(__file__)`（见 `weiren_game/data/lang.py`）。
模板写法与 base 相同：`{名字}` + 调用处 `.format(名字=…)`。
"""

from __future__ import annotations

TEXT: dict[str, str] = {

    # ---------------------------------------------------------------- character
    "character.likai.description": "常年流浪的中年人，具有极强的生存能力。",
    "character.likai.name": "老楷",
    "character.likai.tag.0": "25岁-30岁",
    "character.likai.tag.1": "男性",
    "character.likai.tag.2": "无业游民",

    # ---------------------------------------------------------------- dlc
    "dlc.likai_test.characters.likai._rebirth_ability.1": "老楷的重生",
    "dlc.likai_test.characters.likai._rebirth_ability.2": "死亡后有 x% 可能以全新访客的身份回到访客池；概率 = 75% - 15%×死亡次数（最低 5%）。每次死亡后，老楷再次入住时最大生命值 +10×死亡次数。",
    "dlc.likai_test.characters.likai.module.1": "老楷·死亡次数",
    "dlc.likai_test.characters.likai.module.2": "测试 DLC：likai_test",
    "dlc.likai_test.items.painting._painting_turn_start.1": "印象派名画",

    # ---------------------------------------------------------------- item
    "item.impressionist_painting.description": "一副临摹很好看的印象派名画；放在屋主物品栏时，每回合开始为所有房客回复2理智。",
    "item.impressionist_painting.name": "印象派名画",
}

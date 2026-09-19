"""_template 的文字总表（lang）：本包面向玩家的文字都住这里，别处只引用。

包自己的模块这样取：`TEXT = pack_text_from_file(__file__)`（见 `weiren_game/data/lang.py`）。
模板写法与 base 相同：`{名字}` + 调用处 `.format(名字=…)`。
"""

from __future__ import annotations

TEXT: dict[str, str] = {

    # ---------------------------------------------------------------- dlc
    "dlc._template.personalities.example_persona.LABEL": "示例性格",

    # ---------------------------------------------------------------- emotion
    "emotion.example_emotion.description": "一句话风味描述。",
    "emotion.example_emotion.label": "示例情绪",

    # ---------------------------------------------------------------- status
    "status.example_status.description": "一句话风味描述。",
    "status.example_status.label": "示例状态",
}

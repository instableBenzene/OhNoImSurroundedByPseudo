"""房客档案：斜阳（21 号）。"""

from ..types import CharacterDefinition
from weiren_game.data.lang import TEXT

CHARACTER = CharacterDefinition(
    "sunset", 21, TEXT["character.sunset.name"], TEXT["character.sunset.description"], "keen", "impatient", 3, (TEXT["character.sunset.tag.0"], TEXT["character.sunset.tag.1"]),
    source_note=TEXT["data.characters.sunset.module.1"],
)

# 界面头像图标（内容自声明）。
AVATAR = "i-av8"

"""房客档案：白龙（19 号）。"""

from ..types import CharacterDefinition
from weiren_game.data.lang import TEXT

CHARACTER = CharacterDefinition(
    "whitedragon", 19, TEXT["character.whitedragon.name"], TEXT["character.whitedragon.description"], "steady", "gentle", 3, (TEXT["character.whitedragon.tag.0"], TEXT["character.whitedragon.tag.1"], TEXT["character.whitedragon.tag.2"]),
    source_note=TEXT["data.characters.whitedragon.module.1"],
)

# 界面头像图标（内容自声明）。
AVATAR = "i-av10"

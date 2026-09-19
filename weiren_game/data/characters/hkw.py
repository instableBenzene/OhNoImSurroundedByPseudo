"""房客档案：HKW（18 号）。"""

from ..types import CharacterDefinition
from weiren_game.data.lang import TEXT

CHARACTER = CharacterDefinition(
    "hkw", 18, TEXT["character.hkw.name"], TEXT["character.hkw.description"], "suspicious", "stubborn", 4, (TEXT["character.hkw.tag.0"], TEXT["character.hkw.tag.1"], TEXT["character.hkw.tag.2"]),
    source_note=TEXT["data.characters.hkw.module.1"],
)

# 界面头像图标（内容自声明）。
AVATAR = "i-av11"

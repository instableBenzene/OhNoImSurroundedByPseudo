"""房客档案：端（20 号）。"""

from ..types import CharacterDefinition
from weiren_game.data.lang import TEXT

CHARACTER = CharacterDefinition(
    "dragonboat", 20, TEXT["character.dragonboat.name"], TEXT["character.dragonboat.description"], "stubborn", "suspicious", 3, (TEXT["character.dragonboat.tag.0"], TEXT["character.dragonboat.tag.1"], TEXT["character.dragonboat.tag.2"]),
    source_note=TEXT["data.characters.dragonboat.module.1"],
)

# 界面头像图标（内容自声明）。
AVATAR = "i-av6"

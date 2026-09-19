"""房客档案：小五（23 号）。"""

from ..types import CharacterDefinition
from weiren_game.data.lang import TEXT

CHARACTER = CharacterDefinition(
    "fiver", 23, TEXT["character.fiver.name"], TEXT["character.fiver.description"], "gentle", "steady", 2, (TEXT["character.fiver.tag.0"], TEXT["character.fiver.tag.1"], TEXT["character.fiver.tag.2"], TEXT["character.fiver.tag.3"]),
    source_note=TEXT["data.characters.fiver.module.1"],
)

# 界面头像图标（内容自声明）。
AVATAR = "i-av8"

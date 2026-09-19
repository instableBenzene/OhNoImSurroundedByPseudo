"""房客档案：古雕塑（16 号，创作性白板补位）。

形象：22 岁职场白领，安静得像一尊古雕塑，表情与情绪极少外露。

改名记录：原名"沈屹"，2026-09-17 起显示名改为"古雕塑"（与标签、形象一致）。
`tenant_id` 仍是 `stone`，**没有改** —— 存档只认 id，改名不影响老存档。
目前是白板角色：只有基础档案，暂无被动/主动技能；后续设计技能时按
definition / modifier / function 三节补在本文件即可。
"""

from ..types import CharacterDefinition
from weiren_game.data.lang import TEXT

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "stone", 16, TEXT["character.stone.name"],
    TEXT["character.stone.description"],
    "steady", "loner", 3, (TEXT["character.stone.tag.0"], TEXT["character.stone.tag.1"], TEXT["character.stone.tag.2"], TEXT["character.stone.tag.3"]),
    available=False,
    source_note=TEXT["data.characters.stone.module.1"],
)

# 暂无 modifier / function（白板角色没有技能，本节留空待后续补充）。

# 界面头像图标（内容自声明）。
AVATAR = "i-av7"

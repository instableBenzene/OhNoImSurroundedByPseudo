"""房客档案：沈屹（16 号，创作性白板补位）。

形象：22 岁职场白领，安静得像一尊古雕塑，表情与情绪极少外露。
目前是白板角色：只有基础档案，暂无被动/主动技能；后续设计技能时按
definition / modifier / function 三节补在本文件即可。
"""

from ..types import CharacterDefinition

# ---------------------------------------------------------------- definition
CHARACTER = CharacterDefinition(
    "stone", 16, "沈屹",
    "像一尊古雕塑的职场白领，习惯长时间不动与沉默，情绪极少外露，但工作一丝不苟。",
    "steady", "loner", 3, ("职场白领", "22岁", "公司文员", "像古雕塑"),
    available=False,
    source_note="16 号创作性补位：白板角色，暂无技能；暂不进入房客池。",
)

# 暂无 modifier / function（白板角色没有技能，本节留空待后续补充）。

# 界面头像图标（内容自声明）。
AVATAR = "i-av7"

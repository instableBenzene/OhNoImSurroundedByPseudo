"""示例状态与情绪（id 全局唯一）。"""

from weiren_game.condition import EmotionDefinition, StatusDefinition
from weiren_game.data.lang import pack_text_from_file
TEXT = pack_text_from_file(__file__)

STATUSES = (
    StatusDefinition("example_status", TEXT["status.example_status.label"], "mental",
                     description=TEXT["status.example_status.description"]),
)

EMOTIONS = (
    EmotionDefinition("example_emotion", TEXT["emotion.example_emotion.label"], "mental",
                      kind="erosion", description=TEXT["emotion.example_emotion.description"]),
)

# 注册后会自动补 `reveal_example_emotion` 标记状态，并同步 data 层中文名表。

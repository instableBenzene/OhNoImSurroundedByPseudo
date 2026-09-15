"""示例状态与情绪（id 全局唯一）。"""

from weiren_game.condition import EmotionDefinition, StatusDefinition

STATUSES = (
    StatusDefinition("example_status", "示例状态", "mental",
                     description="一句话风味描述。"),
)

EMOTIONS = (
    EmotionDefinition("example_emotion", "示例情绪", "mental",
                      kind="erosion", description="一句话风味描述。"),
)

# 注册后会自动补 `reveal_example_emotion` 标记状态，并同步 data 层中文名表。

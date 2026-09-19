"""图鉴「机制」分页：面向屋主的规则教程（内容层，独立可导入）。

这里是「教程」正文，遵循两条原则：
- **只讲规则，不列内容**：具体角色/物品/羁绊/伪人的效果在各自分页，本文件只解释通用机制。
- **与代码一致**：数值以 `weiren_game/systems/` 的实现为准（原稿差异见设计稿附录 A）。

结构：``MECHANICS = ({"title": 标题, "icon": 图标 id, "tint": 强调色, "entries": ((术语, 说明), ...)}, ...)``。
``tint`` 是**低饱和**的分节色（界面用它给图标上色/描一圈），免得整页清一色琥珀。
"""

from __future__ import annotations
from weiren_game.data.lang import TEXT


MECHANICS = (
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.0.title"],
        "tint": "#c9b06a",
        "icon": "i-info",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.5.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.0.entries.6.0"], TEXT["data.codex_mechanics.MECHANICS.0.entries.6.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.1.title"],
        "tint": "#7fa8c9",
        "icon": "i-clock",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.1.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.1.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.1.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.1.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.1.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.1.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.1.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.1.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.1.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.1.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.1.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.1.entries.5.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.2.title"],
        "tint": "#a79ac9",
        "icon": "i-hand",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.5.1"]),
            ("ESC", TEXT["data.codex_mechanics.MECHANICS.2.entries.6.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.7.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.7.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.2.entries.8.0"], TEXT["data.codex_mechanics.MECHANICS.2.entries.8.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.3.title"],
        "tint": "#b08a6a",
        "icon": "i-gate",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.5.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.3.entries.6.0"], TEXT["data.codex_mechanics.MECHANICS.3.entries.6.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.4.title"],
        "tint": "#6fb3a6",
        "icon": "i-search",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.5.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.6.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.6.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.4.entries.7.0"], TEXT["data.codex_mechanics.MECHANICS.4.entries.7.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.5.title"],
        "tint": "#c9a86a",
        "icon": "i-bag",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.5.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.5.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.5.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.5.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.5.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.5.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.5.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.5.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.5.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.5.entries.4.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.6.title"],
        "tint": "#68b998",
        "icon": "i-pill",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.6.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.6.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.6.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.6.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.6.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.6.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.6.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.6.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.6.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.6.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.6.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.6.entries.5.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.7.title"],
        "tint": "#9a8ad0",
        "icon": "i-disorder",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.7.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.7.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.7.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.7.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.7.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.7.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.7.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.7.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.7.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.7.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.7.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.7.entries.5.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.8.title"],
        "tint": "#c98a7a",
        "icon": "i-trauma",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.5.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.8.entries.6.0"], TEXT["data.codex_mechanics.MECHANICS.8.entries.6.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.9.title"],
        "tint": "#d9a52e",
        "icon": "i-shock",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.9.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.9.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.9.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.9.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.9.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.9.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.9.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.9.entries.3.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.10.title"],
        "tint": "#c98aa0",
        "icon": "i-emotion",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.10.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.10.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.10.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.10.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.10.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.10.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.10.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.10.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.10.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.10.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.10.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.10.entries.5.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.11.title"],
        "tint": "#b07a4a",
        "icon": "i-mark",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.11.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.11.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.11.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.11.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.11.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.11.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.11.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.11.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.11.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.11.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.11.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.11.entries.5.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.12.title"],
        "tint": "#a8b06a",
        "icon": "i-target",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.12.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.12.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.12.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.12.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.12.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.12.entries.2.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.13.title"],
        "tint": "#9fb8c9",
        "icon": "i-tool",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.13.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.13.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.13.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.13.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.13.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.13.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.13.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.13.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.13.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.13.entries.4.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.13.entries.5.0"], TEXT["data.codex_mechanics.MECHANICS.13.entries.5.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.14.title"],
        "tint": "#71a6c4",
        "icon": "i-note",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.14.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.14.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.14.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.14.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.14.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.14.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.14.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.14.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.14.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.14.entries.4.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.15.title"],
        "tint": "#c05b4d",
        "icon": "i-seal",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.15.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.15.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.15.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.15.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.15.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.15.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.15.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.15.entries.3.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.15.entries.4.0"], TEXT["data.codex_mechanics.MECHANICS.15.entries.4.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.16.title"],
        "tint": "#8fa0d8",
        "icon": "i-hand",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.16.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.16.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.16.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.16.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.16.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.16.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.16.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.16.entries.3.1"]),
        ),
    },
    {
        "title": TEXT["data.codex_mechanics.MECHANICS.17.title"],
        "tint": "#b0a08a",
        "icon": "i-gear",
        "entries": (
            (TEXT["data.codex_mechanics.MECHANICS.17.entries.0.0"], TEXT["data.codex_mechanics.MECHANICS.17.entries.0.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.17.entries.1.0"], TEXT["data.codex_mechanics.MECHANICS.17.entries.1.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.17.entries.2.0"], TEXT["data.codex_mechanics.MECHANICS.17.entries.2.1"]),
            (TEXT["data.codex_mechanics.MECHANICS.17.entries.3.0"], TEXT["data.codex_mechanics.MECHANICS.17.entries.3.1"]),
        ),
    },
)

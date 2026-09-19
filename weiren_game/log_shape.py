"""把播报原文按**形状**归并成明细行（谁 / 多少 / 为什么）。

为什么在 log 层做：这些行的格式本来就受 `docs/STYLE.md` §11 约束（主语 + 事实 + 因为谁），
**形状是稳定的**；在这里解析，内容层与技能侧就不必各自组装明细
（见 `docs/DECISIONS.md`「把 AOE 折叠统一到 log 层」）。

**只认形状，不认任何内容名**：单位/来源一律当通用片段捕获，所以这里不会出现角色名、技能名、情绪名。
命中的行产出结构化行；**没命中的行原样保留**（内容层自己写的自由文本不会丢）。
"""

from __future__ import annotations

import re
from weiren_game.data.lang import TEXT

# `X因{因为}流失/消耗/受到{N}{单位}。` —— 值层的损失类播报都长这样。
_LOSS = re.compile(
    TEXT["log_shape.module.1"]
)
# `（前缀：）X的{单位}层数+{N}。` —— 状态/情绪的层数累积。
_GAIN_LAYERS = re.compile(
    TEXT["log_shape.module.2"]
)


def row_from_line(line: str) -> dict | None:
    """把一行播报解析成 `{label, value, note}`；认不出形状就返回 None。"""
    text = (line or "").strip()
    match = _LOSS.match(text)
    if match:
        return {
            "label": match.group("who"),
            "value": "−%s %s" % (match.group("amount"), match.group("unit")),
            "note": match.group("why"),
        }
    match = _GAIN_LAYERS.match(text)
    if match:
        return {
            "label": match.group("who"),
            "value": "+%s %s" % (match.group("amount"), match.group("unit")),
            "note": TEXT["log_shape.row_from_line.1"],
        }
    return None


def rows_from_lines(lines: list) -> list[dict]:
    """一批播报 → 明细行；**认不出的行保持原文**（向后兼容，永不丢信息）。

    入参允许混装：字符串（播报原文，按形状解析）与已经是 `{label, …}` 的字典（原样保留）——
    收集器内部可能已经存了结构化行，两边都要吃得下。
    """
    rows: list[dict] = []
    for line in lines:
        if isinstance(line, dict):
            rows.append(line)
            continue
        rows.append(row_from_line(str(line)) or {"label": str(line)})
    return rows

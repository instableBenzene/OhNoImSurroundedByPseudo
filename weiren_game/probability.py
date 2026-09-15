"""统一概率规则。

- 先看是否有“必定”结果（0 或 1）：若有且不冲突，直接采用；
- 若出现互相矛盾的必定（如必定遭遇与必定规避），忽略必定、进入计算；
- 计算过程中允许越界（>95% 或 <5%），但最终结果必须落在 5%~95%，
  除非该结果是明确的必定 0/100。
"""

from __future__ import annotations

LOWER = .05
UPPER = .95


def single_guarantee(value: float) -> float | None:
    """把“必定”值归一为 0.0/1.0；普通概率返回 None。"""
    if value >= 1.0:
        return 1.0
    if value <= 0.0:
        return 0.0
    return None


def resolve(base: float, guarantees: object = ()) -> float:
    """按统一规则结算最终概率。

    ``guarantees`` 为各项“必定”声明（0/1）。仅当只有一个方向成立时采用；
    出现冲突或没有必定时，返回 ``base`` 夹取到 5%~95% 的结果。
    """
    forced: set[float] = set()
    for value in guarantees:
        guarantee = single_guarantee(float(value))
        if guarantee is not None:
            forced.add(guarantee)
    if len(forced) == 1:
        return forced.pop()
    return max(LOWER, min(UPPER, float(base)))


__all__ = ["LOWER", "UPPER", "resolve", "single_guarantee"]

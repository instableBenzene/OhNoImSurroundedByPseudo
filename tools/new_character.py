"""脚手架：生成一个新的房客内容模块（零改核心，自动发现生效）。

用法：
    python tools/new_character.py <ascii_id> <中文名> [--carry N] [--primary KEY] [--secondary KEY]

生成后填好人设/标签/技能，再跑 ``python tools/validate_content.py`` 与单测。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from weiren_game.data import CHARACTERS, PERSONALITIES  # noqa: E402


TEMPLATE = '''"""房客档案：__NAME__（__NO__ 号）。"""

from ..types import A, CharacterDefinition, T
from weiren_game.types import EngineProtocol

CHARACTER = CharacterDefinition(
    "__SLUG__",
    __NO__,
    "__NAME__",
    "TODO：一句话人设。",
    "__PRIMARY__",  # 主性格可选：__PERSONALITIES__
    "__SECONDARY__",
    __CARRY__,
    ("TODO标签",),
    actives=(A("__SLUG___skill", "主动名", "TODO：描述。"),),
)


def use_skill(engine: EngineProtocol, actor, **kwargs) -> None:
    """TODO：主动技能结算（按需使用 kwargs 的 target_id/option/amount）。"""
    engine._log(f"{engine.character(actor).name} 使用了「主动名」。")


ACTIVE_DISPATCH = {"__SLUG___skill": use_skill}

# 需要玩家选择时，内容自描述候选（前端/CLI 通用渲染）：
# def candidates(engine, actor):
#     return [{"value": ..., "label": ..., "desc": ...}]
# TARGET_OPTIONS = {"__SLUG___skill": candidates}

# 图鉴补充（可选）：
# def CODEX_EXTRA():
#     return [{"title": "标题", "entries": [("名称", "说明")]}]

# 界面头像图标（内容自声明；形状 i-av1 ~ i-av12）。
AVATAR = "__AVATAR__"
'''


def main() -> int:
    """生成模块文件并提示后续步骤。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    parser.add_argument("name")
    parser.add_argument("--carry", type=int, default=3)
    parser.add_argument("--primary", default="steady")
    parser.add_argument("--secondary", default="keen")
    args = parser.parse_args()

    slug = re.sub(r"[^a-z0-9_]", "", args.id.lower())
    if not slug:
        print("id 必须是 ascii 小写字母/数字/下划线")
        return 2
    target = ROOT / "weiren_game" / "data" / "characters" / f"{slug}.py"
    if target.exists():
        print("文件已存在：", target.relative_to(ROOT))
        return 2
    if args.primary not in PERSONALITIES or args.secondary not in PERSONALITIES:
        print("性格必须是：", "、".join(PERSONALITIES))
        return 2

    source_id = max([c.source_id for c in CHARACTERS.values()] or [0]) + 1
    avatar = f"i-av{source_id % 12 + 1}"
    text = (
        TEMPLATE.replace("__SLUG__", slug)
        .replace("__NAME__", args.name)
        .replace("__NO__", str(source_id))
        .replace("__PRIMARY__", args.primary)
        .replace("__SECONDARY__", args.secondary)
        .replace("__CARRY__", str(args.carry))
        .replace("__PERSONALITIES__", "、".join(PERSONALITIES))
        .replace("__AVATAR__", avatar)
    )
    target.write_text(text, encoding="utf-8")
    print("已生成：", target.relative_to(ROOT))
    print("source_id =", source_id, "| AVATAR =", avatar)
    print("下一步：填人设/标签/技能 → python tools/validate_content.py → 跑单测")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

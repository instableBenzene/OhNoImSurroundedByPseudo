"""脚手架：生成一个新的房客内容模块（零改核心，自动发现生效）。

用法：
    python tools/new_character.py <ascii_id> <中文名> [--carry N] [--primary KEY] [--secondary KEY]

同时把**文本**写进 `weiren_game/data/lang.py`（新的文本一律住那里，见 `AGENTS.md` §3 与各 skill）；
生成后去 lang 表把人设/标签/技能文案填好，再跑 ``python tools/validate_content.py`` 与单测。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from weiren_game.data import CHARACTERS, PERSONALITIES  # noqa: E402


TEMPLATE = '''"""房客档案：__NAME__（__NO__ 号）。"""

from ..types import A, CharacterDefinition, T
from weiren_game.types import EngineProtocol
from weiren_game.data.lang import TEXT

CHARACTER = CharacterDefinition(
    "__SLUG__",
    __NO__,
    TEXT["character.__SLUG__.name"],
    TEXT["character.__SLUG__.description"],
    "__PRIMARY__",  # 主性格可选：__PERSONALITIES__
    "__SECONDARY__",
    __CARRY__,
    (TEXT["character.__SLUG__.tag.0"],),
    actives=(A("__SLUG___skill", TEXT["ability.__SLUG___skill.name"],
               TEXT["ability.__SLUG___skill.description"]),),
)


def use_skill(engine: EngineProtocol, actor, **kwargs) -> None:
    """TODO：主动技能结算（按需使用 kwargs 的 target_id/option/amount）。"""
    engine._log(TEXT["data.characters.__SLUG__.use_skill.1"].format(
        p1=engine.character(actor).name,
        p2=TEXT["ability.__SLUG___skill.name"],
    ))


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
    added = _append_lang({
        "character.%s.name" % slug: args.name,
        "character.%s.description" % slug: "TODO：一句话人设。",
        "character.%s.tag.0" % slug: "TODO标签",
        "ability.%s_skill.name" % slug: "主动名",
        "ability.%s_skill.description" % slug: "TODO：描述。",
        "data.characters.%s.use_skill.1" % slug: "{p1} 使用了「{p2}」。",
    })
    target.write_text(text, encoding="utf-8", newline="\n")
    print("已生成：", target.relative_to(ROOT))
    print("已写入 lang：", "、".join(added) or "（键已存在，跳过）")
    print("source_id =", source_id, "| AVATAR =", avatar)
    print("下一步：到 weiren_game/data/lang.py 填好人设/标签/技能文案"
          " → python tools/validate_content.py → 跑单测")
    return 0


def _append_lang(entries: dict[str, str]) -> list[str]:
    """把新键插进 `data/lang.py` 的 `TEXT` 字典（已存在的不覆盖），返回实际写入的键。"""
    path = ROOT / "weiren_game" / "data" / "lang.py"
    source = path.read_text(encoding="utf-8")
    idx = source.rstrip().rfind("}")                 # TEXT 是文件最后一坨
    head, tail = source[:idx], source[idx:]
    added = []
    lines = []
    for key, value in entries.items():
        if '"%s"' % key in head:
            continue
        lines.append("    %s: %s," % (json.dumps(key, ensure_ascii=False),
                                      json.dumps(value, ensure_ascii=False)))
        added.append(key)
    if lines:
        path.write_text(head.rstrip() + "\n" + "\n".join(lines) + "\n" + tail,
                        encoding="utf-8", newline="\n")
    return added


if __name__ == "__main__":
    raise SystemExit(main())

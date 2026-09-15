"""分离度自检：

1) 系统层（systems/、engine.py、cli.py、web_ui.py）与前端（webui/index.html）
   不得出现具体内容名（角色/物品/地点/信息/伪人/性格），也不得硬编码内容 id。
2) 内容层（data/）不得依赖具体系统实现（不得 import weiren_game.systems）。

用法：``python tools/audit_separation.py``（退出码 0 = 通过）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from weiren_game.data import (  # noqa: E402
    CHARACTERS, ITEMS, INFORMATION_TEMPLATES, LOCATIONS, PERSONALITY_LABELS, PSEUDOS,
)

_names = set(PERSONALITY_LABELS.values())
for _collection in (CHARACTERS.values(), ITEMS.values(), PSEUDOS.values(),
                    LOCATIONS.values(), INFORMATION_TEMPLATES.values()):
    for _definition in _collection:
        _names.add(getattr(_definition, "name", ""))
CONTENT_NAMES = {name for name in _names if len(name) >= 2}

CONTENT_ID_LITERALS = re.compile(
    r'"(draw_fate|emergency_treatment|rose_recover|intent_awareness|'
    r'permission_transfer|information_collect|chaos)"'
)

SYSTEM_GLOBS = (
    "weiren_game/systems/**/*.py",
    "weiren_game/engine.py",
    "weiren_game/cli.py",
    "weiren_game/web_ui.py",
    "weiren_game/content.py",
    "weiren_game/dlc.py",
    "weiren_game/webui/index.html",
)
DATA_GLOBS = ("weiren_game/data/**/*.py",)

# 前端不得写死的"内容/机制专属文案"（可扩展；通用机制名词如"回合/搜索/印记"不在此列）。
FRONTEND_FORBIDDEN = (
    "正位", "逆位", "抽牌", "命运牌", "塔罗", "阿卡纳", "改定", "牌面", "愚者", "魔术师",
    "女祭司", "女皇", "皇帝", "教皇", "恋人", "战车", "力量", "隐者", "战车",
)
# 前端不得复算/重排"机制"（必须在后端算好下发）。
FRONTEND_FORBIDDEN_PATTERNS = (
    (r"\.tiers\s*\.\s*filter\s*\(", "前端计算羁绊档位"),
    (r"STATE\.intel\s*(\.sort|\]\.sort|\)\.slice\(\)\.sort)", "前端重排信息顺序"),
)

# 仅匹配真正的 import 语句（注释/文档串不算）
DATA_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(?:\.{0,2}systems\b|weiren_game\.systems\b)", re.M)


def _system_targets():
    for pattern in SYSTEM_GLOBS:
        yield from ROOT.glob(pattern)


def _data_targets():
    for pattern in DATA_GLOBS:
        yield from ROOT.glob(pattern)


def main() -> int:
    """返回 0 表示无问题，1 表示发现问题。"""
    problems = []
    for path in _system_targets():
        if "__pycache__" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        names = sorted(name for name in CONTENT_NAMES if name in text)
        if names:
            problems.append((path, "内容名", names))
        ids = sorted(set(CONTENT_ID_LITERALS.findall(text)))
        if ids:
            problems.append((path, "内容 id", ids))
    frontend = ROOT / "weiren_game" / "webui" / "index.html"
    if frontend.is_file():
        text = frontend.read_text(encoding="utf-8")
        words = sorted(word for word in FRONTEND_FORBIDDEN if word in text)
        if words:
            problems.append((frontend, "内容文案", words))
        logic = sorted({label for pattern, label in FRONTEND_FORBIDDEN_PATTERNS
                        if re.search(pattern, text)})
        if logic:
            problems.append((frontend, "前端机制逻辑", logic))
    for path in _data_targets():
        if "__pycache__" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        if DATA_IMPORT_RE.search(text):
            problems.append((path, "依赖 systems 实现", ["weiren_game.systems"]))
    if not problems:
        print("OK：系统/前端无内容泄漏；内容层不依赖 systems 实现。")
        return 0
    print("发现分离度问题：")
    for path, kind, hits in problems:
        print(f"  {path.relative_to(ROOT)} [{kind}] {hits}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

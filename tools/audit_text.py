"""日志文案自检：扫 `_log()` 里的字面量，只报**机械项**，不判内容好坏。

规则见 `docs/STYLE.md` §11。它只做机器能确定的事：
  - error：没有以 `。！？` 收尾；出现了 `**`（日志不用加粗）
  - warn ：估长超过上限；出现含糊词（似乎 / 好像 / 也许 / 大概）；出现 `·` 或换行

用法：``python tools/audit_text.py [--max-len 40] [--quiet]``
退出码：有 error 时 1，否则 0（方便挂进"每次改完的固定动作"）。
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN_DIRS = (ROOT / "weiren_game", ROOT / "dlc")

CALL = re.compile(r"_log\(\s*f?((?:\"[^\"]*\"|'[^']*')+)")
LITERAL = re.compile(r"\"([^\"]*)\"|'([^']*)'")
PLACEHOLDER = re.compile(r"\{[^}]*\}")

END_OK = ("\u3002", "\uff01", "\uff1f")          # 。！？
HAZY = ("\u4f3c\u4e4e", "\u597d\u50cf", "\u4e5f\u8bb8", "\u5927\u6982")   # 似乎 / 好像 / 也许 / 大概


def scan(path: pathlib.Path) -> list[tuple[str, str, str]]:
    """返回 [(等级, 说明, 原文)]；等级 ∈ {"error", "warn"}。"""
    rows: list[tuple[str, str, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for chunk in CALL.findall(text):
        literal = "".join(a or b for a, b in LITERAL.findall(chunk))
        if not literal.strip():
            continue                                  # 纯表达式（全是占位符），没有可审的文字
        estimated = len(PLACEHOLDER.sub("\u5360\u4f4d\u5360", literal))   # 占位符按 3 字估长
        if not literal.endswith(END_OK):
            rows.append(("error", "\u672a\u6536\u5c3e\uff08\u7f3a\u53e5\u53f7\uff09", literal))
        if "**" in literal:
            rows.append(("error", "\u542b\u52a0\u7c97\u6807\u8bb0 **", literal))
        if estimated > MAX_LEN:
            rows.append(("warn", "\u4f30\u957f %d\uff08>%d\uff09" % (estimated, MAX_LEN), literal))
        for word in HAZY:
            if word in literal:
                rows.append(("warn", "\u542b\u6a21\u7cca\u8bcd " + word, literal))
        if "\u00b7" in literal or "\\n" in literal:
            rows.append(("warn", "\u542b\u00b7\u6216\u6362\u884c", literal))
    return rows


def main() -> int:
    global MAX_LEN
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-len", type=int, default=40)
    parser.add_argument("--quiet", action="store_true", help="\u53ea\u8f93\u51fa\u8ba1\u6570")
    args = parser.parse_args()
    MAX_LEN = args.max_len

    errors = 0
    warns = 0
    for base in SCAN_DIRS:
        for path in sorted(base.rglob("*.py")):
            for level, why, literal in scan(path):
                if level == "error":
                    errors += 1
                else:
                    warns += 1
                if not args.quiet:
                    rel = path.relative_to(ROOT)
                    print("[%s] %s:%s  %s" % (level, rel, why, literal))
    print("\n\u65e5\u5fd7\u6587\u6848\u81ea\u68c0\uff1aerror %d\uff0cwarn %d" % (errors, warns))
    return 1 if errors else 0


MAX_LEN = 40

if __name__ == "__main__":
    sys.exit(main())

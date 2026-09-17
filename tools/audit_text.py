"""日志文案自检：扫 `_log()` 里的字面量，只报**机械项**，不判内容好坏。

规则见 `docs/STYLE.md` §11。只做机器能确定的事：
  - error：没有以 `。！？` 收尾；出现了 `**`（日志不用加粗）
  - warn ：估长超过上限；出现含糊词（似乎 / 好像 / 也许 / 大概）；出现 `·` 或换行

实现上只认可见播报 `_log(`（**不认 `_record_log(`**），并按 f-string 的**花括号深度**取字面量：
只收顶层字面量（`{…}` 里的字符串是表达式，不算正文），所以 `f"甲{x}乙{y}丙。"` 会拼成 `甲乙丙。`。
`====` / `----` 这类结构行豁免句号与换行。

用法：``python tools/audit_text.py [--max-len 40] [--quiet]``
退出码：有 error 时 1，否则 0。
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN_DIRS = (ROOT / "weiren_game", ROOT / "dlc")

# 可见播报：`_log(`，且前一个字符不是单词字符（这样 `_record_log(` 不会被命中）
CALL = re.compile(r"(?<![\w])_log\(")
STRUCT = re.compile(r"[=\-]{4,}")

END_OK = ("\u3002", "\uff01", "\uff1f")                                   # 。！？
HAZY = ("\u4f3c\u4e4e", "\u597d\u50cf", "\u4e5f\u8bb8", "\u5927\u6982")   # 似乎/好像/也许/大概
PLACEHOLDER_W = 3          # 估长时每个 `{…}` 按 3 字算


def _argument(text: str, start: int) -> str:
    """从 `(` 之后取到配对的 `)`；按深度扫描，字符串里的括号不算数。"""
    depth = 1
    quote = ""
    buf: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\":
                if i + 1 < len(text):
                    buf.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return "".join(buf)
        buf.append(ch)
        i += 1
    return "".join(buf)


OPEN = "([{"
CLOSE = ")]}"


def _parts(argument: str) -> tuple[str, int, bool]:
    """取**最外层**字面量拼成正文；返回 (正文, `{…}` 占位符个数, 最后一段是否字面量)。

    注意：f-string 的 `{}` 是**写在引号里**的，所以引号状态里也要数花括号深度
    （只在引号外数，会把 `{item.name}` 整段当正文——这正是 v1 那一批假阳性的来源）。
    """
    sentence: list[str] = []
    braces = 0
    depth = 0
    quote = ""
    last_literal = False
    i = 0
    while i < len(argument):
        ch = argument[i]
        if quote:
            if ch == "\\":
                if depth == 0:
                    sentence.append(argument[i + 1] if i + 1 < len(argument) else "")
                    last_literal = True
                i += 2
                continue
            if ch == quote:
                quote = ""
                i += 1
                continue
            if ch == "{":
                depth += 1
                if depth == 1:
                    braces += 1
                    last_literal = False
                i += 1
                continue
            if ch == "}":
                depth = max(0, depth - 1)
                i += 1
                continue
            if depth == 0:
                sentence.append(ch)
                last_literal = True
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            i += 1
            continue
        if ch in OPEN:
            depth += 1
            if ch == "{" and depth == 1:
                braces += 1
        elif ch in CLOSE:
            depth = max(0, depth - 1)
        # 字符串外的字符（f 前缀、换行、缩进、+ 号）都不是正文，不进句子
        i += 1
    return "".join(sentence).strip(), braces, last_literal


def scan(path: pathlib.Path) -> list[tuple[str, str, str]]:
    """返回 [(等级, 说明, 原文)]；等级 ∈ {"error", "warn"}。"""
    rows: list[tuple[str, str, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for match in CALL.finditer(text):
        argument = _argument(text, match.end())
        sentence, braces, last_literal = _parts(argument)
        if not sentence:
            continue                                     # 全是占位符 / 表达式，没有可审的文字
        if STRUCT.search(sentence):
            continue                                     # 结构行（回合分隔）不按句子的规则要求
        if not sentence.endswith(END_OK):
            if last_literal:
                rows.append(("error", "\u672a\u6536\u5c3e\uff08\u7f3a\u53e5\u53f7\uff09", sentence))
            else:
                rows.append(("warn", "\u7ed3\u5c3e\u662f\u53d8\u91cf\uff0c\u53e5\u53f7\u53ef\u80fd\u5728\u5b83\u91cc\uff08\u4eba\u773c\u4e00\u770b\uff09", sentence))
        if "**" in sentence:
            rows.append(("error", "\u542b\u52a0\u7c97\u6807\u8bb0 **", sentence))
        if len(sentence) + braces * PLACEHOLDER_W > MAX_LEN:
            rows.append(("warn", "\u4f30\u957f > %d" % MAX_LEN, sentence))
        for word in HAZY:
            if word in sentence:
                rows.append(("warn", "\u542b\u6a21\u7cca\u8bcd " + word, sentence))
        if "\u00b7" in sentence or "\n" in sentence:
            rows.append(("warn", "\u542b\u00b7\u6216\u6362\u884c", sentence))
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
            for level, why, sentence in scan(path):
                if level == "error":
                    errors += 1
                else:
                    warns += 1
                if not args.quiet:
                    print("[%s] %s:%s  %s" % (level, path.relative_to(ROOT), why, sentence))
    print("\n\u65e5\u5fd7\u6587\u6848\u81ea\u68c0\uff1aerror %d\uff0cwarn %d" % (errors, warns))
    return 1 if errors else 0


MAX_LEN = 40

if __name__ == "__main__":
    sys.exit(main())

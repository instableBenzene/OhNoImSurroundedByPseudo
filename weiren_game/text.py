"""风味文本的轻量标记渲染。

约定（供内容作者使用）：
- ``**加粗**``：成对双星号包裹的片段渲染为加粗；
- ``*斜体*``：成对单星号包裹的片段渲染为斜体（常用来表示对话）；
- 换行：文本中的 ``\\n`` 原样保留。

终端不支持/不需要样式时（如重定向到文件），用 :func:`strip_markup` 去掉标记；
图形界面用 :func:`segments` 取出“片段 + 样式”再套用自身标签。
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"\*\*(.+?)\*\*|(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)", re.S)
_ANSI_BOLD = "\033[1m"
_ANSI_ITALIC = "\033[3m"
_ANSI_RESET = "\033[0m"


def segments(text: str):
    """把标记文本拆成 ``(片段, bold, italic)`` 序列（不含标记本身）。"""
    position = 0
    for match in _TOKEN.finditer(text or ""):
        if match.start() > position:
            yield (text[position:match.start()], False, False)
        if match.group(1) is not None:
            yield (match.group(1), True, False)
        else:
            yield (match.group(2), False, True)
        position = match.end()
    if text and position < len(text):
        yield (text[position:], False, False)


def strip_markup(text: str) -> str:
    """去掉加粗/斜体标记，返回纯文本（保留换行）。"""
    if not text or "*" not in text:
        return text
    return "".join(part for part, _b, _i in segments(text))


def render_markup(text: str, *, ansi: bool = True) -> str:
    """把标记渲染为 ANSI 样式；``ansi=False`` 时退化为纯文本。"""
    if not text or "*" not in text:
        return text
    if not ansi:
        return strip_markup(text)
    out = []
    for part, bold, italic in segments(text):
        if bold:
            out.append(f"{_ANSI_BOLD}{part}{_ANSI_RESET}")
        elif italic:
            out.append(f"{_ANSI_ITALIC}{part}{_ANSI_RESET}")
        else:
            out.append(part)
    return "".join(out)

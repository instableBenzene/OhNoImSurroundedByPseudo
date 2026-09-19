"""核心方法总清单：把 `weiren_game/`（不含 `data/`、`webui/`）的类/函数/方法扫成一张表。

用途：**核心出问题前先看这份表**，弄清哪些是通用机制、哪些是给内容层的扩展点，
避免"为了一个罕见机制改核心"（见 `docs/DECISIONS.md` 的边界条目）。

只读。用法::

    python tools/dump_core.py            # 写入 docs/CORE.md
    python tools/dump_core.py --print    # 直接打到标准输出
"""

from __future__ import annotations

import argparse
import ast
import collections
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GROUPS = (
    ("引擎与调度", ("engine.py",)),
    ("核心系统", ("systems/",)),
    ("效果内核", ("modifier_rules.py", "probability.py", "effects/")),
    ("内容边界与包管理", ("content.py", "config.py", "dlc.py", "lifecycle.py")),
    ("数据模型与状态", ("models.py", "tenant.py", "session.py", "condition.py",
                        "global_event.py", "marks.py", "items.py", "ability.py",
                        "pseudo.py", "types.py")),
    ("交互层", ("cli.py", "web_ui.py", "ui.py", "__main__.py")),
    ("外围", ("text.py", "log_shape.py", "random_log.py", "paths.py", "exceptions.py",
              "avatars.py", "item_icons.py", "icon_files.py", "asset_layers.py",
              "resourcepack_loader.py")),
)


def _files(patterns):
    out = []
    for pattern in patterns:
        target = ROOT / "weiren_game" / pattern
        if target.is_dir():
            out.extend(sorted(p for p in target.rglob("*.py") if "__pycache__" not in str(p)))
        elif target.is_file():
            out.append(target)
    return out


def _first_line(node) -> str:
    doc = ast.get_docstring(node) or ""
    return doc.strip().splitlines()[0].strip() if doc.strip() else ""


def _signature(node) -> str:
    args = ast.unparse(node.args)
    returns = " -> %s" % ast.unparse(node.returns) if node.returns else ""
    return "(%s)%s" % (args, returns)


def _rows(tree):
    rows = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append(("", node.name, _signature(node), _first_line(node), node.lineno))
        elif isinstance(node, ast.ClassDef):
            rows.append(("", "**class %s**" % node.name, "", _first_line(node), node.lineno))
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    rows.append((node.name, sub.name, _signature(sub), _first_line(sub), sub.lineno))
    return rows


HOOK_TABLES = {
    "NODE_HOOKS", "CHARACTER_NODE_HOOKS", "CHARACTER_VALUE_HOOKS", "SCENARIO_HANDLERS",
    "HANDLERS", "MODIFIER_REGISTRY", "VALUE_HOOKS", "ITEM_HOOKS", "TAG_BEHAVIORS",
    "TURN_START_HOOKS", "HEALTH_CHANGED_HOOKS", "SEARCH_REWARD", "VALUE_HOOKS",
}


def _table_name(node) -> str:
    if isinstance(node, ast.Name) and node.id in HOOK_TABLES:
        return node.id
    if isinstance(node, ast.Attribute) and node.attr in HOOK_TABLES:
        return node.attr
    if isinstance(node, ast.Name) and (node.id.endswith("_HOOKS") or node.id.endswith("_REGISTRY")):
        return node.id
    return ""


def _extension_points():
    found = []
    for title, patterns in GROUPS:
        for path in _files(patterns):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            functions = [n for n in ast.walk(tree)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            for node in functions:
                tables: set[str] = set()
                keys: set[str] = set()
                for sub in ast.walk(node):
                    table = ""
                    if isinstance(sub, ast.Call) and sub.args:
                        table = _table_name(sub.func)
                        if not table and isinstance(sub.func, ast.Attribute):
                            table = _table_name(sub.func.value)      # `TABLE.get("节点")`
                    elif isinstance(sub, ast.Subscript):
                        table = _table_name(sub.value)
                    elif isinstance(sub, ast.Compare):
                        table = _table_name(sub.left)
                    if table:
                        tables.add(table)
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                            and sub.func.attr == "get" and sub.args \
                            and isinstance(sub.args[0], ast.Constant) \
                            and isinstance(sub.args[0].value, str):
                        keys.add(sub.args[0].value)
                if tables:
                    found.append((rel, node.name, "、".join(sorted(tables)),
                                  "、".join(sorted(keys)) or "—"))
    return sorted(found)


def _content_id_hits():
    from weiren_game.data import CHARACTERS, ITEMS, LOCATIONS, PSEUDOS  # noqa: E402

    tokens = set()
    for collection in (CHARACTERS, ITEMS, PSEUDOS, LOCATIONS):
        for key, definition in collection.items():
            tokens.add(key)
            if getattr(definition, "name", ""):
                tokens.add(definition.name)
    tokens = {t for t in tokens if len(t) >= 4}          # 短 id（如 tear）噪声太大，只查长 id
    hits = []
    for title, patterns in GROUPS:
        for path in _files(patterns):
            rel = path.relative_to(ROOT).as_posix()
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#") or '"""' in line:
                    continue
                for token in tokens:
                    quoted = '"%s"' % token
                    if quoted not in line and "'%s'" % token not in line:
                        continue
                    # 协议字段（`"chips": …`）不是内容 id，跳过。
                    import re as _re

                    if _re.search(r'["\']%s["\']\s*:' % _re.escape(token), line):
                        continue
                    if '"%s"' % token in line or "'%s'" % token in line:
                        hits.append((rel, lineno, token))
    return hits


_PLAIN_NAME = re.compile(r"[A-Za-z_]\w*\Z")


def _module_label(rel: str) -> str:
    """`weiren_game/systems/item_system.py` → `systems.item_system`（用于拼调用者全名）。"""
    text = rel
    for prefix in ("weiren_game/", "dlc/"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.endswith(".py"):
        text = text[:-3]
    return text.replace("/", ".")


def _reference_index(roots):
    """按 **AST** 扫给定目录，统计每个名字被**哪些方法**引用（注释/文档串天然不算）。

    收三类：`.名字`（属性访问，含方法调用）、裸 `名字`（调用/取值/`from x import 名字`）、
    以及**恰好等于名字**的字符串字面量（`getattr(obj, "名字")` 这类派发）。

    保守之处（**故意**）：只按名字匹配，同名的不同方法会合并计数——宁可漏报"死"，
    也不要误删。返回 `{名字: {(所在文件, 调用者全名)}}`，调用者形如
    `systems.value_system.ValueSystemMixin._restore_sanity`。
    """
    refs: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in str(path):
                continue
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            parents: dict[int, ast.AST] = {}
            for parent in ast.walk(tree):
                for child in ast.iter_child_nodes(parent):
                    parents[id(child)] = parent

            def caller(node: ast.AST) -> str:
                cur = node
                names = []
                while id(cur) in parents:
                    cur = parents[id(cur)]
                    if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        names.append(cur.name)
                inner = ".".join(reversed(names[:2]))
                return "%s.%s" % (_module_label(rel), inner or "(模块级)")

            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    refs[node.attr].add((rel, caller(node)))
                elif isinstance(node, ast.Name):
                    refs[node.id].add((rel, caller(node)))
                elif isinstance(node, ast.alias):
                    # `from x import 名字 as 别名`：**原名与别名都算引用**（只记别名会漏）。
                    refs[node.name].add((rel, _module_label(rel) + ".<import>"))
                    if node.asname:
                        refs[node.asname].add((rel, _module_label(rel) + ".<import>"))
                elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and _PLAIN_NAME.match(node.value):
                    refs[node.value].add((rel, caller(node)))
    return refs


def build_refs() -> str:
    """每个核心符号「被谁引用」的清单：0 次=死代码；≤5 次列出引用处；>5 次只记数。"""
    refs = _reference_index((ROOT / "weiren_game", ROOT / "dlc"))
    extra_refs = _reference_index((ROOT / "tools", ROOT / "tests"))
    lines = [
        "# 核心符号的引用面（`weiren_game/`，不含 `data/` 与 `webui/`）",
        "",
        "> 由 `python tools/dump_core.py --refs` 生成（生成于 %s）。**别手改**。"
        % datetime.date.today().isoformat(),
        "> 口径：**AST 扫描**——注释与 docstring 不算引用；收 `.名字` / 裸 `名字` /",
        "> `from x import 名字` / 恰好等于名字的字符串（`getattr(obj, \"名字\")` 派发）。",
        "> **只算运行时**（`weiren_game/` + `dlc/`）；`tests/` 与 `tools/` 单独标注。",
        "> `引用处` 列的是**调用者的方法名**（`模块.类.方法`，已去重、不含行号）；",
        "> **同一个文件**只表示调用者在同一个模块里（内部 helper），不是自引用。",
        "> **>5 次算高频，只记数**；0 次=可疑死代码（名字级匹配，保守）。",
        "",
        "| 文件 | 类 | 方法 | 引用数 | 同文件 | 跨文件 | 引用处（≤5 时列出） |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    dead = []
    total = 0
    for title, patterns in GROUPS:
        for path in _files(patterns):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for owner in [tree] + [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                for node in owner.body:
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    total += 1
                    sites = sorted(refs.get(node.name, ()))
                    extra = sorted(extra_refs.get(node.name, ()))
                    same = sum(1 for site_rel, _ in sites if site_rel == rel)
                    callers = sorted({name for _, name in sites})
                    extra_callers = sorted({name for _, name in extra})
                    implicit = node.name.startswith("__") and node.name.endswith("__")
                    label = "`%s`" % node.name
                    owner_name = owner.name if isinstance(owner, ast.ClassDef) else ""
                    if not sites and not implicit:
                        dead.append("%s:%d %s.%s" % (rel, node.lineno, owner_name, node.name))
                        note = ("仅被测试/工具引用：%s" % " ".join("`%s`" % s for s in extra_callers[:3])
                                if extra else "⚠️ 无引用")
                        lines.append("| `%s` | %s | %s | **0** | 0 | 0 | %s |"
                                     % (rel, owner_name, label, note))
                    elif len(sites) <= 5:
                        lines.append("| `%s` | %s | %s | %d | %d | %d | %s |"
                                     % (rel, owner_name, label, len(callers), same,
                                        len(sites) - same,
                                        "、".join("`%s`" % s for s in callers)))
                    else:
                        lines.append("| `%s` | %s | %s | %d | %d | %d | （高频，略） |"
                                     % (rel, owner_name, label, len(callers), same,
                                        len(sites) - same))
    head = "\n".join(lines[:8]).replace(
        "| 文件 |", "**合计 %d 项，其中 0 引用 %d 项。**\n\n| 文件 |" % (total, len(dead)))
    body = "\n".join(lines[8:])
    return head + "\n" + body + "\n" + _protocol_gap(refs)


def _protocol_gap(refs) -> str:
    """`EngineProtocol`（内容能碰什么的权威）与**实测内容面**的差集。

    加内容时若调了协议外的方法，这里会红：要么补进协议，要么别调。
    """
    engine_files = [ROOT / "weiren_game" / "engine.py"] + \
        sorted((ROOT / "weiren_game" / "systems").glob("*.py"))
    own: set[str] = set()
    for path in engine_files:
        if path.name == "__init__.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                own.add(node.name)
    protocol = set()
    for node in ast.walk(ast.parse((ROOT / "weiren_game" / "types.py").read_text(encoding="utf-8"))):
        if isinstance(node, ast.ClassDef) and node.name == "EngineProtocol":
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    protocol.add(sub.name)
    surface = {name for name in own
               if any(rel.startswith(("weiren_game/data/", "dlc/"))
                      for rel, _ in refs.get(name, ()))}
    missing = sorted(surface - protocol)
    extra = sorted(protocol - surface)
    out = ["## EngineProtocol vs 实测内容面", ""]
    out.append("> 协议是「内容能碰到什么引擎 API」的权威（`weiren_game/types.py`）。"
               "下面非空说明协议该更新了。")
    out.append("")
    out.append("- **内容在用、协议未声明（%d）**：%s" % (len(missing), "、".join(missing) or "无"))
    out.append("- **协议声明、内容未用（%d）**：%s" % (len(extra), "、".join(extra) or "无"))
    out.append("")
    return "\n".join(out)


def build() -> str:
    extensions = _extension_points()
    content_hits = _content_id_hits()
    lines = [
        "# 核心方法总清单（`weiren_game/`，不含 `data/` 与 `webui/`）",
        "",
        "> 由 `python tools/dump_core.py` 生成（生成于 %s）。**别手改本文件**——改代码后重跑。"
        % datetime.date.today().isoformat(),
        "> 目的：核心尽量不动。**要加内容先看 `docs/ADD_CONTENT.md` 的扩展点；"
        "只有『多处共用』的东西才考虑进核心**（判据见 `docs/PRINCIPLES.md` §二.2 与 `docs/DECISIONS.md`）。",
        "",
        "说明：`说明` 列取函数/类的 docstring 首行；`参数` 列是签名（已去注解细节）。",
        "",
    ]
    lines.append("## 扩展点：内容层往这里挂东西（%d 处）" % len(extensions))
    lines.append("")
    lines.append("> 核心**只在通用节点/注册表上派发**；内容在各处登记。"
                 "想加效果先在这里找挂点，找不到再考虑改核心。")
    lines.append("")
    lines.append("| 文件 | 函数 | 钩子表 | 节点/键 |")
    lines.append("| --- | --- | --- | --- |")
    for rel, func, table, key in extensions:
        lines.append("| `%s` | `%s` | `%s` | `%s` |" % (rel, func, table, key))
    lines.append("")
    lines.append("## 核心里的内容 id / 内容名引用（%d 处）" % len(content_hits))
    lines.append("")
    lines.append("> 正常情况下应为 0 或只剩**说明性**的注释/docstring。"
                 "出现实质引用 = 又往核心塞了专属机制（见 `docs/DECISIONS.md` 的边界条目）。")
    lines.append("")
    if content_hits:
        lines.append("| 文件 | 行 | 命中 |")
        lines.append("| --- | --- | --- |")
        for rel, lineno, hit in content_hits:
            lines.append("| `%s` | %d | `%s` |" % (rel, lineno, hit))
    else:
        lines.append("（无）")
    lines.append("")
    total = 0
    for title, patterns in GROUPS:
        files = _files(patterns)
        if not files:
            continue
        group_rows = [(path, _rows(ast.parse(path.read_text(encoding="utf-8")))) for path in files]
        count = sum(len(rows) for _, rows in group_rows)
        total += count
        lines.append("## %s（%d 项）" % (title, count))
        lines.append("")
        for path, rows in group_rows:
            rel = path.relative_to(ROOT).as_posix()
            if not rows:
                continue
            lines.append("### `%s`" % rel)
            lines.append("")
            lines.append("| 类 | 方法 | 参数 | 说明 |")
            lines.append("| --- | --- | --- | --- |")
            for owner, name, signature, doc, _ in rows:
                lines.append("| %s | `%s` | `%s` | %s |"
                             % (owner, name, signature.replace("|", "\\|"), doc.replace("|", "\\|")))
            lines.append("")
    lines.insert(5, "**合计 %d 项**（类 + 顶层函数 + 方法）。" % total)
    lines.insert(6, "")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="导出核心方法总清单")
    parser.add_argument("--print", action="store_true", help="打到标准输出而不是写文件")
    parser.add_argument("--compact", action="store_true",
                        help="紧凑版：只有「类.方法 | 说明」两列（便于贴进对话）")
    parser.add_argument("--out", default="", help="输出路径（默认 docs/CORE.md）")
    parser.add_argument("--refs", action="store_true",
                        help="生成「核心符号被谁引用」清单（默认 docs/CORE_REFS.md）")
    args = parser.parse_args()
    if args.refs:
        text = build_refs()
        out = pathlib.Path(args.out) if args.out else ROOT / "docs" / "CORE_REFS.md"
        out.write_text(text, encoding="utf-8", newline="\n")
        print("-> %s (%d lines)" % (out, text.count("\n")))
        return 0
    if args.compact:
        lines = []
        for title, patterns in GROUPS:
            files = _files(patterns)
            if not files:
                continue
            lines.append("## %s" % title)
            lines.append("")
            for path in files:
                rows = _rows(ast.parse(path.read_text(encoding="utf-8")))
                if not rows:
                    continue
                lines.append("**`%s`**" % path.relative_to(ROOT).as_posix())
                lines.append("")
                lines.append("| 方法 | 说明 |")
                lines.append("| --- | --- |")
                for owner, name, _sig, doc, _lineno in rows:
                    label = ("%s.%s" % (owner, name)) if owner else name
                    lines.append("| `%s` | %s |" % (label, doc.replace("|", "\\|")[:40]))
                lines.append("")
        text = "\n".join(lines) + "\n"
    else:
        text = build()
    if args.print:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(text)
        return 0
    out = pathlib.Path(args.out) if args.out else ROOT / "docs" / "CORE.md"
    out.write_text(text, encoding="utf-8", newline="\n")
    print("-> %s (%d lines)" % (out, text.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

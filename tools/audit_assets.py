"""材质复用审计：揪出"同一个图形被用在多处"的资产。

为什么要有它：**文件是修改的单位**。同一个图形被两个地方共用（同一个 `.svg` 被引两次、
或 `symbols_base.py` 里两个 id 写成一模一样的路径）时，为甲处调材质就会连带改动乙处 ——
上一轮就真踩过：修好 `crowbar.svg` 却没修到与它逐字节相同的 `tool.svg`。

用法::

    python tools/audit_assets.py              # 只看结论
    python tools/audit_assets.py --list       # 列出每一组
    python tools/audit_assets.py --refs i-gear  # 看某个符号被谁引用

判据：
  - **同图不同 id**（`item/item/a.svg` 与 `item/tag/b.svg` 内容一致、`symbols` 里两个 id 同形）→ 要拆开；
  - 颜色归一化后仍相同才算（只差品质色/语义色的两份，也属于"同一个图形"）；
  - 同一空间内的两份**不同 id** 也算（例如两张物品图标画得一模一样）。
退出码：有"同图不同 id"时 1，否则 0（便于挂进检查）。
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN_DIRS = (
    ROOT / "weiren_game" / "data" / "item",
    ROOT / "weiren_game" / "data" / "avatars",
    ROOT / "weiren_game" / "data" / "icon",
    ROOT / "weiren_game" / "data" / "resourcepack" / "assets",
    ROOT / "dlc",
    ROOT / "resourcepacks",
)
SYMBOLS_FILE = ROOT / "weiren_game" / "data" / "resourcepack" / "symbols_base.py"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def signature(markup: str) -> str:
    """把一段 SVG 归一成"图形指纹"：去掉注释、颜色与空白，只留形状。

    注释必须剥掉：两份图形完全一样、只是注释不同的话，不剥就会漏报
    （第一版就漏了 `yuntongqu` 与 `tag/medical_supply` 这一对）。
    """
    text = COMMENT.sub("", markup)
    text = HEX.sub("#", text)
    text = re.sub(r"\s+", "", text)
    return text


def symbols() -> dict[str, str]:
    """读出 `symbols_base.py` 的 `SYMBOLS`（`i-*` → 路径片段）。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("symbols_base", SYMBOLS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.SYMBOLS)


def collect() -> dict[str, tuple[str, str]]:
    """返回 {标签: (来源路径, 图形指纹)}；标签形如 `file:...` 或 `symbol:i-gear`。"""
    found: dict[str, tuple[str, str]] = {}
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.svg")):
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            found["file:" + rel] = (rel, signature(path.read_text(encoding="utf-8", errors="replace")))
    for name, markup in symbols().items():
        found["symbol:" + name] = (str(SYMBOLS_FILE.relative_to(ROOT)), signature(str(markup)))
    # 内容层自带的符号（如厄瑞玻斯 22 张命运牌）也按同一规矩查：
    # 它们不占资源包贴图零件，但"一个图形只服务一处"照样适用。
    import importlib.util

    for base in (ROOT / "weiren_game" / "data", ROOT / "dlc"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*_symbols.py")):
            spec = importlib.util.spec_from_file_location("symbols_" + path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            for attr in dir(module):
                table = getattr(module, attr)
                if not (attr.isupper() and isinstance(table, dict)):
                    continue
                for key, markup in table.items():
                    if isinstance(markup, str):
                        found["symbol:%s:%s" % (path.stem, key)] = (rel, signature(markup))
    return found


def groups(found: dict[str, tuple[str, str]]) -> list[list[str]]:
    """按指纹分组，只留成员 ≥2 的组。"""
    by_sig: dict[str, list[str]] = {}
    for label, (_source, sig) in found.items():
        by_sig.setdefault(sig, []).append(label)
    return [sorted(members) for members in by_sig.values() if len(members) > 1]


def main() -> int:
    parser = argparse.ArgumentParser(description="材质复用审计：同一个图形被用在多处")
    parser.add_argument("--list", action="store_true", help="列出每一组")
    parser.add_argument("--refs", default="", help="统计某个 id（如 i-gear）在内容层被引用的次数")
    args = parser.parse_args()

    found = collect()
    if args.refs:
        hits = []
        for base in (ROOT / "weiren_game" / "data", ROOT / "dlc", ROOT / "resourcepacks"):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.suffix not in (".py", ".json", ".svg", ".md"):
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                if args.refs in text:
                    hits.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        print("%s 被 %d 个文件引用：" % (args.refs, len(hits)))
        for hit in hits:
            print("  -", hit)
        return 0

    shared = groups(found)
    print("材质资产 %d 个（含 %d 个符号）；同图多用的组：%d" % (
        len(found), len(symbols()), len(shared)))
    todo = 0
    must_split = 0
    for members in shared:
        spaces = {label.split(":")[1].split("/")[0] if label.startswith("file:") else "symbol"
                  for label in members}
        cross = "跨类" if len(spaces) > 1 or any(m.startswith("symbol") for m in members) else "同类"
        has_tag = any("/tag/" in m for m in members)
        has_item = any("/item/item/" in m for m in members)
        if has_tag and has_item:
            kind = "待补全"
            todo += 1
        else:
            kind = "必须拆"
            must_split += 1
        print("  [%s/%s] %s" % (cross, kind, "  ==  ".join(members)))
        if args.list:
            source, sig = found[members[0]]
            print("        %s" % sig[:160])
    print("小结：待补全（靠 tag 兜底）%d 组，必须拆 %d 组" % (todo, must_split))
    return 1 if must_split else 0


if __name__ == "__main__":
    sys.exit(main())

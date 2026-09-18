"""把技能正文导出成 JSON，供排版复核（配合 `tools/render_text_sheet.mjs`）。

为什么要有它：图鉴/技能正文是**玩家会认真读**的长文本，而且改的是"版面"不是"数据"——
写完必须按真实渲染看一眼。导出时**直接导入内容层**，不手抄：
手抄的清单会在源码改动后变成过期数据（这条踩过）。

用法::

    python tools/dump_codex_text.py                    # 全部技能
    python tools/dump_codex_text.py --long 60 --out D:\\tmp\\texts.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from weiren_game.config import CONFIG  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="导出技能正文（含 chips）供渲染复核")
    parser.add_argument("--long", type=int, default=60, help="只导出超过这个字数的（0 = 全部）")
    parser.add_argument("--out", default="", help="输出 JSON 路径（默认系统临时目录）")
    args = parser.parse_args()

    CONFIG.pack_order = ["base"]
    CONFIG.resourcepack_order = ["base"]
    CONFIG.enabled_dlc = []

    from weiren_game.data import CHARACTER_MODULES

    rows = []
    for character_id, module in sorted(CHARACTER_MODULES.items()):
        # 角色模块暴露的是 `CHARACTER`（CharacterDefinition）——别猜，先 dir()。
        definition = getattr(module, "CHARACTER", None)
        if definition is None:
            continue
        for ability in (*definition.actives, *definition.passives):
            rows.append({
                "module": character_id,
                "character": definition.name,
                "ability_id": getattr(ability, "ability_id", ""),
                "ability": ability.name,
                "text": ability.description,
                "chips": list(getattr(ability, "chips", ()) or ()),
            })

    if args.long:
        rows = [row for row in rows if len(row["text"]) > args.long]
    out = pathlib.Path(args.out) if args.out else (
        pathlib.Path(__import__("tempfile").gettempdir()) / "weiren-codex-texts.json")
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rows=%d long=%d -> %s" % (len(rows), args.long, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

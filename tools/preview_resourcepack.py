"""把一个资源包渲染成 PNG，供人（和 AI）直接看：封面+标题、物品图标、头像。

用法::

    python tools/preview_resourcepack.py night_ward
    python tools/preview_resourcepack.py blood_moon --out D:\\tmp\\shots

产物（默认写到系统临时目录 `weiren-preview/<包名>/`）：
    view_bg.png      背景素材 + 标题素材（叠在一起看构图与对比度）
    view_bgplain.png 只有背景（不被标题挡住）
    view_items.png   包内所有 `item/item/*.svg` 的联络表（按品质色轮换着色）
    view_avatars.png 包内头像 vs base 立绘对照
    view_big.png     包内头像放大（看细节）

为什么有这个工具：贴图/图标这种东西**只看代码不算验证**。渲染出来自己读一遍，
一轮几乎总能抓到硬伤（写错的数字、压过界的标题、糊掉的形状）。
需要 Edge；只读资源，不改游戏状态。
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EDGE_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/microsoft-edge",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
QUALITY_COLORS = ["#8a8f8c", "#4f8f6d", "#4a7fb5", "#8a6bb5", "#b5544f"]


def find_edge() -> str:
    """找一个能用的 Edge/Chromium 可执行文件。"""
    for path in EDGE_CANDIDATES:
        if pathlib.Path(path).exists():
            return path
    raise SystemExit("找不到 Edge/Chromium；用 --edge 指定路径")


def page(body: str) -> str:
    """套一层统一外壳：暗底 + 卡片 + 联络表版式。"""
    return (
        "<!doctype html><meta charset='utf-8'>"
        "<style>:root{--ink:#dfe8e6;--ink-hi:#f4fbfa}"
        "body{margin:0;background:#0f1314;font-family:monospace}"
        ".bg{position:fixed;inset:0;width:100%;height:100%;object-fit:cover}"
        ".sheet{display:flex;flex-wrap:wrap;gap:18px;padding:24px}"
        ".cell{background:#191f20;border:1px solid #333c3c;border-radius:8px;padding:10px;text-align:center}"
        ".cell svg{width:96px;height:96px}.cap{color:#a2acaa;font-size:11px;margin-top:6px}"
        "</style><body>" + body + "</body>"
    )


def render(edge: str, work: pathlib.Path, name: str, markup: str, size: tuple[int, int]) -> pathlib.Path:
    """把一段 HTML 渲成 PNG，返回图片路径。"""
    html_path = work / ("view_%s.html" % name)
    html_path.write_text(markup, encoding="utf-8")
    png = work / ("view_%s.png" % name)
    subprocess.run(
        [edge, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
         "--force-device-scale-factor=1", "--window-size=%d,%d" % size,
         "--screenshot=%s" % png, html_path.as_uri()],
        capture_output=True, timeout=120,
    )
    return png


def main() -> int:
    parser = argparse.ArgumentParser(description="把资源包渲染成 PNG 供肉眼复核")
    parser.add_argument("pack", help="resourcepacks/ 下的包名")
    parser.add_argument("--out", default="", help="输出目录（默认系统临时目录）")
    parser.add_argument("--edge", default="", help="Edge/Chromium 可执行文件路径")
    args = parser.parse_args()

    edge = args.edge or find_edge()
    pack = ROOT / "resourcepacks" / args.pack
    if not pack.is_dir():
        raise SystemExit("没有这个资源包：%s" % pack)

    work = pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.gettempdir()) / "weiren-preview" / args.pack
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    # 素材拷成 ASCII 路径（file:// 遇中文路径容易出问题）
    assets: dict[str, str] = {}
    for path in sorted((pack / "assets").glob("*.svg")):
        shutil.copy(path, work / path.name)
        assets[path.stem] = path.name
    for path in sorted((pack / "item" / "item").glob("*.svg")):
        shutil.copy(path, work / ("item_" + path.name))
    for path in sorted((pack / "avatars" / "characters").glob("*.svg")):
        shutil.copy(path, work / ("pack_" + path.name))
    for path in sorted((ROOT / "weiren_game" / "data" / "avatars" / "characters").glob("*.svg")):
        if (pack / "avatars" / "characters" / path.name).exists():
            shutil.copy(path, work / ("base_" + path.name))
            break
    base_portrait = next(
        (path.name for path in sorted((ROOT / "weiren_game" / "data" / "avatars" / "characters").glob("*.svg"))
         if (pack / "avatars" / "characters" / path.name).exists()),
        "",
    )

    sheets: dict[str, tuple[str, tuple[int, int]]] = {}
    if "background" in assets:
        body = "<img class='bg' src='%s'>" % assets["background"]
        sheets["bgplain"] = (page(body), (1600, 900))
        if "title" in assets:
            body += ("<img class='bg' src='%s' style='object-fit:contain;"
                     "object-position:50% 12%%;height:46%%'>" % assets["title"])
        sheets["bg"] = (page(body), (1600, 900))

    items = sorted(path.stem for path in (pack / "item" / "item").glob("*.svg"))
    if items:
        cells = []
        for index, item in enumerate(items):
            markup = (work / ("item_" + item + ".svg")).read_text(encoding="utf-8")
            markup = markup.replace("#d7ddd2", "currentColor")
            markup = markup.replace("#a77ad1", QUALITY_COLORS[index % len(QUALITY_COLORS)])
            markup = markup.replace("<svg ", "<svg style='color:#dfe8e6' ", 1)
            cells.append("<div class='cell'>%s<div class='cap'>%s</div></div>" % (markup, item))
        sheets["items"] = (page("<div class='sheet'>" + "".join(cells) + "</div>"), (1000, 780))

    avatars = sorted(path.name for path in (pack / "avatars" / "characters").glob("*.svg"))
    if avatars:
        cells = []
        if base_portrait:
            cells.append(("<div class='cell'>%s<div class='cap'>base %s</div></div>" % (
                (work / ("base_" + base_portrait)).read_text(encoding="utf-8").replace(
                    "<svg ", "<svg style='width:220px;height:220px' ", 1), base_portrait)))
        for name in avatars:
            cells.append("<div class='cell'>%s<div class='cap'>%s</div></div>" % (
                (work / ("pack_" + name)).read_text(encoding="utf-8").replace(
                    "<svg ", "<svg style='width:220px;height:220px' ", 1), name))
        sheets["avatars"] = (page("<div class='sheet'>" + "".join(cells) + "</div>"), (860, 400))
        big = []
        for name in avatars:
            big.append("<div class='cell'>%s<div class='cap'>%s</div></div>" % (
                (work / ("pack_" + name)).read_text(encoding="utf-8").replace(
                    "<svg ", "<svg style='width:300px;height:300px' ", 1), name))
        sheets["big"] = (page("<div class='sheet'>" + "".join(big) + "</div>"), (860, 420))

    for name, (markup, size) in sheets.items():
        png = render(edge, work, name, markup, size)
        print("%-10s %s (%d bytes)" % (name, png, png.stat().st_size if png.exists() else 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

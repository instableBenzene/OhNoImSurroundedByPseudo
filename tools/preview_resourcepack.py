"""把一个资源包渲染成 PNG，供人（和 AI）直接看：封面+标题、物品图标、头像。

用法::

    python tools/preview_resourcepack.py night_ward
    python tools/preview_resourcepack.py blood_moon --out D:\\tmp\\shots
    python tools/preview_resourcepack.py base          # 内置材质（content 层）也照这个流程看

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


def _symbol_sheet(work: pathlib.Path, symbols: dict[str, str]) -> tuple[str, tuple[int, int]]:
    """把 `SYMBOLS`（`i-*` 贴图零件）铺成联络表：24×24 viewBox，放大到 72px 看轮廓。"""
    cells = []
    for name in sorted(symbols):
        markup = "%s" % symbols[name]
        cells.append(
            "<div class='cell'><svg viewBox='0 0 24 24' style='width:72px;height:72px;color:#dfe8e6'"
            " fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round'"
            " stroke-linejoin='round'>%s</svg><div class='cap'>%s</div></div>" % (markup, name)
        )
    size = (1180, 240 + 120 * (len(cells) // 13))
    return page("<div class='sheet'>" + "".join(cells) + "</div>"), size


def _file_sheet(work: pathlib.Path, paths: list[pathlib.Path], prefix: str,
                box: int = 96) -> tuple[str, tuple[int, int]]:
    """把一批 svg 文件铺成联络表（每格按 box 像素渲染，标签写文件名）。"""
    cells = []
    for path in paths:
        markup = (work / (prefix + path.name)).read_text(encoding="utf-8")
        markup = markup.replace("<svg ", "<svg style='width:%dpx;height:%dpx;color:#dfe8e6' " % (box, box), 1)
        cells.append("<div class='cell'>%s<div class='cap'>%s</div></div>" % (markup, path.stem))
    size = (1180, 260 + (box + 60) * max(1, len(cells) // 10))
    return page("<div class='sheet'>" + "".join(cells) + "</div>"), size


def _base_sheets(work: pathlib.Path) -> dict[str, tuple[str, tuple[int, int]]]:
    """base（content 层）的材质联络表：贴图零件、头像零件/立绘、物品与标签图标、封面。"""
    data = ROOT / "weiren_game" / "data"
    sheets: dict[str, tuple[str, tuple[int, int]]] = {}

    for path in sorted((data / "resourcepack" / "assets").glob("*.svg")):
        shutil.copy(path, work / ("cover_" + path.name))
    cover = {path.stem for path in (data / "resourcepack" / "assets").glob("*.svg")}
    if "background" in cover:
        body = "<img class='bg' src='cover_background.svg'>"
        sheets["bgplain"] = (page(body), (1600, 900))
        if "title" in cover:
            body += ("<img class='bg' src='cover_title.svg' style='object-fit:contain;"
                     "object-position:50%% 12%%;height:46%%'>")
        sheets["bg"] = (page(body), (1600, 900))

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "symbols_base", data / "resourcepack" / "symbols_base.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sheets["symbols"] = _symbol_sheet(work, module.SYMBOLS)
    except Exception as exc:  # noqa: BLE001 - 缺这份表就跳过
        print("symbols skipped:", exc)

    for section in ("shapes", "features", "characters"):
        directory = data / "avatars" / section
        if not directory.is_dir():
            continue
        paths = sorted(directory.glob("*.svg"))
        for path in paths:
            shutil.copy(path, work / ("av_" + path.name))
        box = 84 if section != "characters" else 96
        sheets["avatar_" + section] = _file_sheet(work, paths, "av_", box)

    for section in ("item", "tag"):
        directory = data / "item" / section
        if not directory.is_dir():
            continue
        paths = sorted(directory.glob("*.svg"))
        for path in paths:
            shutil.copy(path, work / ("ic_" + path.name))
        sheets["item_" + section] = _file_sheet(work, paths, "ic_", 72)
    return sheets


def main() -> int:
    parser = argparse.ArgumentParser(description="把资源包渲染成 PNG 供肉眼复核")
    parser.add_argument("pack", help="resourcepacks/ 下的包名")
    parser.add_argument("--out", default="", help="输出目录（默认系统临时目录）")
    parser.add_argument("--edge", default="", help="Edge/Chromium 可执行文件路径")
    parser.add_argument("--zoom", default="",
                        help="只渲这几张（base 模式：立绘/零件文件名，逗号分隔），配合 --box 放大看细节")
    parser.add_argument("--box", type=int, default=96, help="头像/图标格子的像素边长（默认 96）")
    args = parser.parse_args()

    edge = args.edge or find_edge()
    is_base = args.pack == "base"
    pack = (ROOT / "weiren_game" / "data") if is_base else (ROOT / "resourcepacks" / args.pack)
    if not pack.is_dir():
        raise SystemExit("没有这个包：%s" % pack)

    work = pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.gettempdir()) / "weiren-preview" / args.pack
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    if is_base:
        sheets = _base_sheets(work)
        if args.zoom:
            wanted = {name.strip() for name in args.zoom.split(",") if name.strip()}
            zoom_paths = []
            for section in ("characters", "shapes", "features"):
                for path in sorted((pack / "avatars" / section).glob("*.svg")):
                    if path.stem in wanted:
                        shutil.copy(path, work / ("av_" + path.name))
                        zoom_paths.append(path)
            for section in ("item", "tag"):
                for path in sorted((pack / "item" / section).glob("*.svg")):
                    if path.stem in wanted:
                        shutil.copy(path, work / ("ic_" + path.name))
                        zoom_paths.append(path)
            if zoom_paths:
                prefix = "av_" if zoom_paths[0].parent.name in ("characters", "shapes", "features") else "ic_"
                sheets = {"zoom": _file_sheet(work, zoom_paths, prefix, args.box)}
        for name, (markup, size) in sheets.items():
            png = render(edge, work, name, markup, size)
            print("%-16s %s (%d bytes)" % (name, png, png.stat().st_size if png.exists() else 0))
        return 0

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
                     "object-position:50%% 12%%;height:46%%'>" % assets["title"])
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

"""把本作品打成可静态托管的浏览器版本（VibeHub 用）。

引擎是纯标准库 Python，所以在页面里用 Pyodide（CPython→WebAssembly）跑，
前端原本请求的 /api/* 改成直接调用 Python。产物顶层有 index.html，
可以直接交给官方 CLI：

    python3 tools/build_vibehub.py --out dist
    vibehub deploy --dir dist ...

只读源码：所有改动都发生在输出目录里的副本上，仓库本身不受影响。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools" / "vibehub"

PYODIDE_VERSION = "314.0.7"
PYODIDE_FILES = (
    "pyodide.mjs",
    "pyodide.asm.mjs",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
)

# 产物里 python 源码树的根（浏览器内挂到 /app）。
APP_DIRNAME = "app"
SKIP_DIRS = {"__pycache__", "webui"}

SDK_URL = "https://vibe.lumigrav.space/sdk/v3/vibehub.js"


def fail(message: str) -> None:
    print("BUILD FAILED:", message, file=sys.stderr)
    raise SystemExit(1)


def patch(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            fail(f"锚点命中 {count} 次（应为 1 次）：{path}\n---\n{old[:200]}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def copy_tree(src: Path, dst: Path) -> None:
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = Path(base).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            if name.endswith((".pyc", ".pyo")):
                continue
            shutil.copy2(Path(base) / name, dst / rel / name)


def fetch_pyodide(cache_dir: Path, explicit: Path | None) -> Path:
    """本地没有 Pyodide 时从 npm registry 拉官方发行包并解压到缓存目录。"""
    if explicit is not None:
        if not (explicit / "pyodide.mjs").is_file():
            fail(f"--pyodide-dir 里没有 pyodide.mjs：{explicit}")
        return explicit
    target = cache_dir / f"pyodide-{PYODIDE_VERSION}"
    if (target / "pyodide.mjs").is_file():
        return target
    cache_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE_VERSION}.tgz"
    print(f"downloading {url}")
    archive = cache_dir / f"pyodide-{PYODIDE_VERSION}.tgz"
    with urllib.request.urlopen(url, timeout=300) as resp, archive.open("wb") as out:
        shutil.copyfileobj(resp, out)
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            name = Path(member.name).name
            if member.isfile() and name in PYODIDE_FILES:
                member.name = name
                tar.extract(member, target)
    archive.unlink(missing_ok=True)
    missing = [n for n in PYODIDE_FILES if not (target / n).is_file()]
    if missing:
        fail("Pyodide 发行包缺少文件：" + ", ".join(missing))
    return target


def loader_html() -> str:
    return f'''<script src="{SDK_URL}"></script>
<style>
/* 中文随作品打包（assets/fonts/ 是 Noto Sans SC 的子集）：不依赖玩家设备系统字体。 */
@font-face{{font-family:"Weiren Sans";src:url("fonts/weiren-sans-regular.woff2") format("woff2");
  font-weight:400;font-style:normal;font-display:swap}}
@font-face{{font-family:"Weiren Sans";src:url("fonts/weiren-sans-bold.woff2") format("woff2");
  font-weight:700;font-style:normal;font-display:swap}}
</style>
<div id="vhBoot" style="position:fixed;inset:0;z-index:9999;display:flex;align-items:center;
justify-content:center;background:#12100e;color:#e8e2d6;font:14px/1.9 system-ui,sans-serif;text-align:center">
<div><div style="font-size:15px;letter-spacing:.08em">《完蛋，我被伪人包围了！？》</div>
<div id="vhBootMsg" style="opacity:.72;margin-top:8px">正在准备浏览器引擎…</div>
<div style="opacity:.45;margin-top:6px;font-size:12px">首次打开需下载运行文件，之后会走浏览器缓存</div></div></div>
<script>
window.__vhReady = (async function(){{
  const msg = function(t){{ const el=document.getElementById("vhBootMsg"); if(el) el.textContent=t; }};
  try{{
    const m = await import("./bridge.js");
    await m.start(msg);
  }}catch(e){{
    const el = document.getElementById("vhBoot");
    if (el) el.innerHTML = '<div style="max-width:620px;padding:0 20px">浏览器引擎启动失败'
      + '<div style="opacity:.7;margin-top:10px;font-size:12px;word-break:break-all">'
      + String(e && e.message ? e.message : e) + '</div></div>';
    throw e;
  }}
}})();
</script>
'''


def patch_sources(app: Path) -> None:
    """把三处"后端 URL"改成内联 data URL，并让中文走作品自带的字体。"""
    shutil.copy2(TOOLS / "static_assets.py", app / "weiren_game" / "static_assets.py")
    shutil.copy2(TOOLS / "vibehub_bridge.py", app / "vibehub_bridge.py")

    patch(app / "weiren_game" / "icon_files.py", [(
        '''def icon_url(section: str, icon_id: str, *, dlc_root: str | Path | None = None,
             rp_root: str | Path | None = None) -> str:
    """图标的 URL（找不到返回空串，界面回退内置单线图标）。"""
    if resolve_icon(section, icon_id, dlc_root=dlc_root, rp_root=rp_root) is None:
        return ""
    return f"/api/icon/{section}/{icon_id}"''',
        '''def icon_url(section: str, icon_id: str, *, dlc_root: str | Path | None = None,
             rp_root: str | Path | None = None) -> str:
    """浏览器版本：图标内联为 data URL（页面里没有后端可以请求）。"""
    from .static_assets import data_url_for

    return data_url_for(resolve_icon(section, icon_id, dlc_root=dlc_root, rp_root=rp_root))''',
    )])

    patch(app / "weiren_game" / "avatars.py", [
        (
            "import re\nfrom pathlib import Path\n",
            "import re\nfrom pathlib import Path\n\nfrom .static_assets import data_url_for\n",
        ),
        (
            '        return {"full": f"/api/avatar/{SECTION_CHARACTERS}/{character_id}"}',
            '        return {"full": data_url_for(full)}',
        ),
        (
            '    shape = f"/api/avatar/{SECTION_SHAPES}/{shape_id}" if shape_id in index[SECTION_SHAPES] else ""',
            '    shape = data_url_for(index[SECTION_SHAPES][shape_id]) if shape_id in index[SECTION_SHAPES] else ""',
        ),
        (
            '''    feature = (
        f"/api/avatar/{SECTION_FEATURES}/{feature_id}"
        if feature_id in index[SECTION_FEATURES] else ""
    )''',
            '''    feature = (
        data_url_for(index[SECTION_FEATURES][feature_id])
        if feature_id in index[SECTION_FEATURES] else ""
    )''',
        ),
    ])

    patch(app / "weiren_game" / "data" / "resourcepack" / "__init__.py", [(
        '''def register_assets(assets: object, *, pack: str = "") -> None:
    """登记素材位：``ASSETS = {"background": "moon.svg"}`` → 文件在 ``<包目录>/assets/moon.svg``。"""
    for kind, filename in dict(assets or {}).items():
        RESOURCE_ASSETS[str(kind)] = (
            f"{ASSET_URL_PREFIX}?pack={quote(str(pack))}&file={quote(str(filename))}"
        )''',
        '''def register_assets(assets: object, *, pack: str = "") -> None:
    """浏览器版本：素材位文件内联为 data URL（页面里没有后端可以请求）。"""
    from ...static_assets import pack_asset_data_url

    for kind, filename in dict(assets or {}).items():
        RESOURCE_ASSETS[str(kind)] = pack_asset_data_url(str(pack), str(filename))''',
    )])


def main() -> int:
    parser = argparse.ArgumentParser(description="把作品打成 VibeHub 用的静态站点")
    parser.add_argument("--out", default="dist", help="输出目录（默认 dist）")
    parser.add_argument("--pyodide-dir", default=None,
                        help="已有 Pyodide 发行目录（默认从 npm registry 下载并缓存）")
    parser.add_argument("--cache-dir", default=None, help="Pyodide 下载缓存目录")
    args = parser.parse_args()

    out = (REPO / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    cache = Path(args.cache_dir) if args.cache_dir else Path(
        os.environ.get("VIBEHUB_BUILD_CACHE") or (Path(tempfile.gettempdir()) / "vibehub-build")
    )

    if not (REPO / "weiren_game" / "webui" / "index.html").is_file():
        fail(f"看起来不在仓库根目录：{REPO}")
    font_dir = REPO / "assets" / "fonts"
    for name in ("weiren-sans-regular.woff2", "weiren-sans-bold.woff2"):
        if not (font_dir / name).is_file():
            fail(f"缺少随作品打包的字体：{font_dir / name}")

    pyodide = fetch_pyodide(cache, Path(args.pyodide_dir) if args.pyodide_dir else None)

    if out.exists():
        shutil.rmtree(out)
    app = out / APP_DIRNAME
    app.mkdir(parents=True)

    # 1. Python 源码树（副本；剔除前端与缓存）
    for name in ("weiren_game", "dlc", "resourcepacks"):
        copy_tree(REPO / name, app / name)
    shutil.copy2(REPO / "game_config.json", app / "game_config.json")

    # 2. 后端 URL → 内联 data URL
    patch_sources(app)

    # 3. 前端与启动器
    shutil.copy2(REPO / "weiren_game" / "webui" / "index.html", out / "index.html")
    shutil.copy2(TOOLS / "bridge.js", out / "bridge.js")
    (out / "fonts").mkdir()
    for name in ("weiren-sans-regular.woff2", "weiren-sans-bold.woff2"):
        shutil.copy2(font_dir / name, out / "fonts" / name)

    patch(out / "index.html", [
        # 启动器（含 SDK、@font-face 与 Pyodide 引导）插在主脚本之前
        ("<script>", loader_html() + "<script>"),
        # 中文优先用作品自带字体；其余仍是原来的系统字体链
        ('--mono:Consolas,"Cascadia Mono","Courier New",monospace;',
         '--mono:Consolas,"Cascadia Mono","Courier New","Weiren Sans",monospace;'),
        ('--sans:"Microsoft YaHei UI","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif;',
         '--sans:"Weiren Sans","Microsoft YaHei UI","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif;'),
        ('--serif:"STKaiti","KaiTi",serif;', '--serif:"Weiren Sans","STKaiti","KaiTi",serif;'),
        ('--px-font:"Zpix","Fusion Pixel 12px","Minecraft","SimSun","Microsoft YaHei UI",monospace;',
         '--px-font:"Zpix","Fusion Pixel 12px","Minecraft","SimSun","Weiren Sans","Microsoft YaHei UI",monospace;'),
        ('--hei:"Microsoft YaHei UI","Microsoft YaHei","SimHei","PingFang SC","Noto Sans CJK SC",sans-serif;',
         '--hei:"Weiren Sans","Microsoft YaHei UI","Microsoft YaHei","SimHei","PingFang SC",sans-serif;'),
        # /api/* 走页面内的 Python 引擎
        (
            '''async function api(path, body){
  const resp = await fetch(path, {method: body?"POST":"GET", headers:{"Content-Type":"application/json"}, body: body?JSON.stringify(body):undefined});
  return resp.json();
}''',
            '''async function api(path, body){
  /* 浏览器版本：规则引擎跑在本页的 WebAssembly 里，/api/* 直接调 Python。 */
  if(window.vhApi) return window.vhApi(body?"POST":"GET", path, body||null);
  const resp = await fetch(path, {method: body?"POST":"GET", headers:{"Content-Type":"application/json"}, body: body?JSON.stringify(body):undefined});
  return resp.json();
}''',
        ),
        # 导出走后端同一份逻辑，结果落成 Blob
        (
            '''function downloadUrl(url){
  const a=document.createElement("a"); a.href=url; a.download=""; a.rel="noopener";
  document.body.appendChild(a); a.click(); a.remove();
}''',
            '''function downloadUrl(url){
  /* 浏览器版本：导出仍用同一份后端逻辑，只是把结果落成 Blob。 */
  if(window.vhExport){
    const text = window.vhExport(url);
    const blob = new Blob([text], {type:"text/plain;charset=utf-8"});
    const href = URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=href; a.download="weiren_log.txt"; a.rel="noopener";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(href), 15000);
    return;
  }
  const a=document.createElement("a"); a.href=url; a.download=""; a.rel="noopener";
  document.body.appendChild(a); a.click(); a.remove();
}''',
        ),
        # 等引擎就绪再启动界面
        (
            "(async function boot(){\n  await loadLang();",
            '''(async function boot(){
  /* 浏览器版本：等 WebAssembly 引擎就绪后再取语言表 / 资源包。 */
  if(window.__vhReady){
    try{ await window.__vhReady; }
    catch(e){ console.error("引擎初始化失败", e); return; }
  }
  await loadLang();''',
        ),
    ])

    # 资源包的主题 token 同样优先用自带字体
    patch(app / "weiren_game" / "data" / "resourcepack" / "theme.py", [
        ('"--mono": \'Consolas,"Cascadia Mono","Courier New",monospace\',',
         '"--mono": \'Consolas,"Cascadia Mono","Courier New","Weiren Sans",monospace\','),
        ('"--sans": \'"Microsoft YaHei UI","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif\',',
         '"--sans": \'"Weiren Sans","Microsoft YaHei UI","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif\','),
        ('"--serif": \'"STKaiti","KaiTi",serif\',',
         '"--serif": \'"Weiren Sans","STKaiti","KaiTi",serif\','),
        ('"--px-font": \'"Zpix","Fusion Pixel 12px","Minecraft","SimSun","Microsoft YaHei UI",monospace\',',
         '"--px-font": \'"Zpix","Fusion Pixel 12px","Minecraft","SimSun","Weiren Sans","Microsoft YaHei UI",monospace\','),
        ('"--hei": \'"Microsoft YaHei UI","Microsoft YaHei","SimHei","PingFang SC","Noto Sans CJK SC",sans-serif\',',
         '"--hei": \'"Weiren Sans","Microsoft YaHei UI","Microsoft YaHei","SimHei","PingFang SC",sans-serif\','),
    ])

    # 4. Pyodide 运行时（自托管：不依赖第三方 CDN，也不受跨源策略影响）
    pyo = out / "pyodide"
    pyo.mkdir()
    for name in PYODIDE_FILES:
        shutil.copy2(pyodide / name, pyo / name)

    # 5. 文件清单（浏览器按它把源码写进 Pyodide 的虚拟文件系统）
    files = sorted(
        str(p.relative_to(app)).replace("\\", "/")
        for p in app.rglob("*") if p.is_file()
    )
    (out / "app-manifest.json").write_text(
        json.dumps({"files": files}, ensure_ascii=False, indent=0), encoding="utf-8"
    )

    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"out: {out}")
    print(f"python files: {len(files)}")
    print(f"total size: {total / 1048576:.1f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

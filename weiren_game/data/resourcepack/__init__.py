"""资源包（resource pack）：材质（CSS 变量 / 字体 / 额外 CSS）与贴图（SVG 零件）。

- **base 资源包就是本目录**（默认材质），由 ``_discovery`` 自动发现、按文件名顺序登记；
- 内容包 / DLC 可自带 ``resourcepack/``（见 ``weiren_game/dlc.py``）：
- 装载→卸载走 ``content.py`` 的快照回滚（``_BASE_CONTAINERS``）。

贴图零件的写法：``SYMBOLS = {"i-av13": '<circle .../><path .../>'}``（viewBox 统一 24×24）；
主题的写法：``THEME = {"tokens": {"--amber": "#ffcc66"}, "css": "..."}``。
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from .._discovery import discover_modules
from weiren_game.data.lang import TEXT

# 贴图零件：图标 id → <symbol> 内部标记（前端注入 <defs>，`<use href="#id">` 即可用）。
RESOURCE_SYMBOLS: dict[str, str] = {}

# 主题：tokens（CSS 变量，含字体栈）+ css（追加的样式表，可写 @font-face 等）。
RESOURCE_THEME: dict[str, object] = {"tokens": {}, "css": ""}

# 素材位：kind → URL。资源包在自己的 `assets/` 里放文件，用 ASSETS 声明即可（见 register_assets）。
# 约定 kind：`background`（主页面封面背景）、`title`（大标题）。内容也可自行扩展 kind。
RESOURCE_ASSETS: dict[str, str] = {}

ASSET_URL_PREFIX = "/api/resourcepack/asset"

# ---------------------------------------------------------------- 锁定 token
# 「含义 / 尺寸」不该随皮肤变，因此**资源包不得覆盖**（base 资源包除外，它负责给默认值）：
#   · 语义提示：好 / 危险 / 警告 / 信息（红黄绿蓝是"意思"，换个皮肤也不能变意思）
#   · 品质色：白绿蓝紫金红（对应物资品质）
#   · 羁绊位阶：铜 / 银 / 金 / 棱彩（含渐变）
#   · 尺寸：格子边长、描边粗细（**布局不受皮肤影响**）
# 其余（底色/面板/线/文字/琥珀强调/字体栈）就是"材质色调"，资源包可以覆盖。
LOCKED_TOKENS: frozenset[str] = frozenset({
    "--ok", "--danger", "--warn", "--info",
    "--danger-1", "--danger-2", "--danger-hi-1", "--danger-hi-2",   # 危险按钮的红，属"提示"语义
    "--diff-hard", "--diff-easy", "--diff-neutral",                 # 难度标签（更难/更易/基准）
    "--danger-ink",                                                 # 危险按钮/提示上的浅红文字
    "--q0", "--q1", "--q2", "--q3", "--q4", "--q5",
    "--slot", "--w",
})


def register_symbols(symbols: object) -> None:
    """登记一批贴图零件（同 id 覆盖 → 后装载/更高优先级的资源包赢）。"""
    RESOURCE_SYMBOLS.update({str(key): str(value) for key, value in dict(symbols or {}).items()})


def register_assets(assets: object, *, pack: str = "") -> None:
    """登记素材位：``ASSETS = {"background": "moon.svg"}`` → 文件在 ``<包目录>/assets/moon.svg``。"""
    for kind, filename in dict(assets or {}).items():
        RESOURCE_ASSETS[str(kind)] = (
            f"{ASSET_URL_PREFIX}?pack={quote(str(pack))}&file={quote(str(filename))}"
        )


def register_theme(theme: object, *, allow_locked: bool = False) -> None:
    """登记/覆盖主题：token 逐个覆盖（换材质/换字体都改 token），``css`` 追加。

    ``allow_locked=False``（一般资源包/DLC）时忽略 :data:`LOCKED_TOKENS`
    ——那些是**语义提示色 / 品质色 / 尺寸**，换了皮肤也不能改含义或布局；
    羁绊位阶（``--bronze/--silver/--gold/--prism``）**已解锁**——羁绊本就是内容可自定义的。
    base 资源包用 ``allow_locked=True`` 提供默认值。
    """
    theme = dict(theme or {})
    tokens = theme.get("tokens")
    if isinstance(tokens, dict):
        accepted: dict[str, str] = {}
        for key, value in tokens.items():
            key = str(key)
            if not allow_locked and key in LOCKED_TOKENS:
                print(TEXT["data.resourcepack.__init__.register_theme.1"].format(p1=key))
                continue
            accepted[key] = str(value)
        RESOURCE_THEME["tokens"].update(accepted)
    css = theme.get("css")
    if css:
        current = str(RESOURCE_THEME.get("css") or "")
        RESOURCE_THEME["css"] = "\n".join(part for part in (current, str(css)) if part)


def register_pack_module(module: object, *, allow_locked: bool = False, pack: str = "",
                         css: bool = True) -> None:
    """装载一个资源包模块（base 自动发现、DLC 内嵌、独立资源包共用这一条路径）。"""
    register_symbols(getattr(module, "SYMBOLS", None))
    theme = getattr(module, "THEME", None)
    if not css and isinstance(theme, dict) and "css" in theme:
        theme = {key: value for key, value in theme.items() if key != "css"}
    register_theme(theme, allow_locked=allow_locked)
    register_assets(getattr(module, "ASSETS", None), pack=pack)


# base 资源包 = 默认材质：它负责给出**全部** token（含被锁定的那些）。
# 记住这批模块，是为了让 `base` 在资源包清单里**可调位次**：轮到 base 时重新套一遍
# （见 `content.overlay_resourcepack_base` 与 `resourcepack_loader.apply_resourcepack_order`）。
BASE_RESOURCE_MODULES: tuple[object, ...] = tuple(
    discover_modules(__name__, Path(__file__).parent).values()
)


def apply_base_material(*, css: bool = True) -> None:
    """把内置材质重新盖到当前资源包容器上（= 把 ``base`` 抬到清单里的当前位置）。

    ``css=False`` 用于"base 已在基线里"的场景：token/零件需要重新赢一遍，
    但追加型容器（``css``）不必重复叠加。
    """
    for module in BASE_RESOURCE_MODULES:
        register_pack_module(module, allow_locked=True, pack="", css=css)


apply_base_material()


__all__ = [
    "BASE_RESOURCE_MODULES",
    "LOCKED_TOKENS",
    "RESOURCE_ASSETS",
    "RESOURCE_SYMBOLS",
    "RESOURCE_THEME",
    "apply_base_material",
    "register_assets",
    "register_pack_module",
    "register_symbols",
    "register_theme",
]

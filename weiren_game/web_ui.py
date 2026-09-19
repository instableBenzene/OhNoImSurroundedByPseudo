"""本地 Web 界面：标准库 http.server + 静态前端 + JSON API（零依赖）。

前端（`webui/`）只认「状态 JSON + 动作 JSON」，不引用任何游戏规则。
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .condition import AWAKENING_EMOTIONS, EMOTION_DEFINITIONS, EROSION_EMOTIONS
from .config import CONFIG, save_config
from .content import CONTENT
from .data import DIFFICULTIES, DIFFICULTY_INFO
from .dlc import (
    apply_pack_order, available_dlcs, load_configured_dlc, load_single_dlc,
    loaded_dlcs,
)
from .engine import GameEngine, RuleViolation
from .data.labels import ACTIVE_USES_CHIP
from .data.lang import TEXT

from .paths import app_base, resource_dir, saves_dir
from weiren_game.data.lang import TEXT

WEBUI_DIR = resource_dir("webui")
DEFAULT_PORT = 8730
SAVES_DIR = saves_dir()
SAVE_PATH = SAVES_DIR / "savegame.json"
INDEX_PATH = SAVES_DIR / "index.json"

def avatar_of(character_id: str) -> str:
    """角色自声明的头像图标（模块属性 AVATAR），缺省用通用头像。"""
    from .data import CHARACTER_MODULES

    module = CHARACTER_MODULES.get(character_id)
    return getattr(module, "AVATAR", "i-av4")


def persona_display(engine, tenant) -> str:
    """房客卡的运行时性格显示：内容可经模块 ``PERSONA_LABEL`` 钩子覆写（如未固定自我时）。"""
    from .data import CHARACTER_MODULES, PERSONALITY_LABELS

    primary, secondary = engine._tenant_personalities(tenant)
    module = CHARACTER_MODULES.get(tenant.character_id)
    override = getattr(module, "PERSONA_LABEL", None) if module else None
    if override is not None:
        try:
            value = override(engine, tenant)
        except Exception:  # noqa: BLE001 - 展示钩子失败不应中断状态下发
            value = None
        if value:
            return str(value)
    return f"{PERSONALITY_LABELS.get(primary, primary)}-{PERSONALITY_LABELS.get(secondary, secondary)}"


CATEGORY_ICON = {
    "medical": "i-cross", "food": "i-snack", "tool": "i-tool",
    "craft": "i-craft", "information": "i-note", "character": "i-key",
}


def _location_supply(location) -> str:
    """把地点的掉落/修正压成一句简述（供搜索选择界面显示）。"""
    from .data.labels import tag_label, tier_label

    parts = []
    for tags, weight in location.tag_distribution:
        label = "、".join(tag_label(tag) for tag in tags)
        parts.append(f"{weight:g}% {'【' + label + '】' if label else '其他物资'}")
    for key, value in location.quality_modifiers:
        parts.append(TEXT["web_ui._location_supply.1"].format(p1=tier_label(key), p2=(float(value) - 1) * 100))
    for key, value in location.item_tag_modifiers:
        parts.append(TEXT["web_ui._location_supply.2"].format(p1=tag_label(key), p2=value))
    return "；".join(parts)


def _location_drop(location) -> list[dict]:
    """掉落的**结构化**视图：``[{tags, weight}]``（界面分行显示，不再是一长句）。"""
    from .data.labels import tag_label

    return [
        {"tags": [tag_label(tag) for tag in tags], "weight": weight}
        for tags, weight in location.tag_distribution
    ]


def _location_mechanics(location) -> list[str]:
    """地点特殊设定，逐条（界面用小列表渲染）。"""
    mech = []
    if location.fixed:
        mech.append(TEXT["web_ui._location_mechanics.1"])
    if location.turn_delta:
        mech.append(TEXT["web_ui._location_mechanics.2"].format(p1=location.turn_delta))
    if location.behavior_delta:
        mech.append(TEXT["web_ui._location_mechanics.3"].format(p1=location.behavior_delta))
    if location.encounter_bonus:
        mech.append(TEXT["web_ui._location_mechanics.4"].format(p1=location.encounter_bonus))
    return mech


def _item_icon(item) -> str:
    from .data.labels import ITEM_TAG_ICONS, ITEM_TAG_ICON_PRIORITY

    for tag in ITEM_TAG_ICON_PRIORITY:
        if tag in item.tags and tag in ITEM_TAG_ICONS:
            return ITEM_TAG_ICONS[tag]
    return CATEGORY_ICON.get(item.category, "i-note")


def _pseudo_progress(engine, scenario_id: str) -> str:
    """伪人场景的进度摘要文本（由内容层提供）。"""
    from .data import SCENARIO_HANDLERS

    fn = SCENARIO_HANDLERS.get(scenario_id, {}).get("progress_text")
    try:
        return fn(engine) if fn else ""
    except Exception:  # noqa: BLE001 - 进度文本失败不应中断状态
        return ""


def _pseudo_card(engine, scenario_id: str) -> dict | None:
    """伪人卡：解放/突破进度 + 技能 + 印记阈值（由内容层提供）。"""
    from .data import SCENARIO_HANDLERS

    fn = SCENARIO_HANDLERS.get(scenario_id, {}).get("card_info")
    try:
        return fn(engine) if fn else None
    except Exception:  # noqa: BLE001
        return None


def _pseudo_slot(engine, scenario_id: str) -> list[dict]:
    """伪人袖珍卡的小面板：内容声明 ``CARD_SLOT``（与房客小面板同一种条目形状）。"""
    from .data import PSEUDO_CARD_SLOTS

    fn = PSEUDO_CARD_SLOTS.get(scenario_id)
    if fn is None:
        return []
    try:
        items = list(fn(engine) or ())
    except Exception:  # noqa: BLE001 - 面板内容出错不应拖垮状态下发
        return []
    return _project_slot(items, {})


def _visitor_preview(character_id: str | None) -> dict | None:
    """门外访客的简要信息（用于悬浮查看）。"""
    from .data import CHARACTERS, PERSONALITY_LABELS

    definition = CHARACTERS.get(character_id or "")
    if definition is None:
        return None
    return {
        "id": character_id,
        "name": definition.name,
        "avatar": avatar_of(character_id),
        "persona": (
            f"{PERSONALITY_LABELS.get(definition.primary, definition.primary)}-"
            f"{PERSONALITY_LABELS.get(definition.secondary, definition.secondary)}"
        ),
        "tags": list(definition.tags),
        "desc": definition.description,
        "abilities": [
            {"name": ab.name, "text": ab.description}
            for ab in (*definition.actives, *definition.passives)
        ],
    }


def _item_entry(item, count: int, durability: int = 0) -> list:
    """把物品定义 + 数量映射为前端渲染条目。"""
    from .data.items.flavor import ITEM_FLAVOR
    from .data.items import item_is_directly_usable
    from .data.labels import tag_label
    from .item_icons import item_icon_markup

    return [
        _item_icon(item), item.name, item.quality, count, item.stack_size > 1,
        item.item_id,
        [tag_label(tag) for tag in item.tags],           # 中文标签（悬浮显示）
        item.description, ITEM_FLAVOR.get(item.item_id, ""),
        not item_is_directly_usable(item.item_id),       # 装备/携带 还是 直接使用
        int(durability or 0), int(item.max_durability),  # 当前 / 上限耐久
        # 内容层图标（白底 + 品质色特征的内联标记）；没图时为空，前端回退内置 i-* 零件。
        item_icon_markup(item),
    ]


# 屋主仓库最小格数（3 行 × 9 列）；物品放到更后的格子时自动扩展。
WAREHOUSE_MIN_SLOTS = 27


def _slot_entries(instances, size: int) -> list:
    """把一组带 plot 槽位的物品实例铺成定长数组（空格为 None）。"""
    entries: list = [None] * max(1, int(size))
    for instance in instances:
        definition = CONTENT.items().get(instance.item_id)
        if definition is None:
            continue
        plot = max(0, int(instance.plot))
        if plot >= len(entries):
            entries.extend([None] * (plot + 1 - len(entries)))
        entries[plot] = _item_entry(definition, instance.count, instance.durability)
    return entries


def _condition_chips(tenant) -> list[list[str]]:
    """房客的可视状态 chip：遍历全部已注册状态，情绪另走 emotions。

    图标/配色由状态定义（内容层）声明，天然覆盖创伤/紊乱/休克与将来任何新状态。
    """
    from .condition import (
        EMOTION_DEFINITIONS, EmotionDefinition, STATUS_DEFINITIONS,
    )

    chips: list[list[str]] = []
    for key, condition in tenant.conditions.items():
        if not condition.active or isinstance(EMOTION_DEFINITIONS.get(key), EmotionDefinition):
            continue
        definition = STATUS_DEFINITIONS.get(key)
        if definition is not None and definition.chip_hidden:
            continue                      # 内容声明"不进状态栏"（改用详情页小面板等展示）
        label = definition.label if definition is not None else key
        if definition is None or definition.show("intensity"):
            label = f"{label} {condition.intensity}/{condition.layers}"
        icon = (definition.chip_icon if definition is not None else "") or "i-mark"
        css = definition.chip_css if definition is not None else ""
        chips.append([icon, label, css, key])
    return chips


def _project_tiers(raw_tiers: object, scale: int) -> list[dict]:
    """把档位声明投影为刻度：``at`` 或 ``(at, 标注, 刻度配色)``。

    标注意为**提示**（例：`(1, "可发动", "danger")` → 第 1 档画一条红线并写明用途）。
    """
    rows: list[dict] = []
    for entry in raw_tiers or ():
        if isinstance(entry, (tuple, list)):
            at = int(entry[0])
            label = str(entry[1]) if len(entry) > 1 else ""
            css = str(entry[2]) if len(entry) > 2 else ""
        else:
            at, label, css = int(entry), "", ""
        rows.append({
            "at": at,
            "ratio": round(min(1.0, at / scale) * 100, 1),
            "label": label,
            "css": css,
        })
    return rows


def _mark_row(mark: object, current: int) -> dict:
    """一个印记的展示行（含进度条与悬停提示）。"""
    raw_tiers = tuple(getattr(mark, "bar_tiers", ()) or ())
    maximum = getattr(mark, "maximum", None)
    # 无上限时用最后一个阈值当"满槽"参照（超出即满格，数字照实显示更多）。
    fallback = 0
    if raw_tiers:
        last = raw_tiers[-1]
        fallback = int(last[0] if isinstance(last, (tuple, list)) else last)
    scale = maximum if maximum is not None else (fallback or None)
    bar = None
    if scale is not None or raw_tiers:
        scale = max(int(scale or 1), 1)
        bar = {
            "scale": scale,
            "fill": round(min(1.0, current / scale) * 100, 1),
            "tier": sum(
                1 for tier in _project_tiers(raw_tiers, scale) if current >= tier["at"]
            ),
            "tiers": _project_tiers(raw_tiers, scale),
        }
    return {
        "id": mark.id,
        "label": (mark.label or mark.id).split("-")[0],
        "current": int(current),
        "max": maximum,                 # None = 无上限
        "bar": bar,
        # 悬停提示：获得条件 + 特殊用法（内容层文案）。
        "hint": "　".join(part for part in (mark.acquisition, mark.special) if part),
    }


def _project_slot(items: object, mark_rows: dict[str, dict]) -> list[dict]:
    """把内容声明的小面板条目投影成前端可渲染的形状（房客与伪人共用）。

    支持的种类（保持最小集，够用即可）：
    ``mark``（引用自己的某个印记）/ ``bar``（自定义进度条，可带档位刻度）/
    ``text``（一段说明，如人设）/ ``tags``（一排小标签）。
    """
    rows: list[dict] = []
    for raw in items or ():
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("kind") or "")
        if kind == "mark":
            row = mark_rows.get(str(raw.get("id") or ""))
            if row is not None:
                rows.append({"kind": "mark", **row})
        elif kind == "bar":
            value = float(raw.get("value") or 0.0)
            raw_max = raw.get("max")
            scale = float(raw_max) if raw_max is not None else max(value, 1.0)
            scale = max(scale, 1.0)
            rows.append({
                "kind": "bar",
                "label": str(raw.get("label") or ""),
                "value": round(value, 1),
                "max": round(scale, 1),
                "fill": round(min(1.0, value / scale) * 100, 1),
                "tiers": _project_tiers(raw.get("tiers"), int(scale)),
                "hint": str(raw.get("hint") or ""),
            })
        elif kind == "text":
            text = str(raw.get("text") or "")
            if text:
                rows.append({
                    "kind": "text",
                    "label": str(raw.get("label") or ""),
                    "text": text,
                })
        elif kind == "glyph":
            # 装饰性图形（彩蛋）：两种来源 ——
            #   `svg`：**角色自带**的图形（写在自己的 py 里，跟着内容走，正常不可被材质包替换）；
            #   `icon`：引用贴图零件 id（资源包可覆盖/新增）。
            icon = str(raw.get("icon") or "")
            svg = str(raw.get("svg") or "")
            if icon or svg:
                # "cw" = 稳定顺时针；"random" = 每次渲染随机方向与速度。
                spin = str(raw.get("spin") or "")
                rows.append({
                    "kind": "glyph",
                    "icon": icon,
                    "svg": svg,
                    "label": str(raw.get("label") or ""),
                    "hint": str(raw.get("hint") or ""),
                    "spin": spin if spin in ("cw", "random") else "",
                })
        elif kind == "tags":
            items_row = [str(x) for x in (raw.get("items") or ()) if str(x)]
            if items_row:
                rows.append({"kind": "tags", "items": items_row})
    return rows


def _detail_slot(engine: GameEngine, tenant, mark_rows: dict[str, dict]) -> list[dict]:
    """房客详情页的小面板：内容声明 ``DETAIL_SLOT``，没声明就回退为"列出自己的印记"。"""
    from .data import CHARACTER_DETAIL_SLOTS, CHARACTER_MARKS

    fn = CHARACTER_DETAIL_SLOTS.get(tenant.character_id)
    if fn is None:
        items = [
            {"kind": "mark", "id": mark.id}
            for mark in CHARACTER_MARKS.get(tenant.character_id, ())
        ]
    else:
        try:
            items = list(fn(engine, tenant) or ())
        except Exception:  # noqa: BLE001 - 面板内容出错不应拖垮状态下发
            items = []
    return _project_slot(items, mark_rows)


def _panel_item_entry(raw: object) -> list | None:
    """面板格子里的物品：内容只给 item_id / 数量 / 耐久，投影成与仓库同一种条目。"""
    if not isinstance(raw, dict):
        return None
    definition = CONTENT.items().get(str(raw.get("item_id") or ""))
    if definition is None:
        return None
    return _item_entry(
        definition,
        max(1, int(raw.get("count") or 1)),
        max(0, int(raw.get("durability") or 0)),
    )


def _project_panel(engine: GameEngine, tenant, mark_rows: dict[str, dict]) -> dict | None:
    """房客专属面板：内容声明 ``PANEL``，核心只把条目投影成前端能画的样子。

    面板**不是**待处理交互（随时能开、看完能关），所以这里出错只丢面板、不拖垮状态下发
    —— 与 ``DETAIL_SLOT`` 同一个态度。动作名、物品的取舍全由内容决定，核心只转发。
    """
    try:
        view = engine.panel_view(tenant)
    except Exception:  # noqa: BLE001 - 面板内容出错不应拖垮状态下发
        return None
    if not view:
        return None
    slots: list[dict] = []
    for raw in view.get("slots") or ():
        if not isinstance(raw, dict):
            continue
        slots.append({
            "group": int(raw.get("group") or 0),
            "role": str(raw.get("role") or ""),
            "label": str(raw.get("label") or ""),
            "locked": bool(raw.get("locked", True)),
            "onDrop": str(raw.get("on_drop") or ""),
            "onTake": str(raw.get("on_take") or ""),
            "entry": _panel_item_entry(raw.get("item")),
            "rows": _project_slot(raw.get("rows") or (), mark_rows),
        })
    actions: list[dict] = []
    for raw in view.get("actions") or ():
        if not isinstance(raw, dict):
            continue
        actions.append({
            "id": str(raw.get("id") or ""),
            "label": str(raw.get("label") or ""),
            "icon": str(raw.get("icon") or ""),
            "enabled": bool(raw.get("enabled", True)),
            "hint": str(raw.get("hint") or ""),
        })
    return {
        "title": str(view.get("title") or ""),
        "prompt": str(view.get("prompt") or ""),
        "slots": slots,
        "rows": _project_slot(view.get("rows") or (), mark_rows),
        "actions": actions,
        # 底板：内容自带的 svg 内部标记（与 DETAIL_SLOT 的 glyph.svg 同一条路）。
        "backdrop": str(view.get("backdrop") or ""),
    }


def resolve_pack_asset(pack: str, filename: str) -> Path | None:
    """按包名解析素材位文件：base（空包名）/ 独立资源包 / DLC 内嵌。

    只接受**裸文件名**（防目录穿越）；找不到返回 None。
    """
    name = Path(str(filename)).name
    if not name or name != str(filename):
        return None
    from .paths import app_base

    candidates: list[Path] = []
    if not pack:
        candidates.append(Path(__file__).parent / "data" / "resourcepack" / "assets" / name)
    else:
        candidates.append(app_base() / "resourcepacks" / Path(pack).name / "assets" / name)
        candidates.append(app_base() / "dlc" / Path(pack).name / "assets" / name)
    for path in candidates:
        if path.is_file():
            return path
    return None


def resource_pack_state() -> dict:
    """资源包：贴图零件 + 主题（前端启动时取回并应用；内置为默认材质）。

    零件 = ``{"图标 id": "<symbol> 内部标记"}``（viewBox 统一 24×24）；主题 = CSS 变量 + 追加 CSS。
    另有素材位 ``assets``（background / title …）。内容包 / DLC 的 ``resourcepack/``
    与独立资源包都能覆盖同名项（装载顺序 = 各自位次）。
    """
    from .data.resourcepack import RESOURCE_ASSETS, RESOURCE_SYMBOLS, RESOURCE_THEME

    return {
        "symbols": dict(RESOURCE_SYMBOLS),
        "tokens": dict(RESOURCE_THEME.get("tokens") or {}),
        "css": str(RESOURCE_THEME.get("css") or ""),
        "assets": dict(RESOURCE_ASSETS),
    }


def avatar_art(character_id: str) -> dict:
    """角色头像视图：整张（``full``）或「形状 × 专属特征 × 点缀色」的组装。

    零件来自内容层文件（base / 资料包 / 资源包，见 ``weiren_game/avatars.py``）；
    内容可声明 ``AVATAR`` / ``AVATAR_FEATURE`` 覆盖。
    """
    from .avatars import avatar_view
    from .data import CHARACTER_MODULES

    return avatar_view(character_id, CHARACTER_MODULES.get(character_id))


def pseudo_avatar_art(pseudo_id: str) -> dict:
    """伪人**自己**的头像视图。

    以前这里偷懒直接用了它模仿的那个人类的视图，于是伪人卡/图鉴详情里显示的是人类立绘 ——
    那是错的。伪人有自己的 `art`（`data/icon/pseudos/<pseudo_id>`，就是"污染版"立绘）；
    这里再给它一份**按伪人 id** 解析的组装视图，`full` 一般为空，于是前端优先用 `art`。
    """
    from .avatars import avatar_mode, avatar_view
    from .data import PSEUDO_MODULES

    view = avatar_view(pseudo_id, PSEUDO_MODULES.get(pseudo_id))
    # `use_parts` 的本意是"**包**要求用零件"，但 `avatar_view` 在没有整张头像时也会置 True。
    # 伪人默认要显示它自己的**污染版立绘**（上面的 `art`），所以这里按包的声明来定：
    # 默认 art 模式 → False（立绘优先）；包声明 avatar_mode=parts → True（改用零件）。
    view["use_parts"] = avatar_mode() == "parts"
    return view


def _expel_texts(evidence: dict) -> dict:
    """指认（驱逐）的界面文案：**内容层给词**，这里只按"证据是否已证实"挑一份下发。"""
    from .data.labels import ACCUSE_TEXTS

    texts = ACCUSE_TEXTS.get("confirmed" if evidence.get("confirmed") else "pending") or {}
    return {
        "action": str(texts.get("action") or ""),
        "hint": str(texts.get("hint") or ""),
        "confirm": str(texts.get("confirm") or ""),
        # 危险动作：界面据此上危险色（`.btn.danger` / `--danger`），不写死颜色。
        "danger": True,
    }


def _ability_target_options(engine: GameEngine, actor, ability_id: str) -> list[dict]:
    """技能选人时每个候选的**逐项说明**（内容声明 `TARGET_OPTIONS` 时才有）。

    内容只给 `{value,label,desc}`；界面把它画到房客卡上（前端不写任何内容文案）。
    内容出问题就当作没有说明，**不拖垮状态下发**（与面板/小角落同一态度）。
    """
    from .data import ABILITY_TARGET_OPTIONS

    fn = ABILITY_TARGET_OPTIONS.get(ability_id)
    if fn is None:
        return []
    try:
        raw = fn(engine, actor) or ()
    except Exception:  # noqa: BLE001 - 内容出错不该拖垮状态下发
        return []
    rows: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        rows.append({
            "value": str(item.get("value")),
            "label": str(item.get("label") or ""),
            "desc": str(item.get("desc") or ""),
        })
    return rows


def _global_event_rows(engine: GameEngine) -> list[dict]:
    """把生效中的全局事件映射为界面行：图标 + 名称 + 剩余回合 + 内容。

    展示字段全部来自内容层的 ``GlobalEventDefinition``（``icon`` / ``description``），
    未注册定义的事件回退为 id 与空说明。
    """
    from .global_event import GLOBAL_EVENT_DEFINITIONS

    rows: list[dict] = []
    for event_id, instance in engine.state.world.global_events.events.items():
        if not instance.active:
            continue
        definition = GLOBAL_EVENT_DEFINITIONS.get(event_id)
        layers = int(instance.layers)
        # 长期事件（约定 99）显示为「长期」，其余写明确回合数。
        remain = TEXT["web_ui._global_event_rows.1"] if layers >= 99 else TEXT["web_ui._global_event_rows.2"].format(p1=layers)
        rows.append({
            "id": event_id,
            "label": definition.label if definition is not None else event_id,
            "icon": (getattr(definition, "icon", "") or "i-clock") if definition else "i-clock",
            "desc": getattr(definition, "description", "") if definition else "",
            "layers": layers,
            "remain": remain,
        })
    return rows


def build_state(engine: GameEngine) -> dict:
    """把引擎状态映射为前端需要的 JSON（只取前端渲染所需字段）。"""
    flow = engine.state.flow
    meta = engine.state.meta
    pseudo = engine.state.pseudo_state
    house = engine.state.house

    from .data import (
        ABILITY_TARGET_OPTIONS, BOND_DESCRIPTIONS, CHARACTER_MARKS,
        CHARACTERS, DIFFICULTY_INFO, PERSONALITIES, PERSONALITY_LABELS, PSEUDOS, QUALITY_NAMES,
        SEARCH_RETURN_NOTE,
    )
    from .data import codex_pack as _pack
    from .data.personalities import PERSONALITY_MODULES
    from .data.items.flavor import ITEM_FLAVOR
    from .condition import STATUS_DEFINITIONS

    status_info: dict[str, dict] = {}
    for definition in STATUS_DEFINITIONS.values():
        status_info[definition.label] = {"desc": definition.description}
    for definition in EMOTION_DEFINITIONS.values():
        status_info[definition.label] = {"desc": definition.description}
    for marks in CHARACTER_MARKS.values():
        for mark in marks:
            status_info.setdefault(mark.label.split("-")[0], {"desc": mark.description})

    tenants = []
    searching_ids = {tenant.id for tenant in engine.searching_tenants()}
    for tenant in engine.living_tenants():
        info = engine.character(tenant)
        abilities = []
        for kind, group in ((TEXT["web_ui.build_state.1"], info.actives), (TEXT["web_ui.build_state.2"], info.passives)):
            for ability in group:
                state = tenant.ability_state(ability.id)
                entry = {
                    "id": ability.id, "kind": kind, "name": ability.name,
                    "text": ability.description, "target": ability.target,
                    "disabled": bool(getattr(state, "disabled", False)),
                    "used": bool(getattr(state, "used_this_turn", False)),
                    "learned": getattr(state, "acquisition", "original") == "learned",
                    "cooldown": max(0, int(getattr(state, "cooldown_until", 0) or 0)
                                     - engine.state.flow.turn),
                    # True：这条"主动技能"只是打开专属面板（界面渲染成开/关，不走 use_ability）。
                    "opens_panel": bool(getattr(ability, "opens_panel", False)),
                    # 不可撤销的动作：文案由内容声明，界面据此先确认一次；`danger` 决定危险色。
                    "confirm": str(getattr(ability, "confirm", "") or ""),
                    "danger": bool(getattr(ability, "danger", False)),
                    # 目标候选的逐项说明（内容声明 `TARGET_OPTIONS` 时才有；形状同目标候选）。
                    "target_options": _ability_target_options(engine, tenant, ability.id),
                    # 目标选择的界面规格：由内容自描述，前端不写死任何内容文案。
                    "prompt": getattr(ability, "prompt", ""),
                    "options": [list(opt) for opt in getattr(ability, "options", ())],
                    "nested_option": getattr(ability, "nested_option", ""),
                    # 限定 chip 一律由技能自己声明（DLC 同样生效）；未声明且 per_turn 时补默认。
                    "chips": (list(getattr(ability, "chips", ()))
                              or ([ACTIVE_USES_CHIP] if getattr(ability, "per_turn", False) else [])),
                }
                mark = getattr(ability, "amount_mark", "")
                if ability.target == "amount":
                    entry["amount_label"] = getattr(ability, "amount_label", "")
                    entry["amount_max"] = engine._mark_count(tenant, mark) if mark else 0
                provider = ABILITY_TARGET_OPTIONS.get(ability.id)
                if provider is not None:
                    try:
                        entry["candidates"] = list(provider(engine, tenant))
                    except Exception:  # noqa: BLE001 - 候选计算失败不应中断状态下发
                        entry["candidates"] = []
                if ability.target == "tenant_condition":
                    keys = {str(opt[0]) for opt in getattr(ability, "options", ())}
                    targets = []
                    for other in engine.home_tenants():
                        if other.id == tenant.id:
                            continue
                        chips = [c for c in _condition_chips(other)
                                 if len(c) > 3 and c[3] in keys]
                        if not chips:
                            continue
                        other_info = engine.character(other)
                        targets.append({
                            "tenant_id": other.id, "name": other_info.name,
                            "avatar": avatar_of(other.character_id), "conditions": chips,
                        })
                    entry["condition_targets"] = targets
                abilities.append(entry)
        # 声明过的印记一律下发（含 0）：面板里要显示"这位房客有哪些印记"，
        # 否则玩家只在攒到第 1 枚时才第一次看到它。
        mark_rows = {
            mark.id: _mark_row(mark, tenant.marks.count(mark.id))
            for mark in CHARACTER_MARKS.get(tenant.character_id, ())
        }
        emotions = []
        for key in (*EROSION_EMOTIONS, *AWAKENING_EMOTIONS):
            cond = tenant.condition(key)
            if not cond.active or not engine.emotion_visible(tenant, key):
                continue
            definition = EMOTION_DEFINITIONS[key]
            label = definition.label
            if definition.show("intensity"):
                label = f"{label} {cond.intensity}/{cond.layers}"
            emotions.append(["i-emotion", label, ""])
        # 屋主直接驱逐（指认）按钮：只在房客在场且证据达标时下发（离场者无法被指认）。
        evidence = engine.accusation_evidence(tenant.id) if (tenant.alive and tenant.at_home) else None
        can_expel = bool(evidence and evidence["ready"])
        tenants.append({
            "id": tenant.id,
            "searching": tenant.id in searching_ids,
            "expellable": can_expel,
            "expel_risk": bool(can_expel and not evidence["confirmed"]),
            # 指认（驱逐）的界面文案：**由内容层给词**（`data/labels.ACCUSE_TEXTS`），
            # 这里只按"证据是否已证实"挑一份下发；前端不写任何机制说明。
            "expel": _expel_texts(evidence) if can_expel else None,
            "character_id": tenant.character_id,
            "name": info.name,
            "avatar": avatar_of(tenant.character_id),
            "avatar_parts": avatar_art(tenant.character_id),
            "tags": list(info.tags),
            # 运行时性格（随机切换/性格改写会实时反映；内容可经 PERSONA_LABEL 覆写）。
            "persona": persona_display(engine, tenant),
            # 性格/被动失效：**休克同样算**（`systems/personality_system.py` 与 `engine._has_character`
            # 判的就是 `shock or passives_disabled`）。这里只报 passives_disabled 会与机制不符——
            # 玩家看到"性格还在"，但引擎已经把它关掉了（PRINCIPLES §一.4 状态必须如实）。
            "persona_off": bool(tenant.passives_disabled or tenant.shock),
            "hp": round(tenant.health),
            "san": round(tenant.sanity),
            "hp_max": round(tenant.max_health),
            "san_max": round(tenant.max_sanity),
            "carry": engine.tenant_carry_capacity(tenant),
            "carryNote": "",
            "statuses": _condition_chips(tenant),
            "emotions": emotions,
            # 详情页头像右侧的公共小面板：内容声明放什么（印记/进度条/文本/标签）。
            "slot": _detail_slot(engine, tenant, mark_rows),
            # 专属面板（自定义 UI）：内容声明 `PANEL`，没声明就是 None。
            "panel": _project_panel(engine, tenant, mark_rows),
            "mark": "",
            "abilities": abilities,
            "inventory": _slot_entries(tenant.inventory.items, engine.tenant_carry_capacity(tenant)),
        })

    bonds = []
    levels = engine.bond_levels()
    providers: dict[str, list[str]] = {}
    for tenant in engine.home_tenants():
        info = engine.character(tenant)
        p_key, s_key = engine._tenant_personalities(tenant)
        providers.setdefault(p_key, []).append(TEXT["web_ui.build_state.3"].format(p1=info.name))
        providers.setdefault(s_key, []).append(TEXT["web_ui.build_state.4"].format(p1=info.name))
    # 本局可提供各羁绊的房客名单：排除本局被禁用的角色与伪人的人类形态（不参与本局）。
    disabled = set(engine.state.world.disabled_characters)
    pseudo_definition = PSEUDOS.get(engine.state.pseudo_state.scenario_id)
    human_id = pseudo_definition.human_character_id if pseudo_definition else ""
    potential: dict[str, list[str]] = {}
    for cid, definition in sorted(CHARACTERS.items(), key=lambda kv: kv[1].source_id):
        if not definition.available or cid in disabled or cid == human_id:
            continue
        if definition.primary in PERSONALITIES:
            potential.setdefault(definition.primary, []).append(TEXT["web_ui.build_state.5"].format(p1=definition.name))
        if definition.secondary in PERSONALITIES:
            potential.setdefault(definition.secondary, []).append(TEXT["web_ui.build_state.6"].format(p1=definition.name))
    for key in PERSONALITIES:
        label = PERSONALITY_LABELS[key]
        lv = int(levels.get(key, 0))
        module = PERSONALITY_MODULES.get(key)
        raw_tiers = getattr(module, "TIERS", None) if module else None
        thresholds = tuple(raw_tiers) if isinstance(raw_tiers, (tuple, list)) else ()
        if not thresholds:
            thresholds = tuple(_pack.PERSONALITY_TIER_HINTS.get(key, ()))
        active_fn = getattr(module, "ACTIVE_TIERS", None) if module else None
        # 档位一律由引擎方法给出（内容模块的 TIERS/TIER_AT），不在系统里复算。
        tier_value = engine._bond_tier(key, lv)
        if active_fn is not None:
            active_set = {int(tier) for tier in active_fn(lv)}
        else:
            active_set = {tier for tier in thresholds if lv >= tier}
        # 羁绊非继承式激活：只高亮“恰好激活”的那一档。
        reached = 0
        for index, tier in enumerate(thresholds):
            if tier in active_set:
                reached = index + 1
        tier_text = list(_pack.PERSONALITY_TIER_TEXT.get(key, ()))
        effects = [
            [thresholds[index] if index < len(thresholds) else 0, text]
            for index, text in enumerate(tier_text)
        ]
        bonds.append({
            "name": label,
            "icon": f"i-b-{key}",
            "lv": lv,
            "tiers": list(thresholds),
            "tier_value": tier_value,
            "reached": reached,
            "base": _pack.PERSONALITY_BASE.get(key, "") or BOND_DESCRIPTIONS.get(key, ""),
            "effects": effects,
            "providers": providers.get(key, []),
            # 本局仍可能出现、且能提供该羁绊的房客名单（供羁绊概况参考）。
            "potential": potential.get(key, []),
        })

    # 屋主仓库按真实槽位下发：空格保留为 null，允许玩家自由摆放。
    house_instances = list(house.inventory)
    warehouse_size = WAREHOUSE_MIN_SLOTS
    for instance in house_instances:
        warehouse_size = max(warehouse_size, int(instance.plot) + 1)
    warehouse = _slot_entries(house_instances, warehouse_size)

    intel = []
    _intel_order = {"pending": 0, "confirmed": 1, "refuted": 2, "expired": 3}
    from .data.labels import information_kind_label as _kind_label

    def _intel_key(info):
        return (_intel_order.get(info.status, 9), info.expires_turn)

    for info in sorted(house.information, key=_intel_key):
        left = info.expires_turn - engine.state.flow.turn
        intel.append({
            "id": info.info_instance_id, "pending": info.status == "pending",
            "t": info.title,
            "art": art_url("information", info.template_id) if info.template_id else "",
            "state": {"pending": "pending", "confirmed": "true",
                      "refuted": "false", "expired": "expired"}.get(info.status, "true"),
            "desc": info.text,
            "source": info.source or TEXT["web_ui.build_state.7"],
            "kind_label": _kind_label(info.kind),
            "expire": (TEXT["web_ui.build_state.8"].format(p1=left)
                       if info.status in ("pending", "confirmed") and left > 0 else ""),
            "effect": "",
        })

    missions = []
    for mission in engine.state.world.missions:
        tenant = house.tenants.get(mission.tenant_id)
        missions.append({
            "who": engine.character(tenant).name if tenant else "?",
            "place": CONTENT.locations()[mission.location_id].name,
            "eta": max(0, mission.remain_search_turns),
            "carry": [], "rate": f"{mission.search_success_rate:.0%}", "note": "",
        })

    pending: dict = {}
    if engine._pending_choice:
        raw_options = list(engine._pending_choice.get("options", ()))

        def _option_view(value: object) -> dict:
            """把待选项泛化为展示视图：内容层只给值，界面层按注册表补名称/图标/说明。"""
            character = CONTENT.characters().get(value)
            if character is not None:
                cid = str(value)
                return {
                    "kind": "character", "id": cid, "name": character.name,
                    "avatar": avatar_of(cid),
                    "avatar_parts": avatar_art(cid),
                    "no": character.source_id,
                    "persona": f"{PERSONALITY_LABELS.get(character.primary, character.primary)}-"
                               f"{PERSONALITY_LABELS.get(character.secondary, character.secondary)}",
                    "tags": list(character.tags),
                    "desc": character.description,
                }
            if isinstance(value, str) and value in PERSONALITY_LABELS:
                weights = engine._personality_weights()
                return {
                    "kind": "personality", "id": value, "name": PERSONALITY_LABELS[value],
                    "icon": f"i-b-{value}", "weight": round(float(weights.get(value, 0.0)), 1),
                    "desc": _pack.PERSONALITY_BASE.get(value, "") or BOND_DESCRIPTIONS.get(value, ""),
                }
            item = CONTENT.items().get(value)
            if item is not None:
                iid = str(value)
                from .item_icons import item_icon_markup

                return {
                    "kind": "item", "id": iid, "name": item.name,
                    "icon": _item_icon(item), "icon_svg": item_icon_markup(item),
                    "quality": item.quality,
                    "quality_label": QUALITY_NAMES[item.quality]
                    if 0 <= item.quality < len(QUALITY_NAMES) else str(item.quality),
                    "desc": item.description,
                }
            return {"kind": "text", "name": str(value)}

        pending["choice"] = {
            "kind": engine._pending_choice.get("kind", ""),
            "options": [_option_view(value) for value in raw_options],
            "indices": list(range(len(raw_options))),
            "prompt": str(engine._pending_choice.get("prompt", "选择")),
        }
    view = engine.pending_view()
    if view is not None:
        pending["interaction"] = view

    from .data.labels import group_label as _group_label, tag_label as _tag_label

    tag_index: dict = {}
    for _iid, _item in CONTENT.items().items():
        for _tag in _item.tags:
            tag_index.setdefault(_tag_label(_tag), []).append({"id": _iid, "name": _item.name})

    difficulty_entry = next((row for row in DIFFICULTY_INFO if row["id"] == meta.difficulty), None)
    # 悬浮说明显示"累计到本档"的全部新增效果（a-1..a-N / a1..aN）。
    difficulty_effects: list = []
    if meta.difficulty.startswith("a-"):
        for _level in range(1, abs(int(meta.difficulty[2:] or 0)) + 1):
            _entry = next((row for row in DIFFICULTY_INFO if row["id"] == f"a-{_level}"), None)
            difficulty_effects.extend((_entry or {}).get("added", ()))
    elif meta.difficulty.startswith("a") and meta.difficulty != "a0":
        for _level in range(1, int(meta.difficulty[1:] or 0) + 1):
            _entry = next((row for row in DIFFICULTY_INFO if row["id"] == f"a{_level}"), None)
            difficulty_effects.extend((_entry or {}).get("added", ()))

    definition = CONTENT.pseudos().get(pseudo.scenario_id)
    mark_field = getattr(definition, "mark_field", "") if definition else ""
    mark_label = getattr(definition, "mark_label", "") if definition else ""
    try:
        mark_value = getattr(pseudo.scenario(), mark_field, 0) if mark_field else 0
    except Exception:  # noqa: BLE001 - 场景状态缺失时回退
        mark_value = 0
    # 「已确认」= 初访揭示（revealed），或初访前技能生效已被观察到（known）：
    # 两种情况都对外显示身份与印记，卡片不会停在「尚未确认」。
    known = bool(pseudo.revealed or getattr(pseudo, "known", False))

    return {
        "turn": flow.turn, "max_turns": flow.max_turns, "phase": flow.phase,
        # 屋子显示名（内容层标签；将来由所选"地图"覆盖）。前端不写死。
        "home": {"name": _map_shelter(engine)},
        "game_over": flow.game_over, "difficulty": meta.difficulty, "seed": meta.seed,
        "difficulty_label": (difficulty_entry or {}).get("label", ""),
        "difficulty_effects": difficulty_effects,
        "qualityNames": list(QUALITY_NAMES),
        "tagIndex": tag_index,
        "qualityNames": list(QUALITY_NAMES),
        "searchReturnNote": SEARCH_RETURN_NOTE,
        "pseudo": {
            # 未揭示时不泄露名字与印记名（对外只显示"尚未确认"）。
            "name": pseudo.name if known else "",
            "revealed": pseudo.revealed, "known": known, "visits": pseudo.visit_count,
            "mark_label": mark_label if known else "",
            "mark_value": int(mark_value or 0) if known else 0,
            "mark_max": int((_pseudo_card(engine, pseudo.scenario_id) or {}).get("mark_need", 20)),
            "progress": _pseudo_progress(engine, pseudo.scenario_id),
            "card": _pseudo_card(engine, pseudo.scenario_id),
            # 袖珍卡里由内容支配的小面板（可为空）。
            "slot": _pseudo_slot(engine, pseudo.scenario_id),
        },
        "door": [
            {
                "title": e.title, "description": e.description, "kind": e.kind,
                "visitor": _visitor_preview(e.visitor_id) if e.kind == "human" else None,
                "pseudo_id": e.pseudo_id or "",
            }
            for e in engine.state.world.events.door_events
        ],
        "locations": [
            {
                "id": key,
                "name": CONTENT.locations()[key].name,
                "icon": _pack.LOCATION_ICONS.get(key, "i-gate"),
                "art": art_url("locations", key),
                "desc": _pack.LOCATION_TEXT.get(key, CONTENT.locations()[key].description),
                "supply": _location_supply(CONTENT.locations()[key]),
                # 结构化字段：搜索选择界面要分行显示掉落/机制，而不是堆一长句。
                "group_label": _group_label(CONTENT.locations()[key].group),
                "tier": CONTENT.locations()[key].tier,
                "fixed": CONTENT.locations()[key].fixed,
                "tags": sorted({_tag_label(t) for tags, _ in CONTENT.locations()[key].tag_distribution
                                for t in tags}),
                "drop": _location_drop(CONTENT.locations()[key]),
                "mechanics": _location_mechanics(CONTENT.locations()[key]),
            }
            for key in engine.state.world.locations.available_locations
        ],
        "pseudos": [{"id": key, "name": value.name} for key, value in CONTENT.pseudos().items()],
        "tenants": tenants, "bonds": bonds, "events": _global_event_rows(engine),
        "warehouse": warehouse, "warehouseSize": len(warehouse),
        "backpack": [], "intel": intel, "missions": missions, "log": [],
        # 每条是 [回合, 文本, 明细]；没有明细时第三项为 None（前端照旧只渲染文本）。
        "logEntries": [[entry["turn"], entry["text"], entry.get("detail"), entry.get("kind", "")]
                       for entry in engine.state.log.entries if entry.get("shown", True)],
        # 本回合是否已无人可派（当前=已指派过；未来若一回合多次搜索，改这里即可，前端不写死）。
        "searchBlocked": bool(engine.state.round.searched_this_turn),
        "pending": pending, "statusInfo": status_info,
    }


def _map_shelter(engine) -> str:
    """屋子显示名：**只认地图的 `shelter`**（base 地图恒在，所以不需要第二份兜底）。"""
    from .data import BASE_MAP_ID, MAPS

    map_def = MAPS.get(engine.state.meta.map_id) or MAPS.get(BASE_MAP_ID)
    return map_def.shelter if map_def else ""


def _map_menu() -> list[dict]:
    """可选地图列表：默认地图（base）排最前。"""
    from .data import BASE_MAP_ID, MAPS

    order = ([BASE_MAP_ID] if BASE_MAP_ID in MAPS else []) + [
        key for key in sorted(MAPS) if key != BASE_MAP_ID
    ]
    return [{"id": key, "name": MAPS[key].name, "shelter": MAPS[key].shelter,
             "count": len(MAPS[key].locations), "default": key == BASE_MAP_ID}
            for key in order]


def menu_state() -> dict:
    """返回启动器数据：可安装 DLC、难度分层说明、伪人与当前设置。"""
    loaded = set(loaded_dlcs())
    available = {path.name for path in available_dlcs()}
    enabled = [name for name in CONFIG.pack_order if name in available]
    from .resourcepack_loader import available_resourcepacks, resourcepack_label, resourcepack_root

    from .resourcepack_loader import BASE_MATERIAL

    pack_names = {path.name for path in available_resourcepacks()}
    resourcepack_order = [
        str(name) for name in CONFIG.resourcepack_order
        if str(name) == BASE_MATERIAL or str(name) in pack_names
    ]
    if BASE_MATERIAL not in resourcepack_order:
        resourcepack_order.append(BASE_MATERIAL)
    return {
        "dlc": [{"name": path.name, "loaded": path.name in loaded} for path in available_dlcs()],
        # 资源包目录的绝对路径：界面把它显示出来，"可用 0 个"时一眼看出是目录不对还是进程旧。
        "resourcepack_root": str(resourcepack_root()),
        "resourcepacks": [
            {"name": path.name, "label": resourcepack_label(path.name),
             "enabled": path.name in resourcepack_order}
            for path in available_resourcepacks()
        ],
        # 可选地图（区域包）：创建对局页的"地图"下拉用它；第一项就是默认图。
        "maps": _map_menu(),
        "difficulties": list(DIFFICULTIES),
        "difficulty_info": [dict(entry) for entry in DIFFICULTY_INFO],
        "pseudos": [{"id": key, "name": value.name} for key, value in CONTENT.pseudos().items()],
        "settings": {
            "difficulty": CONFIG.difficulty,
            "max_turns": CONFIG.max_turns,
            "pseudo": CONFIG.default_pseudo or "",
            "random_pseudo": CONFIG.random_pseudo,
            "enabled_dlc": enabled,
            # 内容包优先级（高 → 低，含 base）；界面用它做顺序调节。
            "pack_order": list(CONFIG.pack_order) or ["base", *enabled],
            "resourcepack_order": resourcepack_order,
            "show_full_skills": CONFIG.show_full_skills,
            "panel_draggable": bool(CONFIG.panel_draggable),
            "panel_pos": dict(CONFIG.panel_pos or {}),
        },
    }


def art_url(kind: str, entity_id: str) -> str:
    """地点 / 信息 / 伪人图标的 URL（内容层文件，资料包/资源包可覆盖）。

    找不到文件时返回空串，前端回退内置单线图标。按"当前配置 + 文件系统"现算，
    所以换资源包 / 调位次立即生效（见 :mod:`weiren_game.icon_files`）。
    """
    from .icon_files import icon_url

    return icon_url(kind, entity_id)


def _safe_filename(name: str) -> str:
    """把用户输入的存档名转成安全的文件名（去路径分隔符与非法字符）。"""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", str(name).strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    return cleaned[:40] or "save"


def _read_index() -> dict:
    if INDEX_PATH.is_file():
        try:
            raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if isinstance(raw, dict):
            return raw
    return {}


def _write_index(index: dict) -> None:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_summary(path: Path, index: dict) -> dict | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    meta = raw.get("meta") or {}
    flow = raw.get("flow") or {}
    entry = index.get(path.name) or {}
    try:
        stamp = path.stat().st_mtime
    except OSError:
        stamp = 0.0
    created = entry.get("created") or datetime.datetime.fromtimestamp(stamp).isoformat(timespec="seconds")
    return {
        "file": path.name,
        "name": str(entry.get("name") or path.stem),
        "created": created,
        "turn": int(flow.get("turn") or 0),
        "max_turns": int(flow.get("max_turns") or 0),
        "difficulty": str(meta.get("difficulty") or "-"),
        "seed": str(meta.get("seed") or ""),
        "packs": list(meta.get("packs") or []),
        "game_over": bool(flow.get("game_over")),
        "victory": bool(flow.get("victory")),
        "mtime": stamp,
    }


def list_saves() -> list:
    """列出 saves/ 下的存档摘要（按修改时间倒序）。"""
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    index = _read_index()
    result = []
    for path in SAVES_DIR.glob("*.json"):
        if path.name == INDEX_PATH.name:
            continue
        summary = _save_summary(path, index)
        if summary:
            result.append(summary)
    result.sort(key=lambda item: item["mtime"], reverse=True)
    return result


class Session:
    """单局会话：持有引擎并执行动作。"""

    def __init__(self) -> None:
        self.engine: GameEngine | None = None
        self.save_path: Path | None = None
        self._pending_save: dict | None = None

    def new_game(self, options: dict) -> None:
        for name in options.get("dlc") or ():
            try:
                load_single_dlc(name)
            except Exception as exc:  # noqa: BLE001 - 装载失败转为可见错误
                raise RuleViolation(TEXT["web_ui.new_game.1"].format(p1=name, p2=exc))
        self.engine = GameEngine.new_game(
            seed=options.get("seed") or None,
            map_id=str(options.get("map") or "") or None,
            difficulty=options.get("difficulty") or "a0",
            max_turns=int(options.get("max_turns") or 32),
            pseudo_id=options.get("pseudo") or None,
            # 前端未显式给 random_pseudo 时保持 None，由引擎回落到 CONFIG（向后兼容）。
            random_pseudo=options.get("random_pseudo"),
            defer_start=True,
        )
        self.engine.drain_messages()
        display = str(options.get("name") or "").strip()
        self._pending_save = None
        if display:
            SAVES_DIR.mkdir(parents=True, exist_ok=True)
            self.save_path = SAVES_DIR / (_safe_filename(display) + ".json")
            self._pending_save = {"name": display}
        else:
            self.save_path = None
        self.flush_pending_save()

    def flush_pending_save(self) -> None:
        """新对局在选完开局成员后自动落盘一次（等待选择期间不可保存）。"""
        if not self._pending_save or self.engine is None:
            return
        if self.engine._pending_choice is not None or self.engine._pending_ability:
            return
        try:
            path = self.engine.save(self.save_path or (SAVES_DIR / "savegame.json"))
        except RuleViolation:
            return
        index = _read_index()
        index[path.name] = {"name": self._pending_save["name"],
                            "created": datetime.datetime.now().isoformat(timespec="seconds")}
        _write_index(index)
        self.save_path = path
        self._pending_save = None

    def abort_start(self) -> bool:
        """开局「发现」还没选完就强行退出：丢掉这场**还没真正开始**的局。

        `defer_start` 期间引擎一次都没落盘（`flush_pending_save` 遇到待选就跳过），
        所以"回退到开始发现之前"= 直接丢掉引擎 —— 磁盘上仍是上一份存档（或没有存档），
        启动器也不会再被那个待选卡住（前端 `hasPending()` 会随之清掉）。

        返回是否真的丢了一局；已经开打的对局（没有开局待选）不动，返回 False。
        """
        engine = self.engine
        if engine is None:
            return False
        pending = getattr(engine, "_pending_choice", None)
        if not pending or pending.get("kind") != "start_choice":
            return False
        self.engine = None
        self.save_path = None
        self._pending_save = None
        return True

    def load_save(self, filename: str) -> None:
        if not filename:
            raise RuleViolation(TEXT["web_ui.load_save.1"])
        path = SAVES_DIR / Path(filename).name
        if not path.is_file():
            raise RuleViolation(TEXT["web_ui.load_save.2"])
        self.engine = GameEngine.load(path)
        self.save_path = path
        self._pending_save = None
        self.engine.resume_to_action()

    def delete_save(self, filename: str) -> None:
        if not filename:
            raise RuleViolation(TEXT["web_ui.delete_save.1"])
        path = SAVES_DIR / Path(filename).name
        if path.is_file():
            path.unlink()
        index = _read_index()
        index.pop(path.name, None)
        _write_index(index)

    def drain(self) -> list[str]:
        return self.engine.drain_message_entries() if self.engine else []

    def perform(self, payload: dict) -> None:
        if self.engine is None:
            raise RuleViolation(TEXT["web_ui.perform.1"])
        action = payload.get("type")
        if action == "end_turn":
            self.engine.end_turn()
            if not self.engine.state.flow.game_over and self.engine.state.flow.phase in {"created", "between_turns"}:
                self.engine.start_turn()
        elif action == "door":
            decision = payload.get("decision", "inspect")
            self.engine.handle_next_door_event(decision)
        elif action == "discover":
            pending = self.engine._pending_choice
            if not pending:
                raise RuleViolation(TEXT["web_ui.perform.2"])
            options = list(pending.get("options", ()))
            index = int(payload.get("index", 0))
            if not 0 <= index < len(options):
                raise RuleViolation(TEXT["web_ui.perform.3"])
            self.engine.choose_discover(options[index])
        elif action == "start_choice":
            pending = self.engine._pending_choice
            if not pending or pending.get("kind") != "start_choice":
                raise RuleViolation(TEXT["web_ui.perform.4"])
            options = list(pending.get("options", ()))
            index = int(payload.get("index", 0))
            if not 0 <= index < len(options):
                raise RuleViolation(TEXT["web_ui.perform.5"])
            self.engine.commit_start_choice(options[index])
            if not self.engine._pending_choice and self.engine.state.flow.phase in {"created", "between_turns"}:
                self.engine.start_turn()
        elif action == "resolve":
            self.engine.resolve_view(payload.get("value"))
        elif action == "start_search":
            self.engine.start_search(int(payload["tenant_id"]), payload["location_id"])
        elif action == "use_item":
            self.engine.use_item(
                payload["item_id"], payload.get("tenant_id"), payload.get("condition"),
                source_tenant=payload.get("source_tenant"), slot=payload.get("slot"),
            )
        elif action == "equip":
            self.engine.equip_item(
                int(payload["tenant_id"]), payload["item_id"],
                source_tenant=payload.get("source_tenant"), slot=payload.get("slot"),
                target_slot=payload.get("target_slot"),
            )
        elif action == "unequip":
            self.engine.unequip_item(
                int(payload["tenant_id"]), payload["item_id"],
                slot=payload.get("slot"), target_slot=payload.get("target_slot"),
            )
        elif action == "ability":
            self.engine.use_ability(
                int(payload["actor_id"]), payload.get("target_id"), payload["ability_id"],
                payload.get("option"), payload.get("amount"),
                copied_ability_id=payload.get("copied_ability_id"),
                secondary_target_id=payload.get("secondary_target_id"),
                secondary_option=payload.get("secondary_option"),
                secondary_amount=payload.get("secondary_amount"),
            )
        elif action == "accuse":
            self.engine.accuse(int(payload["tenant_id"]))
        elif action == "transfer_item":
            self.engine.transfer_item(
                int(payload["from_tenant"]), int(payload["to_tenant"]), str(payload["item_id"]),
                slot=payload.get("slot"), target_slot=payload.get("target_slot"),
            )
        elif action == "move_item":
            self.engine.move_item(
                container=str(payload.get("container") or "warehouse"),
                from_slot=int(payload["from_slot"]), to_slot=int(payload["to_slot"]),
                tenant_id=payload.get("tenant_id"),
            )
        elif action == "panel":
            # 专属面板动作：核心不解其意，转发给内容声明的处理器（见 data/characters/<id>.py）。
            self.engine.panel_action(
                int(payload["tenant_id"]),
                str(payload.get("panel_action") or ""),
                slot=payload.get("slot"),
                item_id=payload.get("item_id"),
                source=payload.get("source"),
            )
        elif action == "rewind":
            self.engine.rewind_one_turn()
            if not self.engine.state.flow.game_over and self.engine.state.flow.phase != "action":
                self.engine.start_turn()
        elif action == "save":
            target = self.save_path or SAVE_PATH
            path = self.engine.save(target)
            index = _read_index()
            index.setdefault(path.name, {
                "name": path.stem,
                "created": datetime.datetime.now().isoformat(timespec="seconds"),
            })
            _write_index(index)
            self.save_path = path
        elif action == "load":
            if not SAVE_PATH.is_file():
                raise RuleViolation(TEXT["web_ui.perform.6"])
            self.engine = GameEngine.load(SAVE_PATH)
            self.engine.resume_to_action()
        else:
            raise RuleViolation(TEXT["web_ui.perform.7"].format(p1=action))


def _codex_extra(character_id: str) -> list:
    """角色自声明的图鉴补充内容（如命运牌、persona）；缺失则返回空。"""
    from .data import CHARACTER_CODEX_EXTRA

    provider = CHARACTER_CODEX_EXTRA.get(character_id)
    if provider is None:
        return []
    try:
        return list(provider())
    except Exception:  # noqa: BLE001 - 补充内容失败不应中断图鉴
        return []


_BOOK_GAIN_MARKERS = (TEXT["web_ui._BOOK_GAIN_MARKERS.0"], TEXT["web_ui._BOOK_GAIN_MARKERS.1"])


def codex_state() -> dict:
    """图鉴数据：全部静态内容，不依赖任何对局。"""
    from .data import (
        BOND_DESCRIPTIONS,
        CHARACTER_CODEX_EXTRA,
        CHARACTERS,
        INFORMATION_TEMPLATES,
        ITEMS,
        LOCATIONS,
        PERSONALITIES,
        PERSONALITY_LABELS,
        PSEUDO_MODULES,
        PSEUDOS,
        QUALITY_NAMES,
    )
    from .data.items.flavor import ITEM_FLAVOR

    from .data.labels import (
        category_label, group_icon, group_label, information_kind_label, tag_label, tier_label,
    )
    from .data import LOCATION_INFORMATION_MODIFIERS
    from .data import codex_pack as _pack
    from .data.information_text import INFORMATION_TEXT
    from .data.items.codex_text import ITEM_TEXT

    link_map = _pack.build_item_links(ITEMS, PERSONALITY_LABELS, CHARACTERS, PSEUDOS)
    information = []
    for _iid, _info in sorted(INFORMATION_TEMPLATES.items(), key=lambda kv: kv[1].name):
        _loc = LOCATIONS.get(_info.location_id)
        information.append({
            "id": _iid, "name": _info.name,
            "art": art_url("information", _iid),
            "kind": _info.kind, "kind_label": information_kind_label(_info.kind),
            "desc": INFORMATION_TEXT.get(_iid, _info.description),
            "location": _loc.name if _loc else "",
            "duration": _info.duration,
            "rewards": [[r, ITEMS[r].name] for r in _info.reward_ids if r in ITEMS],
            "effect": [
                (TEXT["web_ui.codex_state.1"].format(p1=tag_label(_key.split(':', 1)[1]), p2=float(_val)) if _key.startswith("tag:")
                 else TEXT["web_ui.codex_state.2"].format(p1=tier_label(_key.split(':', 1)[1]), p2=float(_val)) if _key.startswith("quality:")
                 else TEXT["web_ui.codex_state.3"].format(p1=float(_val)))
                for _key, _val in LOCATION_INFORMATION_MODIFIERS.get(_iid, {}).items()
            ],
            "pending": _info.pending, "confirmed": _info.confirmed, "refuted": _info.refuted,
        })

    tag_index: dict = {}
    for _iid, _item in ITEMS.items():
        for _tag in _item.tags:
            tag_index.setdefault(tag_label(_tag), []).append({"id": _iid, "name": _item.name})
    item_name = {iid: item.name for iid, item in ITEMS.items()}

    def items_referencing(field: str, value: str) -> list:
        return [{"id": iid, "name": item_name[iid]}
                for iid, entry in link_map.items() if value in entry.get(field, ())]

    def ability(entry) -> dict:
        return {
            "name": entry.name, "text": entry.description, "target": entry.target,
            "chips": (list(getattr(entry, "chips", ()))
                      or ([ACTIVE_USES_CHIP] if getattr(entry, "per_turn", False) else [])),
        }

    characters = []
    for cid, definition in sorted(CHARACTERS.items(), key=lambda kv: kv[1].source_id):
        characters.append({
            "id": cid,
            "no": definition.source_id,
            "name": definition.name,
            "available": definition.available,
            "carry": definition.carry,
            "avatar": avatar_of(cid),
            "avatar_parts": avatar_art(cid),
            "tags": list(definition.tags),
            "persona": (
                f"{PERSONALITY_LABELS.get(definition.primary, definition.primary)}-"
                f"{PERSONALITY_LABELS.get(definition.secondary, definition.secondary)}"
            ),
            "desc": definition.description,
            "actives": [ability(a) for a in definition.actives],
            "passives": [ability(a) for a in definition.passives],
            "extra": _codex_extra(cid),
            "items": items_referencing("characters", cid),
        })

    items = []
    from .item_icons import item_icon_markup

    for iid, item in sorted(ITEMS.items(), key=lambda kv: (kv[1].category, kv[1].name)):
        items.append({
            "id": iid, "icon": _item_icon(item), "icon_svg": item_icon_markup(item), "name": item.name,
            "category": item.category, "category_label": category_label(item.category),
            "quality": item.quality,
            "quality_label": QUALITY_NAMES[item.quality] if 0 <= item.quality < len(QUALITY_NAMES) else str(item.quality),
            "durability": item.max_durability,
            "desc": item.description, "full": ITEM_TEXT.get(iid, ""),
            "book": "book" in item.tags,
            "book_main": (lambda txt: txt.split(_BOOK_GAIN_MARKERS[0])[0].split(_BOOK_GAIN_MARKERS[1])[0] if any(m in txt for m in _BOOK_GAIN_MARKERS) else txt)(ITEM_TEXT.get(iid, "") or item.description),
            "book_gain": (lambda txt: next((txt[txt.index(m):] for m in _BOOK_GAIN_MARKERS if m in txt), ""))(ITEM_TEXT.get(iid, "") or item.description),
            "flavor": ITEM_FLAVOR.get(iid, ""),
            "tags": [[tag, tag_label(tag)] for tag in item.tags],
            "stack": item.stack_size,
            "links": {
                "bonds": [{"key": k, "label": PERSONALITY_LABELS.get(k, k)}
                          for k in link_map.get(iid, {}).get("bonds", ())],
                "characters": [{"id": c, "name": CHARACTERS[c].name}
                               for c in link_map.get(iid, {}).get("characters", ()) if c in CHARACTERS],
                "pseudos": [{"id": p, "name": PSEUDOS[p].name}
                            for p in link_map.get(iid, {}).get("pseudos", ()) if p in PSEUDOS],
            },
        })

    locations = []
    for lid, loc in sorted(LOCATIONS.items(), key=lambda kv: kv[1].name):
        # 物资类型（按设计稿的完整句式还原掉落分布）。
        supply = "；".join(
            TEXT["web_ui.codex_state.4"].format(p1=weight)
            + ("【" + "、".join(tag_label(tag) for tag in tags) + "】" if tags else TEXT["web_ui.codex_state.5"])
            for tags, weight in loc.tag_distribution
        )
        for key, value in loc.quality_modifiers:
            delta = (float(value) - 1.0) * 100
            tier = tier_label(key)
            if "以上" in tier or "及" in tier:
                supply += TEXT["web_ui.codex_state.6"].format(p1=tier, p2=delta)
            else:
                supply += TEXT["web_ui.codex_state.7"].format(p1=tier, p2=delta)
        for key, value in loc.item_tag_modifiers:
            supply += TEXT["web_ui.codex_state.8"].format(p1=tag_label(key), p2=value)
        locations.append({
            "id": lid, "name": loc.name, "art": art_url("locations", lid),
            "desc": _pack.LOCATION_TEXT.get(lid, loc.description),
            "group": loc.group, "group_label": group_label(loc.group),
            "tier": loc.tier,
            "icon": _pack.LOCATION_ICONS.get(lid, group_icon(loc.group)), "fixed": loc.fixed,
            "supply": supply,
            # 与对局状态共用同一套"结构化"字段（清单/机制分行显示）。
            "mechanics": _location_mechanics(loc),
            "drop": _location_drop(loc),
            "tags": sorted({tag_label(t) for tags, _ in loc.tag_distribution for t in tags}),
        })
    pseudos = []
    for pid, definition in sorted(PSEUDOS.items(), key=lambda kv: kv[1].name):
        human = CHARACTERS.get(definition.human_character_id)
        # 伪人技能的图鉴文案：优先内置静态表；DLC 伪人则由其模块自声明 `CODEX_SKILLS`。
        skills = _pack.PSEUDO_SKILLS.get(pid)
        if not skills:
            module = PSEUDO_MODULES.get(pid)
            skills = getattr(module, "CODEX_SKILLS", ()) if module else ()
        pseudos.append({
            "id": pid, "name": definition.name, "art": art_url("pseudos", pid),
            "desc": definition.description,
            "human": human.name if human else definition.human_character_id,
            "human_id": definition.human_character_id if human else "",
            # 头像用**伪人自己**的：`art` 是污染版立绘，`avatar_parts` 按伪人 id 解析。
            "avatar": getattr(PSEUDO_MODULES.get(pid), "AVATAR", "") or "i-person",
            "avatar_parts": pseudo_avatar_art(pid),
            "mark_label": definition.mark_label, "enters_house": definition.enters_house,
            "breakthrough": definition.breakthrough, "liberation": definition.liberation,
            "skills": [list(skill) for skill in skills],
            "items": items_referencing("pseudos", pid),
        })
    from .data.personalities import PERSONALITY_MODULES

    personalities = []
    for key in PERSONALITIES:
        label = PERSONALITY_LABELS[key]
        module = PERSONALITY_MODULES.get(key)
        raw_tiers = getattr(module, "TIERS", None)
        tiers = list(raw_tiers) if isinstance(raw_tiers, (tuple, list)) else []
        if not tiers:
            tiers = list(_pack.PERSONALITY_TIER_HINTS.get(key, ()))
        providers = []
        for cid, definition in sorted(CHARACTERS.items(), key=lambda kv: kv[1].source_id):
            if definition.primary == key or definition.secondary == key:
                providers.append({
                    "id": cid, "name": definition.name, "avatar": avatar_of(cid),
                    "role": TEXT["web_ui.codex_state.9"] if definition.primary == key else TEXT["web_ui.codex_state.10"],
                })
        personalities.append({
            "key": key, "label": label, "desc": BOND_DESCRIPTIONS.get(key, ""),
            "icon": f"i-b-{key}", "tiers": tiers,
            "base": _pack.PERSONALITY_BASE.get(key, ""),
            "requirement": _pack.PERSONALITY_REQUIREMENT.get(key, ""),
            "tier_text": list(_pack.PERSONALITY_TIER_TEXT.get(key, ())),
            "providers": providers,
            "items": items_referencing("bonds", key),
        })
    return {
        "stats": {
            "characters": sum(1 for c in CHARACTERS.values() if c.available),
            "characters_total": len(CHARACTERS),
            "items": len(ITEMS), "locations": len(LOCATIONS),
            "information": len(INFORMATION_TEMPLATES), "pseudos": len(PSEUDOS),
        },
        "characters": characters, "items": items, "locations": locations,
        "information": information,
        "pseudos": pseudos, "personalities": personalities,
        "tagIndex": tag_index,
        "qualityNames": list(QUALITY_NAMES),
        "mechanics": [
            {"title": sec["title"], "icon": sec["icon"], "tint": sec.get("tint", ""),
             "entries": [list(e) for e in sec["entries"]]}
            for sec in _pack.MECHANICS
        ] + [
            {"title": sec.get("title", ""), "icon": sec.get("icon", "i-info"),
             "tint": sec.get("tint", ""),
             "entries": [list(e) for e in sec.get("entries", ())]}
            for sec in _pack.EXTRA_SECTIONS
        ],
    }


def apply_dlc(order: list, resourcepack_order: list | None = None) -> dict:
    """运行期热切换内容包（免重启）：按优先级重建注册表并持久化配置。

    ``order`` 为**高 → 低优先级**的内容包序列（可含 ``base``）；
    ``resourcepack_order`` 为资源包序列（高 → 低，只有独立资源包）。
    """
    available = {path.name for path in available_dlcs()}
    ordered: list[str] = []
    for name in order or ():
        name = str(name)
        if (name == "base" or name in available) and name not in ordered:
            ordered.append(name)
    if "base" not in ordered:
        ordered.append("base")
    CONFIG.pack_order = ordered
    CONFIG.enabled_dlc = [name for name in ordered if name != "base"]
    if resourcepack_order is not None:
        from .resourcepack_loader import BASE_MATERIAL, available_resourcepacks

        pack_names = {path.name for path in available_resourcepacks()}
        kept = [
            str(name) for name in resourcepack_order
            if str(name) == BASE_MATERIAL or str(name) in pack_names
        ]
        # `base` = 内置材质，恒在清单里（缺失则垫底）——位次可调，但不可移除。
        if BASE_MATERIAL not in kept:
            kept.append(BASE_MATERIAL)
        CONFIG.resourcepack_order = kept
    apply_pack_order(ordered)
    save_config(CONFIG)
    return menu_state()


def apply_settings(payload: dict) -> None:
    """把启动器设置持久化到 game_config.json。"""
    available = {path.name for path in available_dlcs()}
    if "difficulty" in payload and payload["difficulty"]:
        difficulty = str(payload["difficulty"])
        if difficulty not in DIFFICULTIES:
            raise RuleViolation(TEXT["web_ui.apply_settings.1"].format(p1=difficulty))
        CONFIG.difficulty = difficulty
    if "max_turns" in payload and payload["max_turns"]:
        CONFIG.max_turns = max(1, int(payload["max_turns"]))
    if "pseudo" in payload:
        CONFIG.default_pseudo = str(payload["pseudo"]) or None
    if "random_pseudo" in payload:
        CONFIG.random_pseudo = bool(payload["random_pseudo"])
    if "enabled_dlc" in payload:
        selected = [str(name) for name in (payload["enabled_dlc"] or ()) if str(name) in available]
        # 保持既有顺序与 base 位置，新启用的包追加到末尾（优先级最低）。
        order = [name for name in CONFIG.pack_order if name == "base" or name in selected]
        order += [name for name in selected if name not in order]
        CONFIG.pack_order = order
        CONFIG.enabled_dlc = [name for name in order if name != "base"]
    if "resourcepack_order" in payload:
        from .resourcepack_loader import available_resourcepacks

        pack_names = {path.name for path in available_resourcepacks()}
        CONFIG.resourcepack_order = [
            str(name) for name in (payload["resourcepack_order"] or ()) if str(name) in pack_names
        ]
    if "show_full_skills" in payload:
        CONFIG.show_full_skills = bool(payload["show_full_skills"])
    if "panel_draggable" in payload:
        CONFIG.panel_draggable = bool(payload["panel_draggable"])
    if "panel_pos" in payload and isinstance(payload["panel_pos"], dict):
        # 只收 [0..1, 0..1] 这样的视口比例，别的一律丢弃（玩家侧宽容）。
        clean: dict = {}
        for key, value in payload["panel_pos"].items():
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                continue
            try:
                left, top = float(value[0]), float(value[1])
            except (TypeError, ValueError):
                continue
            clean[str(key)] = [min(1.0, max(0.0, left)), min(1.0, max(0.0, top))]
        CONFIG.panel_pos = clean
    save_config(CONFIG)


def make_handler(session: Session, *, quit_server=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:  # noqa: N802
            pass

        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            # 状态/图鉴随代码与内容变动：禁止缓存，避免浏览器展示旧数据。
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path: Path) -> None:
            if not path.is_file():
                self.send_error(404)
                return
            body = path.read_bytes()
            types = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                     ".js": "application/javascript; charset=utf-8", ".svg": "image/svg+xml"}
            self.send_response(200)
            self.send_header("Content-Type", types.get(path.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            # 前端改动频繁：禁用缓存，避免浏览器展示旧版本。
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(body)

        def _send_text(self, text: str, filename: str) -> None:
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header(
                "Content-Disposition", f'attachment; filename="{filename}"'
            )
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            split = urlsplit(self.path)
            path = split.path
            if path == "/api/state":
                state = build_state(session.engine) if session.engine else {"started": False}
                self._send_json({"ok": True, "state": state, "messages": session.drain()})
                return
            if path == "/api/resourcepack":
                self._send_json({"ok": True, **resource_pack_state()})
            if path == "/api/lang":
                self._send_json({"ok": True, "text": TEXT})
                return
            if path == "/api/resourcepack/asset":
                from urllib.parse import parse_qs

                query = parse_qs(split.query)
                target = resolve_pack_asset(
                    (query.get("pack") or [""])[0], (query.get("file") or [""])[0]
                )
                if target is None:
                    self.send_error(404)
                    return
                self._send_file(target)
                return
            if path.startswith("/api/avatar/"):
                from urllib.parse import unquote

                from .avatars import resolve_avatar_part

                parts = path[len("/api/avatar/"):].split("/", 1)
                target = resolve_avatar_part(
                    unquote(parts[0]), unquote(parts[1])
                ) if len(parts) == 2 else None
                if target is None:
                    self.send_error(404)
                    return
                self._send_file(target)
                return
            if path.startswith("/api/icon/"):
                from urllib.parse import unquote

                from .icon_files import resolve_icon

                parts = path[len("/api/icon/"):].split("/", 1)
                target = resolve_icon(
                    unquote(parts[0]), unquote(parts[1])
                ) if len(parts) == 2 else None
                if target is None:
                    self.send_error(404)
                    return
                self._send_file(target)
                return
            if path == "/api/export":
                from urllib.parse import parse_qs

                name = (parse_qs(split.query).get("file") or [""])[0]
                try:
                    if name:
                        target = SAVES_DIR / Path(name).name
                        if not target.is_file():
                            self._send_json({"ok": False, "error": TEXT["web_ui.do_GET.1"]}, 404)
                            return
                        engine = GameEngine.load(target)
                        stem = target.stem
                    elif session.engine is not None:
                        engine = session.engine
                        stem = "current"
                    else:
                        self._send_json({"ok": False, "error": TEXT["web_ui.do_GET.2"]}, 400)
                        return
                    text = engine.export_full_log()
                except RuleViolation as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 400)
                    return
                self._send_text(text, f"weiren_{stem}.txt")
                return
            if path == "/api/menu":
                self._send_json({"ok": True, "menu": menu_state()})
                return
            if path == "/api/saves":
                self._send_json({"ok": True, "saves": list_saves()})
                return
            if path == "/api/codex":
                self._send_json({"ok": True, "codex": codex_state()})
                return
            target = WEBUI_DIR / ("index.html" if path in {"/", ""} else path.lstrip("/"))
            self._send_file(target)

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            try:
                if path == "/api/new":
                    session.new_game(payload)
                elif path == "/api/action":
                    session.perform(payload)
                elif path == "/api/delete_save":
                    session.delete_save(str(payload.get("file") or ""))
                elif path == "/api/load_save":
                    session.load_save(str(payload.get("file") or ""))
                elif path == "/api/abort_start":
                    # 开局「发现」期间强退：把这场还没开始的局丢掉（等价于回退到发现之前）。
                    aborted = session.abort_start()
                    self._send_json({
                        "ok": True, "aborted": aborted,
                        "state": build_state(session.engine) if session.engine else {"started": False},
                    })
                    return
                elif path == "/api/settings":
                    apply_settings(payload)
                elif path == "/api/quit":
                    # 退出游戏：与「停止游戏UI.bat」等效——先落盘，再停服，最后确保进程退出
                    # （bat 是按命令行强杀；这里补上"存档先落盘"，比强杀更稳，且不会留残留进程）。
                    self._send_json({"ok": True})
                    if quit_server is not None:
                        try:
                            session.flush_pending_save()
                        except Exception:  # noqa: BLE001 - 落盘失败不应挡住退出
                            pass
                        threading.Timer(0.25, quit_server).start()
                    return
                elif path == "/api/dlc":
                    order = payload.get("pack_order")
                    if order is None:
                        order = payload.get("enabled_dlc")
                    self._send_json({
                        "ok": True,
                        "menu": apply_dlc(order, payload.get("resourcepack_order")),
                    })
                    return
                else:
                    self._send_json({"ok": False, "error": TEXT["web_ui.do_POST.1"]}, 404)
                    return
            except RuleViolation as exc:
                self._send_json({"ok": False, "error": str(exc), "messages": session.drain()})
                return
            session.flush_pending_save()
            state = build_state(session.engine) if session.engine else {"started": False}
            self._send_json({"ok": True, "state": state, "messages": session.drain()})

    return Handler


def run_server(port: int = DEFAULT_PORT, *, open_browser: bool = True) -> None:
    try:
        load_configured_dlc()
    except Exception as exc:  # noqa: BLE001 - 单个包损坏不应阻止启动界面
        print(TEXT["web_ui.run_server.1"].format(p1=exc))
    session = Session()
    holder: dict = {}

    def _quit() -> None:
        """停服 + 确保进程退出（有卡住的请求线程也不会留下"僵尸服务"）。"""
        try:
            holder["server"].shutdown()
        except Exception:  # noqa: BLE001
            pass
        threading.Timer(0.8, lambda: __import__("os")._exit(0)).start()

    server = ThreadingHTTPServer(
        ("127.0.0.1", port),
        make_handler(session, quit_server=_quit),
    )
    holder["server"] = server
    url = f"http://127.0.0.1:{port}/"
    print(TEXT["web_ui.run_server.2"].format(p1=url))
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=TEXT["web_ui.main.1"])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    run_server(args.port, open_browser=not args.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""内容注册表、目录统计、DLC 版本门槛与分离度自检。"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from weiren_game.content import CONTENT
from weiren_game.data import CHARACTERS, INFORMATION_TEMPLATES, ITEMS, LOCATIONS, PSEUDOS
from weiren_game.data.characters import CHARACTER_CONTAINERS, CHARACTER_PANELS
from weiren_game.data.characters import erebus as erebus_module
from weiren_game.data.characters import (
    ABILITY_TARGET_OPTIONS, PROTECTED_STARTERS, SEARCH_REWARD_HOOKS,
)
from weiren_game.data import locations as location_module
from weiren_game.data import personalities as personality_module
from weiren_game.data import tags as tag_module
from weiren_game.data.labels import ITEM_TAG_LABELS, LOCATION_GROUP_LABELS
from weiren_game.config import CONFIG
from weiren_game.dlc import apply_pack_order, load_single_dlc
from weiren_game.engine import GameEngine
from weiren_game.global_event import GLOBAL_EVENT_DEFINITIONS, emotion_reveal_event
from weiren_game import data
from weiren_game import condition as condition_module
from weiren_game.tenant import CONTAINER_TYPES, TenantState

ROOT = Path(__file__).resolve().parents[1]


def _effect_totals() -> tuple[int, ...]:
    """四张效果表的条目总数：静态修饰器 / 修饰器 provider / 静态闸门 / 闸门 provider。"""
    from weiren_game.modifier_rules import (
        GATE_PROVIDERS, GATE_REGISTRY, MODIFIER_PROVIDERS, MODIFIER_REGISTRY,
    )

    return tuple(
        sum(len(bucket) for bucket in table.values())
        for table in (MODIFIER_REGISTRY, MODIFIER_PROVIDERS, GATE_REGISTRY, GATE_PROVIDERS)
    )


class ArchitectureTests(unittest.TestCase):
    def test_content_views_and_manifest(self) -> None:
        self.assertIs(CONTENT.characters(), data.CHARACTERS)
        self.assertIs(CONTENT.items(), data.ITEMS)
        self.assertIs(CONTENT.locations(), data.LOCATIONS)
        self.assertIs(CONTENT.pseudos(), data.PSEUDOS)
        self.assertIn("mcdangdang", CONTENT.items())
        self.assertIn("surgery_kit", data.TAG_BEHAVIORS)
        engine = GameEngine.new_game(seed="packs")
        self.assertIn("base", engine.state.meta.packs)
        self.assertEqual(tuple(sorted(engine.state.meta.packs)), CONTENT.manifest())

    def test_catalogue_counts(self) -> None:
        self.assertEqual(
            (len(CHARACTERS), sum(v.available for v in CHARACTERS.values())), (24, 23)
        )
        self.assertEqual(len(ITEMS), 57)
        self.assertEqual(len(LOCATIONS), 25)
        self.assertEqual(len(INFORMATION_TEMPLATES), 22)
        self.assertEqual(len(erebus_module.FATE), 22)
        self.assertEqual(set(PSEUDOS), {"pseudo_benzene", "pseudo_onion", "pseudo_fries"})

    def test_dlc_version_gate(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            too_new = root / "too_new"
            too_new.mkdir()
            (too_new / "dlc.json").write_text(
                json.dumps({"name": "too_new", "min_game_version": "99.0.0"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "要求游戏版本"):
                load_single_dlc("too_new", root=folder)
            harmless = root / "harmless"
            harmless.mkdir()
            (harmless / "dlc.json").write_text(
                json.dumps({"name": "harmless", "version": "0.1.0"}), encoding="utf-8",
            )
            load_single_dlc("harmless", root=folder)

    def test_dlc_content_channels_and_rollback(self) -> None:
        """DLC 目录投放：性格 / 状态·情绪 / tag 行为 / 地点分组 / 角色钩子；卸载后完整回滚。"""
        character_module = "\n".join((
            "from weiren_game.data.types import A, CharacterDefinition",
            "CHARACTER = CharacterDefinition(",
            "    'probe2', 9001, '探针二', '探针', 'probe2_persona', 'cheerful', 2,",
            "    ('probe2_tag',), actives=(A('probe2_active', '探针技', '探针', target='information'),),",
            ")",
            "ACTIVE_DISPATCH = {'probe2_active': lambda *a, **k: None}",
            "TARGET_OPTIONS = {'probe2_active': lambda *a, **k: []}",
            "SEARCH_REWARD = lambda *a, **k: None",
            "PROTECTED_STARTER = True",
            "from weiren_game.modifier_rules import (",
            "    gate, register_gate, register_gate_provider, register_modifier,",
            "    register_modifier_provider, spec,",
            ")",
            "register_modifier(spec('sanityConsume').path('probe2.path').flat(1))",
            "register_modifier_provider('sanityConsume', lambda context: iter(()))",
            "register_gate(gate('probe2.gate').path('probe2.path').any())",
            "register_gate_provider('probe2.gate', lambda context: iter(()))",
            "from dataclasses import dataclass",
            "@dataclass",
            "class Probe2Box:",
            "    step: int = 0",
            "    def to_dict(self):",
            "        return {'step': self.step}",
            "    @classmethod",
            "    def from_dict(cls, raw):",
            "        return cls(int(raw.get('step', 0)))",
            "CONTAINERS = {'probe2_box': Probe2Box}",
            "def _probe_panel(engine, tenant):",
            "    return {'title': '探针面板', 'prompt': '探针', 'slots': [], 'rows': [], 'actions': []}",
            "def _probe_panel_action(engine, tenant, action, slot=None, item_id=None, source=None):",
            "    tenant.turn_counters['probe_poke'] = tenant.turn_counters.get('probe_poke', 0) + 1",
            "PANEL = (_probe_panel, _probe_panel_action)",
        ))
        # 同 id 角色替换：验证"高位包覆盖内置内容"。
        replace_module = "\n".join((
            "from weiren_game.data.types import CharacterDefinition",
            "CHARACTER = CharacterDefinition('dragon', 1, '替换版房客', '替换版', 'cheerful', 'gentle', 5)",
        ))
        personality = "\n".join((
            "LABEL = '探针性格二'",
            "TIERS = (1, 2)",
            "HOOKS = {'probe2.node': lambda *a, **k: None}",
        ))
        statuses = "\n".join((
            "from weiren_game.condition import EmotionDefinition, StatusDefinition",
            "STATUSES = (StatusDefinition('probe2_status', '探针状态二', 'mental'),)",
            "EMOTIONS = (EmotionDefinition('probe2_emotion', '探针情绪二', 'mental', kind='erosion'),)",
        ))
        locations = "\n".join((
            "from weiren_game.data.types import L",
            "LOCATIONS = {'probe2_spot': L('probe2_spot', '探针地点二', '探针', 'probe2_group', (((), 1.0),))}",
            "MAP_GROUPS = {'probe2_group': {'weight': 20, 'label': '探针组', 'required': True}}",
        ))
        with tempfile.TemporaryDirectory() as folder:
            dlc = Path(folder) / "probe2"
            for name, text in (
                ("characters/probe2.py", character_module),
                ("characters/dragon.py", replace_module),
                ("personalities/probe2_persona.py", personality),
                ("statuses/probe2.py", statuses),
                ("tags/probe2_tag.py", "def after_use(engine, *a, **k):\n    return None\n"),
                ("locations/probe2.py", locations),
            ):
                path = dlc / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            (dlc / "__init__.py").write_text(
                "def register(ctx):\n    ctx.register_item_tag_label('probe2_tag', '探针标签二')\n",
                encoding="utf-8",
            )
            before = (
                set(personality_module.PERSONALITY_MODULES), set(tag_module.TAG_BEHAVIORS),
                set(condition_module.EMOTION_DEFINITIONS), set(location_module.LOCATIONS),
                set(SEARCH_REWARD_HOOKS), set(PROTECTED_STARTERS), set(ABILITY_TARGET_OPTIONS),
            )
            effects_before = _effect_totals()
            apply_pack_order(["probe2", "base"], root=folder)   # 探针包置于 base 之上
            effects_loaded = _effect_totals()
            self.assertEqual(
                tuple(now - was for now, was in zip(effects_loaded, effects_before)),
                (1, 1, 1, 1),
            )   # 静态修饰器 / 修饰器 provider / 静态闸门 / 闸门 provider 各 +1
            base_dragon = "火龙"
            self.assertNotEqual(CHARACTERS["dragon"].name, base_dragon)   # 覆盖内置角色
            self.assertIn("probe2_persona", personality_module.PERSONALITY_MODULES)
            self.assertEqual(personality_module.PERSONALITY_LABELS["probe2_persona"], "探针性格二")
            self.assertIn("probe2_persona", personality_module.PERSONALITIES)
            self.assertIn("probe2_status", condition_module.STATUS_DEFINITIONS)
            self.assertIn("probe2_emotion", condition_module.EMOTION_DEFINITIONS)
            # 情绪显现是**全局事件**（不再是被塞进房客的状态）
            self.assertIn(emotion_reveal_event("probe2_emotion"), GLOBAL_EVENT_DEFINITIONS)
            self.assertIn("probe2_emotion", condition_module.EROSION_EMOTIONS)
            self.assertIn("probe2_tag", tag_module.TAG_BEHAVIORS)
            self.assertEqual(ITEM_TAG_LABELS.get("probe2_tag"), "探针标签二")
            self.assertIn("probe2", SEARCH_REWARD_HOOKS)
            self.assertIn("probe2", PROTECTED_STARTERS)
            self.assertIn("probe2_active", ABILITY_TARGET_OPTIONS)
            self.assertIn(("probe2", "probe2_box"), CONTAINER_TYPES)   # 专属容器类型表
            self.assertIn("probe2", CHARACTER_CONTAINERS)              # 专属容器声明表
            self.assertIn("probe2", CHARACTER_PANELS)                  # 专属面板
            self.assertIn("probe2_group", location_module.BASE_MAP_GROUPS)
            self.assertEqual(LOCATION_GROUP_LABELS.get("probe2_group"), "探针组")
            # 地图是**显式名单**：新分组进了抽取权重，但地点本身要先"放进地图"才会出现。
            from weiren_game.data import BASE_MAP_ID, MAPS
            from weiren_game.data.maps import register_map_location

            self.assertNotIn("probe2_spot", MAPS[BASE_MAP_ID].locations)   # DLC 地点默认不进图
            register_map_location(BASE_MAP_ID, "probe2_spot")              # ctx.register_map_location
            self.assertIn("probe2_spot", MAPS[BASE_MAP_ID].locations)
            saved_order = list(CONFIG.pack_order)
            try:
                CONFIG.pack_order = ["probe2", "base"]
                probe_engine = GameEngine.new_game("probe2-locations", "a0")
                opening = probe_engine.state.world.locations.available_locations
                self.assertIn("probe2_spot", opening)                      # 进图后必抽（required 组）
                # 专属面板：核心只"下发视图 + 转发动作"，语义全在内容侧
                probe_tenant = TenantState(id=9901, character_id="probe2")
                probe_engine.state.house.tenants[9901] = probe_tenant
                self.assertEqual(probe_engine.panel_view(probe_tenant)["title"], "探针面板")
                probe_engine.panel_action(9901, "poke", slot=0)
                self.assertEqual(probe_tenant.turn_counters.get("probe_poke"), 1)
            finally:
                CONFIG.pack_order = saved_order
                MAPS[BASE_MAP_ID] = MAPS[BASE_MAP_ID].__class__(
                    **{**MAPS[BASE_MAP_ID].__dict__,
                       "locations": tuple(k for k in MAPS[BASE_MAP_ID].locations
                                          if k != "probe2_spot")})
            # base 调到包上方 → 内置角色重新胜出（同 id 覆盖被撤销）。
            apply_pack_order(["base", "probe2"], root=folder)
            self.assertEqual(CHARACTERS["dragon"].name, base_dragon)
            apply_pack_order(["probe2", "base"], root=folder)
            self.assertEqual(_effect_totals(), effects_loaded)   # 重复应用不累积
            apply_pack_order([], root=folder)          # 卸载 → 必须完整还原
            self.assertEqual(
                (
                    set(personality_module.PERSONALITY_MODULES), set(tag_module.TAG_BEHAVIORS),
                    set(condition_module.EMOTION_DEFINITIONS), set(location_module.LOCATIONS),
                    set(SEARCH_REWARD_HOOKS), set(PROTECTED_STARTERS), set(ABILITY_TARGET_OPTIONS),
                ),
                before,
            )
            self.assertEqual(_effect_totals(), effects_before)   # 效果表同样回滚
            self.assertNotIn(("probe2", "probe2_box"), CONTAINER_TYPES)
            self.assertNotIn("probe2", CHARACTER_CONTAINERS)
            self.assertNotIn("probe2", CHARACTER_PANELS)
            self.assertNotIn("probe2_group", location_module.BASE_MAP_GROUPS)
            self.assertNotIn("probe2_tag", ITEM_TAG_LABELS)

    def test_resource_pack_channels_and_rollback(self) -> None:
        """资源包：DLC 可覆盖材质 token、追加 CSS、新增贴图零件（贴图/材质也在内容层）。"""
        from weiren_game.data.resourcepack import RESOURCE_SYMBOLS, RESOURCE_THEME

        base_amber = RESOURCE_THEME["tokens"]["--amber"]
        # 贴图零件（SYMBOLS）：通用/地点/性格 59 个**内置零件现在也住内容层**
        # （`data/resourcepack/symbols_base.py`），前端只留一个被 CSS 引用的 svg 渐变。
        # 角色专属图形（月/太极那种）仍然写在角色自己的 py 里，不占这里。
        self.assertIn("i-person", RESOURCE_SYMBOLS)
        self.assertEqual(len(RESOURCE_SYMBOLS), 59)
        # 头像零件已独立成内容层文件：data/avatars/{shapes,features,characters}
        from weiren_game.avatars import avatar_index

        index = avatar_index()
        self.assertEqual((len(index["shapes"]), len(index["features"])), (12, 14))
        self.assertIn("hkw", index["characters"])          # 立绘就在 data/avatars/characters/（可被包覆盖）

        with tempfile.TemporaryDirectory() as folder:
            pack = Path(folder) / "skinned"
            (pack / "resourcepack").mkdir(parents=True)
            (pack / "resourcepack" / "skin.py").write_text(
                "SYMBOLS = {'i-avX': '<circle cx=\"12\" cy=\"12\" r=\"6\"/>'}\n"
                "THEME = {'tokens': {'--amber': '#ffcc66', '--q4': '#000000',"
                " '--danger': '#00ff00', '--slot': '20px', '--my-custom': '#123456'},"
                " 'css': '.skinned{color:red}'}\n",
                encoding="utf-8",
            )
            apply_pack_order(["skinned", "base"], root=folder)
            self.assertEqual(RESOURCE_THEME["tokens"]["--amber"], "#ffcc66")   # 覆盖内置材质
            # 语义色 / 品质色 / 尺寸被锁定：资源包改不动（含义与布局不随皮肤变）
            self.assertNotEqual(RESOURCE_THEME["tokens"]["--q4"], "#000000")
            self.assertNotEqual(RESOURCE_THEME["tokens"]["--danger"], "#00ff00")
            self.assertEqual(RESOURCE_THEME["tokens"]["--slot"], "60px")
            self.assertEqual(RESOURCE_THEME["tokens"]["--my-custom"], "#123456")  # 自定义 token 允许
            self.assertIn("i-avX", RESOURCE_SYMBOLS)                            # 可新增零件
            self.assertIn(".skinned", str(RESOURCE_THEME["css"]))

            apply_pack_order([], root=folder)                                    # 卸载 → 全部回滚
            self.assertEqual(RESOURCE_THEME["tokens"]["--amber"], base_amber)
            self.assertNotIn("--my-custom", RESOURCE_THEME["tokens"])
            self.assertNotIn("i-avX", RESOURCE_SYMBOLS)
            # 回滚回的是 **base 材质**（内置零件仍在），不是"什么都没有"
            self.assertEqual(len(RESOURCE_SYMBOLS), 59)
            self.assertNotIn(".skinned", str(RESOURCE_THEME["css"]))

    def test_resource_pack_defaults_match_frontend_fallback(self) -> None:
        """前端 `:root` 兜底块必须与 base 资源包**逐一相同**。

        否则资源包一取不到就掉材质——不只颜色/字体，**布局 token 也会没**：
        `--slot` 消失会让仓库网格 `repeat(6,var(--slot))` 整条声明失效，变成一格一排。
        """
        import io
        import re as _re

        from weiren_game.data.resourcepack import RESOURCE_THEME

        html = (ROOT / "weiren_game" / "webui" / "index.html").read_text(encoding="utf-8")
        block = _re.search(r":root\{(.*?)\n  \}", html, _re.S)
        self.assertIsNotNone(block, "index.html 缺少 :root 默认材质块")
        fallback = {
            name: value.strip()
            for name, value in _re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+)", block.group(1))
        }
        self.assertEqual(fallback, dict(RESOURCE_THEME["tokens"]))
        # --amber-rgb 是 --amber 的分量，供 rgba(var(--amber-rgb),α) 的透明叠加用：必须同步。
        hex_amber = fallback["--amber"].lstrip("#")
        rgb = ",".join(str(int(hex_amber[index:index + 2], 16)) for index in (0, 2, 4))
        self.assertEqual(fallback["--amber-rgb"], rgb)

    def test_standalone_resourcepack_apply_and_rollback(self) -> None:
        """独立资源包：只改外观、可回滚、锁定 token 改不动、素材位可解析且防目录穿越。"""
        from weiren_game.data.resourcepack import RESOURCE_ASSETS, RESOURCE_THEME
        from weiren_game.resourcepack_loader import apply_resourcepack_order, available_resourcepacks
        from weiren_game.web_ui import resolve_pack_asset

        self.assertIn("blood_moon", [path.name for path in available_resourcepacks()])
        base_bg = RESOURCE_THEME["tokens"]["--bg"]
        locked_q4 = RESOURCE_THEME["tokens"]["--q4"]

        apply_resourcepack_order(["blood_moon"])
        self.assertNotEqual(RESOURCE_THEME["tokens"]["--bg"], base_bg)      # 色调跟着变
        self.assertEqual(RESOURCE_THEME["tokens"]["--q4"], locked_q4)       # 品质色锁定
        self.assertEqual(RESOURCE_THEME["tokens"]["--slot"], "60px")        # 尺寸锁定
        self.assertIn("blood_moon", RESOURCE_ASSETS["background"])          # 素材位登记
        self.assertTrue(resolve_pack_asset("blood_moon", "background.svg").is_file())
        self.assertIsNone(resolve_pack_asset("blood_moon", "../theme.py"))   # 目录穿越被拒

        apply_resourcepack_order([])                                        # 卸载 → 回默认材质
        self.assertEqual(RESOURCE_THEME["tokens"]["--bg"], base_bg)
        # base 现在**自带封面素材位**（`data/resourcepack/assets/background.svg`）：
        # 回滚回的是 base 的那张，而不是"没有背景"。
        self.assertIn("pack=&file=background.svg", RESOURCE_ASSETS["background"])

    def test_avatar_parts_follow_content_and_pack_priority(self) -> None:
        """头像零件走内容层文件：base → 资料包 → 资源包（位次高者赢）；且与存档解耦。"""
        from types import SimpleNamespace

        from weiren_game import avatars
        from weiren_game.data import CHARACTER_MODULES

        svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'/>"
        saved_order = (list(CONFIG.pack_order), list(CONFIG.resourcepack_order))

        with tempfile.TemporaryDirectory() as dlc_dir, tempfile.TemporaryDirectory() as rp_dir:
            dlc = Path(dlc_dir) / "avatarpack" / "avatars"
            (dlc / "characters").mkdir(parents=True)
            (dlc / "shapes").mkdir(parents=True)
            (dlc / "characters" / "hkw.svg").write_text(svg, encoding="utf-8")
            (dlc / "shapes" / "i-av1.svg").write_text(svg, encoding="utf-8")
            rp = Path(rp_dir) / "avatarpack" / "avatars" / "shapes"
            rp.mkdir(parents=True)
            (rp / "i-av1.svg").write_text(svg, encoding="utf-8")

            CONFIG.pack_order = ["avatarpack", "base"]
            CONFIG.resourcepack_order = ["avatarpack"]
            try:
                # ① 资料包的整张头像盖过外置美术立绘
                view = avatars.avatar_view("hkw", CHARACTER_MODULES.get("hkw"),
                                           dlc_root=dlc_dir, rp_root=rp_dir)
                self.assertEqual(view["full"], "/api/avatar/characters/hkw")
                # ② 零件覆盖：资源包位次高于资料包 → 命中资源包那份文件
                picked = avatars.resolve_avatar_part("shapes", "i-av1",
                                                     dlc_root=dlc_dir, rp_root=rp_dir)
                self.assertEqual(picked, rp / "i-av1.svg")
                # ③ 没立绘的角色走"组装"，形状/特征/点缀色都有具体值
                assembled = avatars.avatar_view("ghost", SimpleNamespace(AVATAR="i-av1"),
                                                dlc_root=dlc_dir, rp_root=rp_dir)
                self.assertEqual(assembled["shape"], "/api/avatar/shapes/i-av1")
                self.assertTrue(assembled["feature"])
                # 缺省派生是**确定性**的：同一 id 每次一样
                plain = avatars.avatar_view("ghost", None)
                self.assertEqual(plain["shape"], avatars.avatar_view("ghost", None)["shape"])
                # 点缀色/点缀环已废弃：不再出现在视图里
                self.assertNotIn("accent", plain)
                self.assertNotIn("decor", plain)
                # ④ 目录穿越/未知分区一律拒绝
                self.assertIsNone(avatars.resolve_avatar_part("shapes", "../theme.py"))
                self.assertIsNone(avatars.resolve_avatar_part("nope", "i-av1"))
            finally:
                CONFIG.pack_order, CONFIG.resourcepack_order = saved_order

        # ⑤ 存档里没有任何头像/资源包数据：资源包可随时移除，不影响存档
        engine = GameEngine.new_game("save-probe", "a0")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            engine.save(path)
            payload = path.read_text(encoding="utf-8")
        # 存档只记 meta/流程/世界/房客…；头像与材质都是"显示层"，一个字段都不进存档
        def keys(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield str(key)
                    yield from keys(value)
            elif isinstance(node, list):
                for value in node:
                    yield from keys(value)

        import json as _json

        def is_presentation(key: str) -> bool:
            name = key.lower()
            # 精确匹配字段名（"start.discover" 这类计数键不算——"art" 是子串）
            return (name in ("art", "theme", "avatar", "resourcepack", "resourcepack_order")
                    or name.startswith("avatar"))

        leaked = [key for key in keys(_json.loads(payload)) if is_presentation(key)]
        self.assertEqual(leaked, [])

    def test_icon_files_and_start_abort(self) -> None:
        """地点/信息/伪人图标走内容层（资料包/资源包可覆盖）；开局发现能整局丢弃。"""
        from types import SimpleNamespace

        from weiren_game import icon_files
        from weiren_game.web_ui import Session

        # ① 三张表都有内容（从 assets/art 搬进 data/icon/）
        for section, expected in (("locations", 25), ("information", 22), ("pseudos", 3)):
            self.assertEqual(len(icon_files.icon_index(section)), expected, section)
            self.assertEqual(icon_files.SECTIONS.count(section), 1)
        # ② URL 走新接口；未知 id / 非法分区 / 目录穿越一律不认
        url = icon_files.icon_url("locations", "county_hospital")
        self.assertEqual(url, "/api/icon/locations/county_hospital")
        self.assertEqual(icon_files.icon_url("locations", "nope"), "")
        self.assertIsNone(icon_files.resolve_icon("nope", "county_hospital"))
        self.assertIsNone(icon_files.resolve_icon("locations", "../config.py"))
        self.assertIsNone(icon_files.resolve_icon("locations", "../../weiren_game/config.py"))
        self.assertEqual(icon_files.icon_index("nope"), {})

        # ③ 包覆盖：资源包位次高于资料包 → 命中资源包那份
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"/>'
        saved = (list(CONFIG.pack_order), list(CONFIG.resourcepack_order))
        with tempfile.TemporaryDirectory() as dlc_dir, tempfile.TemporaryDirectory() as rp_dir:
            dlc = Path(dlc_dir) / "iconpack" / "icon" / "locations"
            dlc.mkdir(parents=True)
            (dlc / "county_hospital.svg").write_text(svg, encoding="utf-8")
            rp = Path(rp_dir) / "iconpack" / "icon" / "locations"
            rp.mkdir(parents=True)
            (rp / "county_hospital.png").write_text("x", encoding="utf-8")
            CONFIG.pack_order = ["iconpack", "base"]
            CONFIG.resourcepack_order = ["iconpack"]
            try:
                picked = icon_files.resolve_icon("locations", "county_hospital",
                                                  dlc_root=dlc_dir, rp_root=rp_dir)
                self.assertEqual(picked, rp / "county_hospital.png")
                # 只有资料包也有这张图时，资源包没提供才落到资料包
                (rp / "county_hospital.png").unlink()
                self.assertEqual(icon_files.resolve_icon("locations", "county_hospital",
                                                          dlc_root=dlc_dir, rp_root=rp_dir),
                                 dlc / "county_hospital.svg")
            finally:
                CONFIG.pack_order, CONFIG.resourcepack_order = saved

        # ④ 开局「发现」还没选完 → abort_start 丢掉这场局（存档回到发现之前）
        engine = GameEngine.new_game("abort-probe", "a0", defer_start=True)
        self.assertEqual(engine._pending_choice.get("kind"), "start_choice")
        session = Session()
        session.engine = engine
        session.save_path = Path("x.json")
        session._pending_save = {"name": "x"}
        self.assertTrue(session.abort_start())
        self.assertIsNone(session.engine)
        self.assertIsNone(session.save_path)
        self.assertIsNone(session._pending_save)
        # 已经开打的局（没有开局待选）不受影响
        session.engine = SimpleNamespace(_pending_choice=None)
        self.assertFalse(session.abort_start())
        self.assertIsNotNone(session.engine)
        session.engine = SimpleNamespace(_pending_choice={"kind": "start_choice"})
        self.assertTrue(session.abort_start())

    def test_item_icons_follow_tags_and_pack_priority(self) -> None:
        """物品图标：专属 → 标签兜底，base → 资料包 → 资源包；品质色特征 + 白底。"""
        from types import SimpleNamespace

        from weiren_game import item_icons
        from weiren_game.data.labels import QUALITY_COLORS
        from weiren_game.data.resourcepack import RESOURCE_THEME

        # 品质色与默认材质的 --q0..--q5 是同一组值（锁定的语义色，资源包改不动）
        tokens = RESOURCE_THEME["tokens"]
        self.assertEqual(list(QUALITY_COLORS),
                         [tokens[f"--q{i}"] for i in range(len(QUALITY_COLORS))])

        here = Path(__file__).resolve().parent.parent / "weiren_game" / "data" / "item"
        index = item_icons.item_icon_index()
        self.assertEqual(len(index["item"]), 57)          # 57 张物品图标已进内容层
        self.assertIn("surgery_kit", index["tag"])        # 标签兜底图

        # ① 专属图标优先：有 item/item/<id>.svg 就绝不用标签图
        item = ITEMS["emergency_medicine"]
        self.assertEqual(item_icons.resolve_item_icon(item.item_id, item.tags),
                         here / "item" / "emergency_medicine.svg")
        # ② 没有专属图标 → 按**具象标签优先**挑 tag 图（耐久度消耗品不该抢占手术包）
        ghost = SimpleNamespace(item_id="ghost_item",
                                tags=("durability_consumable", "surgery_kit"), quality=5)
        self.assertEqual(item_icons.resolve_item_icon(ghost.item_id, ghost.tags),
                         here / "tag" / "surgery_kit.svg")
        # ③ 两色：底色 → currentColor（界面给主题 --ink）、特征色 → 该物品的品质色
        markup = item_icons.item_icon_markup(ghost)
        self.assertIn("currentColor", markup)
        self.assertNotIn("#d7ddd2", markup)               # 旧底色已被替换
        self.assertNotIn("#a77ad1", markup)               # 标签图的烘焙色也被替换
        self.assertIn(QUALITY_COLORS[5], markup)          # 该物品的品质色
        self.assertIn('style="color:var(--ink)"', markup)
        self.assertNotRegex(markup.split(">")[0], r'(?<![-\w])(?:width|height)\s*=')  # 尺寸交给 CSS
        # ④ 未知物品 / 目录穿越一律不认（标签名只接受裸 tag）
        self.assertIsNone(item_icons.resolve_item_icon("nope", ("nope_tag",)))
        self.assertIsNone(item_icons.resolve_item_icon("../theme", ("../../config",)))
        self.assertIsNone(item_icons.resolve_item_icon("nope", ("../item/surgery_kit",)))
        self.assertEqual(item_icons.item_icon_markup(SimpleNamespace(item_id="nope", tags=(), quality=0)), "")

        # ⑤ 包覆盖：资料包加一张专属图就能当"自带物品的材质"，资源包位次更高者赢
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
               '<path d="M4 4h24" stroke="#d7ddd2"/><path d="M4 9h24" stroke="#d7ddd2"/></svg>')
        saved_order = (list(CONFIG.pack_order), list(CONFIG.resourcepack_order))
        with tempfile.TemporaryDirectory() as dlc_dir, tempfile.TemporaryDirectory() as rp_dir:
            dlc = Path(dlc_dir) / "itempack" / "item" / "item"
            dlc.mkdir(parents=True)
            (dlc / "ghost_item.svg").write_text(svg, encoding="utf-8")
            rp = Path(rp_dir) / "itempack" / "item" / "item"
            rp.mkdir(parents=True)
            (rp / "ghost_item.svg").write_text(svg, encoding="utf-8")
            CONFIG.pack_order = ["itempack", "base"]
            CONFIG.resourcepack_order = ["itempack"]
            try:
                picked = item_icons.resolve_item_icon("ghost_item", (),
                                                     dlc_root=dlc_dir, rp_root=rp_dir)
                self.assertEqual(picked, rp / "ghost_item.svg")   # 资源包 > 资料包
                # 资源包也提供 tag 图时，标签兜底同样能命中
                tag = Path(rp_dir) / "itempack" / "item" / "tag"
                tag.mkdir(parents=True)
                (tag / "surgery_kit.svg").write_text(svg, encoding="utf-8")
                self.assertEqual(item_icons.resolve_item_icon("nope", ("surgery_kit",),
                                                              dlc_root=dlc_dir, rp_root=rp_dir),
                                 tag / "surgery_kit.svg")
            finally:
                CONFIG.pack_order, CONFIG.resourcepack_order = saved_order

        # ⑥ 带脚本的图标整张丢弃（内联进 HTML 前必须拒绝）
        with tempfile.TemporaryDirectory() as folder:
            sized = Path(folder) / "sized.svg"
            sized.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"'
                             ' viewBox="0 0 32 32"><path d="M2 2h28" stroke="#d7ddd2"/></svg>',
                             encoding="utf-8")
            with unittest.mock.patch.object(item_icons, "resolve_item_icon", return_value=sized):
                sized_markup = item_icons.item_icon_markup(ghost)
            self.assertNotRegex(sized_markup.split(">")[0], r'(?<![-\w])(?:width|height)\s*=')
            evil = Path(folder) / "x.svg"
            evil.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>x</script></svg>',
                            encoding="utf-8")
            with unittest.mock.patch.object(item_icons, "resolve_item_icon", return_value=evil):
                self.assertEqual(item_icons.item_icon_markup(ghost), "")

    def test_resourcepack_base_row_and_wafu_style(self) -> None:
        """资源包清单里的 `base` 可调位次；血月包把**全部头像配件**换成和风（含色槽规则）。"""
        from weiren_game import avatars
        from weiren_game.data import CHARACTER_MODULES
        from weiren_game.data.resourcepack import RESOURCE_ASSETS
        from weiren_game.resourcepack_loader import apply_resourcepack_order

        def bg() -> str:
            from weiren_game.data.resourcepack import RESOURCE_THEME

            return str(RESOURCE_THEME["tokens"]["--bg"])

        saved = (list(CONFIG.pack_order), list(CONFIG.resourcepack_order))
        base_bg = bg()
        try:
            # ① base 垫底（缺省）：血月的外观生效
            CONFIG.resourcepack_order = ["blood_moon", "base"]
            self.assertEqual(apply_resourcepack_order(CONFIG.resourcepack_order),
                             ["blood_moon", "base"])
            self.assertNotEqual(bg(), base_bg)
            # ② 血月声明 avatar_mode=parts → 全员改用零件组装（跳过立绘兜底）
            self.assertEqual(avatars.avatar_mode(), "parts")
            view = avatars.avatar_view("hkw", CHARACTER_MODULES.get("hkw"))
            self.assertEqual(view["full"], "")
            # 界面据此**忽略立绘**（否则包那套零件永远看不到）
            self.assertTrue(view["use_parts"])
            self.assertEqual(view["shape"], "/api/avatar/shapes/i-av11")
            self.assertTrue(view["shape_svg"] and view["feature_svg"])    # 和风零件自带颜色 → 内联
            self.assertNotIn("width=", view["shape_svg"].split(">")[0])   # 尺寸交给 CSS
            # ③ base 抬到血月上方：内置材质赢，但血月新增的素材位保留
            CONFIG.resourcepack_order = ["base", "blood_moon"]
            apply_resourcepack_order(CONFIG.resourcepack_order)
            self.assertEqual(bg(), base_bg)
            self.assertIn("title", RESOURCE_ASSETS)
            # ④ 空清单 / 只给包名：base 自动补齐且垫底
            self.assertEqual(apply_resourcepack_order([]), ["base"])
            self.assertEqual(apply_resourcepack_order(["blood_moon"]), ["blood_moon", "base"])
            # ⑤ 色槽：零件写了 var(--a/b) 就能被创作者填色，缺省退主题 token；
            #    色槽是留给创作者的 —— base 与血月自带的零件**都不写**色槽。
            here = Path(__file__).resolve().parent.parent / "weiren_game" / "data"
            self.assertEqual(avatars.part_markup(here / "avatars" / "shapes" / "i-av1.svg"), "")
            with tempfile.TemporaryDirectory() as folder:
                part = Path(folder) / "slot.svg"
                part.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                    '<path d="M4 4h16" stroke="var(--a)"/><path d="M4 9h16" stroke="var(--b)"/>'
                    "</svg>",
                    encoding="utf-8",
                )
                markup = avatars.part_markup(part, colors={"a": "#123456"})
                self.assertIn("#123456", markup)        # 创作者给的颜色
                self.assertIn("var(--ink)", markup)     # 没给的槽退回主题 token
                self.assertNotIn("var(--a)", markup)
                self.assertNotIn("<script", avatars.part_markup(
                    part, colors={"a": '"><script>'}))   # 非法颜色不会漏进标记
        finally:
            CONFIG.pack_order, CONFIG.resourcepack_order = saved[0], ["base"]
            apply_resourcepack_order(["base"])

    def test_separation_audit(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "audit_separation.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

"""Deterministic, saveable rules engine for the complete manuscript scenario.

The engine deliberately performs no input/output.  The terminal UI is one client;
tests and future graphical clients can drive exactly the same public methods.
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any, Sequence

from weiren_game.content import CONTENT
from .data import (
    AWAKENING_EMOTIONS,
    BASE_MAP_GROUPS,
    BOND_DESCRIPTIONS,
    DEFAULT_PSEUDO,
    DIFFICULTIES,
    EROSION_EMOTIONS,
    EVENT_IDS,
    FIXED_LOCATIONS,
    GAME_VERSION,
    INFORMATION_TEMPLATES,
    LOCATION_GROUPS,
    MAP_DRAW_WEIGHTS,
    PERSONALITY_LABELS,
    RARE_EMOTIONS,
    PROTECTED_STARTERS,
    START_LOOT_TABLE,
    CharacterDefinition,
    CODEX_SUMMARY_HOOKS,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from .models import GameState
from .tenant import TenantState
from .ability import AbilityState
from .session import GameFlowState, InstancePool, SaveMetadata
from .pseudo import PseudoRuntime
from .exceptions import RuleViolation


from .systems.random_system import RandomSystemMixin
from .systems.item_system import ItemSystemMixin
from .systems.personality_system import PersonalitySystemMixin
from .systems.condition_system import ConditionSystemMixin
from .systems.value_system import ValueSystemMixin
from .systems.visitor_system import VisitorSystemMixin
from .systems.search_system import SearchSystemMixin
from .systems.pseudo_system import PseudoSystemMixin
from .systems.information_system import InformationSystemMixin
from .systems.ability_system import AbilitySystemMixin
from .systems.cost_system import CostSystemMixin
from .systems.round_effects import RoundEffectsSystemMixin
from .systems.marks_system import MarksSystemMixin
class GameEngine(
    RandomSystemMixin,
    ItemSystemMixin,
    PersonalitySystemMixin,
    ConditionSystemMixin,
    ValueSystemMixin,
    VisitorSystemMixin,
    SearchSystemMixin,
    PseudoSystemMixin,
    InformationSystemMixin,
    AbilitySystemMixin,
    CostSystemMixin,
    RoundEffectsSystemMixin,
    MarksSystemMixin,
):
    """Complete round loop and game rules, with deterministic event randomness."""

    # 伪人到访采用累加概率：起始与增量默认 15%（a0），错过一次 +15%，
    # 命中后回到起始值；起始/增量可由难度（a3=20%、a-3=10%）调整。
    # 日历由 PseudoSystem._roll_next_pseudo_visit 在开局与每次到访后生成。
    # 基础搜索回合按携带容量的 ±25% 范围由 SearchSystem 计算。

    def __init__(self, state: GameState):
        """初始化引擎，绑定游戏状态并准备消息队列。"""
        self.state = state
        self._messages: list[tuple[str, dict | None]] = []
        self._log_collector: list[dict] | None = None
        self._pending_ability: list[dict[str, Any]] = []
        self._pending_interaction: object | None = None
        # 通用待选（任何 discover 期间）：非 None 时禁止其它行为。
        self._pending_choice: dict[str, Any] | None = None
        from .ui import CliUI

        self.ui: object = CliUI()
        # 最近一次存档路径：discover 开始前自动保存。
        self._save_path: Path | None = None
        # 技能/概率效果的“多次扳机”聚合：skill_id -> 是否至少成功一次。
        self._skill_outcome_records: dict[str, bool] = {}
        # 待选后续动作（如该性格第二次 discover 或选择后的应用）。
        self._pending_resume: Any | None = None

    def _autosave_before_discover(self) -> None:
        """discover 是原子行为：开始前若已有存档路径则自动保存（不打扰玩家）。"""
        if self._save_path is not None and self._pending_choice is None:
            self.save(self._save_path, quiet=True)

    def _require_no_pending_choice(self) -> None:
        """存在待选（discover 未结算）时禁止其它行为。"""
        if self._pending_choice is not None:
            raise RuleViolation("正在等待玩家选择，无法进行其它操作。")

    def choose_discover(self, option: object) -> object:
        """提交一次 discover 选择并解除待选状态。"""
        if self._pending_choice is None:
            raise RuleViolation("当前没有待选择项。")
        if option not in self._pending_choice.get("options", ()):
            raise RuleViolation("该选项不在本次选择范围内。")
        self._pending_choice = None
        resume = self._pending_resume
        self._pending_resume = None
        if resume is not None:
            resume(option)
        return option

    def _clear_pending_choice(self) -> None:
        """内部直接清除待选（自动选择/结算完成时）。"""
        self._pending_choice = None
        self._pending_resume = None

    def pending_view(self) -> dict | None:
        """返回当前待处理交互的通用视图（prompt/options/cancel），供任意前端渲染。"""
        from .data import PENDING_VIEWS

        for build, _resolve in PENDING_VIEWS:
            view = build(self)
            if view is not None:
                return view
        return None

    def resolve_view(self, value: object) -> None:
        """把玩家选择交回当前待处理交互的解析器（由内容声明）。"""
        from .data import PENDING_VIEWS

        for build, resolve in PENDING_VIEWS:
            if build(self) is not None:
                resolve(self, value)
                return
        raise RuleViolation("当前没有待处理的交互。")

    # ------------------------------------------------------------------ setup
    @classmethod
    def new_game(
        cls,
        seed: str | None = None,
        difficulty: str | None = None,
        max_turns: int | None = None,
        pseudo_id: str | None = None,
        disabled_character_ids: Sequence[str] | None = None,
        random_pseudo: bool | None = None,    # 置 True 时按种子随机伪人，并按 20% 比例自动禁用角色。
        start_choices: Sequence[str] | None = None,  #开局两次 Discover(3) 的玩家选择；缺省时确定性自动补选。
        defer_start: bool = False,            # 置 True 时先不选房客，交出待选让前端分步选择。
        map_id: str | None = None,            # 本局用哪张地图（区域包）；None = 默认地图。
    ) -> "GameEngine":
        """按种子与参数创建一局新游戏，完成初始房客、地点与补给生成后返回引擎。"""
        from weiren_game.config import CONFIG
        from weiren_game.dlc import load_configured_dlc

        # 启动装载：按总配置的 pack_order（高 → 低优先级）装载启用的内容包。
        load_configured_dlc()
        difficulty = CONFIG.difficulty if difficulty is None else difficulty
        max_turns = CONFIG.max_turns if max_turns is None else max_turns
        random_pseudo = (
            CONFIG.random_pseudo if random_pseudo is None else random_pseudo
        )
        resolved_seed = seed or secrets.token_hex(6)
        if pseudo_id is None:
            pseudo_id = CONFIG.default_pseudo or DEFAULT_PSEUDO
        if pseudo_id not in PSEUDOS and PSEUDOS:
            pseudo_id = next(iter(PSEUDOS))
        from weiren_game.random_log import LoggedRandom

        start_log: list[str] = []
        choice_rng = LoggedRandom(
            resolved_seed,
            "开局选择",
            lambda line: start_log.append(line),
        )
        if random_pseudo:
            pseudo_id = choice_rng.choice(tuple(PSEUDOS))
        if difficulty not in DIFFICULTIES:
            raise RuleViolation(f"未知难度：{difficulty}")
        if max_turns < 12:
            raise RuleViolation("目标回合数不能少于12。")
        if pseudo_id not in PSEUDOS:
            raise RuleViolation(f"未知伪人：{pseudo_id}")

        pseudo_def = PSEUDOS[pseudo_id]
        disabled: list[str] = []
        # 运行时计算：DLC 加载后 PSEUDOS 会变，模块级常量会漏掉 DLC 伪人的人类形态。
        human_characters = {value.human_character_id for value in PSEUDOS.values()}

        for character_id in disabled_character_ids or ():
            if character_id not in CHARACTERS or not CHARACTERS[character_id].available:
                raise RuleViolation(f"无法禁用未知或未公开房客：{character_id}")
            if character_id in PROTECTED_STARTERS:
                raise RuleViolation("开局核心角色不能被禁用。")
            if character_id in human_characters:
                raise RuleViolation("伪人的人类原型不能列入禁用角色。")
            if character_id not in disabled:
                disabled.append(character_id)
        from .data import BASE_MAP_ID, MAPS

        resolved_map_id = str(map_id or BASE_MAP_ID)
        if resolved_map_id not in MAPS:
            resolved_map_id = BASE_MAP_ID
        ids = InstancePool()
        state = GameState(
            meta=SaveMetadata(
                version=GAME_VERSION,
                seed=resolved_seed,
                difficulty=difficulty,
                packs=CONTENT.manifest(),
                map_id=resolved_map_id,
            ),
            flow=GameFlowState(max_turns=max_turns),
            ids=ids,
            pseudo_state=PseudoRuntime(
                pseudo_instance_id=ids.allocate_pseudo(),
                scenario_id=pseudo_id,
                name=pseudo_def.name,
            ),
        )
        state.world.disabled_characters = list(disabled)
        engine = cls(state)
        for line in start_log:
            engine._record_log(line)
        state.world.visitors.next_pseudo_turn = engine._roll_next_pseudo_visit(1)
        roster = [
            key for key, definition in CHARACTERS.items()
            if definition.available and key != pseudo_def.human_character_id and key not in disabled
        ]
        if random_pseudo:
            ban_count = min(5, int(len(roster) * 0.2))
            ban_count = max(0, min(ban_count, len(roster) - 2))
            ban_candidates = [
                key for key in roster if key not in PROTECTED_STARTERS
            ]
            ban_count = min(ban_count, len(ban_candidates))
            for character_id in choice_rng.sample(ban_candidates, ban_count):
                roster.remove(character_id)
                disabled.append(character_id)
        state.world.disabled_characters = list(disabled)
        starter_count = max(
            1,
            2 + int(DIFFICULTIES[difficulty].get("start_tenants_delta", 0)),
        )
        if len(roster) < starter_count:
            raise RuleViolation(
                f"禁用角色过多，至少需要 {starter_count} 名可用人类房客。"
            )
        pool = list(roster)
        if defer_start and start_choices is None:
            engine._start_pool = pool
            engine._start_count = starter_count
            engine._start_starters: list[str] = []
            engine._begin_start_pick()
            return engine
        starters: list[str] = []
        for pick_index in range(starter_count):
            guaranteed = [key for key in CHARACTERS if key in PROTECTED_STARTERS and key in pool]
            options = engine.discover(
                pool,
                count=3,
                required=guaranteed or None,
                event_id=EVENT_IDS["start.discover"],
                event_suffix=(pick_index,),
            )
            chosen = None
            if start_choices is not None:
                chosen = (
                    start_choices[pick_index]
                    if pick_index < len(start_choices)
                    else None
                )
                if chosen not in options:
                    names = "、".join(CHARACTERS[value].name for value in options)
                    raise RuleViolation(
                        f"第{pick_index + 1}次发现必须从以下选项选择：{names}。"
                    )
            if chosen is None:
                chosen = options[0]
            starters.append(chosen)
            engine._clear_pending_choice()
            pool.remove(chosen)
        engine._finish_start(starters, pool)
        return engine

    def _begin_start_pick(self) -> list[str]:
        """计算下一次开局 Discover(3) 的候选，作为待选交出去。"""
        pool = self._start_pool
        pick_index = len(self._start_starters)
        guaranteed = [key for key in CHARACTERS if key in PROTECTED_STARTERS and key in pool]
        options = list(self.discover(
            pool, count=3, required=guaranteed or None,
            event_id=EVENT_IDS["start.discover"], event_suffix=(pick_index,),
        ))
        self._pending_choice = {"kind": "start_choice", "pick_index": pick_index, "options": options}
        return options

    def commit_start_choice(self, choice: str | None = None) -> None:
        """提交一次开局选人；全部选完后创建房客并完成开局。"""
        pending = self._pending_choice
        if not pending or pending.get("kind") != "start_choice":
            raise RuleViolation("当前没有开局选择。")
        options = list(pending["options"])
        chosen = choice if choice in options else options[0]
        self._clear_pending_choice()
        self._start_starters.append(chosen)
        self._start_pool.remove(chosen)
        if len(self._start_starters) < self._start_count:
            self._begin_start_pick()
            return
        starters, pool = self._start_starters, self._start_pool
        for attr in ("_start_pool", "_start_count", "_start_starters"):
            if hasattr(self, attr):
                delattr(self, attr)
        self._finish_start(starters, pool)

    def _finish_start(self, starters: list[str], pool: list[str]) -> None:
        """开局收尾：创建初始房客、生成地点、激活羁绊并记录日志。"""
        state = self.state
        difficulty = str(state.meta.difficulty)
        max_turns = state.flow.max_turns
        pseudo_def = PSEUDOS[state.pseudo_state.scenario_id]
        for character_id in starters:
            self._add_tenant(character_id)
        # 初始房客视为“开局瞬间被接纳”，结算入住赠礼与该性格治愈。
        for tenant in self.home_tenants():
            self._on_tenant_accepted(tenant)
        # 难度词条：开局房客的当前/最大生命与理智调整（仅开局这一次）。
        vital_entry = DIFFICULTIES[difficulty]
        vital_pct = float(vital_entry.get("start_vital_pct", 0.0))
        max_pct = float(vital_entry.get("start_vital_max_pct", 0.0))
        if vital_pct or max_pct:
            for tenant in self.home_tenants():
                if max_pct:
                    tenant.max_health *= 1 + max_pct
                    tenant.max_sanity *= 1 + max_pct
                if vital_pct:
                    tenant.health = max(0.0, tenant.health * (1 + vital_pct))
                    tenant.sanity = max(0.0, tenant.sanity * (1 + vital_pct))
        # 难度词条：开局房客的初始消沉值。
        depression_delta = float(
            vital_entry.get("start_depression_delta", 0.0)
        )
        if depression_delta:
            for tenant in self.home_tenants():
                tenant.depression = max(
                    -10000.0, min(10000.0, tenant.depression + depression_delta)
                )
        state.world.visitors.visitor_pool = list(pool)
        # 访客到访顺序随机（按种子确定），不再按角色注册顺序。
        self._rng(EVENT_IDS["visitor.queue"]).shuffle(state.world.visitors.visitor_pool)
        state.world.locations.available_locations = self._generate_locations()
        # 开局补给（需在地点生成之后：报纸/录像带等载体会即时兑换为信息）。
        # 时运走修饰器管线：全局 fortune_delta（a4/a-4）与仅开局生效的
        # start_fortune_delta 都以「开局」为 source 在此处被收集。
        start_fortune = self._apply_modifiers(
            "search", 0.0, ("开局", "时运"), {"tenant": None, "rng": None},
        )
        draw_delta = int(DIFFICULTIES[difficulty].get("start_loot_draws", 0))
        for label, count in self._start_loot_schedule(draw_delta):
            candidates = list(START_LOOT_TABLE.get(label, ()))
            if not candidates:
                continue
            for item_id in self._start_loot_draw(candidates, count, start_fortune, label):
                self._gain_item(item_id)
        self._activate_new_bonds(initial=True)
        names = "、".join(self.character(t).name for t in self.home_tenants())
        self._log(f"本局种子：{state.meta.seed}；难度：{difficulty}（{DIFFICULTIES[difficulty]['label']}）。", shown=False)
        human = CHARACTERS.get(pseudo_def.human_character_id)
        human_name = human.name if human else pseudo_def.human_character_id
        self._log(f"本局伪人：{pseudo_def.name}。人类形态“{human_name}”不会自然出现。", shown=False)
        self._log(f"天色已暗。{names}已经在屋里，门外的道路一片漆黑。")
        self._log(f"目标：撑到第{max_turns}回合结束，或先完成伪人的解放条件。")

    def _start_loot_schedule(self, draw_delta: int) -> list[tuple[str, int]]:
        """开局补给次数表：基础为食物 2 / 医疗 1 / 工具 1 / 载体 1。

        ``draw_delta`` 即"多抽/少抽几次池子"：为正时额外抽若干次，为负时随机去掉
        若干次（类别不再固定，按种子确定）。
        """
        labels = ["food", "food", "medical", "tool", "carrier"]
        categories = ["food", "medical", "tool", "carrier"]
        if draw_delta > 0:
            rng = self._rng("start.loot.draws")
            labels.extend(rng.choice(categories) for _ in range(int(draw_delta)))
        elif draw_delta < 0:
            rng = self._rng("start.loot.draws")
            for _ in range(-int(draw_delta)):
                if len(labels) > 1:
                    labels.pop(rng.randrange(len(labels)))
        return [
            (label, labels.count(label))
            for label in categories
            if labels.count(label) > 0
        ]

    def defer_search_report(self, mission, text: str) -> None:
        """记录"搜索期间发生、但应在房客返程时播报"的事件。"""
        mission.reports.append(str(text))

    def _generate_locations(self) -> list[str]:
        """按**本局地图**的名单 + 分组权重，确定本局可用的地点（默认 10 个）。

        地图的 ``locations`` 是显式名单：没列进来的地点（含 DLC 后加的）本局不会出现。
        """
        from .data import BASE_MAP_ID, MAPS

        map_def = MAPS.get(self.state.meta.map_id) or MAPS.get(BASE_MAP_ID)
        pool = [key for key in (map_def.locations if map_def else ()) if key in LOCATIONS]
        if not pool:                          # 地图缺失/名单为空：退回全部地点，别让开局挂掉
            pool = list(LOCATIONS)
        want = int(map_def.draw_count) if map_def else 10
        result = [key for key in FIXED_LOCATIONS if key in pool]
        rng = self._rng(EVENT_IDS["world.locations"])
        for group in BASE_MAP_GROUPS:
            choices = [key for key in LOCATION_GROUPS.get(group, ())
                       if key in pool and key not in result]
            if choices:                       # 内容缺失/空分组一律容忍
                result.append(rng.choice(choices))
        group_weights = MAP_DRAW_WEIGHTS
        attempts = 0
        while len(result) < want and attempts < 200:
            attempts += 1
            group = self._weighted_choice(group_weights, rng=rng)
            choices = [key for key in LOCATION_GROUPS.get(group, ())
                       if key in pool and key not in result]
            if choices:
                result.append(rng.choice(choices))
        if len(result) < want:
            result.extend(key for key in pool if key not in result)
        return result[:want]

    @classmethod
    def load(cls, path: str | Path) -> "GameEngine":
        """从指定存档文件恢复引擎；版本不匹配时直接报错。"""
        source = Path(path)
        raw = json.loads(source.read_text(encoding="utf-8"))
        meta = raw.get("meta") or {}
        version = meta.get("version")
        if version != GAME_VERSION:
            raise RuleViolation(f"存档版本 {version} 与游戏版本 {GAME_VERSION} 不兼容。")
        saved_packs = tuple(meta.get("packs") or ())
        if sorted(saved_packs) != sorted(CONTENT.manifest()):
            raise RuleViolation(
                "存档启用内容包与当前启动内容包不一致："
                f"存档={saved_packs}，当前={CONTENT.manifest()}。"
            )
        engine = cls(GameState.from_dict(raw))
        engine._save_path = source
        engine._log("进入游戏。")
        engine.migrate_carriers()
        return engine
    def save(self, path: str | Path, *, quiet: bool = False) -> Path:
        """将当前状态序列化后原子写入指定文件并返回目标路径。

        ``quiet=True``（自动存档）时只在完整日志里留痕，不进入玩家的可见消息。
        """
        if self._pending_ability:
            raise RuleViolation("命运抽牌结算期间无法保存。")
        if self._pending_choice is not None:
            raise RuleViolation("正在等待玩家选择，无法保存。")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)
        self._save_path = target
        self._log("保存游戏。", shown=not quiet)
        return target

    # ---------------------------------------------------------------- messages/actions
    def drain_messages(self) -> list[str]:
        """取出并清空待展示的可见消息（只要文本；CLI 等旧入口用这个）。"""
        result = [text for text, _detail, _kind in self._messages]
        self._messages.clear()
        return result

    def drain_message_entries(self) -> list[tuple[str, dict | None]]:
        """取出并清空可见消息（文本 + 明细），供前端渲染可折叠日志。"""
        result = self._messages[:]
        self._messages.clear()
        return result

    def _collect_start(self) -> None:
        """开始收集可见播报（配合 `_collect_flush`）：块内不逐条播，仍逐条进完整日志。"""
        self._log_collector = []

    def _collect_flush(self, summary: str, *, detail: dict | None = None) -> None:
        """把收集到的播报合并成**一条**汇总播出（明细挂在其下，前端可折叠）。"""
        collected, self._log_collector = self._log_collector, None
        if not collected:
            return
        self._show_message(summary, detail or {"rows": collected})

    def _log(self, message: str, *, shown: bool = True, detail: dict | None = None,
             kind: str = "") -> None:
        """统一日志入口：`shown=True` 进玩家可见日志，否则只落完整日志。

        收集期内（`_collect_start` 之后、`_collect_flush` 之前）可见播报会被收起：
        仍然逐条写进完整日志，但玩家只看到 flush 出来的那一条汇总 —— 明细点开看。

        `kind` 是**给界面用的类别**（目前只有 `"warn"` / `"danger"`），由内容层声明；
        界面把它映射到锁定语义色。**默认空**：颜色只作为冗余提示，别当主要表达手段。
        """
        if self._log_collector is not None:
            self._record_log(message)
            self._log_collector.append({"label": message})
            return
        if shown:
            self._show_message(message, detail, kind)
        else:
            self._record_log(message, detail)

    def _record_log(self, message: str, detail: dict | None = None) -> None:
        """把一条文本记入完整对局日志，不进入玩家的可见消息队列。"""
        entry: dict = {"turn": self.state.flow.turn, "shown": False, "text": message}
        if detail:
            entry["detail"] = detail
        self.state.log.entries.append(entry)

    def _show_message(self, message: str, detail: dict | None = None, kind: str = "") -> None:
        """把一条文本同时记入日志并作为可见消息交给玩家（可带明细）。"""
        self._messages.append((message, detail, kind))
        entry: dict = {"turn": self.state.flow.turn, "shown": True, "text": message}
        if detail:
            entry["detail"] = detail
        if kind:
            entry["kind"] = kind
        self.state.log.entries.append(entry)

    def _log_lines(self) -> list[str]:
        """将完整日志逐行渲染为文本（含未公开记录与对应回合号）。"""
        return [f"[第{entry['turn']}回合] {entry['text']}" for entry in self.state.log.entries]

    def full_log_text(self) -> str:
        """返回完整对局日志文本，便于导出为 txt 文件。"""
        return "\n".join(self._log_lines())

    def export_full_log(self) -> str:
        """导出整局完整文本：元数据 + 全部消息日志 + 全部动作记录。"""
        pseudo = self.state.pseudo_state
        ending = f"{'胜利' if self.state.flow.victory else '失败'}：{self.state.flow.ending}" if self.state.flow.game_over else "未结束"
        lines = [
            f"版本：{self.state.meta.version}",
            f"种子：{self.state.meta.seed}",
            f"难度：{self.state.meta.difficulty}",
            f"伪人：{pseudo.name}（{pseudo.scenario_id}）",
            f"结局：{ending}",
            "",
            "===== 对局消息与事件 =====",
            *self._log_lines(),
            "",
            "===== 动作记录 =====",
        ]
        for record in self.state.log.action_log:
            payload = json.dumps(record, ensure_ascii=False, sort_keys=True)
            lines.append(payload)
        return "\n".join(lines)

    def _record_action(self, action: str, **data: Any) -> None:
        """记录一条对局事件到当前回合与总动作日志（完整保留，不截断）。"""
        record = {"turn": self.state.flow.turn, "action": action, **data}
        self.state.log.current_turn_actions.append(record)
        self.state.log.action_log.append(record)


    # -------------------------------------------------------------------- queries
    def character(self, tenant: TenantState | str) -> CharacterDefinition:
        """按房客对象或角色 ID 返回对应的角色定义。"""
        character_id = (
            tenant.character_id if isinstance(tenant, TenantState) else tenant
        )
        return CHARACTERS[character_id]

    def living_tenants(self) -> list[TenantState]:
        """返回当前仍存活的房客列表。"""
        return [tenant for tenant in self.state.house.tenants.values() if tenant.alive]

    def home_tenants(self) -> list[TenantState]:
        """返回当前在屋内的存活房客列表。"""
        return [tenant for tenant in self.living_tenants() if tenant.at_home]

    def searching_tenants(self) -> list[TenantState]:
        """返回正在外出搜索的存活房客列表。"""
        mission_ids = {mission.tenant_id for mission in self.state.world.missions}
        return [tenant for tenant in self.living_tenants() if tenant.id in mission_ids]

    def container(self, tenant: TenantState, key: str) -> object | None:
        """取该房客的专属容器（不存在就按内容声明的类型建一个）；没声明过则返回 None。

        容器是**内容自有的状态**（核心只负责存取与序列化）：角色模块声明
        ``CONTAINERS = {"<key>": <类>}``，类自己实现 ``to_dict`` / ``from_dict``。
        """
        from .tenant import CONTAINER_TYPES

        existing = tenant.containers.get(key)
        if existing is not None:
            return existing
        cls = CONTAINER_TYPES.get((tenant.character_id, key))
        if cls is None:
            return None
        created = cls.from_dict({})
        tenant.containers[key] = created
        return created

    def panel_view(self, tenant: TenantState) -> dict | None:
        """返回该房客的专属面板视图（内容声明 ``PANEL``）；没声明则返回 None。

        面板**不是**待处理交互：它随时能开、看完能关，"开着没有"由前端记，
        所以这里只负责把内容算好的视图交出去，不参与回合流程。
        """
        from .data import CHARACTER_PANELS

        entry = CHARACTER_PANELS.get(tenant.character_id)
        if entry is None:
            return None
        return entry[0](self, tenant) or None

    def panel_action(
        self,
        tenant_id: int,
        action: str,
        *,
        slot: int | None = None,
        item_id: str | None = None,
        source: object = None,
    ) -> None:
        """把面板动作转交给内容声明的处理器（核心不解其意，只转发）。"""
        from .data import CHARACTER_PANELS

        tenant = self.state.house.tenants.get(int(tenant_id))
        if tenant is None:
            raise RuleViolation("该房客不在屋内。")
        entry = CHARACTER_PANELS.get(tenant.character_id)
        if entry is None:
            raise RuleViolation("该房客没有可用的专属面板。")
        entry[1](
            self, tenant, str(action), slot=slot, item_id=item_id, source=source
        )

    def tenant_name(self, tenant_id: int) -> str:
        """按房客 ID 返回其角色名称；查无此人时返回“未知房客”。"""
        tenant = self.state.house.tenants.get(tenant_id)
        return self.character(tenant).name if tenant else "未知房客"

    def _add_tenant(self, character_id: str) -> TenantState:
        """为可用角色登记一名新房客，分配 ID 与初始情绪后加入状态。"""
        if character_id not in CHARACTERS or not CHARACTERS[character_id].available:
            raise RuleViolation("该房客在原稿中尚未开放。")
        tenant_id = self.state.ids.allocate_tenant()
        tenant = TenantState(id=tenant_id, character_id=character_id)
        definition = CHARACTERS[character_id]
        tenant.abilities = [
            AbilityState(ability.id, acquisition="original")
            for ability in (*definition.actives, *definition.passives)
        ]
        from weiren_game.data.characters import CHARACTER_MODULES

        module = CHARACTER_MODULES.get(character_id)
        initial_setup = getattr(module, "initial_setup", None)
        if initial_setup is not None:
            initial_setup(self, tenant)
        self.state.house.tenants[tenant_id] = tenant
        return tenant

    def _require_home_tenant(self, tenant_id: int | None, *, must_act: bool = False) -> TenantState:
        """校验房客在场、存活且满足行动条件后返回该房客。"""
        if not tenant_id or tenant_id not in self.state.house.tenants:
            raise RuleViolation("未找到该房客。")
        tenant = self.state.house.tenants[tenant_id]
        if not tenant.alive or not tenant.at_home:
            raise RuleViolation("该房客目前不在屋内。")
        if must_act and tenant.skip_until_turn >= self.state.flow.turn:
            raise RuleViolation("该房客本回合无法行动。")
        return tenant

    def _has_character(self, character_id: str, home_only: bool = True) -> bool:
        """检查当前房客中是否存在指定角色（默认仅限屋内，且技能未被禁用）。"""
        group = self.home_tenants() if home_only else self.living_tenants()
        # Queries (including the status screen) must never consume randomness.
        # A concrete passive trigger performs its own failure roll.
        return any(
            t.character_id == character_id and not t.shock and not t.passives_disabled
            for t in group
        )
    # --------------------------------------------------------------- round start
    def _log_searching_summary(self) -> None:
        """回合开始阶段：打印仍在搜索中的房客摘要（与既有流程同位置）。"""
        if self.state.world.missions:
            details = "；".join(
                f"{self.tenant_name(mission.tenant_id)}在外"
                f"{mission.elapsed_search_turns}回合，还剩"
                f"{max(0, mission.remain_search_turns)}回合返回"
                for mission in self.state.world.missions
            )
            self._log(f"搜索中：{details}。")

    def _run_pseudo_end_effects(self) -> None:
        """回合结束阶段：执行当前伪人场景注册的 settle_end 处理器。"""
        from weiren_game.data import SCENARIO_HANDLERS

        handler = SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {}).get(
            "settle_end"
        )
        if handler is not None:
            handler(self)

    def start_turn(self) -> None:
        """开始新回合：记录快照并依次执行回合开始阶段的各类结算。"""
        self._require_no_pending_choice()
        if self._pending_ability:
            raise RuleViolation("命运抽牌结算期间无法开始新回合。")
        if self.state.flow.game_over:
            raise RuleViolation("本局已经结束。")
        if self.state.flow.phase == "action":
            raise RuleViolation("当前回合尚未结束。")
        snapshot = self.state.to_dict(include_history=False)
        self.state.log.history.append(snapshot)
        self.state.log.history = self.state.log.history[-20:]
        self.state.flow.turn += 1
        self.state.flow.phase = "turn_start"
        self.state.round.searched_this_turn = False
        self.state.round.item_uses_this_turn = 0
        self.state.log.current_turn_actions = []
        # 回合初重置“当回合生效”的命运抽牌效果（属该角色运行时）。
        self._log(f"\n========== 第 {self.state.flow.turn} 回合：回合开始 ==========")

        # 阶段顺序由 lifecycle.START_TURN_PHASES 表声明（当前顺序与重构前一致）。
        from weiren_game.lifecycle import START_TURN_PHASES

        for _node_name, method_name in START_TURN_PHASES:
            getattr(self, method_name)()
        self._flush_skill_outcomes()
        if not self.state.flow.game_over:
            self.state.flow.phase = "action"
            if self.state.world.events.door_events:
                self._log(f"门外有 {len(self.state.world.events.door_events)} 个事件等待处理，暂时不能结束回合。")

    # --------------------------------------------------------------- round end
    def resume_to_action(self) -> None:
        """读档/回溯后回到玩家行动阶段：非行动阶段则推进（有待选/无房客/已结束时跳过）。"""
        flow = self.state.flow
        if flow.game_over or flow.phase == "action":
            return
        if self._pending_choice is not None or self._pending_ability:
            return
        if not self.home_tenants():
            return
        try:
            self.start_turn()
        except RuleViolation:
            pass

    def end_turn(self) -> None:
        """结束行动阶段，执行回合末结算并判断胜利或进入回合间歇。"""
        self._require_no_pending_choice()
        if self.state.flow.phase != "action":
            raise RuleViolation("当前不在玩家行动阶段。")
        if self.state.world.events.door_events:
            raise RuleViolation("门外仍有未处理事件，不能结束回合。")
        if self._pending_ability:
            raise RuleViolation("仍有命运牌尚未选择或反悔，不能结束回合。")
        self.state.flow.phase = "turn_end"
        self._record_action("end_turn")
        self._log(f"---------- 第 {self.state.flow.turn} 回合：回合结束 ----------")

        # 阶段顺序由 lifecycle.END_TURN_PHASES 表声明（当前顺序与重构前一致）。
        from weiren_game.lifecycle import END_TURN_PHASES

        for _node_name, method_name in END_TURN_PHASES:
            getattr(self, method_name)()
        self._flush_skill_outcomes()
        # 回合末：全局事件（世界级条件）剩余回合 -1。
        self._decay_global_events()

        if not self.state.flow.game_over and self.state.flow.turn >= self.state.flow.max_turns:
            self._finish(True, "你们撑到了日出。第一束阳光照进屋内，伪人的阴影消失在晨雾中。")
        elif not self.state.flow.game_over:
            self.state.flow.phase = "between_turns"

    def _remove_tenant_from_house(self, tenant: TenantState) -> None:
        """把房客移出屋内的公共收尾：屋内死亡与驱逐共用同一条路径。

        归还遗物、清任务、通知死亡响应（伪人计数 / 角色死亡被动、健康变更）。
        **屋内死亡与驱逐的唯一区别只是播报文本**（以及驱逐额外的同伴理智惩罚，由调用方负责）。
        """
        # 仅在屋内时把遗物归入仓库；屋外死亡（搜索途中）视为物资遗失。
        if tenant.at_home:
            self._return_tenant_items(tenant)
        tenant.alive = False
        tenant.at_home = False
        self.state.world.missions = [mission for mission in self.state.world.missions if mission.tenant_id != tenant.id]
        self._notify_tenant_death()
        self._after_health_changed()

    def _kill_tenant(self, tenant: TenantState, reason: str) -> None:
        """处理房客死亡：触发替身驱逐等特殊分支，移出屋内并记录日志。"""
        if not tenant.alive:
            return
        if tenant.is_pseudo:
            handler = self._pseudo_handler("expel_infiltrator")
            if handler is not None:
                handler(self, "替身死亡")
            return
        self._remove_tenant_from_house(tenant)
        # 重后果（红色）：房客死亡不可逆。
        self._log(f"死亡：{self.character(tenant).name}{reason}。", kind="danger")

    def _notify_tenant_death(self) -> None:
        """房客死亡节点：通知当前伪人场景与角色光环/被动的死亡响应。"""
        from weiren_game.data import SCENARIO_HANDLERS

        death_handler = SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {}).get(
            "tenant_death"
        )
        if death_handler is not None:
            death_handler(self)
        from weiren_game.data import CHARACTER_DEATH_HOOKS

        for hook in CHARACTER_DEATH_HOOKS:
            hook(self)

    def _check_survival(self) -> None:
        """房客全部死亡时以失败结局结束本局。"""
        if not self.state.flow.game_over and not self.living_tenants():
            self._finish(False, "最后一名房客也倒下了，屋主再也无力抵挡敲门声。")

    def _finish(self, victory: bool, ending: str) -> None:
        """以给定胜负与结局文本结束本局游戏。"""
        self.state.flow.game_over = True
        self.state.flow.victory = victory
        self.state.flow.ending = ending
        self.state.flow.phase = "finished"
        self._log(("胜利：" if victory else "失败：") + ending)

    # ------------------------------------------------------------ replay/status
    def rewind_one_turn(self) -> None:
        """回退至上一回合开始前的快照并恢复状态。"""
        if not self.state.log.history:
            raise RuleViolation("没有可以回溯的回合。")
        old_history = self.state.log.history[:-1]
        snapshot = self.state.log.history[-1]
        # 回溯只回退规则状态；完整日志是单调历史，保留下来供回看/导出。
        entries = self.state.log.entries
        self.state = GameState.from_dict(snapshot)
        self.state.log.history = old_history
        self.state.log.entries = entries
        self._log(f"已回溯至第{self.state.flow.turn + 1}回合开始前；相同操作会得到相同随机结果。")

    def emotion_visible(self, tenant: object, key: str) -> bool:
        """屋主是否能看到某情绪。

        **内建基础谓词**（强度>5 / 「情绪显现」全局事件仍在）**OR**
        内容声明的 ``emotion.visible`` 闸门（角色/伪人场景；path=("显示情绪", 情绪键)）。
        """
        from .global_event import emotion_reveal_event

        base = (
            tenant.condition(key).intensity > 5
            or self.state.world.global_events.active(emotion_reveal_event(key))
        )
        return self._eval_gate(
            "emotion.visible",
            source=("显示情绪", key),
            context={"tenant": tenant, "key": key},
            base=base,
        )

    def status_lines(self) -> list[str]:
        """生成包含伪人进度、房客状态与搜索任务的局面摘要文本。"""
        from weiren_game.data import CHARACTER_MODULES

        lines = [
            f"回合 {self.state.flow.turn}/{self.state.flow.max_turns} | 阶段：{self.state.flow.phase} | "
            f"难度：{self.state.meta.difficulty} | 种子：{self.state.meta.seed}"
        ]
        pseudo = self.state.pseudo_state
        # 「已确认」含初访前就生效的技能（known），与伪人卡口径一致。
        if pseudo.revealed or pseudo.known:
            from weiren_game.data import SCENARIO_HANDLERS

            progress_handler = SCENARIO_HANDLERS.get(pseudo.scenario_id, {}).get(
                "progress_text"
            )
            progress = progress_handler(self) if progress_handler is not None else ""
            lines.append(f"伪人：{pseudo.name} | 到访{pseudo.visit_count}次 | {progress}")
        else:
            lines.append(f"伪人：尚未确认（场景：{pseudo.name}）")
        bonds = self.bond_levels()
        lines.append("性格加权：" + ("、".join(f"{PERSONALITY_LABELS[key]}({value})" for key, value in bonds.items()) or "无"))
        for tenant in self.living_tenants():
            definition = self.character(tenant)
            if tenant.at_home:
                # Fries is a perfect substitute; exposing this flag here would
                # make its information-and-accusation game moot.
                place = "屋内"
            elif tenant.temporarily_away:
                remaining = max(0, tenant.return_turn - self.state.flow.turn)
                place = f"离屋，剩{remaining}回合返回"
            else:
                place = "搜索中"
            statuses: list[str] = []
            if tenant.trauma.active:
                statuses.append(f"创伤{tenant.trauma.intensity}/{tenant.trauma.layers}")
            if tenant.disorder.active:
                statuses.append(f"紊乱{tenant.disorder.intensity}/{tenant.disorder.layers}")
            for key, label in {**EROSION_EMOTIONS, **AWAKENING_EMOTIONS, **RARE_EMOTIONS}.items():
                condition = tenant.condition(key)
                if condition.active and self.emotion_visible(tenant, key):
                    statuses.append(f"{label}{condition.intensity}/{condition.layers}")
            if tenant.shock:
                statuses.append(f"休克{tenant.shock}/{tenant.shock_layers}")
            personality = self._tenant_personalities(tenant)
            lines.append(
                f"{tenant.id} {definition.name:<8} [{place}] 生命{tenant.health:>5.1f}/{tenant.max_health:g} "
                f"理智{tenant.sanity:>5.1f} 消沉[隐藏] "
                f"{PERSONALITY_LABELS.get(personality[0], personality[0])}-{PERSONALITY_LABELS.get(personality[1], personality[1])} | "
                + ("、".join(statuses) or "无显现状态")
            )
            if tenant.inventory.items:
                lines.append("    装备：" + "、".join(
                    f"{ITEMS[held.item_id].name}" + (f"({held.durability})" if held.durability else "")
                    for held in tenant.inventory.items
                ))
        for mission in self.state.world.missions:
            searching_tenant = self.state.house.tenants.get(mission.tenant_id)
            carried_groups = (
                self._tenant_item_group_count(searching_tenant)
                if searching_tenant
                else 0
            )
            remaining = max(0, mission.remain_search_turns)
            lines.append(
                f"  ↳ {self.tenant_name(mission.tenant_id)}在{LOCATIONS[mission.location_id].name}："
                f"搜索{mission.elapsed_search_turns}/{mission.actual_search_turns}回合，剩{remaining}回合返回；"
                f"携带物资 {carried_groups}/{mission.carry_capacity}（实际/上限），"
                f"预计带回{len(mission.rewards)}件"
            )
        return lines

    def inventory_lines(self) -> list[str]:
        """生成当前共享物资栏的逐行文本描述。"""
        house = self.state.house.inventory
        if not house:
            return ["物资栏为空。"]
        result = []
        item_ids = sorted(
            {value.item_id for value in house},
            key=lambda item_id: (ITEMS[item_id].category, ITEMS[item_id].quality, item_id),
        )
        for item_id in item_ids:
            item = ITEMS[item_id]
            amount = house.count(item_id)
            durability = ""
            if item.durable:
                values = [
                    value.durability
                    for value in house.all_with(
                        lambda candidate, item_id=item_id: candidate.item_id == item_id
                        and candidate.durability > 0
                    )
                ]
                durability = " [耐久:" + ",".join(map(str, values)) + "]"
            result.append(f"{item_id}: {item.name} ×{amount}{durability} — {item.description}")
        return result

    def location_lines(self) -> list[str]:
        """生成本局可用地点的逐行文本描述。"""
        return [
            f"{key}: {LOCATIONS[key].name}（回合{LOCATIONS[key].turn_delta:+d}，行为{LOCATIONS[key].behavior_delta:+d}）— {LOCATIONS[key].description}"
            for key in self.state.world.locations.available_locations
        ]

    def codex_lines(self) -> list[str]:
        """生成图鉴统计文本；具体内容可在各自模块里追加统计行。"""
        lines = [
            f"房客 {sum(c.available for c in CHARACTERS.values())}/{len(CHARACTERS)}",
            f"物资 {len(ITEMS)} 种；搜索地点 {len(LOCATIONS)} 个"
            f"（本局 {len(self.state.world.locations.available_locations)} 个）；"
            f"信息模板 {len(INFORMATION_TEMPLATES)} 类",
            f"伪人 {len(PSEUDOS)} 类：" + "、".join(value.name for value in PSEUDOS.values()),
            "羁绊：" + "；".join(f"{PERSONALITY_LABELS[key]}—{value}" for key, value in BOND_DESCRIPTIONS.items()),
        ]
        for hook in CODEX_SUMMARY_HOOKS:
            lines.extend(hook(self))
        return lines

    def assert_invariants(self) -> None:
        """校验当前状态满足各项游戏不变量（供测试使用）。"""
        assert self.state.meta.version == GAME_VERSION
        assert self.state.pseudo_state.scenario_id in PSEUDOS
        assert len(set(self.state.world.locations.available_locations)) == len(self.state.world.locations.available_locations)
        assert all(key in LOCATIONS for key in self.state.world.locations.available_locations)
        for tenant in self.state.house.tenants.values():
            assert -100 <= tenant.health <= tenant.max_health <= 100
            assert -100 <= tenant.sanity <= 100
            assert 0 <= tenant.shock <= 4 and 0 <= tenant.shock_layers <= 99
            for condition in (tenant.trauma, tenant.disorder, *tenant.conditions.values()):
                assert 0 <= condition.intensity <= 10
                assert 0 <= condition.layers <= 99
                assert (condition.intensity == 0) == (condition.layers == 0)
            for held in tenant.inventory.items:
                assert held.item_id in ITEMS and held.durability >= 0
        mission_ids = {mission.tenant_id for mission in self.state.world.missions}
        for tenant in self.searching_tenants():
            assert tenant.id in mission_ids
        for mission in self.state.world.missions:
            assert mission.location_id in LOCATIONS
            assert 0 <= mission.search_success_rate <= 1
            assert mission.remain_search_turns == max(0, mission.actual_search_turns - mission.elapsed_search_turns)
            carrying_tenant = self.state.house.tenants.get(mission.tenant_id)
            assert len(mission.rewards) + (
                self._tenant_item_group_count(carrying_tenant)
                if carrying_tenant
                else 0
            ) <= mission.carry_capacity
        for instance in self.state.house.inventory:
            assert instance.item_id in ITEMS
            definition = ITEMS[instance.item_id]
            assert instance.durability >= 0
            if definition.durable:
                assert 0 < instance.durability <= definition.max_durability

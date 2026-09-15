"""确定性随机源（种子派生/留痕/抽取），保证同一局可复现。"""

from __future__ import annotations


import hashlib
import random
from typing import Any, Callable, Iterable, Sequence

from weiren_game.content import CONTENT
from weiren_game.data import (
    EVENT_IDS,
    GAME_VERSION,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.models import SearchMission

from weiren_game.exceptions import RuleViolation


_EVENT_ID_NAMES = {value: key for key, value in EVENT_IDS.items()}


class RandomSystemMixin:

    # ----------------------------------------------------------- deterministic RNG
    def _rng(self, event_id: str | int, *suffix: object) -> random.Random:
        """按回合、事件 ID 与调用次数取得确定性随机源，并递增调用计数。

        ``event_id`` 传整数时按 ``EVENT_IDS`` 反查事件名；``suffix`` 用于
        拼回原动态事件（如 ``"<事件名>.{tenant.id}"`` 的基础编号 + 实例后缀）。
        两种写法生成完全相同的随机素材，迁移不影响已有对局。
        """
        name = (
            event_id
            if isinstance(event_id, str)
            else _EVENT_ID_NAMES.get(int(event_id), str(event_id))
        )
        material = name
        if suffix:
            material = ".".join((name, *(str(part) for part in suffix)))
        key = f"{self.state.flow.turn}:{material}"
        index = self.state.world.events.event_counters.get(key, 0)
        self.state.world.events.event_counters[key] = index + 1
        return self._seeded_rng(self.state.flow.turn, material, index)

    def _seeded_rng(self, *parts: object) -> random.Random:
        """用种子与参数派生确定性随机源，保证同一局结果可复现。"""
        material = "|".join((GAME_VERSION, self.state.meta.seed, *(str(part) for part in parts))).encode("utf-8")
        value = int.from_bytes(hashlib.sha256(material).digest()[:16], "big")
        from weiren_game.random_log import LoggedRandom

        label = "|".join(str(part) for part in parts)
        return LoggedRandom(value, label, self._record_log)

    def _mission_rng(self, mission: SearchMission, stream: str, index: int = 0) -> random.Random:
        """为指定搜索任务派生独立的确定性随机源。"""
        return self._seeded_rng(
            mission.search_start_turn, mission.search_instance_id, stream, index
        )
    def _weighted_choice(
        self,
        values: Iterable[tuple[Any, float]],
        event_id: str | None = None,        #前文提到，event_id用int会更好。
        rng: random.Random | None = None,   # 传入既有随机源可复用同一流；缺省按 event_id 派生。
        event_suffix: Sequence[object] = (),
    ) -> Any:
        """按权重从候选中随机选取一项并返回。"""
        entries = [(value, float(weight)) for value, weight in values if float(weight) > 0]
        if not entries:
            raise RuleViolation("随机候选池为空。")
        local = rng or self._rng(event_id or "weighted", *event_suffix)
        total = sum(weight for _, weight in entries)
        point = local.uniform(0, total)
        cursor = 0.0
        for value, weight in entries:
            cursor += weight
            if point <= cursor:
                return value
        return entries[-1][0]

    def _loot_draw(
        self,
        pool: Sequence[Any],
        count: int,
        event_id: str | int | None = None,
        *suffix: object,
    ) -> list[Any]:
        """从战利品表抽取 ``count`` 件物资（允许重复），用于无需玩家选择的掉落。"""
        if not pool or count <= 0:
            return []
        local = self._rng(event_id or "loot", *suffix)
        result = [local.choice(list(pool)) for _ in range(count)]
        material = str(event_id or "loot")
        if suffix:
            material = ".".join(
                (material, *(str(part) for part in suffix))
            )
        self._record_log(
            f"[抽取/战利品] {material} 从 [{'、'.join(str(v) for v in pool)}] "
            f"中抽到了 [{'、'.join(str(v) for v in result)}]"
        )
        return result

    def discover(
        self,
        pool: Sequence[Any],
        *,
        count: int = 3,
        constraint: Callable[[Any], bool] | None = None,
        required: Sequence[Any] | None = None,
        event_id: str | None = None,
        event_suffix: Sequence[object] = (),
    ) -> list[Any]:
        """发现（discover）：按种子从候选池抽出 ``count`` 个互不重复的选项。

        该方法是通用功能，不含任何具体游戏内容的语义；由玩家从返回值中
        选择一项，调用方再把选择接入自己的规则。

        若合法候选数量不足 ``count``，会自动把 ``count`` 缩小为候选数
        （不会抛出“不足”错误）；只有候选池为空时才报错。

        可选参数：
        - ``constraint``：先按条件过滤候选池；
        - ``required``：需要保底的调用方（如开局层）可要求结果包含该集合
          中至少一项；
        - ``event_id``：确定性随机的事件上下文。
        - **权重池**：池里可以混入 ``(值, 权重)`` 形式（权重为数字），加权不放回抽取；
          纯值池保持原有的均匀抽样与随机流不变。
        随机结果完全由种子系统决定且可复现。
        """
        entries: list[tuple[Any, float]] = []
        weighted = False
        for item in pool:
            if (
                isinstance(item, tuple)
                and len(item) == 2
                and isinstance(item[1], (int, float))
                and not isinstance(item[1], bool)
            ):
                entries.append((item[0], float(item[1])))
                weighted = True
            else:
                entries.append((item, 1.0))
        candidates = [
            (value, weight) for value, weight in entries
            if constraint is None or constraint(value)
        ]
        self._autosave_before_discover()
        count = min(count, len(candidates))
        if not candidates:
            raise RuleViolation(
                "发现候选池为空，无法提供任何选项。"
            )
        local = self._rng(event_id or "discover", *event_suffix)
        if weighted:
            result = self._weighted_sample(candidates, count, local, required)
        else:
            values = [value for value, _ in candidates]
            if required:
                guaranteed = [value for value in values if value in required]
                if guaranteed:
                    first = local.choice(guaranteed)
                    rest = [value for value in values if value != first]
                    others = local.sample(rest, count - 1)
                    result = local.sample([first, *others], count)
                else:
                    result = local.sample(values, count)
            else:
                result = local.sample(values, count)
        material = str(event_id or "discover")
        if event_suffix:
            material = ".".join(
                (material, *(str(part) for part in event_suffix))
            )
        self._record_log(
            f"[发现] {material} 从 [{'、'.join(str(v) for v in candidates)}] "
            f"中选择了 [{'、'.join(str(v) for v in result)}]"
        )
        self._pending_choice = {"options": list(result)}
        return result

    def _weighted_sample(
        self,
        entries: Sequence[tuple[Any, float]],
        count: int,
        rng: random.Random,
        required: Sequence[Any] | None = None,
    ) -> list[Any]:
        """按权重不放回抽 ``count`` 个；``required`` 中的值保证至少出现一个。"""
        pool = [(value, float(weight)) for value, weight in entries]
        picked: list[Any] = []
        if required:
            guaranteed = [(value, weight) for value, weight in pool if value in required]
            if guaranteed:
                first = self._weighted_pick(guaranteed, rng)
                picked.append(first)
                pool = [(value, weight) for value, weight in pool if value != first]
        while pool and len(picked) < count:
            value = self._weighted_pick(pool, rng)
            picked.append(value)
            pool = [(item, weight) for item, weight in pool if item != value]
        return picked

    @staticmethod
    def _weighted_pick(
        entries: Sequence[tuple[Any, float]], rng: random.Random
    ) -> Any:
        """按权重随机挑一个（``entries`` 至少一项）。"""
        total = sum(max(0.0, weight) for _, weight in entries)
        if total <= 0:
            return rng.choice([value for value, _ in entries])
        point = rng.uniform(0, total)
        cursor = 0.0
        for value, weight in entries:
            cursor += max(0.0, weight)
            if point <= cursor:
                return value
        return entries[-1][0]

    def _start_loot_draw(
        self,
        pool: Sequence[str],
        count: int,
        fortune: float = 0.0,
        *suffix: object,
    ) -> list[str]:
        """开局补给抽取：按品质权重 × 时运修正从类别池中抽 ``count`` 件（允许重复）。

        权重公式与搜索一致：``品质权重 × max(.01, 1 + 时运×0.1×(品质+2))``。
        这里的「时运」只作用于开局补给池（难度 ``fortune_delta`` + ``start_loot_fortune``）。
        """
        if not pool or count <= 0:
            return []
        from weiren_game.data import QUALITY_WEIGHTS

        entries = [
            (
                item_id,
                float(QUALITY_WEIGHTS[ITEMS[item_id].quality])
                * max(.01, 1 + float(fortune) * .1 * (ITEMS[item_id].quality + 2)),
            )
            for item_id in pool
            if item_id in ITEMS
        ]
        if not entries:
            return []
        local = self._rng(EVENT_IDS["start.loot"], *suffix)
        result = [self._weighted_choice(entries, rng=local) for _ in range(count)]
        material = ".".join(("start.loot", *(str(part) for part in suffix)))
        self._record_log(
            f"[抽取/开局补给] {material} 从 [{'、'.join(value for value, _ in entries)}] "
            f"中抽到了 [{'、'.join(str(value) for value in result)}]"
        )
        return result

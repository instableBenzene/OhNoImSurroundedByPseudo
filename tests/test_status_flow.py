"""状态流转：通用回合末衰减、状态效果、高生命免疫、情绪与消沉。

合并自原 status_decay / trauma-disorder 表格 / analgesia / high-health / emotion /
depression / turn_start_status_once 用例。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from weiren_game.effects.health_sanity import refresh_high_health_immunity
from weiren_game.engine import GameEngine
from weiren_game.global_event import emotion_reveal_event
from weiren_game.models import Condition, GameState, Information
from weiren_game.pseudo import PseudoRuntime
from weiren_game.session import GameFlowState, SaveMetadata
from weiren_game.tenant import TenantState


def bare_engine(seed: str, pseudo_id: str = "pseudo_benzene") -> GameEngine:
    engine = GameEngine.new_game(seed, "a0", pseudo_id=pseudo_id)
    engine.state.house.tenants.clear()
    engine.state.world.visitors.visitor_pool.clear()
    engine.state.world.events.door_events.clear()
    engine.state.house.information.clear()
    engine.state.flow.turn = 1
    engine.state.flow.phase = "action"
    return engine


class StatusFlowTests(unittest.TestCase):
    def test_generic_turn_end_decay(self) -> None:
        engine = bare_engine("status-decay")
        tenant = engine._add_tenant("hkw")
        tenant.set_status("fiji_afterglow", intensity=1, layers=3)
        tenant.set_status("chaos_carry", intensity=4, layers=99)
        tenant.condition("chaos_carry").layers = 40
        tenant.set_status("high_health_immunity", intensity=1, layers=1)
        tenant.set_status("trauma", intensity=2, layers=5)
        tenant.set_status("shock", intensity=1, layers=3)
        engine._decay_conditions()
        self.assertEqual(tenant.condition("fiji_afterglow").layers, 2)   # 持续状态 -1
        self.assertEqual(tenant.condition("chaos_carry").layers, 99)     # 永续回满
        self.assertTrue(tenant.condition("high_health_immunity").active)  # 自管跳过
        self.assertEqual(tenant.trauma.layers, 4)                        # 创伤走通用
        self.assertEqual(tenant.condition("shock").layers, 2)            # 休克走通用

    def test_high_health_immunity_lifecycle(self) -> None:
        engine = bare_engine("immunity")
        tenant = engine._add_tenant("hkw")
        tenant.health = 100.0
        refresh_high_health_immunity(engine, tenant)
        self.assertEqual(tenant.condition("high_health_immunity").intensity, 1)
        self.assertFalse(engine._set_condition(tenant, tenant.trauma, 1, 1, "测试"))
        self.assertFalse(tenant.trauma.active)
        self.assertFalse(tenant.condition("high_health_immunity").active)  # 充能耗尽
        self.assertTrue(engine._set_condition(tenant, tenant.trauma, 1, 1, "测试"))

        low = engine._add_tenant("hkw")
        low.health = 90.0
        refresh_high_health_immunity(engine, low)
        self.assertFalse(low.condition("high_health_immunity").active)      # 不满足高生命

        unused = engine._add_tenant("hkw")
        unused.health = 100.0
        refresh_high_health_immunity(engine, unused)
        engine._run_status_effect_node("turn_end.status_effects", unused)
        self.assertFalse(unused.condition("high_health_immunity").active)   # 没用到则过期

    def test_status_loss_tables_and_analgesia(self) -> None:
        engine = bare_engine("status-tables")
        physical = engine._add_tenant("hkw")
        mental = engine._add_tenant("dragonboat")
        physical.trauma = Condition(4, 2)
        mental.disorder = Condition(4, 2)
        with patch.object(engine, "_rng", return_value=SimpleNamespace(random=lambda: 1.0)):
            engine._apply_status_end(physical, physical.trauma, physical=True, label="创伤")
            engine._apply_status_end(mental, mental.disorder, physical=False, label="紊乱")
        self.assertEqual((physical.health, physical.sanity), (90, 95))
        self.assertEqual((mental.health, mental.sanity), (95, 90))

        analgesia = bare_engine("analgesia")
        target = analgesia._add_tenant("hkw")
        target.trauma = Condition(4, 2)
        target.set_status("analgesia_trauma", intensity=1, layers=2)
        self.assertFalse(analgesia._condition_extra_effect_active(target, "trauma"))
        with patch.object(analgesia, "_rng", return_value=SimpleNamespace(random=lambda: 1.0)):
            analgesia._apply_status_end(target, target.trauma, physical=True, label="创伤")
            analgesia._decay_conditions()
        self.assertEqual((target.health, target.sanity), (90, 95))  # 只吃基础流失
        self.assertEqual(target.trauma, Condition(4, 1))

    def test_emotion_value_and_depression(self) -> None:
        engine = GameEngine.new_game(seed="emotion")
        engine.state.house.tenants.clear()
        tenant = engine._add_tenant("dragon")
        tenant.sanity = 80
        tenant.irritation = Condition(2, 3)
        tenant.conditions["happiness"] = Condition(1, 1)
        engine.start_turn()
        self.assertAlmostEqual(tenant.depression, 4.0)

        passive = bare_engine("depression-passive")
        victim = passive._add_tenant("hkw")
        victim.depression = 1001
        with patch.object(passive, "_rng", return_value=SimpleNamespace(random=lambda: .75)):
            self.assertTrue(passive._passive_available(victim, "test.pass"))
        with patch.object(passive, "_rng", return_value=SimpleNamespace(random=lambda: .25)):
            self.assertFalse(passive._passive_available(victim, "test.fail"))
        active = bare_engine("depression-active")
        actor = active._add_tenant("dragon")
        actor.depression = 1001
        self.assertTrue(active._ability_failed(actor, "call_friends"))

    def test_turn_start_status_effect_runs_once_per_tenant(self) -> None:
        engine = GameEngine(GameState(
            meta=SaveMetadata(version="2.1.0", seed="status-once", difficulty="a0"),
            flow=GameFlowState(max_turns=20),
            pseudo_state=PseudoRuntime(pseudo_instance_id=1, scenario_id="pseudo_benzene"),
        ))
        engine.state.world.visitors.next_pseudo_turn = 999
        for index, character_id in enumerate(("hkw", "fiver"), start=1):
            tenant = TenantState(id=index, character_id=character_id)
            tenant.sanity = 50.0
            tenant.set_status("mcdangdang_aftertaste", intensity=1, layers=99)
            engine.state.house.tenants[tenant.id] = tenant
        engine.start_turn()
        for tenant in engine.home_tenants():
            self.assertEqual(tenant.sanity, 53.0)   # 每名房客只 +3 一次

    def test_emotion_reveal_is_global_event(self) -> None:
        """情绪显现是**全局事件**：证实后不黏在房客身上，而是让该情绪整体可见。"""
        engine = bare_engine("emotion-reveal")
        tenant = engine._add_tenant("hkw")
        tenant.irritation = Condition(2, 3)            # 低于"强度 > 5"的基础阈值
        self.assertFalse(engine.emotion_visible(tenant, "irritation"))

        info = Information(
            info_instance_id=1, title="有人藏不住了", text="烦躁露了馅。",
            status="confirmed", gained_turn=1, expires_turn=6, truth=True,
            kind="emotion_reveal", subtype="irritation",
            target_ids=[tenant.id], data={"reveal_duration": 3},
        )
        engine.state.house.information.append(info)
        engine._resolve_information_effect(info)

        self.assertTrue(
            engine.state.world.global_events.active(emotion_reveal_event("irritation"))
        )
        self.assertTrue(engine.emotion_visible(tenant, "irritation"))
        self.assertFalse(tenant.condition("reveal_irritation").active)   # 不再是房客身上的状态
        other = engine._add_tenant("dragonboat")                          # 世界级：别人也可见
        other.irritation = Condition(2, 3)
        self.assertTrue(engine.emotion_visible(other, "irritation"))

    def test_mark_bar_projection(self) -> None:
        """印记进度条与档位刻度：有上限按 maximum；无上限用末档当参照；都没声明则不画条。"""
        from weiren_game.data.types import MarkDefinition
        from weiren_game.web_ui import _mark_row

        bounded = MarkDefinition(
            id="demon", label="恶魔印记", acquisition="受伤时获得。", maximum=6,
            bar_tiers=((3, "临界"), (4, "可驱逐", "danger"), (6, "转化", "warn")),
        )
        row = _mark_row(bounded, 4)
        self.assertEqual((row["label"], row["current"], row["max"]), ("恶魔印记", 4, 6))
        self.assertEqual(row["bar"]["fill"], 66.7)
        self.assertEqual(row["bar"]["tier"], 2)                      # 已过 3 与 4 两档
        self.assertEqual([t["at"] for t in row["bar"]["tiers"]], [3, 4, 6])
        self.assertEqual(row["bar"]["tiers"][1]["label"], "可驱逐")   # 档位标注（提示性）
        self.assertEqual(row["bar"]["tiers"][1]["css"], "danger")     # 刻度配色
        self.assertEqual(row["bar"]["tiers"][2]["ratio"], 100.0)
        self.assertIn("受伤时获得", row["hint"])

        unbounded = MarkDefinition(
            id="star", label="星之印记", acquisition="", maximum=None, bar_tiers=(10,)
        )
        self.assertEqual(_mark_row(unbounded, 7)["bar"]["fill"], 70.0)
        self.assertEqual(_mark_row(unbounded, 12)["bar"]["fill"], 100.0)   # 超出参照即满格
        self.assertIsNone(
            _mark_row(MarkDefinition(id="x", label="X", acquisition=""), 3)["bar"]
        )

    def test_detail_slot_and_chip_hidden(self) -> None:
        """详情页小面板：内容声明 ``DETAIL_SLOT``；未声明则回退为列印记；``chip_hidden`` 不进状态栏。"""
        from weiren_game.web_ui import build_state

        engine = GameEngine.new_game(seed="slot", difficulty="a0")
        engine.state.house.tenants.clear()
        fries = engine._add_tenant("fries")
        fries.set_status("persona_lucky", intensity=1, layers=99)   # 人设：应进小面板而非状态栏
        rose = engine._add_tenant("rose")
        engine._gain_mark(rose, "demon", 4)

        state = build_state(engine)
        fries_row = next(row for row in state["tenants"] if row["id"] == fries.id)
        self.assertNotIn("persona_lucky", [chip[3] for chip in fries_row["statuses"]])
        self.assertEqual(fries_row["slot"][0]["kind"], "text")
        self.assertIn("幸运", fries_row["slot"][0]["text"])

        rose_row = next(row for row in state["tenants"] if row["id"] == rose.id)
        self.assertEqual([item["kind"] for item in rose_row["slot"]], ["mark", "mark"])
        demon = rose_row["slot"][0]
        self.assertEqual((demon["label"], demon["current"], demon["max"]), ("恶魔印记", 4, 6))
        self.assertEqual([tier["at"] for tier in demon["bar"]["tiers"]], [3, 4, 6])

    def test_slot_easter_eggs(self) -> None:
        """彩蛋：厄瑞玻斯的明月只在「伟大的封印」期间出现；混的太极图随「纯真的自我」定转。"""
        from weiren_game.web_ui import build_state

        engine = GameEngine.new_game(seed="eggs", difficulty="a0")
        engine.state.house.tenants.clear()
        erebus = engine._add_tenant("erebus")
        chaos_tenant = engine._add_tenant("chaos")

        def slot_of(tenant):
            state = build_state(engine)
            return next(row for row in state["tenants"] if row["id"] == tenant.id)["slot"]

        self.assertEqual([item["kind"] for item in slot_of(erebus)], ["bar"])   # 封印前：只有牌堆
        erebus.set_status("great_seal", intensity=1, layers=99)
        moon = slot_of(erebus)[-1]
        self.assertEqual(
            (moon["kind"], moon["label"], moon["hint"], moon["spin"]),
            ("glyph", "明月", "厄瑞玻斯-正在杀出月球", ""),
        )
        # 图形**自带**在角色 py 里（不引用资源包贴图），所以跟内容走、正常不可被材质包替换
        self.assertTrue(moon["svg"] and moon["icon"] == "")

        taiji = slot_of(chaos_tenant)[0]
        self.assertTrue(taiji["svg"] and taiji["icon"] == "")
        self.assertEqual(taiji["spin"], "random")   # 不定向
        chaos_tenant.set_status("pure_self", intensity=1, layers=99)
        taiji = slot_of(chaos_tenant)[0]
        self.assertEqual((taiji["spin"], taiji["label"]), ("cw", "纯真的自我"))   # 稳定顺时针


if __name__ == "__main__":
    unittest.main()

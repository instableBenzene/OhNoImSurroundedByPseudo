"""cost→effect 消耗层与能力结果派发。"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest

from weiren_game.data.types import A, B, CE, T
from weiren_game.engine import GameEngine
from weiren_game import data


class AbilityCostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine.new_game(seed="cost-system")
        self.engine.state.house.tenants.clear()
        self.engine.state.flow.turn = 1
        self.engine.state.flow.phase = "action"

    def test_forced_and_normal_cost_packs(self) -> None:
        forced = A(
            "intent_awareness", "意图觉察", "描述", "amount",
            branches=(B(
                max_on_force=True,
                terms=(T("mark", None, key="alert", maximum=True), T("sanity", 30, optional=True)),
                forced_terms=(T("health", 10, payer="target"), T("sanity", 10, payer="target")),
            ),),
        )
        actor = self.engine._add_tenant("zero329")
        target = self.engine._add_tenant("hkw")
        self.engine._gain_mark(actor, "alert", 3)
        self.engine._pay_cost_pack(actor, forced, forced=True, target=target)
        self.assertEqual(self.engine._mark_count(actor, "alert"), 3)   # 强制只付 forced_terms
        self.assertEqual((target.health, target.sanity), (90, 90))

        normal = A(
            "intent_awareness", "意图觉察", "描述",
            branches=(B(terms=(T("mark", None, key="alert", maximum=True), T("sanity", 30, optional=True))),),
        )
        payer = self.engine._add_tenant("zero329")
        self.engine._gain_mark(payer, "alert", 2)
        self.engine._pay_cost_pack(payer, normal)
        self.assertEqual((self.engine._mark_count(payer, "alert"), payer.sanity), (0, 100))

    def test_cost_expressions_and_turns(self) -> None:
        optional = A("sample", "示例", "描述", branches=(B(
            terms=(T("sanity", 10), T("sanity", 20, optional=True)),
        ),))
        payer = self.engine._add_tenant("dragon")
        self.engine._pay_cost_pack(payer, optional, include_optional=True)
        self.assertEqual(payer.sanity, 70)
        turn_ability = A("skip", "封锁", "描述", branches=(B(terms=(T("turns", 2),)),))
        self.engine._pay_cost_pack(payer, turn_ability)
        self.assertEqual(payer.skip_until_turn, self.engine.state.flow.turn + 2)

        either = A("emotion_strip", "情绪剥离", "描述", branches=(B(
            terms=(T("mark", 1, key="empathy", tag="empathy"), T("sanity", 15, tag="sanity")),
            cost_expr=CE("or", "empathy", "sanity"),
        ),))
        with_empathy = self.engine._add_tenant("hkw")
        self.engine._gain_mark(with_empathy, "empathy", 1)
        self.assertIsNone(self.engine._cost_pack_payable(with_empathy, either))
        self.engine._pay_cost_pack(with_empathy, either)
        self.assertEqual((self.engine._mark_count(with_empathy, "empathy"), with_empathy.sanity), (0, 100))
        broke = A("emotion_strip", "情绪剥离", "描述", branches=(B(
            terms=(T("mark", 1, key="empathy", tag="empathy"), T("sanity", 999, tag="sanity")),
            cost_expr=CE("or", "empathy", "sanity"),
        ),))
        self.assertIsNotNone(self.engine._cost_pack_payable(self.engine._add_tenant("demit"), broke))

    def test_ability_and_skill_outcome_dispatch(self) -> None:
        actor = self.engine._add_tenant("dragon")
        seen: list[tuple[str, str]] = []
        data.ABILITY_USED_HOOKS.append(lambda e, a, i: seen.append(("used", i)))
        data.ABILITY_FAILED_HOOKS.append(lambda e, a, i: seen.append(("failed", i)))
        try:
            self.engine._ability_release_failed = False
            self.engine._run_ability_outcome(actor, "x")
            self.engine._mark_ability_failed()
            self.engine._run_ability_outcome(actor, "y")
            self.engine._skill_outcome(actor, "s", False)
            self.engine._skill_outcome(actor, "s", True)
            self.engine._flush_skill_outcomes()
        finally:
            data.ABILITY_USED_HOOKS.pop()
            data.ABILITY_FAILED_HOOKS.pop()
        self.assertEqual(seen, [("used", "x"), ("failed", "y"), ("used", "s")])


if __name__ == "__main__":
    unittest.main()

"""修饰器九阶段公式与概率收敛。

要点：未出现的阶段不参与计算（加算缺省 0、乘算缺省 1）；
乘算必须作用在真实 base 上，传 0 会被吃掉。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest

from weiren_game.engine import GameEngine
from weiren_game.modifier_rules import calculate_modified_amount, spec
from weiren_game.probability import resolve


def _amount(base: float, *mods) -> float:
    return calculate_modified_amount(base, [m.build() for m in mods])


class ModifierFormulaTests(unittest.TestCase):
    def test_stages_and_identities(self) -> None:
        self.assertEqual(_amount(7.0), 7.0)                       # 空修饰器 = 恒等
        self.assertEqual(_amount(5.0, spec("x").flat(3)), 8.0)    # 缺乘算不参与
        self.assertEqual(_amount(4.0, spec("x").percent(0.5)), 6.0)
        self.assertEqual(_amount(5.0, spec("x").mul(2.0)), 10.0)

    def test_limited_mul_and_range_limit(self) -> None:
        # 有限制乘算：(10)×(3−1)=20 超出 limit=2 → 转同号特殊加算 +2。
        self.assertEqual(_amount(10.0, spec("x").mul(3.0, limit=2)), 12.0)
        mods = [spec("x").flat(100), spec("x").final().max(10)]
        self.assertEqual(_amount(0.0, *mods), 10.0)

    def test_zero_base_swallows_multiply(self) -> None:
        """调用方传 0 会让乘算失效——值型通道必须传真实数值。"""
        self.assertEqual(_amount(0.0, spec("x").mul(2.0)), 0.0)

    def test_probability_resolution(self) -> None:
        self.assertEqual(resolve(0.5), 0.5)
        self.assertEqual(resolve(-0.2), 0.05)
        self.assertEqual(resolve(1.2), 0.95)
        self.assertEqual(resolve(0.3, [1.0]), 1.0)        # 单一必定
        self.assertEqual(resolve(0.3, [1.0, 0.0]), 0.3)   # 必定冲突 → 回落计算

    def test_engine_channel_uses_path_and_source(self) -> None:
        # a2 的「受到伤害 ×1.1」经 healthDamage 通道在最终阶段生效。
        engine = GameEngine.new_game(seed="modifier-channel", difficulty="a2")
        engine.state.house.tenants.clear()
        tenant = engine._add_tenant("hkw")
        engine.state.flow.phase = "action"
        engine._damage_health(tenant, 10, "测试")
        self.assertAlmostEqual(tenant.health, 89.0)


if __name__ == "__main__":
    unittest.main()

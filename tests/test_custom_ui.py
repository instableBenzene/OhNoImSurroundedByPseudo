"""自定义 UI：专属状态容器与专属面板（样例 = 花尔维纳的「田」）。

覆盖三件事：专属容器进存档、田的规则（水分/生长/干旱/枯萎/采收），以及面板的分发契约。
"""

try:
    import _baseline  # noqa: F401
except ModuleNotFoundError:
    pass

import unittest

from weiren_game.data.characters import CHARACTER_PANELS, flowey
from weiren_game.engine import GameEngine
from weiren_game.exceptions import RuleViolation
from weiren_game.items import ItemInstance
from weiren_game.tenant import CONTAINER_TYPES, TenantState

FOOD = "common_food"
WATER = "water"


class GardenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine.new_game(seed="garden")
        self.tenant = TenantState(id=9901, character_id="flowey")
        self.engine.state.house.tenants[9901] = self.tenant
        self.field = self.engine.container(self.tenant, flowey.FIELD_KEY)

    def give(self, item_id: str, count: int = 1) -> None:
        """塞点东西进他的背包（种下/浇水都从这里扣）。"""
        self.tenant.inventory.add(
            ItemInstance(self.engine.state.ids.allocate_item(), item_id, count=count)
        )

    def drop(self, index: int, item_id: str) -> None:
        self.engine.panel_action(9901, "drop", slot=index, item_id=item_id)

    def tick(self) -> None:
        flowey.turn_start(self.engine, self.tenant)

    def slot(self, index: int, role: str) -> dict:
        slots = self.engine.panel_view(self.tenant)["slots"]
        return next(s for s in slots if s["group"] == index and s["role"] == role)

    def water_when_dry(self, index: int = 0) -> None:
        """不满水就补一瓶（满水再浇会被拒，所以先看状态）。"""
        plot = self.field.plot(index)
        if plot["seed"] and plot["moisture"] < flowey.MOISTURE_MAX:
            self.give(WATER)
            self.drop(index, WATER)

    # ---------------------------------------------------------------- 容器
    def test_container_is_declared_and_survives_save(self) -> None:
        self.assertIs(CONTAINER_TYPES[("flowey", flowey.FIELD_KEY)], flowey.FieldState)
        self.assertIsNotNone(self.field)
        self.give(FOOD)
        self.drop(0, FOOD)
        restored = type(self.engine.state).from_dict(self.engine.state.to_dict())
        plot = restored.house.tenants[9901].containers[flowey.FIELD_KEY].plot(0)
        self.assertEqual(plot["seed"], FOOD)

    # ---------------------------------------------------------------- 面板
    def test_panel_view_shape(self) -> None:
        self.assertIsNone(self.engine.panel_view(TenantState(id=9902, character_id="dragon")))
        view = self.engine.panel_view(self.tenant)
        self.assertEqual(len(view["slots"]), flowey.PLOT_COUNT * 2)   # 每块地：地格 + 产物格
        self.assertTrue(self.slot(0, "seed")["on_drop"])              # 空地可以拖入
        self.assertFalse(self.slot(0, "seed")["locked"])
        self.give(FOOD)
        self.drop(0, FOOD)
        self.assertTrue(self.slot(0, "seed")["locked"])               # 种下之后取不出来
        self.assertEqual(self.slot(0, "seed")["item"]["item_id"], FOOD)

    def test_drop_rules(self) -> None:
        with self.assertRaisesRegex(RuleViolation, "空着"):
            self.drop(0, WATER)                                       # 空地不能浇水
        self.give("garlic")                                           # seasoning 也是 food
        self.give("newspaper")                                        # 非食物
        with self.assertRaisesRegex(RuleViolation, "只能种"):
            self.drop(0, "newspaper")
        self.drop(0, "garlic")
        with self.assertRaisesRegex(RuleViolation, "已经种着"):
            self.give(FOOD)
            self.drop(0, FOOD)
        with self.assertRaisesRegex(RuleViolation, "满了"):
            self.give(WATER)
            self.drop(0, WATER)                                       # 刚种下就是满水
        with self.assertRaisesRegex(RuleViolation, "空着"):
            self.give(WATER)
            self.drop(1, WATER)                                       # 1 号地空着

    # ---------------------------------------------------------------- 规则
    def test_growth_water_and_harvest(self) -> None:
        self.give(FOOD, count=1)
        self.drop(0, FOOD)                                            # 种下即满水
        for _ in range(4):                                            # 每回合补满水 → 每回合 +2
            self.tick()
            self.water_when_dry()
        self.assertEqual(self.field.plot(0)["progress"], 0)           # 一熟就腾地
        self.assertEqual(self.slot(0, "seed")["item"], None)          # 地腾出来了
        product = self.slot(0, "product")
        self.assertEqual(product["item"], {"item_id": FOOD, "count": flowey.BASE_YIELD})
        self.assertFalse(product["locked"])
        before = self.engine.state.house.inventory.count(FOOD)
        self.engine.panel_action(9901, "take", slot=0)
        self.assertEqual(
            self.engine.state.house.inventory.count(FOOD) - before, flowey.BASE_YIELD
        )
        self.assertEqual(self.slot(0, "product")["item"], None)

    def test_drought_loses_yield_then_withers(self) -> None:
        self.give(FOOD)
        self.drop(0, FOOD)
        for _ in range(3):                                            # 前 3 回合：满水 → +2 → +1 → +1
            self.tick()
        self.assertEqual(self.field.plot(0)["progress"], 4)
        self.assertEqual(self.field.plot(0)["moisture"], 0)
        self.tick()                                                   # 断水第 1 回合：停住
        self.assertEqual(self.field.plot(0)["progress"], 4)
        self.tick()                                                   # 断水第 2 回合：减产
        self.assertEqual(self.field.plot(0)["yield_max"], flowey.BASE_YIELD - 1)
        self.tick()                                                   # 断水第 3 回合：枯
        self.assertEqual(self.field.plot(0)["seed"], "")
        self.assertEqual(self.field.plot(0)["progress"], 0)

    def test_replant_after_harvest(self) -> None:
        self.give(FOOD, count=2)
        self.drop(0, FOOD)
        for _ in range(4):
            self.tick()
            self.water_when_dry()
        self.assertEqual(self.slot(0, "seed")["item"], None)
        with self.assertRaisesRegex(RuleViolation, "收成"):
            self.drop(0, FOOD)                                        # 收成没收走之前不能接着种
        self.engine.panel_action(9901, "take", slot=0)
        self.drop(0, FOOD)
        self.assertEqual(self.slot(0, "seed")["item"]["item_id"], FOOD)

    def test_panel_is_registered_for_rollback(self) -> None:
        self.assertIn("flowey", CHARACTER_PANELS)
        self.assertEqual(CHARACTER_PANELS["flowey"], flowey.PANEL)

    def test_web_state_carries_the_projected_panel(self) -> None:
        """状态下发：格子里的物品被投影成与仓库同一种条目（前端只画，不去别处查）。"""
        from weiren_game import web_ui

        def card() -> dict:
            state = web_ui.build_state(self.engine)
            return next(t for t in state["tenants"] if t["id"] == 9901)

        self.assertEqual(card()["panel"]["title"], flowey.NAME_FIELD)
        self.assertTrue(card()["panel"]["backdrop"])
        seed = card()["panel"]["slots"][0]
        self.assertEqual((seed["role"], seed["onDrop"], seed["onTake"]), ("seed", "drop", ""))
        self.assertIsNone(seed["entry"])                       # 空地
        self.give(FOOD)
        self.drop(0, FOOD)
        entry = card()["panel"]["slots"][0]["entry"]
        self.assertEqual(entry[1], "常见的食物")                # 名字由后端查好
        self.assertIsInstance(entry[12], str)                   # 内容层图标标记

    def test_gardener_ability_only_opens_the_panel(self) -> None:
        """入口技能只声明"打开面板"：引擎不结算它，界面负责开合。"""
        ability = flowey.CHARACTER.actives[0]
        self.assertEqual(ability.id, "gardener")
        self.assertTrue(ability.opens_panel)
        self.engine.state.flow.phase = "action"
        self.engine.state.flow.turn = 1          # `skip_until_turn(0) >= turn(0)` 会被判成"无法行动"
        with self.assertRaisesRegex(RuleViolation, "在界面里打开"):
            self.engine.use_ability(self.tenant.id, ability_id="gardener")


if __name__ == "__main__":
    unittest.main()

"""印记系统：印记实例的获得/消耗/计数，并派发 mark.* 节点。"""

from __future__ import annotations

from weiren_game.marks import MarkInstance


class MarksSystemMixin:
    """通用印记机制（种类与上下限由角色档案的 MARKS 声明）。"""

    def _mark_definition(self, tenant: object, mark_id: str):
        """返回该角色某印记的定义（无则 None）。"""
        from weiren_game.data import CHARACTER_MARKS

        for definition in CHARACTER_MARKS.get(tenant.character_id, ()):
            if getattr(definition, "id", None) == mark_id:
                return definition
        return None

    def _mark_count(self, tenant: object, mark_id: str) -> float:
        """返回该房客某印记的累计数值。"""
        return tenant.marks.count(mark_id)

    def _gain_mark(
        self, tenant: object, mark_id: str, amount: float = 1.0, *, external: bool = False
    ):
        """获得印记（按定义上限钳制），派发 mark.gained / mark.reached。"""
        if tenant.character_id is None:
            return None
        definition = self._mark_definition(tenant, mark_id)
        if external and getattr(definition, "externally_locked", False):
            return None
        value = float(amount)
        maximum = getattr(definition, "maximum", None)
        if maximum is not None:
            value = min(value, max(0.0, float(maximum) - tenant.marks.count(mark_id)))
        if value <= 0:
            return None
        instance = MarkInstance(self.state.ids.allocate_mark(), mark_id, value)
        tenant.marks.add(instance)
        self._dispatch_mark_node("gained", tenant, mark_id, value)
        if maximum is not None and tenant.marks.count(mark_id) >= float(maximum):
            self._dispatch_mark_node("reached", tenant, mark_id, float(maximum))
        return instance

    def _consume_mark(
        self, tenant: object, mark_id: str, amount: float = 1.0, *, external: bool = False
    ) -> float:
        """消耗印记（实例编号最小者优先），派发 mark.consumed，返回实际消耗。"""
        if external and getattr(
            self._mark_definition(tenant, mark_id), "externally_locked", False
        ):
            return 0.0
        consumed = tenant.marks.consume(mark_id, float(amount))
        if consumed > 0:
            self._dispatch_mark_node("consumed", tenant, mark_id, consumed)
        return consumed

    def _dispatch_mark_node(
        self, kind: str, tenant: object, mark_id: str, amount: float
    ) -> None:
        """按 gained/consumed/reached 派发印记节点钩子。"""
        from weiren_game.data import (
            MARK_CONSUMED_HOOKS,
            MARK_GAINED_HOOKS,
            MARK_REACHED_HOOKS,
        )

        hooks = {
            "gained": MARK_GAINED_HOOKS,
            "consumed": MARK_CONSUMED_HOOKS,
            "reached": MARK_REACHED_HOOKS,
        }[kind]
        for hook in hooks:
            hook(self, tenant, mark_id, amount)

    def _emit_node(self, node: str, **context: object) -> None:
        """派发通用内容节点（door.* / item.* / bond.* / tenant.* 等）。"""
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get(node, ()):
            hook(self, **context)

    # ------------------------------------------------------- global events
    def _set_global_event(
        self, event_id: str, value: float = 0.0, layers: int = 1
    ) -> None:
        """设置/刷新一个全局事件（世界级条件）。"""
        self.state.world.global_events.set(event_id, value, layers)

    def _global_event_active(self, event_id: str) -> bool:
        """全局事件是否生效。"""
        return self.state.world.global_events.active(event_id)

    def _global_event_value(self, event_id: str, default: float = 0.0) -> float:
        """全局事件数值（未生效返回默认值）。"""
        return self.state.world.global_events.value_of(event_id, default)

    def _consume_global_event(self, event_id: str) -> object:
        """一次性消费一个全局事件（返回实例或 None）。"""
        return self.state.world.global_events.consume(event_id)

    def _decay_global_events(self) -> None:
        """回合末：全部全局事件剩余回合 -1，归 0 移除。"""
        self.state.world.global_events.decay()

    # ------------------------------------------- 统一修饰器入口（声明式）
    def _apply_modifiers(
        self,
        effect_type: str,
        base: float,
        source: object = (),
        context: object = None,
    ) -> float:
        """统一入口：收集某通道的修饰器并编译（不含概率收敛）。"""
        from weiren_game.modifier_rules import (
            calculate_modified_amount,
            collect_modifiers,
        )

        merged: dict[str, object] = {"engine": self}
        if isinstance(context, dict):
            merged.update(context)
        return calculate_modified_amount(
            base, collect_modifiers(effect_type, source, merged)
        )

    def _eval_gate(
        self,
        gate_type: str,
        source: object = (),
        context: object = None,
        base: bool = False,
    ) -> bool:
        """统一闸门入口：收集某闸门的贡献项并做逻辑聚合。

        **纯查询**：不掷骰、不写状态（见 docs/ARCH.md §2 硬规则）。掷骰/消耗放在结算点。
        """
        from weiren_game.modifier_rules import collect_gates, evaluate_gate

        merged: dict[str, object] = {"engine": self}
        if isinstance(context, dict):
            merged.update(context)
        return evaluate_gate(base, collect_gates(gate_type, source, merged))

    # ------------------------------------------------------ pseudo caps
    # 说明：描述层说的“压制/受到抑制”，在代码层并无独立概念，而是
    # “禁用伪人的某些行为位”。世界牌/该角色正义执行只是选择禁用其中几项；
    # 解放（liberate）不属任何行为位，不受影响。
    _PSEUDO_SUPPRESS_CAPS = ("visit", "cast", "breakthrough", "auto_expel")

    def _suppress_pseudo(self, layers: int, capabilities: object = None) -> None:
        """禁用伪人的指定行为位（默认 visit/cast/breakthrough/auto_expel）。

        “压制”只是描述用词；实现上就是为对应能力位登记禁用全局事件。
        """
        caps = tuple(capabilities) if capabilities is not None else self._PSEUDO_SUPPRESS_CAPS
        for cap in caps:
            self._set_global_event(f"suppress.pseudo.{cap}", 1.0, layers)

    def _pseudo_capability(self, name: str) -> bool:
        """伪人某行为位是否可用（未处于对应禁用事件中）。"""
        return not self._global_event_active(f"suppress.pseudo.{name}")

    def _pseudo_enters_house(self) -> bool:
        """当前伪人是否会亲自到访（推动门口事件）。"""
        from weiren_game.data import PSEUDOS

        definition = PSEUDOS.get(self.state.pseudo_state.scenario_id)
        return True if definition is None else definition.enters_house

    # ------------------------------------------------------------ personas
    def _has_persona(self, tenant: object, persona: str) -> bool:
        """房客是否持有某个人设（人设即隐藏 condition）。"""
        return tenant.condition(f"persona_{persona}").active

    def _personas_of(self, tenant: object) -> list[str]:
        """返回房客当前持有的人设列表（按状态表内顺序）。"""
        return [
            key[len("persona_"):]
            for key, value in tenant.conditions.items()
            if key.startswith("persona_") and value.active
        ]

    def _set_personas(self, tenant: object, values: list[str]) -> None:
        """整体设置房客人设（清除未列出的，写入列出的）。"""
        cleaned = [value for value in values if value]
        for key in [key for key in tenant.conditions if key.startswith("persona_")]:
            tenant.clear_status(key)
        for persona in cleaned:
            tenant.set_status(f"persona_{persona}", intensity=1, layers=99)

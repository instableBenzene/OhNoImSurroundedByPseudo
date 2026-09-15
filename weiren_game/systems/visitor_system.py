"""门口事件：人类访客/伪人到访/补给的接纳与拒绝。"""

from __future__ import annotations



from weiren_game.content import CONTENT
from weiren_game.data import (
    EVENT_IDS,
    PERSONALITY_LABELS,
)
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.models import DoorEvent
from weiren_game.tenant import TenantState as Tenant

from weiren_game.exceptions import RuleViolation

class VisitorSystemMixin:

    def _return_departed_tenants(self) -> None:
        """为到达返回回合且尚无事件的暂时离开房客生成敲门事件。"""
        for tenant in self.living_tenants():
            if (
                tenant.temporarily_away and not tenant.return_event_pending
                and tenant.return_turn <= self.state.flow.turn
            ):
                tenant.return_event_pending = True
                definition = self.character(tenant)
                self.state.world.events.door_events.append(DoorEvent(
                    "human", f"离开的访客返回：{definition.name}",
                    f"{definition.name}在黑暗里徘徊许久后再次敲门，必须重新决定是否接纳。",
                    visitor_id=definition.tenant_id,
                    metadata={"returning_tenant_id": tenant.id},
                ))
                self._log(f"曾离开的{definition.name}再次来到门外。")

    # --------------------------------------------------------------- door events
    def _queue_scheduled_visitors(self) -> None:
        """按伪人到访日程生成门口事件，伪人未到期则排队普通访客，并补入额外访客。"""
        pseudo = self.state.pseudo_state
        pseudo_can_act = self._pseudo_capability("visit")
        door_visit_ok = self._pseudo_enters_house()
        pseudo_due = (
            door_visit_ok and not pseudo.liberated and pseudo_can_act
            and self.state.flow.turn >= self.state.world.visitors.next_pseudo_turn
        )
        if pseudo_due:
            count = 1 + int(self._global_event_value("visitor.extra_pseudo", 0.0))
            self._consume_global_event("visitor.extra_pseudo")
            for _ in range(count):
                definition = PSEUDOS[pseudo.scenario_id]
                self.state.world.events.door_events.append(DoorEvent(
                    "pseudo", f"伪人到访：{definition.name}", definition.description,
                    pseudo_id=pseudo.scenario_id,
                ))
            self.state.world.visitors.next_pseudo_turn = self._roll_next_pseudo_visit(self.state.flow.turn)
        else:
            self._queue_human_visitor()

        extra = int(self._global_event_value("visitor.extra", 0.0))
        self._consume_global_event("visitor.extra")
        from weiren_game.data import NODE_HOOKS

        interval = None
        for hook in NODE_HOOKS.get("visitor.extra_interval", ()):
            interval = hook(self)
            if interval:
                break
        if interval and self.state.flow.turn % interval == 0:
            extra += 1
        for _ in range(extra):
            self._queue_human_visitor("额外访客来到了门前。")

    def _queue_human_visitor(self, reason: str | None = None, *, force_supply: bool = False) -> None:
        """从访客名册排队一位人类访客；名册为空时视规则改为补给事件。"""
        if self._global_event_active("visitor.suppress"):
            self._log("下一次访客来访被取消。")
            return
        if self._global_event_active("visitor.supply"):
            white_only = self._global_event_value("visitor.supply", 1.0) >= 2
            self._consume_global_event("visitor.supply")
            self.state.world.events.door_events.append(DoorEvent(
                "supply", "神秘的补给", "门外无人，只有一个无署名纸箱。",
                metadata={"white_only": white_only},
            ))
            return
        if self.state.world.visitors.visitor_pool:
            character_id = self.state.world.visitors.visitor_pool.pop(0)
            definition = CHARACTERS[character_id]
            personalities = f"{PERSONALITY_LABELS[definition.primary]}-{PERSONALITY_LABELS[definition.secondary]}"
            self.state.world.events.door_events.append(DoorEvent(
                "human", f"访客：{definition.name}",
                f"{definition.description} 性格：{personalities}；携带能力：{definition.carry}。",
                visitor_id=character_id,
            ))
            if reason:
                self._log(reason)
        else:
            from weiren_game.data import NODE_HOOKS

            supply_active = any(
                hook(self) for hook in NODE_HOOKS.get("visitor.supply", ())
            )
            # Only an active Gentle bond turns an impossible visit into a
            # supply that counts as accepted.  Fire Dragon's active ability has
            # its own explicit supply fallback, but that alone is not an
            # acceptance trigger.
            if force_supply or supply_active:
                self.state.world.events.door_events.append(DoorEvent(
                    "supply", "神秘的补给", "访客名册已经空了，门口留下一个无署名纸箱。",
                    metadata={"counts_as_accept": supply_active},
                ))
                if reason:
                    self._log(reason.replace("访客", "补给"))

    def handle_next_door_event(self, decision: str = "inspect") -> None:
        """处理门口首个事件：按类型结算人类接纳/拒绝、补给领取或伪人到访。"""
        self._require_no_pending_choice()
        if not self.state.world.events.door_events:
            raise RuleViolation("门外目前没有待处理事件。")
        event = self.state.world.events.door_events[0]
        if event.kind == "human":
            if decision not in {"accept", "reject"}:
                raise RuleViolation("人类访客必须选择 accept（接纳）或 reject（拒绝）。")
            returning_id = event.metadata.get("returning_tenant_id")
            if decision == "accept" and not returning_id and len(self.living_tenants()) >= 10:
                raise RuleViolation("屋内最多容纳10名房客；请拒绝这位访客或先腾出位置。")
            self.state.world.events.door_events.pop(0)
            self._visitor_arrived(counts_as_visit=True)
            definition = CHARACTERS[event.visitor_id or ""]
            self._observe_visit_information(
                "returning_visit" if event.metadata.get("returning_tenant_id") else "human_visit",
                character_id=definition.tenant_id,
                tenant_id=returning_id or 0,
            )
            if decision == "accept":
                if returning_id:
                    tenant = self.state.house.tenants.get(returning_id)
                    if not tenant or not tenant.alive:
                        raise RuleViolation("这位返回者已经无法再次入住。")
                    tenant.at_home = True
                    tenant.temporarily_away = False
                    tenant.return_event_pending = False
                    self._log(f"你重新接纳了{definition.name}（{tenant.id}）。")
                    self._on_accept_healing(tenant)
                else:
                    tenant = self._add_tenant(definition.tenant_id)
                    self._log(f"你接纳了{definition.name}，其房客编号为{tenant.id}。")
                    self._on_tenant_accepted(tenant)
                self.state.world.visitors.visitor_rejections[definition.tenant_id] = 0
                self._pseudo_visitor_mark()
                count = tenant.turn_counters.get("visit_count", 0) + 1
                tenant.turn_counters["visit_count"] = count
                self._emit_node(
                    "door.accept",
                    kind="human",
                    tenant=tenant,
                    character_id=definition.tenant_id,
                    returning=bool(returning_id),
                )
                if returning_id:
                    self._emit_node(
                        "tenant.returned",
                        tenant=tenant,
                        character_id=definition.tenant_id,
                        visit_count=count,
                    )
            else:
                rejected = self.state.world.visitors.visitor_rejections.get(definition.tenant_id, 0) + 1
                self.state.world.visitors.visitor_rejections[definition.tenant_id] = rejected
                if returning_id:
                    tenant = self.state.house.tenants.get(returning_id)
                    if tenant:
                        tenant.return_event_pending = False
                        if rejected < 2:
                            tenant.temporarily_away = True
                            tenant.return_turn = self.state.flow.turn + 2
                        else:
                            tenant.temporarily_away = False
                            tenant.alive = False
                elif rejected < 2:
                    self.state.world.visitors.visitor_pool.append(definition.tenant_id)
                suffix = "；连续拒绝两次后将不再来访" if rejected >= 2 else "；他/她以后还会再尝试一次"
                self._log(f"你拒绝了{definition.name}，脚步声消失在黑暗中{suffix}。")
                self._emit_node(
                    "door.reject",
                    kind="human",
                    character_id=definition.tenant_id,
                    returning=bool(returning_id),
                )
            self._record_action("door", kind="human", decision=decision, visitor=definition.tenant_id)
            self._activate_new_bonds()
            return

        self.state.world.events.door_events.pop(0)
        counts_as_accept = bool(event.metadata.get("counts_as_accept"))
        self._visitor_arrived(
            # The manuscript's information taxonomy distinguishes ordinary
            # “访客来访” from “伪人来访”; fear marks use the former wording.
            counts_as_visit=counts_as_accept
        )
        if event.kind == "supply":
            if event.metadata.get("white_only"):
                candidates = [
                    value.item_id for value in ITEMS.values()
                    if value.searchable and value.quality == 0
                ]
                rewards = [
                    self._rng(EVENT_IDS["supply"], "white", index).choice(candidates)
                    for index in range(2)
                ]
            else:
                rewards = [
                    self._random_item(event_id=EVENT_IDS["supply"], event_suffix=(index,))
                    for index in range(2)
                ]
            for item_id in rewards:
                self._gain_item(item_id)
            self._log("你收下补给：" + "、".join(ITEMS[item_id].name for item_id in rewards) + "。")
            if counts_as_accept:
                self._pseudo_visitor_mark()
                self._on_accept_healing(None)
            self._emit_node("door.accept", kind="supply")
            self._record_action("door", kind="supply")
            return
        if event.kind == "pseudo":
            self._observe_visit_information("pseudo_visit")
            self._record_action("door", kind="pseudo", pseudo=event.pseudo_id)
            self._resolve_pseudo_visit()
            return
        raise RuleViolation(f"未知门口事件：{event.kind}")

    def _visitor_arrived(self, *, counts_as_visit: bool = False) -> None:
        """访客到达的统一结算：按条件累计伪人恐惧印记。"""
        if counts_as_visit:
            self._pseudo_visitor_mark()

    def _pseudo_visitor_mark(self) -> None:
        """访客到达标记：由当前伪人场景注册的 visitor_mark 决定是否累加。"""
        from weiren_game.data import SCENARIO_HANDLERS

        handler = SCENARIO_HANDLERS.get(self.state.pseudo_state.scenario_id, {}).get(
            "visitor_mark"
        )
        if handler is not None:
            handler(self)

    def _on_tenant_accepted(self, tenant: Tenant) -> None:
        """新房客入住时结算其带来的赠礼（该角色、该角色、该角色等）。"""
        self._on_accept_healing(tenant)
        from weiren_game.data import CHARACTER_NODE_HOOKS

        hook = CHARACTER_NODE_HOOKS.get(tenant.character_id, {}).get("on_arrival")
        if hook is not None:
            hook(self, tenant)
        # 难度词条 a10：被接纳时附带 1/99 的创伤或紊乱。
        from weiren_game.data import DIFFICULTIES

        if DIFFICULTIES[self.state.meta.difficulty].get("start_condition_trauma_disorder"):
            condition_id = (
                "trauma"
                if self._rng("difficulty.accept_condition", tenant.id).random() < .5
                else "disorder"
            )
            tenant.set_status(condition_id, intensity=1, layers=99)
            self._log(f"{self.character(tenant).name}带着难以言说的伤痛入住。")
        # 入住即结算免疫：a-10 一次性获得 99 点常驻充能；高生命给 1 点。
        from weiren_game.effects.health_sanity import (
            grant_permanent_trauma_disorder_immunity,
            refresh_high_health_immunity,
        )

        grant_permanent_trauma_disorder_immunity(self, tenant)
        refresh_high_health_immunity(self, tenant)

    def _on_accept_healing(self, accepted: Tenant | None) -> None:
        """按该性格性格与羁绊等级，为屋内房客结算接纳访客时的治愈效果。"""
        from weiren_game.data import NODE_HOOKS

        for hook in NODE_HOOKS.get("visitor.accept_healing", ()):
            hook(self, accepted)

"""物资实例管理（装备/使用/耐久/损耗）与 tag/on_use 效果分发。"""

from __future__ import annotations


import math

from weiren_game.content import CONTENT
from weiren_game.data import (
    EVENT_IDS,
    ITEM_EFFECTS,
    TAG_BEHAVIORS,
    ItemDefinition,
)
from weiren_game.data.lang import TEXT
CHARACTERS = CONTENT.characters()
ITEMS = CONTENT.items()
LOCATIONS = CONTENT.locations()
PSEUDOS = CONTENT.pseudos()
from weiren_game.tenant import TenantState as Tenant
from weiren_game.items import ItemInstance

from weiren_game.exceptions import RuleViolation

class ItemSystemMixin:

    # ---------------------------------------------------------------- inventory

    def _tenant_item_ids(self, tenant: Tenant) -> list[str]:
        """返回房客背包当前全部物品 ID（每个实例一条，按槽位顺序）。"""
        return [value.item_id for value in tenant.inventory.items]

    def _tenant_item_group_count(self, tenant: Tenant) -> int:
        """按“每实例占一格”计算房客背包当前占用组数。"""
        return len(tenant.inventory.items)

    # ------------------------------------------------------------- slot helpers
    def _return_tenant_items(self, tenant: Tenant) -> None:
        """把房客背包中的全部物资归还屋主仓库（可堆叠品按堆叠合并）。"""
        for instance in list(tenant.inventory.items):
            tenant.inventory.remove(instance.item_instance_id)
            item = ITEMS.get(instance.item_id)
            if item is not None and item.stack_size > 1:
                self._merge_house_item(instance.item_id, instance.count, instance.durability)
            else:
                self.state.house.inventory.add(instance)

    def _spill_tenant_overflow(self, tenant: Tenant) -> None:
        """容量缩小时，把超出当前格数的物资移回屋主仓库（不凭空消失）。"""
        capacity = self.tenant_carry_capacity(tenant)
        overflow = [value for value in list(tenant.inventory.items) if value.plot >= capacity]
        if not overflow:
            return
        for instance in overflow:
            tenant.inventory.remove(instance.item_instance_id)
            item = ITEMS.get(instance.item_id)
            if item is not None and item.stack_size > 1:
                self._merge_house_item(instance.item_id, instance.count, instance.durability)
            else:
                self.state.house.inventory.add(instance)
        names = "、".join(ITEMS[value.item_id].name for value in overflow if value.item_id in ITEMS)
        self._log(
            TEXT["systems.item_system._spill_tenant_overflow.1"].format(p1=self.character(tenant).name, p2=names)
        )

    def move_item(
        self,
        *,
        container: str,
        from_slot: int,
        to_slot: int,
        tenant_id: int | None = None,
    ) -> None:
        """在仓库或某房客背包内把一件物资移动到指定格（目标已占用则交换）。"""
        self._require_no_pending_choice()
        if container == "warehouse":
            inventory = self.state.house.inventory
        elif container == "tenant":
            tenant = self._require_home_tenant(tenant_id)
            inventory = tenant.inventory
            if not (0 <= int(to_slot) < self.tenant_carry_capacity(tenant)):
                raise RuleViolation(TEXT["systems.item_system.move_item.1"])
        else:
            raise RuleViolation(TEXT["systems.item_system.move_item.2"])
        instance = inventory.at_plot(int(from_slot))
        if instance is None:
            raise RuleViolation(TEXT["systems.item_system.move_item.3"])
        inventory.move_to(instance, int(to_slot))
        self._record_action(
            "move_item", container=container, tenant=tenant_id,
            item=instance.item_id, slot=int(to_slot),
        )

    def _item_tag_fn(self, item: ItemDefinition, name: str):
        """按物品 tag 顺序找行为模块里的某个钩子（先命中先执行，找不到返回 None）。

        钩子名由**消费方**决定：`use`（使用该物资）、`after_food`（食用后）等；
        行为体一律就近住在 `data/tags/<tag>.py`，核心不认识具体是哪种物资。
        """
        for tag in item.tags:
            module = TAG_BEHAVIORS.get(tag)
            fn = getattr(module, name, None) if module is not None else None
            if fn is not None:
                return fn
        return None

    def _add_house_item(self, item_id: str, durability: int = 0, count: int = 1):
        """在屋主仓库中创建一个新物品实例并返回它。"""
        instance = ItemInstance(
            self.state.ids.allocate_item(), item_id, count=max(1, int(count)), durability=int(durability)
        )
        self.state.house.inventory.add(instance)
        return instance

    def _merge_house_item(self, item_id: str, amount: int, durability: int = 0) -> None:
        """按 stack_size 把若干单位并入屋主仓库（可堆叠品合并，否则逐件新实例）。"""
        remaining = max(0, int(amount))
        size = max(1, ITEMS[item_id].stack_size)
        if size <= 1:
            for _ in range(remaining):
                self._add_house_item(item_id, durability)
            return
        for instance in self.state.house.inventory.by_item_id(item_id):
            if instance.durability != durability:
                continue
            room = size - instance.count
            if room <= 0:
                continue
            take = min(room, remaining)
            instance.count += take
            remaining -= take
            if remaining <= 0:
                return
        while remaining > 0:
            take = min(size, remaining)
            self._add_house_item(item_id, durability, take)
            remaining -= take

    def _gain_loot_item(self, item_id: str, event_name: str, *suffix: object) -> None:
        """战利品授予：可堆叠品按 obtain_range 掷出数量后并入仓库（不可堆叠固定 1）。"""
        item = ITEMS.get(item_id)
        if item is None:
            return
        if item.durable or item.stack_size <= 1:
            self._gain_item(item_id)
            return
        if item.obtain_range is not None:
            low, high = item.obtain_range
        else:
            # 默认区间：stack_size / 4 ± 1（下限 ≥1，上限 ≤stack_size）。
            center = max(1, item.stack_size // 4)
            low, high = max(1, center - 1), min(item.stack_size, center + 1)
        low = max(1, min(int(low), int(high)))
        high = max(low, min(int(item.stack_size), int(high)))
        quantity = self._rng(event_name, item_id, *suffix).randint(low, high)
        self._gain_item(item_id, quantity)

    def _gain_item(self, item_id: str, amount: int = 1, *, process_carrier: bool = True) -> None:
        """将物品以实例形式加入屋主仓库；信息载体与手机即时兑换为信息。"""
        if item_id not in ITEMS or amount <= 0:
            return
        item = ITEMS[item_id]
        from weiren_game.data.items import item_gain_info_spec

        spec = item_gain_info_spec(item_id) if process_carrier else None
        if spec is not None:
            kinds = set(spec["kinds"]) if spec.get("kinds") else None
            if not spec.get("keep"):
                for _ in range(amount):
                    for _ in range(int(spec["truth"])):
                        self._create_random_information(True, item.name, kinds)
                    for _ in range(int(spec["false"])):
                        self._create_random_information(False, item.name, kinds)
                if spec.get("log"):
                    self._log(f"{item.name}{spec['log']}")
                return
        durability = item.max_durability if item.durable else 0
        self._merge_house_item(item_id, amount, durability)
        # 保留实物的载体（该信息载体）在入库后附带生成信息。
        if spec is not None and spec.get("keep"):
            kinds = set(spec["kinds"]) if spec.get("kinds") else None
            for _ in range(amount):
                for _ in range(int(spec["false"])):
                    self._create_random_information(False, item.name, kinds)

    def transfer_item(
        self,
        from_id: int,
        to_id: int,
        item_id: str,
        *,
        slot: int | None = None,
        target_slot: int | None = None,
    ) -> None:
        """把一件物资从一名房客的背包移到另一名房客的背包（可指定目标格）。"""
        self._require_no_pending_choice()
        if self.state.flow.phase != "action":
            raise RuleViolation(TEXT["systems.item_system.transfer_item.1"])
        source = self._require_home_tenant(from_id)
        target = self._require_home_tenant(to_id)
        if source.id == target.id:
            return
        if target_slot is not None and not (
            0 <= int(target_slot) < self.tenant_carry_capacity(target)
        ):
            raise RuleViolation(TEXT["systems.item_system.transfer_item.2"])
        if len(target.inventory.items) >= self.tenant_carry_capacity(target):
            raise RuleViolation(TEXT["systems.item_system.transfer_item.3"])
        instance = (
            source.inventory.at_plot(int(slot)) if slot is not None
            else source.inventory.remove_first(item_id)
        )
        if instance is not None and instance.item_id != item_id:
            instance = None
        if instance is None:
            raise RuleViolation(TEXT["systems.item_system.transfer_item.4"])
        if slot is not None:
            source.inventory.remove(instance.item_instance_id)
        target.inventory.add(instance, plot=target_slot)
        self._spill_tenant_overflow(source)
        self._record_action("transfer", tenant=target.id, source=source.id, item=item_id)
        self._log(TEXT["systems.item_system.transfer_item.5"].format(p1=self.character(source).name, p2=self.character(target).name, p3=ITEMS[item_id].name))

    def migrate_carriers(self) -> None:
        """"获得即兑换"的信息载体（keep=False）不该留存：读档时统一兑换为信息。"""
        from weiren_game.data.items import item_gain_info_spec

        def convert(inventory) -> None:
            for instance in list(inventory.items):
                spec = item_gain_info_spec(instance.item_id)
                if spec is not None and not spec.get("keep"):
                    amount = int(instance.count)
                    inventory.consume(instance.item_id, instance.count)
                    self._gain_item(instance.item_id, amount)

        convert(self.state.house.inventory)
        for tenant in self.state.house.tenants.values():
            convert(tenant.inventory)

    def _take_item(self, item_id: str, inventory=None, *, spot=None) -> int:
        """从指定容器（默认屋主仓库）消耗 1 个单位并返回其耐久。"""
        source = inventory if inventory is not None else self.state.house.inventory
        if spot is not None and spot in source.items and spot.item_id == item_id:
            instance = spot
        else:
            instance = next((v for v in source if v.item_id == item_id), None)
        if instance is None:
            name = ITEMS[item_id].name if item_id in ITEMS else item_id
            raise RuleViolation(TEXT["systems.item_system._take_item.1"].format(p1=name))
        durability = instance.durability
        if instance.count > 1:
            instance.count -= 1
        else:
            source.remove(instance.item_instance_id)
        return durability

    def _durability_multiplier(self) -> float:
        """返回全局耐久消耗倍率（下限为 0）。"""
        return max(0.0, self._global_event_value("item.durability.multiplier", 1.0))

    def _fragile_chance(self, base: float, tenant: Tenant | None = None) -> float:
        """计算物品易损概率，叠加羁绊与性格修饰后限制在 5% 至 100%。"""
        if base <= 0:
            return 0.0
        source = (TEXT["systems.item_system._fragile_chance.1"],) + ((tenant.character_id,) if tenant else ())
        value = self._apply_modifiers("chance", base, source, {"tenant": tenant})
        value *= max(0.0, self._global_event_value("item.fragile.multiplier", 1.0))
        from weiren_game.probability import resolve

        return resolve(value)
#注意，易损品和耐久度消耗品并不是一类东西，易损品指的是在一定条件后可能直接被消耗，这类物品没有耐久度；耐久度消耗品是在一定条件后会消耗耐久度，当耐久度归零后该物品实例消失。且羁绊效果同样是可能作用的对象也有所不同，这里的表达不够清晰。
# 通用概率统一夹取在 5%~95%；“必定”(100%) 属于必然结果，不参与夹取。
    def _consume_durability(
        self, item_id: str, amount: int, *, tenant: Tenant | None = None,
        inventory=None, spot=None,
    ) -> bool:
        """消耗指定容器（默认屋主仓库）最靠前一件同款耐久品的耐久。"""
        source = inventory if inventory is not None else self.state.house.inventory
        if (
            spot is not None and spot in source.items
            and spot.item_id == item_id and spot.durability > 0
        ):
            instance = spot
        else:
            instance = source.earliest(
                lambda value: value.item_id == item_id and value.durability > 0
            )
        if instance is None:
            return False
        cost = max(1, math.ceil(amount * self._durability_multiplier()))
        instance.durability -= cost
        if instance.durability <= 0:
            source.remove(instance.item_instance_id)
            self._log(TEXT["systems.item_system._consume_durability.1"].format(p1=ITEMS[item_id].name))
            self._emit_node("item.broken", item_id=item_id)
            return True
        return False

    def equip_item(
        self,
        tenant_id: int,
        item_id: str,
        *,
        source_tenant: int | None = None,
        slot: int | None = None,
        target_slot: int | None = None,
    ) -> None:
        """行动阶段把一件物资装入指定屋内房客的背包（可指定来源与目标格）。"""
        self._require_no_pending_choice()
        if self.state.flow.phase != "action":
            raise RuleViolation(TEXT["systems.item_system.equip_item.1"])
        if item_id not in ITEMS:
            raise RuleViolation(TEXT["systems.item_system.equip_item.2"])
        tenant = self._require_home_tenant(tenant_id)
        source = self._require_home_tenant(source_tenant) if source_tenant else None
        inventory = source.inventory if source is not None else self.state.house.inventory
        item = ITEMS[item_id]
        if target_slot is not None and not (
            0 <= int(target_slot) < self.tenant_carry_capacity(tenant)
        ):
            raise RuleViolation(TEXT["systems.item_system.equip_item.3"])
        same_owner = source is not None and source.id == tenant.id
        if same_owner:
            instance = (
                inventory.at_plot(int(slot)) if slot is not None
                else inventory.remove_first(item_id)
            )
            if instance is None or instance.item_id != item_id:
                raise RuleViolation(TEXT["systems.item_system.equip_item.4"])
            if target_slot is not None:
                inventory.move_to(instance, int(target_slot))
            self._record_action("equip", tenant=tenant.id, item=item_id)
            self._log(TEXT["systems.item_system.equip_item.5"].format(p1=self.character(tenant).name, p2=item.name), shown=False)
            return
        if slot is not None:
            instance = inventory.at_plot(int(slot))
            if instance is None or instance.item_id != item_id:
                raise RuleViolation(TEXT["systems.item_system.equip_item.6"])
            inventory.remove(instance.item_instance_id)
        else:
            instance = inventory.remove_first(item_id)
            if instance is None:
                raise RuleViolation(TEXT["systems.item_system.equip_item.7"])
        if len(tenant.inventory.items) >= self.tenant_carry_capacity(tenant):
            inventory.add(instance, plot=slot if slot is not None else None)
            raise RuleViolation(TEXT["systems.item_system.equip_item.8"])
        tenant.inventory.add(instance, plot=target_slot)
        if source is not None:
            self._spill_tenant_overflow(source)
        self._record_action("equip", tenant=tenant.id, item=item_id)
        self._log(TEXT["systems.item_system.equip_item.9"].format(p1=self.character(tenant).name, p2=item.name), shown=False)

    def unequip_item(
        self,
        tenant_id: int,
        item_id: str,
        *,
        slot: int | None = None,
        target_slot: int | None = None,
    ) -> None:
        """卸下房客携带的物品，连同耐久放回物资栏（可指定目标格）。"""
        self._require_no_pending_choice()
        tenant = self._require_home_tenant(tenant_id)
        if slot is not None:
            held = tenant.inventory.at_plot(int(slot))
            if held is not None and held.item_id != item_id:
                held = None
        else:
            held = tenant.inventory.remove_first(item_id)
        if not held:
            raise RuleViolation(TEXT["systems.item_system.unequip_item.1"])
        if slot is not None:
            tenant.inventory.remove(held.item_instance_id)
        self.state.house.inventory.add(held, plot=target_slot)
        self._spill_tenant_overflow(tenant)
        self._record_action("unequip", tenant=tenant.id, item=item_id)
        self._log(TEXT["systems.item_system.unequip_item.2"].format(p1=self.character(tenant).name, p2=ITEMS[item_id].name), shown=False)

    def use_item(
        self,
        item_id: str,
        tenant_id: int | None = None,
        condition: str | None = None,
        *,
        source_tenant: int | None = None,
        slot: int | None = None,
    ) -> None:
        """行动阶段使用物资：校验限制后分派至医疗、镇痛或普通消耗流程。"""
        self._require_no_pending_choice()
        if self.state.flow.phase != "action":
            raise RuleViolation(TEXT["systems.item_system.use_item.1"])
        if item_id not in ITEMS:
            raise RuleViolation(TEXT["systems.item_system.use_item.2"])
        source = self._require_home_tenant(source_tenant) if source_tenant else None
        inventory = source.inventory if source is not None else self.state.house.inventory
        if inventory.count(item_id) <= 0:
            raise RuleViolation(TEXT["systems.item_system.use_item.3"])
        item = ITEMS[item_id]
        spot = None
        if slot is not None:
            spot = inventory.at_plot(int(slot))
            if spot is None or spot.item_id != item_id:
                raise RuleViolation(TEXT["systems.item_system.use_item.4"])
        from weiren_game.data.items import (
            item_is_carried_only,
            item_is_house_object,
            item_requires_equip,
        )

        if item_requires_equip(item_id):
            raise RuleViolation(TEXT["systems.item_system.use_item.5"])
        if item_is_house_object(item_id):
            raise RuleViolation(TEXT["systems.item_system.use_item.6"])
        if item_is_carried_only(item_id):
            raise RuleViolation(TEXT["systems.item_system.use_item.7"])
        from weiren_game.data.items import item_gain_info_spec

        if item_gain_info_spec(item_id) is not None and not item_gain_info_spec(
            item_id
        ).get("keep"):
            # These normally auto-convert, but this also handles migrated/debug saves.
            self._take_item(item_id, inventory, spot=spot)
            self._gain_item(item_id)
            return
        # 物资只能作用于屋内的房客；无目标物品（target_mode≠tenant）可省略对象。
        if item.target_mode == "tenant":
            if tenant_id is None:
                raise RuleViolation(TEXT["systems.item_system.use_item.8"])
            tenant = self._require_home_tenant(tenant_id)
        else:
            tenant = (
                self._require_home_tenant(tenant_id)
                if tenant_id is not None
                else None
            )

        if tenant is not None:
            from weiren_game.data import NODE_HOOKS

            for hook in NODE_HOOKS.get("item.use_wasted", ()):
                if hook(self, tenant, item_id, item, inventory, spot):
                    return

        if tenant is None:
            effect = ITEM_EFFECTS.get(item.on_use or "")
            if effect is None:
                raise RuleViolation(TEXT["systems.item_system.use_item.9"])
            effect(self, None, item)
            self._spend_item_use(item.item_id, item, None, inventory=inventory, spot=spot)
        else:
            # 有 tag 行为就用它（医药/镇痛等），否则走通用 on_use 消耗品。
            tag_use = self._item_tag_fn(item, "use")
            if tag_use is not None:
                tag_use(self, item, tenant, inventory, spot, condition=condition)
            else:
                self._use_general_item(item, tenant, inventory=inventory, spot=spot)
        self.state.round.item_uses_this_turn += 1
        self._record_action("item", item=item_id, tenant=tenant.id, condition=condition)

    def _spend_item_use(
        self,
        item_id: str,
        item: ItemDefinition,
        tenant: Tenant | None = None,
        cost: int | None = None,
        *,
        inventory=None,
        spot=None,
    ) -> None:
        """按耐久、消耗品或易损规则结算一次物品使用代价。"""
        if item.durable:
            self._consume_durability(
                item_id, cost if cost is not None else item.use_cost,
                tenant=tenant, inventory=inventory, spot=spot,
            )
        elif item.consumable:
            self._take_item(item_id, inventory, spot=spot)
        elif item.fragile_chance:
            chance = self._fragile_chance(item.fragile_chance, tenant)
            if self._rng(EVENT_IDS["item.fragile"], item_id).random() < chance:
                self._take_item(item_id, inventory, spot=spot)

    def _use_general_item(
        self, item: ItemDefinition, tenant: Tenant, *, inventory=None, spot=None
    ) -> None:
        """经 on_use 效果注册表执行普通消耗品效果，并结算使用代价与该角色加成。"""
        effect = ITEM_EFFECTS.get(item.on_use or "")
        if effect is None:
            raise RuleViolation(TEXT["systems.item_system._use_general_item.1"])
        effect(self, tenant, item)
        self._spend_item_use(item.item_id, item, tenant, inventory=inventory, spot=spot)
        after_food = self._item_tag_fn(item, "after_food")
        if after_food is not None:
            after_food(self, tenant, item)
        self._log(TEXT["systems.item_system._use_general_item.2"].format(p1=self.character(tenant).name, p2=item.name))

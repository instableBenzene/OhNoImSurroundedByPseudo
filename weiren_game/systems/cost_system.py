"""CostSystem：技能“前置代价”的统一结算层。

技能结构采用 cost→effect 成对声明（见 data.types.Branch / Term）：
- Term.side="cost"：前置代价，由本层统一侦测与支付；
- Term.side="effect"：技能效果，不由本层支付，交给效果/角色模块结算；
- optional / maximum 为修饰词（可选、至多），强制发动时可选变必选、
  “至多/最大”取最大档；
- Branch.forced_terms（可选）：被强制发动时整体取代该分支 cost 侧；
- 未声明 forced_terms 时，由本层套用公共的“强制替代代价”（被强制方支付
  10 生命 + 10 理智，payer=actor），无需每个技能重复书写混·权限转让的
  特殊分支。
"""

from __future__ import annotations

from weiren_game.exceptions import RuleViolation
from weiren_game.data.types import Term
from weiren_game.data.lang import TEXT


_DEFAULT_FORCED_COST_TERMS: tuple[Term, ...] = (
    Term(side="cost", resource="health", amount=10, payer="actor"),
    Term(side="cost", resource="sanity", amount=10, payer="actor"),
)


class CostSystemMixin:
    def _forced_cost_terms(self, branch: object) -> list[object]:
        """被强制发动时的 cost 条目：优先技能自带 forced_terms，否则用公共默认。"""
        own = tuple(getattr(branch, "forced_terms", ()))
        if own:
            return [term for term in own if term.side == "cost"]
        return list(_DEFAULT_FORCED_COST_TERMS)

    # ------------------------------------------------------------ branch select
    def _select_branch(
        self,
        ability: object,
        *,
        option: str | None = None,
        forced: bool = False,
    ) -> object:
        """按 option / 强制标志选择本次使用的 Branch。"""
        branches = tuple(getattr(ability, "branches", ()))
        if forced:
            for branch in branches:
                if branch.max_on_force or (option and branch.option == option):
                    return branch
        if option:
            for branch in branches:
                if branch.option == option:
                    return branch
        if branches:
            return branches[0]
        return _EmptyBranch()

    def _resolve_branch_cost(
        self,
        branch: object,
        *,
        payer: object,
        target: object | None,
        forced: bool,
        include_optional: bool,
    ) -> list[object]:
        """把分支 cost 侧解析成“本次实际要支付”的条目列表。

        支持 cost_expr 的 and/or；无条件时不要求 Term 带 tag（全部按 AND）。
        """
        if forced:
            return self._forced_cost_terms(branch)
        cost_terms = [term for term in branch.terms if term.side == "cost"]
        expr = getattr(branch, "cost_expr", None)
        if expr is None:
            return cost_terms
        tag_map = {
            term.tag: term for term in cost_terms if getattr(term, "tag", "")
        }
        error = self._expr_error(
            expr,
            tag_map,
            payer=payer,
            target=target,
            forced=forced,
            include_optional=include_optional,
        )
        if error:
            raise RuleViolation(error)
        return self._collect_expr(
            expr,
            tag_map,
            payer=payer,
            target=target,
            forced=forced,
            include_optional=include_optional,
        )

    def _expr_error(
        self,
        expr: object,
        tag_map: dict[str, object],
        *,
        payer: object,
        target: object | None,
        forced: bool,
        include_optional: bool,
    ) -> str | None:
        """计算 cost 表达式的首个不可满足错误；or 分支任一满足即通过。"""
        def ref_error(ref: object) -> str | None:
            """单个引用（tag 或嵌套表达式）的错误文案。"""
            if isinstance(ref, str):
                term = tag_map.get(ref)
                if term is None:
                    return TEXT["cost.unknown_tag"].format(ref=ref)
                if term.optional and not (forced or include_optional):
                    return None
                actual = target if term.payer == "target" else payer
                return self._single_term_error(term, actual)
            return self._expr_error(
                ref, tag_map, payer=payer, target=target,
                forced=forced, include_optional=include_optional,
            )

        if expr.op == "or":
            for ref in expr.refs:
                if ref_error(ref) is None:
                    return None
            return TEXT["cost.or_unpayable"]
        for ref in expr.refs:
            error = ref_error(ref)
            if error:
                return error
        return None

    def _collect_expr(
        self,
        expr: object,
        tag_map: dict[str, object],
        *,
        payer: object,
        target: object | None,
        forced: bool,
        include_optional: bool,
    ) -> list[object]:
        """按 and/or 语义挑选本次实际支付的 cost 条目。"""
        collected: list[object] = []
        if expr.op == "or":
            for ref in expr.refs:
                if self._ref_error(
                    ref,
                    tag_map,
                    payer=payer,
                    target=target,
                    forced=forced,
                    include_optional=include_optional,
                ) is None:
                    if isinstance(ref, str):
                        collected.append(tag_map[ref])
                    else:
                        collected.extend(
                            self._collect_expr(
                                ref, tag_map, payer=payer, target=target,
                                forced=forced, include_optional=include_optional,
                            )
                        )
                    break
            return collected
        for ref in expr.refs:
            if isinstance(ref, str):
                term = tag_map[ref]
                if term.optional and not (forced or include_optional):
                    continue
                collected.append(term)
            else:
                sub = self._collect_expr(
                    ref, tag_map, payer=payer, target=target,
                    forced=forced, include_optional=include_optional,
                )
                if sub:
                    collected.extend(sub)
        return collected

    def _ref_error(
        self,
        ref: object,
        tag_map: dict[str, object],
        *,
        payer: object,
        target: object | None,
        forced: bool,
        include_optional: bool,
    ) -> str | None:
        """返回单个表达式引用的不可满足错误（供 or 短路使用）。"""
        if isinstance(ref, str):
            term = tag_map.get(ref)
            if term is None:
                return TEXT["cost.unknown_tag"].format(ref=ref)
            if term.optional and not (forced or include_optional):
                return None
            actual = target if term.payer == "target" else payer
            return self._single_term_error(term, actual)
        return self._expr_error(
            ref, tag_map, payer=payer, target=target,
            forced=forced, include_optional=include_optional,
        )

    def _single_term_error(self, term: object, payer: object) -> str | None:
        """只检查单条 cost Term 是否满足。"""
        amount = self._resolve_amount(term, payer)
        if term.resource == "sanity":
            if payer.sanity < amount:
                return TEXT["cost.sanity_short"].format(amount=amount)
        elif term.resource == "health":
            if payer.health < amount:
                return TEXT["cost.health_short"].format(amount=amount)
        elif term.resource == "mark":
            if self._role_mark_count(payer, term.key) < amount:
                return TEXT["cost.mark_short"].format(key=term.key, amount=amount)
        elif term.resource == "turns":
            if payer.skip_until_turn > self.state.flow.turn:
                return TEXT["cost.turns_forbidden"]
        elif term.resource == "game":
            if payer.turn_counters.get(term.key, 0):
                return TEXT["cost.game_once"].format(key=term.key)
        return None

    # ------------------------------------------------------------------ payable
    def _ability_costs_payable(
        self,
        payer: object,
        costs: list[object],
        *,
        target: object | None = None,
        forced: bool = False,
        include_optional: bool = False,
    ) -> str | None:
        """侦测一组 cost Term：返回第一条无法满足的原因，满足则 None。"""
        for term in costs:
            if term.optional and not (forced or include_optional):
                continue
            actual = target if term.payer == "target" else payer
            amount = self._resolve_amount(term, actual)
            if term.resource == "sanity":
                if actual.sanity < amount:
                    return TEXT["cost.sanity_short"].format(amount=amount)
            elif term.resource == "health":
                if actual.health < amount:
                    return TEXT["cost.health_short"].format(amount=amount)
            elif term.resource == "mark":
                if self._role_mark_count(actual, term.key) < amount:
                    return TEXT["cost.mark_short"].format(key=term.key, amount=amount)
            elif term.resource == "turns":
                if actual.skip_until_turn > self.state.flow.turn:
                    return TEXT["cost.turns_forbidden"]
            elif term.resource == "game":
                if actual.turn_counters.get(term.key, 0):
                    return TEXT["cost.game_once"].format(key=term.key)
        return None

    def _cost_pack_payable(
        self,
        payer: object,
        ability: object,
        *,
        option: str | None = None,
        target: object | None = None,
        forced: bool = False,
        include_optional: bool = False,
    ) -> str | None:
        """按技能分支选择后统一侦测。"""
        branch = self._select_branch(ability, option=option, forced=forced)
        if forced:
            costs = self._forced_cost_terms(branch)
            return self._ability_costs_payable(
                payer,
                costs,
                target=target,
                forced=forced,
                include_optional=include_optional,
            )
        cost_terms = [term for term in branch.terms if term.side == "cost"]
        expr = getattr(branch, "cost_expr", None)
        if expr is None:
            return self._ability_costs_payable(
                payer,
                cost_terms,
                target=target,
                forced=forced,
                include_optional=include_optional,
            )
        tag_map = {
            term.tag: term for term in cost_terms if getattr(term, "tag", "")
        }
        return self._expr_error(
            expr,
            tag_map,
            payer=payer,
            target=target,
            forced=forced,
            include_optional=include_optional,
        )

    # ---------------------------------------------------------------------- pay
    def _pay_ability_costs(
        self,
        payer: object,
        costs: list[object],
        *,
        target: object | None = None,
        forced: bool = False,
        include_optional: bool = False,
    ) -> None:
        """支付一组 cost Term（effect Term 不会出现在本层）。"""
        for term in costs:
            if term.optional and not (forced or include_optional):
                continue
            actual = target if term.payer == "target" else payer
            amount = self._resolve_amount(term, actual)
            if term.resource == "sanity":
                self._consume_sanity(actual, amount, "ability_consume")
            elif term.resource == "health":
                # 前置代价按原值直扣，不经过伤害管线（护甲/倍率只作用于
                # 技能 effect 造成的伤害）。
                actual.health = max(0.0, actual.health - amount)
            elif term.resource == "mark":
                self._consume_mark(actual, term.key, amount)
            elif term.resource == "turns":
                actual.skip_until_turn = max(
                    actual.skip_until_turn, self.state.flow.turn + int(amount)
                )
            elif term.resource == "game":
                actual.turn_counters[term.key] = 1
            else:
                raise RuleViolation(TEXT["cost.unknown_resource"].format(resource=term.resource))

    def _pay_cost_pack(
        self,
        payer: object,
        ability: object,
        *,
        option: str | None = None,
        target: object | None = None,
        forced: bool = False,
        include_optional: bool = False,
    ) -> None:
        """按技能分支选择后统一支付（普通与强制共用）。"""
        branch = self._select_branch(ability, option=option, forced=forced)
        costs = self._resolve_branch_cost(
            branch,
            payer=payer,
            target=target,
            forced=forced,
            include_optional=include_optional,
        )
        self._pay_ability_costs(
            payer,
            costs,
            target=target,
            forced=forced,
            include_optional=include_optional,
        )

    def _resolve_amount(self, term: object, payer: object) -> float:
        """解析数量：amount=None 表示取该资源当前最大可用。"""
        if term.amount is not None:
            return float(term.amount)
        if term.resource == "mark":
            return float(self._role_mark_count(payer, term.key))
        if term.resource == "sanity":
            return float(payer.sanity)
        if term.resource == "health":
            return float(payer.health)
        return 0.0

    def _role_mark_count(self, payer: object, key: str) -> float:
        """读取角色的印记资源：统一取自房客印记池。"""
        return float(self._mark_count(payer, key))

class _EmptyBranch:
    """无分支技能的空默认分支（此时本层什么都不扣）。"""

    def __init__(self) -> None:
        """构造一个无分支技能的空占位分支。"""
        self.option = ""
        self.max_on_force = False
        self.forced_terms = ()
        self.terms = ()

"""修饰器对象（Modifier）与统一计算。

按规格：Modifier 是**对象、不持有实例状态**；是否生效由调用方的条件判定
（游戏已有大量条件机制，满足条件时直接把这些 Modifier 交给本函数即可）。
数值计算严格按下述顺序：

    基础值
    → 普通固定加算
    → 普通百分比加算
    → 普通无限制固定乘算
    → 普通有限制固定乘算（不满足 limit 时转“特殊加算”）
    → 最终固定加算
    → 最终百分比加算
    → 最终无限制固定乘算
    → 最终有限制固定乘算（不满足 limit 时转“特殊加算”）
    → 最终范围限制

公式：
    ((基础值+普通固定加算)×(1+普通百分比加算)×普通无限制固定乘算×普通有限制固定乘算
    + 最终固定加算)
    ×(1+最终百分比加算)×最终无限制固定乘算×最终有限制固定乘算
"""

from __future__ import annotations

from dataclasses import dataclass

# 修饰器可作用的数值域。
EFFECT_TYPES = frozenset({
    "healthComsume", "healthRestore", "healthLoss", "healthDamage",
    "sanityComsume", "sanityRestore", "sanityLoss", "sanityDamage",
})


@dataclass(frozen=True)
class Modifier:
    """一个修饰器对象（定义，无实例）。

    - ``effect_type``：通道（在哪个数值域被收集）；
    - ``path``：它**响应哪些功能**（与事件 ``source`` 做交集匹配）；
    - ``source``：它**自身的出身**（仅作来源追溯/继承，不参与匹配）。
    """

    modifier_id: str
    effect_type: str
    path: tuple[str, ...] = ()
    source: tuple[str, ...] = ()
    # flat=固定值；percent=百分比；max/min=最终范围限制。
    value_type: str = "flat"
    # add=加算；multiply=乘算。
    operation: str = "add"
    # normal=普通；final=最终。
    stage: str = "normal"
    value: float = 0.0
    # 有限制固定乘算的最大/最小变化量；None 表示无限制。
    limit: float | None = None
    # 匹配模式：any=有交集即命中；all=path 必须是 source 的子集。
    match: str = "any"


# 调用点(effect_type) → 修饰器列表（内容侧在归属文件里登记，计算点按此收集）。
MODIFIER_REGISTRY: dict[str, list[Modifier]] = {}


def register_modifier(modifier: Modifier) -> None:
    """登记一个修饰器到其调用点。"""
    if isinstance(modifier, _Spec):
        modifier = modifier.build()
    MODIFIER_REGISTRY.setdefault(modifier.effect_type, []).append(modifier)


def _source_tokens(source: object) -> set[str]:
    if isinstance(source, str):
        return {source} if source else set()
    return set(source)


def _matches(modifier: Modifier, tokens: set[str]) -> bool:
    """修饰器是否命中：不写 path = 全命中；any=有交集，all=子集。"""
    if not modifier.path:
        return True
    required = set(modifier.path)
    if modifier.match == "all":
        return required <= tokens
    return bool(tokens & required)


def modifiers_for(effect_type: str, source: object = ()) -> list[Modifier]:
    """返回订阅该通道、且 ``path ∩ source ≠ ∅`` 的修饰器。

    - ``source``：事件（调用点）携带的 tag 集合；
    - ``Modifier.path``：修饰器声明响应哪些功能；
    - 修饰器不写 path ⇒ 对所有事件生效。
    """
    tokens = _source_tokens(source)
    return [m for m in MODIFIER_REGISTRY.get(effect_type, ()) if _matches(m, tokens)]


def flat_add(
    effect_type: str, value: float, path: tuple[str, ...] = (), modifier_id: str = ""
) -> Modifier:
    """简写：普通固定加算（游戏内最常用之一）。"""
    return Modifier(modifier_id or effect_type, effect_type, path=path,
                    value_type="flat", operation="add", stage="normal", value=value)


def percent_add(
    effect_type: str, value: float, path: tuple[str, ...] = (), modifier_id: str = ""
) -> Modifier:
    """简写：普通百分比加算（游戏内最常用之一）。"""
    return Modifier(modifier_id or effect_type, effect_type, path=path,
                    value_type="percent", operation="add", stage="normal", value=value)


class _Spec:
    """链式构造器：``spec(effect_type).final().percent(...)...``。"""

    def __init__(self, effect_type: str) -> None:
        self._data: dict[str, object] = {
            "modifier_id": effect_type,
            "effect_type": effect_type,
            "path": (),
            "source": (),
            "value_type": "flat",
            "operation": "add",
            "stage": "normal",
            "value": 0.0,
            "limit": None,
            "match": "any",
        }

    # 阶段
    def normal(self) -> "_Spec":
        self._data["stage"] = "normal"
        return self

    def final(self) -> "_Spec":
        self._data["stage"] = "final"
        return self

    # 加算：flat=固定值 / percent=百分比
    def flat(self, value: float) -> "_Spec":
        self._data.update(value_type="flat", operation="add", value=float(value))
        return self

    def percent(self, value: float) -> "_Spec":
        self._data.update(value_type="percent", operation="add", value=float(value))
        return self

    # 乘算：value=乘数（percent 语义）；limit 给定时为“有限制固定乘算”
    def mul(self, value: float, limit: float | None = None) -> "_Spec":
        self._data.update(
            value_type="percent", operation="multiply",
            value=float(value), limit=limit,
        )
        return self

    # 最终范围限制
    def max(self, value: float) -> "_Spec":
        self._data.update(value_type="max", operation="", value=float(value))
        return self

    def min(self, value: float) -> "_Spec":
        self._data.update(value_type="min", operation="", value=float(value))
        return self

    # 必定修饰：直接把结果锁定为 0 / 1
    def certain(self, value: float) -> "_Spec":
        self._data.update(value_type="certain", operation="", value=float(value))
        return self

    # 响应哪些功能（与事件 source 匹配）
    def path(self, *tags: str) -> "_Spec":
        self._data["path"] = tuple(tags)
        return self

    # 自身出身（仅记录/继承）
    def source(self, *tags: str) -> "_Spec":
        self._data["source"] = tuple(tags)
        return self

    def id(self, modifier_id: str) -> "_Spec":
        self._data["modifier_id"] = modifier_id
        return self

    def match(self, mode: str) -> "_Spec":
        self._data["match"] = mode
        return self

    def build(self) -> Modifier:
        return Modifier(**self._data)  # type: ignore[arg-type]


def spec(effect_type: str = "") -> _Spec:
    """开始链式声明一个修饰器。"""
    return _Spec(effect_type)


# 条件式修饰器提供者：effect_type -> [provider(context) -> Iterable[Modifier]]
# 内容侧在自己归属处注册；调用点用 collect_modifiers 一并收集。
MODIFIER_PROVIDERS: dict[str, list[object]] = {}


def register_modifier_provider(effect_type: str, provider: object) -> None:
    """登记一个“条件满足时返回修饰器”的提供者。"""
    MODIFIER_PROVIDERS.setdefault(effect_type, []).append(provider)


def collect_modifiers(
    effect_type: str, source: object = (), context: object = None
) -> list[Modifier]:
    """收集某调用点当前应生效的全部修饰器（静态 + 条件式 provider）。"""
    result = list(modifiers_for(effect_type, source))
    tokens = _source_tokens(source)
    for provider in MODIFIER_PROVIDERS.get(effect_type, ()):
        produced = provider(context)  # type: ignore[operator]
        if not produced:
            continue
        for modifier in produced:
            if isinstance(modifier, _Spec):
                modifier = modifier.build()
            if _matches(modifier, tokens):
                result.append(modifier)
    return result


def _signed_limit(limit: float, change: float) -> float:
    """把 limit 归一到与变化量同号的方向。"""
    magnitude = abs(limit)
    if change < 0:
        magnitude = -magnitude
    return magnitude


def _within_limit(change: float, limit: float) -> bool:
    """该修饰器自身产生的变化量是否落在 limit 允许范围内。"""
    return abs(change) <= abs(limit)


def calculate_modified_amount(base: float, modifiers: object) -> float:
    """按规格顺序编译一组（已判定生效的）修饰器，返回最终数值。"""
    items = list(modifiers)
    # 必定修饰：只有一个方向时直接输出 0/1（冲突则忽略，进入计算）。
    forced = {
        1.0 if m.value >= 0.5 else 0.0
        for m in items
        if m.value_type == "certain"
    }
    if len(forced) == 1:
        return forced.pop()
    normal = [m for m in items if m.stage == "normal"]
    final = [m for m in items if m.stage == "final"]

    # 普通固定加算 / 普通百分比加算
    normal_flat = sum(
        m.value for m in normal
        if m.value_type == "flat" and m.operation == "add"
    )
    normal_percent = sum(
        m.value for m in normal
        if m.value_type == "percent" and m.operation == "add"
    )
    pre_normal_mul = (base + normal_flat) * (1 + normal_percent)
    amount = pre_normal_mul

    # 普通无限制固定乘算
    for modifier in normal:
        if (
            modifier.operation == "multiply"
            and modifier.value_type == "percent"
            and modifier.limit is None
        ):
            amount *= modifier.value

    # 普通有限制固定乘算：不满足 limit 则转为特殊加算（位于此后、最终固定加算之前）。
    special_normal = 0.0
    for modifier in normal:
        if modifier.operation != "multiply" or modifier.limit is None:
            continue
        change = pre_normal_mul * (modifier.value - 1)
        if _within_limit(change, modifier.limit):
            amount *= modifier.value
        else:
            special_normal += _signed_limit(modifier.limit, change)
    amount += special_normal

    # 最终固定加算 / 最终百分比加算
    final_flat = sum(
        m.value for m in final
        if m.value_type == "flat" and m.operation == "add"
    )
    final_percent = sum(
        m.value for m in final
        if m.value_type == "percent" and m.operation == "add"
    )
    amount += final_flat
    pre_final_mul = amount * (1 + final_percent)
    amount = pre_final_mul

    # 最终无限制固定乘算
    for modifier in final:
        if (
            modifier.operation == "multiply"
            and modifier.value_type == "percent"
            and modifier.limit is None
        ):
            amount *= modifier.value

    # 最终有限制固定乘算：不满足 limit 则转为特殊加算（位于此乘算之后）。
    special_final = 0.0
    for modifier in final:
        if modifier.operation != "multiply" or modifier.limit is None:
            continue
        change = pre_final_mul * (modifier.value - 1)
        if _within_limit(change, modifier.limit):
            amount *= modifier.value
        else:
            special_final += _signed_limit(modifier.limit, change)
    amount += special_final

    # 最终范围限制：对全部 Modifier 计算完的“总变化量”做最终收敛
    # （类似概率最后夹到 5~95）。
    for modifier in final:
        if modifier.value_type == "max":
            amount = min(amount, modifier.value)
        elif modifier.value_type == "min":
            amount = max(amount, modifier.value)
    return amount


# ===========================================================================
# 布尔闸门（Gate）：与「通道 channel」共用 path/source 匹配，只换聚合器。
# 约定见 docs/ARCH.md：闸门是**纯查询**——本模块不掷骰、不写状态。
# ===========================================================================


@dataclass(frozen=True)
class Gate:
    """一个布尔闸门的贡献项（定义，无实例）。

    - ``gate_type``：闸门键（在哪个闸门被收集）；
    - ``path``：它**响应哪些功能**（与调用点 source 做交集/子集匹配）；
    - ``source``：它**自身的出身**（仅追溯，不参与匹配）；
    - ``value``：本次贡献的真值；
    - ``operation``：``any``=把闸门结果抬为真（OR）；``veto``=把结果压为假（NOT）。
    """

    gate_id: str
    gate_type: str
    path: tuple[str, ...] = ()
    source: tuple[str, ...] = ()
    value: bool = True
    operation: str = "any"
    match: str = "any"


GATE_REGISTRY: dict[str, list[Gate]] = {}
GATE_PROVIDERS: dict[str, list[object]] = {}


def register_gate(gate_item: object) -> None:
    """登记一个闸门贡献项到其闸门键。"""
    if isinstance(gate_item, _GateSpec):
        gate_item = gate_item.build()
    GATE_REGISTRY.setdefault(gate_item.gate_type, []).append(gate_item)  # type: ignore[attr-defined]


def register_gate_provider(gate_type: str, provider: object) -> None:
    """登记一个「条件满足时返回闸门贡献」的提供者。"""
    GATE_PROVIDERS.setdefault(gate_type, []).append(provider)


def gates_for(gate_type: str, source: object = ()) -> list[Gate]:
    """返回订阅该闸门、且 ``path`` 命中调用点 ``source`` 的静态贡献项。"""
    tokens = _source_tokens(source)
    return [g for g in GATE_REGISTRY.get(gate_type, ()) if _matches(g, tokens)]  # type: ignore[arg-type]


def collect_gates(
    gate_type: str, source: object = (), context: object = None
) -> list[Gate]:
    """收集某闸门当前应生效的全部贡献项（静态 + 条件式 provider）。"""
    result = list(gates_for(gate_type, source))
    tokens = _source_tokens(source)
    for provider in GATE_PROVIDERS.get(gate_type, ()):
        produced = provider(context)  # type: ignore[operator]
        if not produced:
            continue
        for gate_item in produced:
            if isinstance(gate_item, _GateSpec):
                gate_item = gate_item.build()
            if _matches(gate_item, tokens):
                result.append(gate_item)
    return result


def evaluate_gate(base: bool, gates: object) -> bool:
    """逻辑聚合：``any`` 抬为真（OR）、``veto`` 压为假（NOT）。

    语义固定为「先 OR 后否决」——`veto` 无论出现顺序都最终压为假，避免顺序依赖。
    """
    result = bool(base)
    for gate_item in gates:  # type: ignore[union-attr]
        if not gate_item.value:
            continue
        if gate_item.operation == "veto":
            result = False
        else:
            result = True
    return result


class _GateSpec:
    """链式构造器：``gate(gate_type).path(...).match(...).any()/veto()``。"""

    def __init__(self, gate_type: str) -> None:
        self._data: dict[str, object] = {
            "gate_id": gate_type,
            "gate_type": gate_type,
            "path": (),
            "source": (),
            "value": True,
            "operation": "any",
            "match": "any",
        }

    def path(self, *tags: str) -> "_GateSpec":
        self._data["path"] = tuple(tags)
        return self

    def source(self, *tags: str) -> "_GateSpec":
        self._data["source"] = tuple(tags)
        return self

    def match(self, mode: str) -> "_GateSpec":
        self._data["match"] = mode
        return self

    def any(self, value: bool = True) -> "_GateSpec":
        """命中即把闸门抬为真（OR）。"""
        self._data.update(operation="any", value=bool(value))
        return self

    def veto(self, value: bool = True) -> "_GateSpec":
        """命中即把闸门压为假（NOT / 否决）。"""
        self._data.update(operation="veto", value=bool(value))
        return self

    def id(self, gate_id: str) -> "_GateSpec":
        self._data["gate_id"] = gate_id
        return self

    def build(self) -> Gate:
        return Gate(**self._data)  # type: ignore[arg-type]


def gate(gate_type: str = "") -> _GateSpec:
    """开始链式声明一个布尔闸门贡献项。"""
    return _GateSpec(gate_type)


__all__ = [
    "EFFECT_TYPES",
    "GATE_PROVIDERS",
    "GATE_REGISTRY",
    "Gate",
    "MODIFIER_REGISTRY",
    "MODIFIER_PROVIDERS",
    "Modifier",
    "calculate_modified_amount",
    "collect_gates",
    "collect_modifiers",
    "evaluate_gate",
    "flat_add",
    "gate",
    "gates_for",
    "modifiers_for",
    "percent_add",
    "register_gate",
    "register_gate_provider",
    "register_modifier_provider",
    "register_modifier",
    "spec",
]

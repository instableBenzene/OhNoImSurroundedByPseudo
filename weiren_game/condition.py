"""统一的状态模型。

每个 ``Condition`` 表示一种生理、心理或临时状态（创伤、紊乱、休克、
侵蚀/觉醒/稀有情绪、时效增益与减益）。定义集中承载原先散落在各处状态
属性中的字段：类别、上限、情绪稀有度以及 UI 的 ``shown`` 显示规则。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from weiren_game.effects.health_sanity import decay_high_health_immunity


StatusCategory = Literal["physical", "mental", "other"]
EmotionKind = Literal["erosion", "awakening"]
Rarity = Literal["common", "rare"]


@dataclass(frozen=True)
class StatusDefinition:
    """一种状态的静态描述。"""

    id: str
    label: str
    category: StatusCategory
    # 风味描述（面向屋主的“这是什么感觉”，与机制无关）。
    description: str = ""
    intensity_max: int = 10
    layers_max: int = 99
    # UI presentation: an effect may hide its intensity, its layers or the
    # icon itself.  Buffs/debuffs without an intensity default to intensity 1.
    shown: frozenset[str] = frozenset({"icon", "intensity", "layers", "description"})
    # 产生该状态的对象（item:mcdangdang / ability:xxx / effects:health_sanity），
    # 效果实现与“在哪个节点被调用”的定义与该对象紧贴。
    source_id: str | None = None
    nodes: frozenset[str] = frozenset()
    # False：该状态的衰减/移除由自身 hook 管理（如鼓舞每次 -1 层），
    # 不会被通用回合末状态衰减重复处理。
    auto_decay: bool = True
    # True：参与通用回合末衰减，但立即把层数刷回 layers_max（永续效果）。
    permanent: bool = False
    # 该状态在自己节点触发时的具体效果函数（由产生它的对象就近注册）。
    hook: object | None = None
    # 该状态生效时会禁用哪些情绪（配合 hook 判定），由状态自身声明。
    blocked_emotions: tuple[str, ...] = ()
    # 该状态生效时会压制哪些“状态的额外效果”（配合 hook 判定）。
    suppresses_conditions: tuple[str, ...] = ()
    # 状态 chip 的显示参数（由内容声明；缺省用通用图标/无配色）。
    chip_icon: str = ""
    chip_css: str = ""
    # True：不把这个状态放进房客卡的状态栏（内容改用详情页的小面板等地方展示，
    # 例：薯条的「人设-*」只在头像右侧的面板里出现）。
    chip_hidden: bool = False

    def show(self, field: str) -> bool:
        """返回指定字段是否在 UI 上显示。"""
        return field in self.shown


@dataclass(frozen=True)
class EmotionDefinition(StatusDefinition):
    """情绪状态，归属侵蚀或觉醒族且可能为稀有。

    稀有情绪并非第三种存储桶，只是普通族成员、被选中的概率更低。
    """

    kind: EmotionKind = "erosion"
    rarity: Rarity = "common"

    @property
    def is_rare(self) -> bool:
        """该情绪是否为稀有情绪。"""
        return self.rarity == "rare"


STATUS_DEFINITIONS: dict[str, StatusDefinition] = {
    "trauma": StatusDefinition(
        "trauma", "创伤", "physical",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        chip_icon="i-trauma", chip_css="warn",
        description="皮肉之下留下了难以消退的痛楚，连呼吸都牵着伤口。",
    ),
    "disorder": StatusDefinition(
        "disorder", "紊乱", "physical",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        chip_icon="i-disorder", chip_css="info",
        description="内科的毛病缠上身，忽冷忽热、时好时坏，把人的精神一点点磨掉。",
    ),
    "shock": StatusDefinition(
        "shock", "休克", "physical", intensity_max=4,
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        chip_icon="i-shock", chip_css="danger",
        description="生命体征正在崩塌边缘，意识一点点滑向黑暗。",
    ),
    # 回合到期型临时修饰（原 TenantState.buffs 的第一类）：
    # 强度默认为 1，层数表示剩余持续回合。
    "fiji_afterglow": StatusDefinition(
        "fiji_afterglow", "高级巧克力的余韵", "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="item:fiji_chocolate",
        nodes=frozenset({"turn_start.depression_effect"}),
        description="甜味已经化开，心里却还留着一小块被安抚过的暖意。",
    ),
    # 澪叁贰玖机制型状态（第二类）。
    "vigilant_pseudo_zero329": StatusDefinition(
        "vigilant_pseudo_zero329", "警惕伪人-澪叁贰玖", "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="passive:zero329",
        description="把每一个“同伴”都当成可能的假货，反复核对。",
    ),
    "information_gathering_zero329": StatusDefinition(
        "information_gathering_zero329", "情报搜集-澪叁贰玖", "other",
        shown=frozenset({"icon", "intensity", "layers", "description"}),
        source_id="ability:information_collect@zero329",
        description="不动声色地把零碎线索一条条收进本子。",
    ),
    "high_health_immunity": StatusDefinition(
        "high_health_immunity", "高生命免疫", "other", intensity_max=99,
        shown=frozenset({"icon", "description"}),
        source_id="effects:health_sanity",
        nodes=frozenset({"turn_end.status_effects"}),
        auto_decay=False,
        hook=decay_high_health_immunity,
        description="身体状态尚可，还能替自己挡下一次新的伤口。",
    ),
}


def register_status_definition(definition: StatusDefinition) -> None:
    """注册一个由内容对象携带的状态定义（覆盖同 id 旧定义）。"""
    STATUS_DEFINITIONS[definition.id] = definition


EMOTION_DEFINITIONS: dict[str, EmotionDefinition] = {
    # 侵蚀情绪集（常见）
    "boredom": EmotionDefinition("boredom", "无聊", "mental", kind="erosion",
        description="什么都没意思，时间变得又长又钝。"),
    "irritation": EmotionDefinition("irritation", "烦躁", "mental", kind="erosion",
        description="一点小事就能点着，耐性薄得像纸。"),
    "anxiety": EmotionDefinition("anxiety", "焦虑", "mental", kind="erosion",
        description="心口发紧，总觉得坏事就在下一刻。"),
    "melancholy": EmotionDefinition("melancholy", "忧郁", "mental", kind="erosion",
        description="低落像潮水漫上来，连抬手都嫌费力。"),
    "panic": EmotionDefinition("panic", "恐慌", "mental", kind="erosion",
        description="恐惧接管了身体，只想逃，却无处可逃。"),
    # 觉醒情绪集（常见）
    "satisfaction": EmotionDefinition("satisfaction", "满足", "mental", kind="awakening",
        description="够好了——暂时不必再要求更多。"),
    "focus": EmotionDefinition("focus", "专注", "mental", kind="awakening",
        description="世界安静下来，只剩下手头这一件事。"),
    "trust": EmotionDefinition("trust", "信任", "mental", kind="awakening",
        description="愿意把后背交给身边的人。"),
    "excitement": EmotionDefinition("excitement", "兴奋", "mental", kind="awakening",
        description="心跳加快，什么都想立刻去做。"),
    "happiness": EmotionDefinition("happiness", "快乐", "mental", kind="awakening",
        description="难得的轻松，嘴角不由自主地翘起来。"),
    # 少见情绪：仍然归属侵蚀/觉醒两族，只是出现概率低。
    "reason": EmotionDefinition("reason", "理智", "mental", kind="awakening", rarity="rare",
        description="在疯涨的情绪里，保住一条清醒的缝隙。"),
    "madness": EmotionDefinition("madness", "癫狂", "mental", kind="erosion", rarity="rare",
        description="理智的堤坝出现裂口，某些声音开始说话。"),
}


# 情绪键集合（列表：内容层注册新情绪后，既有模块级绑定同样可见）。
ALL_EMOTIONS: list[str] = list(EMOTION_DEFINITIONS)
EROSION_EMOTIONS: list[str] = [
    key for key, value in EMOTION_DEFINITIONS.items() if value.kind == "erosion"
]
AWAKENING_EMOTIONS: list[str] = [
    key for key, value in EMOTION_DEFINITIONS.items() if value.kind == "awakening"
]


def _register_reveal_event(emotion_key: str) -> None:
    """为一种情绪登记「情绪显现」**全局事件**定义。

    显现是**世界级**状态（该情绪对所有房客可见若干回合），由信息结算写入事件实例；
    不再是黏在某名房客身上的 condition。
    """
    from .global_event import GlobalEventDefinition, emotion_reveal_event, register_global_event

    label = EMOTION_DEFINITIONS[emotion_key].label
    register_global_event(
        GlobalEventDefinition(
            id=emotion_reveal_event(emotion_key),
            label=f"情绪显现（{label}）",
            icon="i-emotion",
            description=f"{label}被看穿了，短时间内藏不住。",
        )
    )


for _emotion_key in ALL_EMOTIONS:
    _register_reveal_event(_emotion_key)


def register_emotion_definition(definition: EmotionDefinition) -> None:
    """注册一种情绪（覆盖同 id 旧定义），并同步键集合、显现标记与 data 层标签表。"""
    EMOTION_DEFINITIONS[definition.id] = definition
    if definition.id not in ALL_EMOTIONS:
        ALL_EMOTIONS.append(definition.id)
    bucket = EROSION_EMOTIONS if definition.kind == "erosion" else AWAKENING_EMOTIONS
    if definition.id not in bucket:
        bucket.append(definition.id)
    _register_reveal_event(definition.id)
    # data 层把情绪按「稀有/侵蚀/觉醒」维护成中文名表，供系统与界面取用。
    from weiren_game import data as _data  # 延迟导入：condition 先于 data 完成导入

    if definition.rarity == "rare":
        _data.RARE_EMOTIONS[definition.id] = definition.label
    elif definition.kind == "erosion":
        _data.EROSION_EMOTIONS[definition.id] = definition.label
    else:
        _data.AWAKENING_EMOTIONS[definition.id] = definition.label


@dataclass
class Condition:
    """单个状态实例：强度（严重度）与层数（持续）的组合，0/0 表示未激活。"""

    intensity: int = 0
    layers: int = 0

    def __post_init__(self) -> None:
        """初始化时立即钳制强度与层数。"""
        self.clamp()

    @property
    def active(self) -> bool:
        """是否处于激活状态（强度与层数均大于 0）。"""
        return self.intensity > 0 and self.layers > 0

    def clamp(
        self,
        *,
        intensity_max: int = 10,
        layers_max: int = 99,
    ) -> None:
        """将强度与层数钳制在 0 到上限之间，任一为 0 则一并归零。"""
        self.intensity = max(0, min(intensity_max, int(self.intensity)))
        self.layers = max(0, min(layers_max, int(self.layers)))
        if not self.intensity or not self.layers:
            self.intensity = self.layers = 0

    def clear(self) -> None:
        """将强度与层数清零，使状态转为未激活。"""
        self.intensity = self.layers = 0

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "Condition":
        """从字典还原 Condition 实例。"""
        return cls(**raw)

    def to_dict(self) -> dict[str, int]:
        """序列化为普通字典。"""
        return {"intensity": self.intensity, "layers": self.layers}

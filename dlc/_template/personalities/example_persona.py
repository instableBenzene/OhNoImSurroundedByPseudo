"""示例性格：文件名 `example_persona` 即性格键（改名为你要的键）。"""
from weiren_game.data.lang import pack_text_from_file
TEXT = pack_text_from_file(__file__)

# 界面显示的中文名（必填；缺省回退为键名）。
LABEL = TEXT["dlc._template.personalities.example_persona.LABEL"]

# 羁绊档位阈值；达到即激活该档。也可改用 TIER_AT / ACTIVE_TIERS 自定义。
TIERS = (2, 5, 8)

# 可选：取整规则（默认向下取整）。
# ROUND_UP = True


def my_hook(engine, **kwargs):
    """节点/被动钩子：签名按挂载的节点约定。"""
    return None


# HOOKS = {"turn_start.bond_effects": my_hook}
# 单值 hook：HEALTH_PROTECTION / END_SANITY_COST / BOND_END_HEALTH /
#           AWAKENING_MULTIPLIER / EMOTION_CHANGE_MULTIPLIER
# 增减益走修饰器：在模块导入时 register_modifier_provider(...)（见内置性格模块）。
# 该表已纳入 base 快照：装载/卸载随包回滚、重复「应用」不累积，**不需要**自己写去重。

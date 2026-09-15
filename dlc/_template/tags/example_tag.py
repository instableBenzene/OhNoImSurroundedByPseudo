"""示例 tag 行为模块：文件名即 tag（与同名 .json 条目配合使用）。"""


def after_use(engine, *args, **kwargs):
    """按 TAG_BEHAVIORS 的节点约定实现；不需要的节点可以不写。"""
    return None

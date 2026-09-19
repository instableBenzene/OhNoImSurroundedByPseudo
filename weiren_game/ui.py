"""界面适配层：把引擎里的交互（选项/确认/选目标）与具体前端解耦。

引擎与内容只调用 ``engine.ui`` 上的方法；命令行（``cli``）与图形界面（``gui``）
各自提供实现，因而同一套动作流程可被两种前端复用。
"""

from __future__ import annotations
from weiren_game.data.lang import TEXT


def _pairs(options):
    """把 ``[value, ...]`` 或 ``[(value, label), ...]`` 规范成 ``[(value, label)]``。"""
    out = []
    for option in options:
        # 允许 ``(value, label, icon, desc)`` —— 第 3、4 项只给界面用（图标/说明）。
        if isinstance(option, tuple) and len(option) >= 2:
            out.append((option[0], str(option[1])))
        else:
            out.append((option, str(option)))
    return out


class UserInterface:
    """前端需要实现的交互接口。"""

    def message(self, text: str) -> None:
        """显示一条信息（可为纯文本）。"""

    def choose(self, prompt: str, options, *, allow_blank: bool = False):
        """从 options 中选择一项，返回其 value；allow_blank 时空输入返回 None。"""
        raise NotImplementedError

    def confirm(self, prompt: str) -> bool:
        """是/否确认。"""
        raise NotImplementedError

    def choose_target(self, engine, exclude=None):
        """选择一名屋内房客，返回实例 id；无目标返回 None。"""
        ids = [t.id for t in engine.home_tenants() if t.id != exclude]
        if not ids:
            return None
        options = [
            (i, f"{i} {engine.character(engine.state.house.tenants[i]).name}") for i in ids
        ]
        return self.choose(TEXT["ui.choose_target.1"], options)


class CliUI(UserInterface):
    """命令行实现：读取标准输入。"""

    def message(self, text: str) -> None:
        print(text)

    def choose(self, prompt: str, options, *, allow_blank: bool = False):
        pairs = _pairs(options)
        for index, (_value, label) in enumerate(pairs, 1):
            print(f"  {index}. {label}")
        while True:
            raw = input(prompt).strip()
            if not raw and allow_blank:
                return None
            for value, _label in pairs:
                if raw == str(value):
                    return value
            if raw.isdigit() and 1 <= int(raw) <= len(pairs):
                return pairs[int(raw) - 1][0]
            print(TEXT["ui.choose.1"])

    def confirm(self, prompt: str) -> bool:
        return input(prompt).strip().lower() in {"1", "y", "yes", TEXT["ui.confirm.1"], TEXT["ui.confirm.2"]}


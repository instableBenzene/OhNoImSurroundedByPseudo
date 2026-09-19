"""带完整日志记录的确定性随机源。"""

from __future__ import annotations

import random
from typing import Callable
from weiren_game.data.lang import TEXT


class LoggedRandom(random.Random):
    """在 random.Random 之上把每次抽取写入完整对局日志。

    random()/uniform()/choice()/randint()/shuffle()/sample() 等最终都会经过
    random() 或 _randbelow()，因此只需要在这两个方法里留痕即可覆盖全部调用。
    """

    def __init__(
        self,
        seed: object,
        label: str,
        logger: Callable[[str], None],
    ) -> None:
        super().__init__(seed)
        self._label = label
        self._logger = logger
        self._sequence = 0

    def _note(self, kind: str, value: object) -> None:
        self._sequence += 1
        self._logger(
            TEXT["random_log._note.1"].format(p1=self._label, p2=self._sequence, p3=kind, p4=value)
        )

    def random(self) -> float:
        value = super().random()
        # 保留原始留痕；返回带比较日志的包装值，使 roll<阈值 等判定
        # 自动记录大小关系与“生效/不生效”。
        self._note("roll", round(value, 6))
        return _LoggedFloat(value, self._label, self._sequence, self._logger)

    def _randbelow(self, n: int) -> int:
        value = super()._randbelow(n)
        self._note(f"randbelow({n})", value)
        return value


class _LoggedFloat(float):
    """浮点子类：参与比较时写出“骰点 关系 阈值 → 生效/不生效”。"""

    def __new__(
        cls,
        value: float,
        label: str,
        sequence: int,
        logger: Callable[[str], None],
    ) -> "_LoggedFloat":
        instance = super().__new__(cls, value)
        instance._roll_label = f"{label} #{sequence + 1}"
        instance._roll_value = round(value, 6)
        instance._logger = logger
        return instance

    def _judge(self, symbol: str, other: object, result: bool) -> bool:
        self._logger(
            TEXT["random_log._judge.1"].format(p1=self._roll_label, p2=self._roll_value, p3=symbol, p4=other, p5='生效' if result else '不生效')
        )
        return result

    def __reduce__(self) -> tuple[object, tuple[float]]:
        """序列化/复制时还原为普通 float，避免被当作包装对象传递。"""
        return (float, (float(self),))

    def __lt__(self, other: object) -> bool:
        return self._judge("<", other, float.__lt__(self, other))

    def __le__(self, other: object) -> bool:
        return self._judge("<=", other, float.__le__(self, other))

    def __gt__(self, other: object) -> bool:
        return self._judge(">", other, float.__gt__(self, other))

    def __ge__(self, other: object) -> bool:
        return self._judge(">=", other, float.__ge__(self, other))

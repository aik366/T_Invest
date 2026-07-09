from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple


class EMAValue(NamedTuple):
    """Значение экспоненциальной скользящей средней."""

    value: Decimal
    index: int


class EMA:
    """Экспоненциальная скользящая средняя (Exponential Moving Average).

    EMA = price * k + EMA_prev * (1 - k)
    где k = 2 / (period + 1)
    """

    def __init__(self, period: int = 14) -> None:
        if period < 1:
            msg = "Period must be >= 1"
            raise ValueError(msg)
        self._period = period
        self._k = Decimal("2") / Decimal(str(period + 1))

    @property
    def period(self) -> int:
        return self._period

    def calculate(self, prices: Sequence[Decimal]) -> list[EMAValue]:
        """Рассчитать EMA для последовательности цен."""
        if len(prices) < self._period:
            return []

        result: list[EMAValue] = []

        first_window = prices[: self._period]
        sma = sum(first_window, Decimal("0")) / Decimal(str(self._period))
        result.append(EMAValue(value=sma, index=self._period - 1))

        for i in range(self._period, len(prices)):
            ema = prices[i] * self._k + result[-1].value * (
                Decimal("1") - self._k
            )
            result.append(EMAValue(value=ema, index=i))

        return result

    def __call__(self, prices: Sequence[Decimal]) -> list[EMAValue]:
        return self.calculate(prices)

    def __str__(self) -> str:
        return f"EMA({self._period})"

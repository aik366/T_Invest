from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple


class SMAValue(NamedTuple):
    """Значение простой скользящей средней."""

    value: Decimal
    index: int


class SMA:
    """Простая скользящая средняя (Simple Moving Average).

    SMA = (sum(prices) / period)
    """

    def __init__(self, period: int = 14) -> None:
        if period < 1:
            msg = "Period must be >= 1"
            raise ValueError(msg)
        self._period = period

    @property
    def period(self) -> int:
        return self._period

    def calculate(self, prices: Sequence[Decimal]) -> list[SMAValue]:
        """Рассчитать SMA для последовательности цен."""
        if len(prices) < self._period:
            return []

        result: list[SMAValue] = []
        for i in range(self._period, len(prices) + 1):
            window = prices[i - self._period : i]
            avg = sum(window, Decimal("0")) / Decimal(str(self._period))
            result.append(SMAValue(value=avg, index=i - 1))
        return result

    def __call__(self, prices: Sequence[Decimal]) -> list[SMAValue]:
        return self.calculate(prices)

    def __str__(self) -> str:
        return f"SMA({self._period})"

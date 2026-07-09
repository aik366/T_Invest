from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple

from invest_sdk.indicators.sma import SMA


class BollingerValue(NamedTuple):
    """Значение полос Боллинджера."""

    middle: Decimal
    upper: Decimal
    lower: Decimal
    index: int


class BollingerBands:
    """Полосы Боллинджера (Bollinger Bands).

    Middle = SMA(period)
    Upper = Middle + k * StdDev
    Lower = Middle - k * StdDev
    """

    def __init__(self, period: int = 20, std_multiplier: Decimal = Decimal("2")) -> None:
        if period < 1:
            msg = "Period must be >= 1"
            raise ValueError(msg)
        self._period = period
        self._k = std_multiplier

    @property
    def period(self) -> int:
        return self._period

    @property
    def std_multiplier(self) -> Decimal:
        return self._k

    def calculate(self, prices: Sequence[Decimal]) -> list[BollingerValue]:
        """Рассчитать полосы Боллинджера."""
        if len(prices) < self._period:
            return []

        sma_values = SMA(self._period).calculate(prices)
        result: list[BollingerValue] = []

        for sv in sma_values:
            start = sv.index - self._period + 1
            window = prices[start : sv.index + 1]
            mean = sv.value

            variance = sum(
                (p - mean) ** 2 for p in window
            ) / Decimal(str(self._period))
            std = variance.sqrt() if variance >= Decimal("0") else Decimal("0")

            upper = mean + self._k * std
            lower = mean - self._k * std

            result.append(
                BollingerValue(
                    middle=mean,
                    upper=upper,
                    lower=lower,
                    index=sv.index,
                )
            )

        return result

    def __call__(
        self, prices: Sequence[Decimal]
    ) -> list[BollingerValue]:
        return self.calculate(prices)

    def __str__(self) -> str:
        return f"Bollinger({self._period}, {self._k})"

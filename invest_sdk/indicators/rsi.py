from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple


class RSIValue(NamedTuple):
    """Значение RSI."""

    value: Decimal
    index: int


class RSI:
    """Индекс относительной силы (Relative Strength Index).

    RSI = 100 - (100 / (1 + RS))
    где RS = avg_gain / avg_loss
    """

    def __init__(self, period: int = 14) -> None:
        if period < 1:
            msg = "Period must be >= 1"
            raise ValueError(msg)
        self._period = period

    @property
    def period(self) -> int:
        return self._period

    def calculate(self, prices: Sequence[Decimal]) -> list[RSIValue]:
        """Рассчитать RSI для последовательности цен."""
        if len(prices) < self._period + 1:
            return []

        gains: list[Decimal] = []
        losses: list[Decimal] = []

        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            if diff > Decimal("0"):
                gains.append(diff)
                losses.append(Decimal("0"))
            else:
                gains.append(Decimal("0"))
                losses.append(abs(diff))

        result: list[RSIValue] = []

        first_gains = gains[: self._period]
        first_losses = losses[: self._period]

        avg_gain = sum(first_gains, Decimal("0")) / Decimal(str(self._period))
        avg_loss = sum(first_losses, Decimal("0")) / Decimal(str(self._period))

        rs = avg_gain / avg_loss if avg_loss > Decimal("0") else Decimal("0")
        rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
        result.append(RSIValue(value=rsi, index=self._period))

        for i in range(self._period, len(gains)):
            avg_gain = (
                avg_gain * Decimal(self._period - 1) + gains[i]
            ) / Decimal(str(self._period))
            avg_loss = (
                avg_loss * Decimal(self._period - 1) + losses[i]
            ) / Decimal(str(self._period))

            rs = (
                avg_gain / avg_loss
                if avg_loss > Decimal("0")
                else Decimal("0")
            )
            rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
            result.append(RSIValue(value=rsi, index=i + 1))

        return result

    def __call__(self, prices: Sequence[Decimal]) -> list[RSIValue]:
        return self.calculate(prices)

    def __str__(self) -> str:
        return f"RSI({self._period})"

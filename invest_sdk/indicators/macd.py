from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple

from invest_sdk.indicators.ema import EMA


class MACDValue(NamedTuple):
    """Значение MACD."""

    macd: Decimal
    signal: Decimal
    histogram: Decimal
    index: int


class MACD:
    """Индикатор MACD (Moving Average Convergence Divergence).

    MACD = EMA(fast) - EMA(slow)
    Signal = EMA(macd, signal_period)
    Histogram = MACD - Signal
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> None:
        if fast_period >= slow_period:
            msg = "fast_period must be less than slow_period"
            raise ValueError(msg)
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period

    @property
    def fast_period(self) -> int:
        return self._fast_period

    @property
    def slow_period(self) -> int:
        return self._slow_period

    @property
    def signal_period(self) -> int:
        return self._signal_period

    def calculate(self, prices: Sequence[Decimal]) -> list[MACDValue]:
        """Рассчитать MACD для последовательности цен."""
        if len(prices) < self._slow_period + self._signal_period:
            return []

        fast_ema = EMA(self._fast_period).calculate(prices)
        slow_ema = EMA(self._slow_period).calculate(prices)

        # Build price -> EMA mapping from the EMA result lists
        fast_map: dict[int, Decimal] = {fe.index: fe.value for fe in fast_ema}
        slow_map: dict[int, Decimal] = {se.index: se.value for se in slow_ema}

        common_indices = sorted(
            set(fast_map.keys()) & set(slow_map.keys())
        )

        macd_line: list[Decimal] = []
        macd_indices: list[int] = []

        for idx in common_indices:
            macd_line.append(fast_map[idx] - slow_map[idx])
            macd_indices.append(idx)

        if len(macd_line) < self._signal_period:
            return []

        signal_ema = EMA(self._signal_period).calculate(macd_line)
        signal_map: dict[int, Decimal] = {
            se.index: se.value for se in signal_ema
        }

        result: list[MACDValue] = []
        for se in signal_ema:
            original_index = macd_indices[se.index]
            m_val = macd_line[se.index]
            s_val = se.value
            result.append(
                MACDValue(
                    macd=m_val,
                    signal=s_val,
                    histogram=m_val - s_val,
                    index=original_index,
                )
            )

        return result

    def __call__(self, prices: Sequence[Decimal]) -> list[MACDValue]:
        return self.calculate(prices)

    def __str__(self) -> str:
        return (
            f"MACD({self._fast_period}, {self._slow_period}, "
            f"{self._signal_period})"
        )

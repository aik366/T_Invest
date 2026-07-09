"""Пример расчёта технических индикаторов."""
from __future__ import annotations

from decimal import Decimal

from invest_sdk.indicators.bollinger import BollingerBands
from invest_sdk.indicators.ema import EMA
from invest_sdk.indicators.macd import MACD
from invest_sdk.indicators.rsi import RSI
from invest_sdk.indicators.sma import SMA


def main() -> None:
    prices = [
        Decimal(str(i)) for i in [
            100, 102, 104, 103, 105, 107, 106, 108,
            110, 109, 111, 113, 112, 114, 115,
        ]
    ]

    sma = SMA(period=5)
    print("=== SMA(5) ===")
    for sv in sma(prices):
        print(f"  [{sv.index}] {sv.value:.2f}")

    ema = EMA(period=5)
    print("\n=== EMA(5) ===")
    for ev in ema(prices):
        print(f"  [{ev.index}] {ev.value:.2f}")

    rsi = RSI(period=5)
    print("\n=== RSI(5) ===")
    for rv in rsi(prices):
        print(f"  [{rv.index}] {rv.value:.2f}")

    macd = MACD(fast_period=3, slow_period=6, signal_period=3)
    print("\n=== MACD ===")
    for mv in macd(prices):
        print(
            f"  [{mv.index}] MACD={mv.macd:.2f} "
            f"Signal={mv.signal:.2f} Hist={mv.histogram:.2f}"
        )

    bb = BollingerBands(period=5)
    print("\n=== Bollinger Bands(5) ===")
    for bv in bb(prices):
        print(
            f"  [{bv.index}] Mid={bv.middle:.2f} "
            f"Upper={bv.upper:.2f} Lower={bv.lower:.2f}"
        )


if __name__ == "__main__":
    main()

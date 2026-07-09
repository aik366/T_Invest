from __future__ import annotations

from decimal import Decimal

import pytest

from invest_sdk.indicators.bollinger import BollingerBands
from invest_sdk.indicators.ema import EMA
from invest_sdk.indicators.macd import MACD
from invest_sdk.indicators.rsi import RSI
from invest_sdk.indicators.sma import SMA


class TestSMA:
    def test_sma_calculation(self) -> None:
        prices = [Decimal(str(i)) for i in range(1, 11)]
        sma = SMA(period=3)
        result = sma.calculate(prices)

        assert len(result) == 8
        assert result[0].value == Decimal("2")  # (1+2+3)/3
        assert result[1].value == Decimal("3")  # (2+3+4)/3
        assert result[-1].value == Decimal("9")  # (8+9+10)/3

    def test_sma_not_enough_data(self) -> None:
        prices = [Decimal("1"), Decimal("2")]
        sma = SMA(period=5)
        assert sma.calculate(prices) == []

    def test_sma_invalid_period(self) -> None:
        with pytest.raises(ValueError):
            SMA(period=0)


class TestEMA:
    def test_ema_calculation(self) -> None:
        prices = [Decimal(str(i)) for i in range(1, 11)]
        ema = EMA(period=3)
        result = ema.calculate(prices)

        assert len(result) == 8
        assert result[0].value == Decimal("2")  # SMA первых 3

    def test_ema_not_enough_data(self) -> None:
        prices = [Decimal("1"), Decimal("2")]
        ema = EMA(period=5)
        assert ema.calculate(prices) == []

    def test_ema_invalid_period(self) -> None:
        with pytest.raises(ValueError):
            EMA(period=0)


class TestMACD:
    def test_macd_calculation(self) -> None:
        prices = [Decimal(str(i)) for i in range(1, 50)]
        macd = MACD(fast_period=6, slow_period=13, signal_period=5)
        result = macd.calculate(prices)

        assert len(result) > 0
        for r in result:
            assert r.histogram == r.macd - r.signal

    def test_macd_not_enough_data(self) -> None:
        prices = [Decimal("1"), Decimal("2")]
        macd = MACD()
        assert macd.calculate(prices) == []

    def test_macd_invalid_periods(self) -> None:
        with pytest.raises(ValueError):
            MACD(fast_period=20, slow_period=10)


class TestRSI:
    def test_rsi_calculation(self) -> None:
        prices = [Decimal(str(i)) for i in range(1, 20)]
        rsi = RSI(period=5)
        result = rsi.calculate(prices)

        assert len(result) > 0
        for r in result:
            assert Decimal("0") <= r.value <= Decimal("100")

    def test_rsi_not_enough_data(self) -> None:
        prices = [Decimal("1")]
        rsi = RSI(period=5)
        assert rsi.calculate(prices) == []

    def test_rsi_invalid_period(self) -> None:
        with pytest.raises(ValueError):
            RSI(period=0)


class TestBollingerBands:
    def test_bollinger_calculation(self) -> None:
        prices = [Decimal(str(i)) for i in range(1, 30)]
        bb = BollingerBands(period=5)
        result = bb.calculate(prices)

        assert len(result) > 0
        for r in result:
            assert r.lower <= r.middle <= r.upper

    def test_bollinger_not_enough_data(self) -> None:
        prices = [Decimal("1"), Decimal("2")]
        bb = BollingerBands(period=5)
        assert bb.calculate(prices) == []

    def test_bollinger_invalid_period(self) -> None:
        with pytest.raises(ValueError):
            BollingerBands(period=0)

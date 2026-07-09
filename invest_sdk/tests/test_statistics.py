from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from invest_sdk.models import Candle, Portfolio, PortfolioPosition
from invest_sdk.statistics import Statistics


class TestStatistics:
    def _make_position(
        self,
        ticker: str,
        quantity: Decimal,
        avg_price: Decimal,
        current_price: Decimal,
        expected_yield: Decimal | None = None,
    ) -> PortfolioPosition:
        if expected_yield is None:
            expected_yield = (current_price - avg_price) * quantity
        return PortfolioPosition(
            figi=f"FIGI_{ticker}",
            instrument_uid=f"UID_{ticker}",
            instrument_type="share",
            ticker=ticker,
            name=f"Test {ticker}",
            quantity=quantity,
            average_price=avg_price,
            current_price=current_price,
            total_value=current_price * quantity,
            expected_yield=expected_yield,
            currency="rub",
        )

    def test_portfolio_summary(self) -> None:
        pos1 = self._make_position("A", Decimal("10"), Decimal("100"), Decimal("120"))
        pos2 = self._make_position("B", Decimal("5"), Decimal("200"), Decimal("180"))

        portfolio = Portfolio(
            account_id="test",
            total_value=pos1.total_value + pos2.total_value,
            total_yield=pos1.expected_yield + pos2.expected_yield,
            total_yield_percent=Decimal("0"),
            positions=[pos1, pos2],
        )

        summary = Statistics.portfolio_summary(portfolio)
        assert summary.position_count == 2
        assert summary.profitable_count == 1
        assert summary.unprofitable_count == 1
        assert summary.total_value > Decimal("0")

    def test_empty_portfolio_summary(self) -> None:
        portfolio = Portfolio(
            account_id="test",
            total_value=Decimal("0"),
            total_yield=Decimal("0"),
            total_yield_percent=Decimal("0"),
            positions=[],
        )
        summary = Statistics.portfolio_summary(portfolio)
        assert summary.position_count == 0
        assert summary.total_value == Decimal("0")

    def test_position_allocations(self) -> None:
        pos1 = self._make_position("A", Decimal("10"), Decimal("100"), Decimal("120"))
        pos2 = self._make_position("B", Decimal("5"), Decimal("200"), Decimal("180"))

        portfolio = Portfolio(
            account_id="test",
            total_value=pos1.total_value + pos2.total_value,
            total_yield=Decimal("0"),
            total_yield_percent=Decimal("0"),
            positions=[pos1, pos2],
        )

        allocs = Statistics.position_allocations(portfolio)
        assert len(allocs) == 1
        assert abs(allocs[0].percent - Decimal("100")) < Decimal("0.01")

    def test_candle_statistics(self) -> None:
        candles = [
            Candle(
                figi="F", instrument_uid="U",
                open=Decimal("100"), high=Decimal("110"),
                low=Decimal("95"), close=Decimal("105"),
                volume=1000, time=datetime(2024, 1, 1),
                interval="DAY",
            ),
            Candle(
                figi="F", instrument_uid="U",
                open=Decimal("105"), high=Decimal("115"),
                low=Decimal("102"), close=Decimal("112"),
                volume=1200, time=datetime(2024, 1, 2),
                interval="DAY",
            ),
            Candle(
                figi="F", instrument_uid="U",
                open=Decimal("112"), high=Decimal("120"),
                low=Decimal("108"), close=Decimal("115"),
                volume=900, time=datetime(2024, 1, 3),
                interval="DAY",
            ),
        ]

        stats = Statistics.candle_statistics(candles)
        assert stats.open == Decimal("100")
        assert stats.close == Decimal("115")
        assert stats.high == Decimal("120")
        assert stats.low == Decimal("95")
        assert stats.change == Decimal("15")

    def test_empty_candle_statistics(self) -> None:
        stats = Statistics.candle_statistics([])
        assert stats.close == Decimal("0")

    def test_diversification_score(self) -> None:
        pos1 = self._make_position("A", Decimal("10"), Decimal("100"), Decimal("100"))
        pos2 = self._make_position("B", Decimal("10"), Decimal("100"), Decimal("100"))

        score = Statistics.diversification_score([pos1, pos2])
        assert score > Decimal("0")

    def test_profitable_positions(self) -> None:
        pos1 = self._make_position("A", Decimal("1"), Decimal("100"), Decimal("150"))
        pos2 = self._make_position("B", Decimal("1"), Decimal("200"), Decimal("150"))

        profitable = Statistics.profitable_positions([pos1, pos2])
        assert len(profitable) == 1
        assert profitable[0].ticker == "A"

    def test_unprofitable_positions(self) -> None:
        pos1 = self._make_position("A", Decimal("1"), Decimal("100"), Decimal("150"))
        pos2 = self._make_position("B", Decimal("1"), Decimal("200"), Decimal("150"))

        unprofitable = Statistics.unprofitable_positions([pos1, pos2])
        assert len(unprofitable) == 1
        assert unprofitable[0].ticker == "B"

    def test_top_positions(self) -> None:
        positions = [
            self._make_position(f"P{i}", Decimal("1"), Decimal(f"{i * 100}"), Decimal(f"{i * 100 + 10}"))
            for i in range(1, 6)
        ]

        top = Statistics.top_positions(positions, top_n=3)
        assert len(top) == 3
        assert top[0].ticker == "P5"

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from invest_sdk.models import (
    Account,
    Candle,
    Instrument,
    OrderBook,
    Portfolio,
    PortfolioPosition,
    UserInfo,
)


class TestModels:
    def test_account(self) -> None:
        acc = Account(
            id="test-id",
            name="Test Account",
            type="ACCOUNT_TYPE_TINKOFF",
            status="ACCOUNT_STATUS_OPEN",
        )
        assert acc.id == "test-id"
        assert acc.name == "Test Account"
        assert acc.type == "ACCOUNT_TYPE_TINKOFF"

    def test_instrument(self) -> None:
        inst = Instrument(
            figi="BBG0000001",
            uid="uid-1",
            ticker="AAPL",
            name="Apple Inc.",
            instrument_type="share",
            currency="usd",
            lot=1,
        )
        assert inst.figi == "BBG0000001"
        assert inst.ticker == "AAPL"

    def test_portfolio_position(self) -> None:
        pos = PortfolioPosition(
            figi="FIGI1",
            instrument_uid="UID1",
            instrument_type="share",
            ticker="SBER",
            name="Sberbank",
            quantity=Decimal("10"),
            average_price=Decimal("250"),
            current_price=Decimal("280"),
            total_value=Decimal("2800"),
            expected_yield=Decimal("300"),
            currency="rub",
        )
        assert pos.ticker == "SBER"
        assert pos.quantity == Decimal("10")
        assert pos.expected_yield == Decimal("300")

    def test_portfolio(self) -> None:
        pos = PortfolioPosition(
            figi="F1",
            instrument_uid="U1",
            instrument_type="share",
            ticker="T1",
            name="Test",
            quantity=Decimal("1"),
            average_price=Decimal("100"),
            current_price=Decimal("150"),
            total_value=Decimal("150"),
            expected_yield=Decimal("50"),
            currency="rub",
        )
        portfolio = Portfolio(
            account_id="acc-1",
            total_value=Decimal("150"),
            total_yield=Decimal("50"),
            total_yield_percent=Decimal("50"),
            positions=[pos],
        )
        assert portfolio.account_id == "acc-1"
        assert len(portfolio.positions) == 1
        assert portfolio.total_value == Decimal("150")

    def test_candle(self) -> None:
        c = Candle(
            figi="FIGI1",
            instrument_uid="UID1",
            open=Decimal("100"),
            high=Decimal("110"),
            low=Decimal("95"),
            close=Decimal("105"),
            volume=1000,
            time=datetime(2024, 1, 1),
            interval="CANDLE_INTERVAL_DAY",
            is_complete=True,
        )
        assert c.open == Decimal("100")
        assert c.close == Decimal("105")
        assert c.is_complete

    def test_order_book(self) -> None:
        ob = OrderBook(
            figi="FIGI1",
            instrument_uid="UID1",
            depth=10,
            bids=[(Decimal("100"), 10)],
            asks=[(Decimal("101"), 5)],
            last_price=Decimal("100.5"),
        )
        assert len(ob.bids) == 1
        assert ob.bids[0][0] == Decimal("100")

    def test_user_info(self) -> None:
        info = UserInfo(
            premium_status="premium",
            qualified_status="qualified",
            tariff="free",
        )
        assert info.premium_status == "premium"
        assert info.tariff == "free"

    def test_models_are_frozen(self) -> None:
        acc = Account(id="1", name="Test", type="A", status="S")
        with pytest.raises(AttributeError):
            acc.name = "Changed"  # type: ignore[misc]

    def test_models_use_slots(self) -> None:
        acc = Account(id="1", name="Test", type="A", status="S")
        with pytest.raises(AttributeError):
            acc.new_attr = "test"  # type: ignore[attr-defined]

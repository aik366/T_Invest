from __future__ import annotations

from decimal import Decimal

import pytest

from invest_sdk.money import Currency, Money


class TestCurrency:
    def test_from_string(self) -> None:
        assert Currency.from_string("rub") == Currency.RUB
        assert Currency.from_string("USD") == Currency.USD
        assert Currency.from_string("Eur") == Currency.EUR

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError, match="Unknown currency code"):
            Currency.from_string("invalid")

    def test_str(self) -> None:
        assert str(Currency.RUB) == "RUB"
        assert str(Currency.USD) == "USD"


class TestMoney:
    def test_create(self) -> None:
        m = Money(Decimal("150.50"), Currency.USD)
        assert m.amount == Decimal("150.50")
        assert m.currency == Currency.USD

    def test_from_units_nano(self) -> None:
        m = Money.from_units_nano(100, 500_000_000, Currency.RUB)
        assert m.amount == Decimal("100.5")

    def test_from_money_value(self) -> None:
        class FakeMoneyValue:
            currency = "usd"
            units = 200
            nano = 750_000_000

        m = Money.from_money_value(FakeMoneyValue())
        assert m.amount == Decimal("200.75")
        assert m.currency == Currency.USD

    def test_from_quotation(self) -> None:
        class FakeQuotation:
            units = 50
            nano = 250_000_000

        m = Money.from_quotation(FakeQuotation(), Currency.RUB)
        assert m.amount == Decimal("50.25")

    def test_zero(self) -> None:
        m = Money.zero(Currency.USD)
        assert m.amount == Decimal("0")
        assert m.currency == Currency.USD
        assert m.is_zero()

    def test_rounding(self) -> None:
        m = Money(Decimal("10.5678"))
        rounded = m.rounded(2)
        assert rounded.amount == Decimal("10.57")

    def test_add_same_currency(self) -> None:
        a = Money(Decimal("100"), Currency.USD)
        b = Money(Decimal("50"), Currency.USD)
        assert (a + b).amount == Decimal("150")

    def test_add_different_currency(self) -> None:
        a = Money(Decimal("100"), Currency.USD)
        b = Money(Decimal("50"), Currency.EUR)
        with pytest.raises(ValueError, match="Cannot add"):
            _ = a + b

    def test_subtract(self) -> None:
        a = Money(Decimal("100"), Currency.USD)
        b = Money(Decimal("30"), Currency.USD)
        assert (a - b).amount == Decimal("70")

    def test_multiply(self) -> None:
        m = Money(Decimal("10.5"), Currency.RUB)
        assert (m * 2).amount == Decimal("21.0")

    def test_divide(self) -> None:
        m = Money(Decimal("100"), Currency.RUB)
        assert (m / 4).amount == Decimal("25")

    def test_neg(self) -> None:
        m = Money(Decimal("50"))
        assert (-m).amount == Decimal("-50")

    def test_abs(self) -> None:
        m = Money(Decimal("-50"))
        assert abs(m).amount == Decimal("50")

    def test_bool(self) -> None:
        assert not Money.zero()
        assert Money(Decimal("1"))

    def test_str(self) -> None:
        m = Money(Decimal("150.50"), Currency.USD)
        assert "150.50" in str(m)
        assert "USD" in str(m)

    def test_auto_decimal_convert(self) -> None:
        m = Money("150.75")
        assert isinstance(m.amount, Decimal)
        assert m.amount == Decimal("150.75")

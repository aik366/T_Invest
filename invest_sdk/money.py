from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from enum import Enum
from typing import Self


class Currency(Enum):
    RUB = "rub"
    USD = "usd"
    EUR = "eur"
    CNY = "cny"
    GBP = "gbp"
    HKD = "hkd"
    CHF = "chf"
    JPY = "jpy"
    TRY = "try"

    def __str__(self) -> str:
        return self.value.upper()

    @classmethod
    def from_string(cls, code: str) -> Self:
        normalized = code.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
            if member.name == normalized.upper():
                return member
        msg = f"Unknown currency code: {code}"
        raise ValueError(msg)


_NANO_DECIMAL = Decimal(1_000_000_000)


@dataclass(slots=True, frozen=True)
class Money:
    """Денежная сумма в указанной валюте.

    Все вычисления выполняются через Decimal.
    Не содержит логики портфеля — только деньги.
    """

    amount: Decimal
    currency: Currency = Currency.RUB

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

    @classmethod
    def from_units_nano(
        cls, units: int, nano: int, currency: Currency = Currency.RUB
    ) -> Money:
        """Создать Money из units/nano (как в MoneyValue/Quotation)."""
        amount = Decimal(units) + Decimal(nano) / _NANO_DECIMAL
        return cls(amount=amount, currency=currency)

    @classmethod
    def from_money_value(
        cls, money_value: object, currency: Currency | None = None
    ) -> Money:
        """Создать Money из protobuf MoneyValue."""
        curr = currency or Currency.from_string(money_value.currency)
        return cls.from_units_nano(
            units=money_value.units,
            nano=money_value.nano,
            currency=curr,
        )

    @classmethod
    def from_quotation(
        cls, quotation: object, currency: Currency = Currency.RUB
    ) -> Money:
        """Создать Money из protobuf Quotation."""
        return cls.from_units_nano(
            units=quotation.units,
            nano=quotation.nano,
            currency=currency,
        )

    @classmethod
    def zero(cls, currency: Currency = Currency.RUB) -> Money:
        """Нулевая сумма в указанной валюте."""
        return cls(amount=Decimal(0), currency=currency)

    def to_decimal(self) -> Decimal:
        """Получить Decimal значение (для вычислений)."""
        return self.amount

    def rounded(self, places: int = 2) -> Money:
        """Округлить до указанного количества знаков."""
        quantize_str = "0" + ("." + "0" * places) if places > 0 else "0"
        return Money(
            amount=self.amount.quantize(
                Decimal(quantize_str), rounding=ROUND_HALF_EVEN
            ),
            currency=self.currency,
        )

    def is_zero(self) -> bool:
        return self.amount == Decimal(0)

    def is_positive(self) -> bool:
        return self.amount > Decimal(0)

    def is_negative(self) -> bool:
        return self.amount < Decimal(0)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            msg = f"Cannot add {self.currency} and {other.currency}"
            raise ValueError(msg)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            msg = f"Cannot subtract {self.currency} and {other.currency}"
            raise ValueError(msg)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, other: Decimal | int | float) -> Money:
        factor = Decimal(str(other)) if not isinstance(other, Decimal) else other
        return Money(amount=self.amount * factor, currency=self.currency)

    def __truediv__(self, other: Decimal | int | float) -> Money:
        factor = Decimal(str(other)) if not isinstance(other, Decimal) else other
        return Money(amount=self.amount / factor, currency=self.currency)

    def __neg__(self) -> Money:
        return Money(amount=-self.amount, currency=self.currency)

    def __abs__(self) -> Money:
        return Money(amount=abs(self.amount), currency=self.currency)

    def __bool__(self) -> bool:
        return not self.is_zero()

    def __str__(self) -> str:
        return f"{self.rounded().amount:.2f} {self.currency}"

    def __repr__(self) -> str:
        return f"Money({self.amount!r}, {self.currency!r})"

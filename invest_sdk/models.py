from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Sequence


@dataclass(slots=True, frozen=True)
class Account:
    """Банковский счёт / брокерский счёт."""

    id: str
    name: str
    type: str
    status: str
    opened_date: datetime | None = None
    closed_date: datetime | None = None
    access_level: str = ""


@dataclass(slots=True, frozen=True)
class Instrument:
    """Торговый инструмент (акция, облигация, ETF и т.д.)."""

    figi: str
    uid: str
    ticker: str
    name: str
    instrument_type: str
    currency: str
    lot: int
    min_price_increment: Decimal = Decimal("0")
    nominal: Decimal = Decimal("0")
    country: str = ""
    sector: str = ""
    short_enabled: bool = False
    buy_enabled: bool = False
    sell_enabled: bool = False
    api_trade_available: bool = False
    class_code: str = ""
    exchange: str = ""
    real_exchange: str = ""


@dataclass(slots=True, frozen=True)
class InstrumentShort:
    """Краткая информация об инструменте для поиска."""

    uid: str
    figi: str
    ticker: str
    name: str
    instrument_type: str
    class_code: str = ""
    exchange: str = ""


@dataclass(slots=True, frozen=True)
class PortfolioPosition:
    """Позиция в портфеле."""

    figi: str
    instrument_uid: str
    instrument_type: str
    ticker: str
    name: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    total_value: Decimal
    expected_yield: Decimal
    currency: str
    lot: int = 0
    blocked: bool = False
    var_margin: Decimal | None = None
    current_nkd: Decimal | None = None
    daily_yield: Decimal = Decimal("0")


@dataclass(slots=True, frozen=True)
class Portfolio:
    """Портфель целиком."""

    account_id: str
    total_value: Decimal
    total_yield: Decimal
    total_yield_percent: Decimal
    positions: Sequence[PortfolioPosition] = field(default_factory=list)
    currency: str = "rub"
    expected_yield: Decimal = Decimal("0")


@dataclass(slots=True, frozen=True)
class Candle:
    """Свеча — единица торговых данных за интервал времени."""

    figi: str
    instrument_uid: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    time: datetime
    interval: str
    is_complete: bool = False


@dataclass(slots=True, frozen=True)
class OrderBook:
    """Стакан цен."""

    figi: str
    instrument_uid: str
    depth: int
    bids: Sequence[tuple[Decimal, int]] = field(default_factory=list)
    asks: Sequence[tuple[Decimal, int]] = field(default_factory=list)
    last_price: Decimal = Decimal("0")
    close_price: Decimal = Decimal("0")
    time: datetime | None = None


@dataclass(slots=True, frozen=True)
class LastPrice:
    """Последняя цена инструмента."""

    figi: str
    instrument_uid: str
    price: Decimal
    time: datetime | None = None


@dataclass(slots=True, frozen=True)
class Trade:
    """Сделка."""

    figi: str
    instrument_uid: str
    price: Decimal
    quantity: int
    time: datetime
    direction: str


@dataclass(slots=True, frozen=True)
class Operation:
    """Операция по счёту."""

    id: str
    parent_operation_id: str = ""
    currency: str = "rub"
    payment: Decimal = Decimal("0")
    price: Decimal = Decimal("0")
    quantity: int = 0
    quantity_remaining: int = 0
    operation_type: str = ""
    state: str = ""
    figi: str = ""
    instrument_uid: str = ""
    date: datetime | None = None
    trades: Sequence[Trade] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class TradingDay:
    """Торговый день."""

    date: datetime
    is_trading_day: bool
    start_time: datetime | None = None
    end_time: datetime | None = None
    opening_time: datetime | None = None
    closing_time: datetime | None = None


@dataclass(slots=True, frozen=True)
class TradingSchedule:
    """Расписание торгов."""

    exchange: str
    days: Sequence[TradingDay] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class Dividend:
    """Дивиденд по инструменту."""

    dividend_net: Decimal
    dividend_yield_percent: Decimal = Decimal("0")
    payment_date: datetime | None = None
    declared_date: datetime | None = None
    record_date: datetime | None = None
    figi: str = ""
    instrument_uid: str = ""
    currency: str = "rub"
    close_price: Decimal = Decimal("0")
    regularity: str = ""


@dataclass(slots=True, frozen=True)
class Coupon:
    """Купон по облигации."""

    figi: str = ""
    instrument_uid: str = ""
    coupon_number: int = 0
    coupon_date: datetime | None = None
    record_date: datetime | None = None
    total_coupon: Decimal = Decimal("0")
    coupon_percent: Decimal = Decimal("0")
    currency: str = "rub"
    coupon_type: str = ""
    next_coupon_date: datetime | None = None
    accrued_int: Decimal = Decimal("0")


@dataclass(slots=True, frozen=True)
class UserInfo:
    """Информация о пользователе."""

    premium_status: str = ""
    qualified_status: str = ""
    tariff: str = ""
    promo_status: str = ""


@dataclass(slots=True, frozen=True)
class AccountValue:
    """Стоимость счёта в разрезе валют / инструментов."""

    currency: str
    total_value: Decimal
    total_blocked: Decimal = Decimal("0")
    total_free: Decimal = Decimal("0")

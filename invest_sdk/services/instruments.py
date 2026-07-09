from __future__ import annotations

from decimal import Decimal

from invest_sdk.models import Instrument, InstrumentShort


class InstrumentService:
    """Сервис для получения справочной информации об инструментах.

    Единственный слой, который напрямую вызывает SDK.
    """

    def __init__(self, sdk_services: object) -> None:
        self._sdk = sdk_services

    def get_shares(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список акций."""
        from t_tech.invest.schemas import InstrumentStatus

        status = InstrumentStatus[instrument_status]
        response = self._sdk.instruments.shares(instrument_status=status)
        return [_build_instrument(s) for s in response.instruments]

    def get_bonds(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список облигаций."""
        from t_tech.invest.schemas import InstrumentStatus

        status = InstrumentStatus[instrument_status]
        response = self._sdk.instruments.bonds(instrument_status=status)
        return [_build_instrument(s) for s in response.instruments]

    def get_etfs(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список ETF."""
        from t_tech.invest.schemas import InstrumentStatus

        status = InstrumentStatus[instrument_status]
        response = self._sdk.instruments.etfs(instrument_status=status)
        return [_build_instrument(s) for s in response.instruments]

    def get_currencies(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список валют."""
        from t_tech.invest.schemas import InstrumentStatus

        status = InstrumentStatus[instrument_status]
        response = self._sdk.instruments.currencies(instrument_status=status)
        return [_build_instrument(s) for s in response.instruments]

    def get_futures(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список фьючерсов."""
        from t_tech.invest.schemas import InstrumentStatus

        status = InstrumentStatus[instrument_status]
        response = self._sdk.instruments.futures(instrument_status=status)
        return [_build_instrument(s) for s in response.instruments]

    def get_instrument_by(
        self,
        id_type: str = "INSTRUMENT_ID_TYPE_FIGI",
        id: str = "",
        class_code: str = "",
    ) -> Instrument | None:
        """Получить инструмент по идентификатору."""
        from t_tech.invest.schemas import InstrumentIdType

        id_type_enum = InstrumentIdType[id_type]
        response = self._sdk.instruments.get_instrument_by(
            id_type=id_type_enum, id=id, class_code=class_code
        )
        if response.instrument is None:
            return None
        return _build_instrument(response.instrument)

    def find_instrument(
        self, query: str, instrument_kind: str | None = None
    ) -> list[InstrumentShort]:
        """Найти инструмент по строке поиска."""
        from t_tech.invest.schemas import InstrumentType

        kind = InstrumentType[instrument_kind] if instrument_kind else None
        response = self._sdk.instruments.find_instrument(
            query=query, instrument_kind=kind
        )
        return [
            InstrumentShort(
                uid=item.uid or "",
                figi=item.figi or "",
                ticker=item.ticker or "",
                name=item.name or "",
                instrument_type=item.instrument_type or "",
                class_code=item.class_code or "",
                exchange=item.exchange or "",
            )
            for item in response.instruments
        ]

    def get_dividends(
        self,
        figi: str = "",
        instrument_id: str = "",
        from_: object = None,
        to: object = None,
    ) -> list:
        """Получить дивиденды по инструменту."""
        response = self._sdk.instruments.get_dividends(
            figi=figi,
            instrument_id=instrument_id,
            from_=from_,
            to=to,
        )
        result = []
        for div in response.dividends:
            result.append(
                {
                    "dividend_net": _money_value_to_dict(div.dividend_net),
                    "payment_date": div.payment_date,
                    "declared_date": div.declared_date,
                    "record_date": div.record_date,
                    "figi": div.figi or figi,
                    "instrument_uid": div.instrument_uid or instrument_id,
                    "currency": div.dividend_net.currency.lower() if div.dividend_net else "rub",
                    "close_price": _money_value_to_dict(div.close_price),
                    "yield_value": div.yield_value,
                    "regularity": div.regularity or "",
                }
            )
        return result

    def get_bond_coupons(
        self,
        figi: str = "",
        instrument_id: str = "",
        from_: object = None,
        to: object = None,
    ) -> list:
        """Получить купоны по облигации."""
        response = self._sdk.instruments.get_bond_coupons(
            figi=figi,
            instrument_id=instrument_id,
            from_=from_,
            to=to,
        )
        result = []
        for coup in response.events:
            result.append(
                {
                    "figi": coup.figi or figi,
                    "instrument_uid": coup.instrument_uid or instrument_id,
                    "coupon_number": coup.coupon_number,
                    "coupon_date": coup.coupon_date,
                    "record_date": coup.record_date,
                    "total_coupon": _money_value_to_dict(coup.pay_one_bond),
                    "coupon_percent": coup.coupon_percent,
                    "currency": coup.pay_one_bond.currency.lower() if coup.pay_one_bond else "rub",
                    "coupon_type": coup.coupon_type or "",
                }
            )
        return result

    def trading_schedules(
        self, exchange: str = "", from_: object = None, to: object = None
    ) -> list:
        """Получить расписание торгов."""
        response = self._sdk.instruments.trading_schedules(
            exchange=exchange, from_=from_, to=to
        )
        result = []
        for sched in response.exchanges:
            days = []
            for day in sched.days:
                days.append(
                    {
                        "date": day.date,
                        "is_trading_day": day.is_trading_day,
                        "start_time": day.start_time,
                        "end_time": day.end_time,
                        "opening_time": day.opening_time,
                        "closing_time": day.closing_time,
                    }
                )
            result.append(
                {
                    "exchange": sched.exchange,
                    "days": days,
                }
            )
        return result


def _build_instrument(sdk_instrument: object) -> Instrument:
    return Instrument(
        figi=getattr(sdk_instrument, "figi", "") or "",
        uid=getattr(sdk_instrument, "uid", "") or "",
        ticker=getattr(sdk_instrument, "ticker", "") or "",
        name=getattr(sdk_instrument, "name", "") or "",
        instrument_type=getattr(sdk_instrument, "instrument_type", "") or "",
        currency=getattr(sdk_instrument, "currency", "").lower() or "rub",
        lot=getattr(sdk_instrument, "lot", 0) or 0,
        min_price_increment=_quotation_to_decimal(
            getattr(sdk_instrument, "min_price_increment", None)
        ),
        nominal=_money_value_to_decimal(
            getattr(sdk_instrument, "nominal", None)
        ),
        country=getattr(sdk_instrument, "country_of_risk", "") or "",
        sector=getattr(sdk_instrument, "sector", "") or "",
        short_enabled=bool(getattr(sdk_instrument, "short_enabled_flag", False)),
        buy_enabled=bool(getattr(sdk_instrument, "buy_available_flag", False)),
        sell_enabled=bool(
            getattr(sdk_instrument, "sell_available_flag", False)
        ),
        api_trade_available=bool(
            getattr(sdk_instrument, "api_trade_available_flag", False)
        ),
        class_code=getattr(sdk_instrument, "class_code", "") or "",
        exchange=getattr(sdk_instrument, "exchange", "") or "",
        real_exchange=getattr(sdk_instrument, "real_exchange", "") or "",
    )


def _quotation_to_decimal(q: object) -> Decimal:
    if q is None:
        return Decimal("0")
    return Decimal(getattr(q, "units", 0)) + Decimal(getattr(q, "nano", 0)) / Decimal(
        1_000_000_000
    )


def _money_value_to_decimal(mv: object) -> Decimal:
    if mv is None:
        return Decimal("0")
    return Decimal(getattr(mv, "units", 0)) + Decimal(getattr(mv, "nano", 0)) / Decimal(
        1_000_000_000
    )


def _money_value_to_dict(mv: object) -> dict:
    if mv is None:
        return {"currency": "", "units": 0, "nano": 0}
    return {
        "currency": getattr(mv, "currency", "").lower() or "rub",
        "units": getattr(mv, "units", 0) or 0,
        "nano": getattr(mv, "nano", 0) or 0,
    }

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta
from decimal import Decimal

from invest_sdk.models import Candle


class CandleService:
    """Сервис для получения исторических свечных данных.

    Единственный слой, который напрямую вызывает SDK.
    """

    _INTERVAL_MAP: dict[str, object] = {}

    def __init__(self, sdk_services: object) -> None:
        self._sdk = sdk_services

    def get_candles(
        self,
        figi: str = "",
        from_: datetime | None = None,
        to: datetime | None = None,
        interval: str = "CANDLE_INTERVAL_DAY",
        instrument_id: str = "",
    ) -> list[Candle]:
        """Получить свечи по инструменту.

        Args:
            figi: FIGI инструмента.
            from_: Начало периода.
            to: Конец периода.
            interval: Интервал свечи (CANDLE_INTERVAL_*).
            instrument_id: UID инструмента (альтернатива figi).
        """
        from t_tech.invest.schemas import CandleInterval

        interval_enum = CandleInterval[interval]
        response = self._sdk.market_data.get_candles(
            figi=figi,
            from_=from_,
            to=to,
            interval=interval_enum,
            instrument_id=instrument_id,
        )
        return [
            Candle(
                figi=figi or instrument_id,
                instrument_uid=instrument_id or figi,
                open=_quotation_to_decimal(c.open),
                high=_quotation_to_decimal(c.high),
                low=_quotation_to_decimal(c.low),
                close=_quotation_to_decimal(c.close),
                volume=c.volume or 0,
                time=c.time,
                interval=interval,
                is_complete=c.is_complete,
            )
            for c in response.candles
        ]

    def get_all_candles(
        self,
        figi: str = "",
        from_: datetime | None = None,
        to: datetime | None = None,
        interval: str = "CANDLE_INTERVAL_DAY",
        instrument_id: str = "",
    ) -> Generator[Candle, None, None]:
        """Получить все свечи за период (с учётом ограничений API).

        Использует встроенную пагинацию SDK.
        """
        from t_tech.invest.schemas import CandleInterval

        interval_enum = CandleInterval[interval]
        for sdk_candle in self._sdk.get_all_candles(
            from_=from_,
            to=to,
            interval=interval_enum,
            figi=figi,
            instrument_id=instrument_id,
        ):
            yield Candle(
                figi=figi or instrument_id,
                instrument_uid=instrument_id or figi,
                open=_quotation_to_decimal(sdk_candle.open),
                high=_quotation_to_decimal(sdk_candle.high),
                low=_quotation_to_decimal(sdk_candle.low),
                close=_quotation_to_decimal(sdk_candle.close),
                volume=sdk_candle.volume or 0,
                time=sdk_candle.time,
                interval=interval,
                is_complete=sdk_candle.is_complete,
            )


def _quotation_to_decimal(q: object) -> Decimal:
    if q is None:
        return Decimal("0")
    return Decimal(getattr(q, "units", 0)) + Decimal(getattr(q, "nano", 0)) / Decimal(
        1_000_000_000
    )

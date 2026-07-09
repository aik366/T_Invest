from __future__ import annotations

from decimal import Decimal

from invest_sdk.models import LastPrice, OrderBook, Trade


class MarketService:
    """Сервис для получения рыночных данных.

    Единственный слой, который напрямую вызывает SDK.
    """

    def __init__(self, sdk_services: object) -> None:
        self._sdk = sdk_services

    def get_order_book(
        self, figi: str = "", depth: int = 10, instrument_id: str = ""
    ) -> OrderBook:
        """Получить биржевой стакан."""
        response = self._sdk.market_data.get_order_book(
            figi=figi, depth=depth, instrument_id=instrument_id
        )
        bids = [
            (_quotation_to_decimal(b.price), b.quantity)
            for b in response.bids
        ]
        asks = [
            (_quotation_to_decimal(a.price), a.quantity)
            for a in response.asks
        ]
        return OrderBook(
            figi=response.figi or figi,
            instrument_uid=response.instrument_uid or instrument_id,
            depth=response.depth or depth,
            bids=bids,
            asks=asks,
            last_price=_quotation_to_decimal(response.last_price),
            close_price=_quotation_to_decimal(response.close_price),
            time=response.orderbook_ts,
        )

    def get_last_prices(
        self,
        figi: list[str] | None = None,
        instrument_id: list[str] | None = None,
    ) -> list[LastPrice]:
        """Получить последние цены."""
        response = self._sdk.market_data.get_last_prices(
            figi=figi, instrument_id=instrument_id
        )
        return [
            LastPrice(
                figi=lp.figi or "",
                instrument_uid=lp.instrument_uid or "",
                price=_quotation_to_decimal(lp.price),
                time=lp.time,
            )
            for lp in response.last_prices
        ]

    def get_trading_status(self, figi: str = "", instrument_id: str = "") -> dict:
        """Получить статус торгов по инструменту."""
        response = self._sdk.market_data.get_trading_status(
            figi=figi, instrument_id=instrument_id
        )
        return {
            "figi": response.figi or figi,
            "instrument_uid": response.instrument_uid or instrument_id,
            "trading_status": str(response.trading_status),
            "limit_order_available_flag": response.limit_order_available_flag,
            "market_order_available_flag": response.market_order_available_flag,
            "api_trade_available_flag": response.api_trade_available_flag,
        }

    def get_close_prices(self, instruments: list[dict]) -> list[dict]:
        """Получить цены закрытия."""
        from t_tech.invest.schemas import InstrumentClosePriceRequest

        requests_list = [
            InstrumentClosePriceRequest(
                instrument_id=inst.get("instrument_id", ""),
            )
            for inst in instruments
        ]
        response = self._sdk.market_data.get_close_prices(
            instruments=requests_list
        )
        return [
            {
                "instrument_uid": cp.instrument_uid or "",
                "price": _quotation_to_dict(cp.price),
                "time": cp.time,
            }
            for cp in response.close_prices
        ]


def _quotation_to_decimal(q: object) -> Decimal:
    if q is None:
        return Decimal("0")
    return Decimal(getattr(q, "units", 0)) + Decimal(getattr(q, "nano", 0)) / Decimal(
        1_000_000_000
    )


def _quotation_to_dict(q: object) -> dict:
    if q is None:
        return {"units": 0, "nano": 0}
    return {
        "units": getattr(q, "units", 0) or 0,
        "nano": getattr(q, "nano", 0) or 0,
    }

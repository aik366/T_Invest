from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from invest_sdk.cache import TTLCache
from invest_sdk.models import (
    Account,
    Candle,
    Instrument,
    InstrumentShort,
    LastPrice,
    OrderBook,
    Portfolio,
    UserInfo,
)
from invest_sdk.services import (
    AccountService,
    CandleService,
    InstrumentService,
    MarketService,
    PortfolioService,
)


class Repository:
    """Репозиторий — прослойка между сервисами и потребителями.

    Отвечает за кэширование данных.
    Ничего не знает о Printer, Statistics, UI.
    """

    def __init__(
        self,
        accounts: AccountService,
        portfolio: PortfolioService,
        instruments: InstrumentService,
        market: MarketService,
        candles: CandleService,
        cache_ttl: int = 300,
    ) -> None:
        self._accounts = accounts
        self._portfolio = portfolio
        self._instruments = instruments
        self._market = market
        self._candles = candles
        self._cache = TTLCache(default_ttl_seconds=cache_ttl)

    def get_accounts(self) -> Sequence[Account]:
        """Получить список счетов (с кэшированием)."""
        cached = self._cache.get("accounts")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._accounts.get_accounts()
        self._cache.set("accounts", result)
        return result

    def get_portfolio(self, account_id: str) -> Portfolio:
        """Получить портфель (с кэшированием)."""
        cache_key = f"portfolio:{account_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._portfolio.get_portfolio(account_id)
        self._cache.set(cache_key, result)
        return result

    def get_shares(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список акций (с кэшированием)."""
        cache_key = f"shares:{instrument_status}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._instruments.get_shares(instrument_status)
        self._cache.set(cache_key, result)
        return result

    def get_bonds(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список облигаций (с кэшированием)."""
        cache_key = f"bonds:{instrument_status}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._instruments.get_bonds(instrument_status)
        self._cache.set(cache_key, result)
        return result

    def get_etfs(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список ETF (с кэшированием)."""
        cache_key = f"etfs:{instrument_status}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._instruments.get_etfs(instrument_status)
        self._cache.set(cache_key, result)
        return result

    def get_currencies(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список валют (с кэшированием)."""
        cache_key = f"currencies:{instrument_status}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._instruments.get_currencies(instrument_status)
        self._cache.set(cache_key, result)
        return result

    def get_futures(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список фьючерсов (с кэшированием)."""
        cache_key = f"futures:{instrument_status}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._instruments.get_futures(instrument_status)
        self._cache.set(cache_key, result)
        return result

    def find_instrument(
        self, query: str, instrument_kind: str | None = None
    ) -> list[InstrumentShort]:
        """Поиск инструмента (с кэшированием)."""
        cache_key = f"find:{query}:{instrument_kind}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._instruments.find_instrument(query, instrument_kind)
        self._cache.set(cache_key, result)
        return result

    def get_order_book(
        self, figi: str = "", depth: int = 10, instrument_id: str = ""
    ) -> OrderBook:
        """Получить стакан (без кэша — данные реального времени)."""
        return self._market.get_order_book(
            figi=figi, depth=depth, instrument_id=instrument_id
        )

    def get_last_prices(
        self,
        figi: list[str] | None = None,
        instrument_id: list[str] | None = None,
    ) -> list[LastPrice]:
        """Получить последние цены (с кэшированием на 10 секунд)."""
        cache_key = f"last_prices:{figi}:{instrument_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._market.get_last_prices(
            figi=figi, instrument_id=instrument_id
        )
        self._cache.set(cache_key, result)
        return result

    def get_candles(
        self,
        figi: str = "",
        from_: datetime | None = None,
        to: datetime | None = None,
        interval: str = "CANDLE_INTERVAL_DAY",
        instrument_id: str = "",
    ) -> list[Candle]:
        """Получить свечи (с кэшированием)."""
        cache_key = (
            f"candles:{figi}:{instrument_id}:{interval}:{from_}:{to}"
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._candles.get_candles(
            figi=figi,
            from_=from_,
            to=to,
            interval=interval,
            instrument_id=instrument_id,
        )
        self._cache.set(cache_key, result)
        return result

    def get_info(self) -> UserInfo:
        """Получить информацию о пользователе (с кэшированием)."""
        cached = self._cache.get("user_info")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = self._accounts.get_info()
        self._cache.set("user_info", result)
        return result

    def invalidate_portfolio(self, account_id: str) -> None:
        """Инвалидировать кэш портфеля."""
        self._cache.invalidate(f"portfolio:{account_id}")

    def invalidate_all(self) -> None:
        """Полностью очистить кэш."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Количество записей в кэше."""
        return self._cache.size

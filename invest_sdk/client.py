from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from invest_sdk.models import (
    Account,
    Candle,
    Instrument,
    InstrumentShort,
    LastPrice,
    OrderBook,
    Portfolio,
    PortfolioPosition,
    UserInfo,
)
from invest_sdk.repository import Repository
from invest_sdk.statistics import (
    PortfolioSummary,
    PositionAllocation,
    Statistics,
)


class InvestClient:
    """Единая точка входа в библиотеку invest_sdk.

    Предоставляет высокоуровневый доступ к данным T-Bank Invest.
    Все внутренние вызовы проходят через сервисы (не напрямую в SDK).

    Usage:
        client = create_client(TOKEN)
        portfolio = client.get_portfolio("account_id")
        print(portfolio.summary())
    """

    def __init__(
        self,
        repository: Repository,
        sdk_services: object,
        sdk_client: object,
    ) -> None:
        self._repository = repository
        self._sdk = sdk_services
        self._sdk_client = sdk_client

    @property
    def repository(self) -> Repository:
        """Получить репозиторий для прямого доступа к данным."""
        return self._repository

    # ── Accounts ──────────────────────────────────────────────

    def get_accounts(self) -> Sequence[Account]:
        """Получить список всех доступных счетов."""
        return self._repository.get_accounts()

    def get_user_info(self) -> UserInfo:
        """Получить информацию о пользователе."""
        return self._repository.get_info()

    # ── Portfolio ─────────────────────────────────────────────

    def get_portfolio(self, account_id: str) -> Portfolio:
        """Получить портфель по ID счёта."""
        return self._repository.get_portfolio(account_id)

    def portfolio_summary(self, account_id: str) -> PortfolioSummary:
        """Получить сводку по портфелю."""
        portfolio = self.get_portfolio(account_id)
        return Statistics.portfolio_summary(portfolio)

    def position_allocations(
        self, account_id: str
    ) -> list[PositionAllocation]:
        """Получить распределение позиций по типам."""
        portfolio = self.get_portfolio(account_id)
        return Statistics.position_allocations(portfolio)

    def top_positions(
        self, account_id: str, top_n: int = 5
    ) -> list[PortfolioPosition]:
        """Получить топ N позиций по стоимости."""
        portfolio = self.get_portfolio(account_id)
        return Statistics.top_positions(portfolio.positions, top_n)

    def diversification_score(
        self, account_id: str
    ) -> Decimal:
        """Получить индекс диверсификации портфеля."""
        portfolio = self.get_portfolio(account_id)
        return Statistics.diversification_score(portfolio.positions)

    # ── Instruments ──────────────────────────────────────────

    def get_shares(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список акций."""
        return self._repository.get_shares(instrument_status)

    def get_bonds(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список облигаций."""
        return self._repository.get_bonds(instrument_status)

    def get_etfs(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список ETF."""
        return self._repository.get_etfs(instrument_status)

    def get_currencies(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список валют."""
        return self._repository.get_currencies(instrument_status)

    def get_futures(
        self, instrument_status: str = "INSTRUMENT_STATUS_BASE"
    ) -> list[Instrument]:
        """Получить список фьючерсов."""
        return self._repository.get_futures(instrument_status)

    def find_instrument(
        self, query: str, instrument_kind: str | None = None
    ) -> list[InstrumentShort]:
        """Найти инструмент по строке поиска."""
        return self._repository.find_instrument(query, instrument_kind)

    # ── Market Data ──────────────────────────────────────────

    def get_order_book(
        self, figi: str = "", depth: int = 10, instrument_id: str = ""
    ) -> OrderBook:
        """Получить биржевой стакан."""
        return self._repository.get_order_book(
            figi=figi, depth=depth, instrument_id=instrument_id
        )

    def get_last_prices(
        self,
        figi: list[str] | None = None,
        instrument_id: list[str] | None = None,
    ) -> list[LastPrice]:
        """Получить последние цены."""
        return self._repository.get_last_prices(
            figi=figi, instrument_id=instrument_id
        )

    # ── Candles ──────────────────────────────────────────────

    def get_candles(
        self,
        figi: str = "",
        from_: datetime | None = None,
        to: datetime | None = None,
        interval: str = "CANDLE_INTERVAL_DAY",
        instrument_id: str = "",
    ) -> list[Candle]:
        """Получить свечи по инструменту."""
        return self._repository.get_candles(
            figi=figi,
            from_=from_,
            to=to,
            interval=interval,
            instrument_id=instrument_id,
        )

    # ── Cache Management ─────────────────────────────────────

    def invalidate_portfolio(self, account_id: str) -> None:
        """Инвалидировать кэш портфеля."""
        self._repository.invalidate_portfolio(account_id)

    def invalidate_cache(self) -> None:
        """Полностью очистить кэш."""
        self._repository.invalidate_all()

    # ── Lifecycle ────────────────────────────────────────────

    def close(self) -> None:
        """Закрыть соединение с API."""
        if hasattr(self._sdk_client, "__exit__"):
            self._sdk_client.__exit__(None, None, None)

    def __enter__(self) -> InvestClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

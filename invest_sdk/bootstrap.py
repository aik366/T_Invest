from __future__ import annotations

from invest_sdk.client import InvestClient
from invest_sdk.repository import Repository
from invest_sdk.services import (
    AccountService,
    CandleService,
    InstrumentService,
    MarketService,
    PortfolioService,
)


def create_client(
    token: str,
    *,
    sandbox_token: str | None = None,
    app_name: str | None = None,
    cache_ttl: int = 300,
    use_sandbox: bool = False,
) -> InvestClient:
    """Создать и настроить InvestClient.

    Args:
        token: Токен доступа к API.
        sandbox_token: Токен для песочницы (опционально).
        app_name: Имя приложения.
        cache_ttl: Время жизни кэша в секундах.
        use_sandbox: Использовать песочницу.

    Returns:
        Настроенный экземпляр InvestClient.
    """
    from t_tech.invest import Client as SDKClient
    from t_tech.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX

    target = INVEST_GRPC_API_SANDBOX if use_sandbox else INVEST_GRPC_API
    sdk_client = SDKClient(
        token=token,
        target=target,
        sandbox_token=sandbox_token,
        app_name=app_name,
    )

    return _build_client(sdk_client, cache_ttl)


def create_sandbox_client(
    token: str,
    *,
    app_name: str | None = None,
    cache_ttl: int = 300,
) -> InvestClient:
    """Создать InvestClient для песочницы."""
    return create_client(
        token=token,
        app_name=app_name,
        cache_ttl=cache_ttl,
        use_sandbox=True,
    )


def _build_client(
    sdk_client: object, cache_ttl: int = 300
) -> InvestClient:
    """Собрать InvestClient через DI.

    Создаёт сервисы, репозиторий и клиент,
    связывая их через конструкторы (композиция).
    """
    sdk = sdk_client.__enter__()

    account_service = AccountService(sdk)
    portfolio_service = PortfolioService(sdk)
    instrument_service = InstrumentService(sdk)
    market_service = MarketService(sdk)
    candle_service = CandleService(sdk)

    repository = Repository(
        accounts=account_service,
        portfolio=portfolio_service,
        instruments=instrument_service,
        market=market_service,
        candles=candle_service,
        cache_ttl=cache_ttl,
    )

    return InvestClient(
        repository=repository,
        sdk_services=sdk,
        sdk_client=sdk_client,
    )

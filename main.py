from __future__ import annotations

import os
import warnings

import certifi

warnings.simplefilter("ignore", DeprecationWarning)

os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
os.environ["SSL_TBANK_VERIFY"] = "true"
from datetime import datetime, timezone
from decimal import Decimal

from t_tech.invest.schemas import (
    GetOperationsByCursorRequest,
    OperationState,
    OperationType,
)

from invest_sdk.bootstrap import create_client


def load_token() -> str:
    """Загрузить токен из .env или переменной окружения."""
    try:
        with open(".env", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("INVEST_TOKEN="):
                    return line.split("=", 1)[1]
    except FileNotFoundError:
        pass
    return os.environ.get("INVEST_TOKEN", "")


def main() -> None:
    token = load_token()
    if not token:
        print("Ошибка: токен не найден.")
        print("Создайте файл .env со строкой: INVEST_TOKEN=ваш_токен")
        return

    with create_client(token, cache_ttl=30) as client:
        accounts = client.get_accounts()

        if not accounts:
            return

        total_value = Decimal("0")
        total_yield = Decimal("0")
        total_daily_yield = Decimal("0")
        for acc in accounts:
            if acc.type not in ("ACCOUNT_TYPE_TINKOFF", "ACCOUNT_TYPE_TINKOFF_IIS"):
                continue

            print(f"\n{acc.name}")
            summary = client.portfolio_summary(acc.id)
            portfolio = client.get_portfolio(acc.id)

            print(f"  {'Тикер':<10} {'Кол-во':<10} {'Средняя':<12} {'Текущая':<12} {'Доход':<12} {'За день':<12}")
            for pos in portfolio.positions:
                if pos.ticker.startswith("RUB"):
                    continue
                yield_val = pos.expected_yield
                daily_yield = pos.daily_yield
                print(f"  {pos.ticker:<10} {pos.quantity:<10.2f} {pos.average_price:<12.2f} {pos.current_price:<12.2f} {yield_val:<+12.2f} {daily_yield:<+12.2f}")

            print(f"  Стоимость: {summary.total_value:,.2f} руб")
            total_value += summary.total_value
            total_yield += sum(
                (pos.expected_yield for pos in portfolio.positions),
                Decimal("0"),
            )
            total_daily_yield += sum(
                (pos.daily_yield for pos in portfolio.positions),
                Decimal("0"),
            )

        

        aggregated: dict[str, dict] = {}
        total_agg_value = Decimal("0")
        for acc in accounts:
            if acc.type not in ("ACCOUNT_TYPE_TINKOFF", "ACCOUNT_TYPE_TINKOFF_IIS"):
                continue
            portfolio = client.get_portfolio(acc.id)
            for pos in portfolio.positions:
                if pos.ticker.startswith("RUB"):
                    continue
                if pos.ticker not in aggregated:
                    aggregated[pos.ticker] = {
                        "quantity": Decimal("0"),
                        "total_cost": Decimal("0"),
                        "current_price": pos.current_price,
                        "total_yield": Decimal("0"),
                        "total_daily_yield": Decimal("0"),
                    }
                agg = aggregated[pos.ticker]
                agg["quantity"] += pos.quantity
                agg["total_cost"] += pos.average_price * pos.quantity
                agg["total_yield"] += pos.expected_yield
                agg["total_daily_yield"] += pos.daily_yield

        print("\nМой капитал")
        print(f"  {'Тикер':<10} {'Кол-во':<10} {'Средняя':<12} {'Текущая':<12} {'Доход':<12} {'За день':<12}")
        for ticker, agg in aggregated.items():
            avg_price = agg["total_cost"] / agg["quantity"] if agg["quantity"] else Decimal("0")
            print(f"  {ticker:<10} {agg['quantity']:<10.2f} {avg_price:<12.2f} {agg['current_price']:<12.2f} {agg['total_yield']:<+12.2f} {agg['total_daily_yield']:<+12.2f}")
            total_agg_value += agg["current_price"] * agg["quantity"]

        print(f"  Стоимость: {total_agg_value:,.2f} руб")
        
        print(f"\n  Суммарная стоимость: {total_value:,.2f} руб")
        print(f"  Суммарный доход:     {total_yield:+,.2f} руб")
        print(f"  Суммарный доход за день: {total_daily_yield:+,.2f} руб")

        total_dividends = Decimal("0")
        for acc in accounts:
            if acc.type not in ("ACCOUNT_TYPE_TINKOFF", "ACCOUNT_TYPE_TINKOFF_IIS"):
                continue
            cursor = ""
            while True:
                req = GetOperationsByCursorRequest(
                    account_id=acc.id,
                    from_=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    to=datetime.now(timezone.utc),
                    state=OperationState.OPERATION_STATE_EXECUTED,
                    cursor=cursor or None,
                    limit=100,
                )
                resp = client._sdk.operations.get_operations_by_cursor(req)
                for item in resp.items:
                    if item.type in (21, 43):  # DIVIDEND or DIV_EXT
                        u = getattr(item.payment, "units", 0)
                        n = getattr(item.payment, "nano", 0)
                        total_dividends += Decimal(u) + Decimal(n) / Decimal(1_000_000_000)
                if not resp.has_next:
                    break
                cursor = resp.next_cursor

        dividend_tax = total_dividends * Decimal("0.87")
        print(f"  Дивиденды получено:  {total_dividends:+,.2f} руб ({dividend_tax:+,.2f} руб)")


if __name__ == "__main__":
    main()

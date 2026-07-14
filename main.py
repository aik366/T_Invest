from __future__ import annotations

import os
import warnings

import certifi

warnings.simplefilter("ignore", DeprecationWarning)

os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
os.environ["SSL_TBANK_VERIFY"] = "true"
from datetime import datetime, timezone
from decimal import Decimal
import json
import urllib.request

from t_tech.invest.schemas import (
    GetOperationsByCursorRequest,
    OperationState,
    OperationType,
)

from invest_sdk.bootstrap import create_client

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def _cval(val: Decimal, width: int = 0, comma: bool = False) -> str:
    color = GREEN if val >= 0 else RED
    fmt = f"{val:+,.2f}" if comma else f"{val:<+{width}.2f}"
    return f"{color}{fmt}{RESET}"


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


def fetch_moex_index(index_ticker: str = "IMOEX") -> tuple[float, float] | None:
    url = f"https://iss.moex.com/iss/engines/stock/markets/index/securities/{index_ticker}.json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        md = data.get("marketdata", {})
        cols = md.get("columns", [])
        rows = md.get("data", [])
        if rows:
            row = rows[0]
            return row[cols.index("CURRENTVALUE")], row[cols.index("LASTCHANGEPRC")]
    except Exception:
        return None


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

        # ── Collect figi→ticker mapping & dividends/coupons per (account, figi) ──
        figi_to_ticker: dict[str, str] = {}
        div_by_figi: dict[str, Decimal] = {}
        div_by_acc_figi: dict[tuple[str, str], Decimal] = {}
        total_div_gross = Decimal("0")
        total_coupon_gross = Decimal("0")
        total_sale_profit = Decimal("0")
        total_commission = Decimal("0")
        total_deposits = Decimal("0")

        for acc in accounts:
            if acc.type not in ("ACCOUNT_TYPE_TINKOFF", "ACCOUNT_TYPE_TINKOFF_IIS"):
                continue

            portfolio = client.get_portfolio(acc.id)
            for pos in portfolio.positions:
                if not pos.ticker.startswith("RUB") and pos.figi:
                    if pos.figi not in figi_to_ticker:
                        figi_to_ticker[pos.figi] = pos.ticker

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
                        figi = getattr(item, "figi", "") or getattr(item, "instrument_uid", "")
                        u = getattr(item.payment, "units", 0)
                        n = getattr(item.payment, "nano", 0)
                        amount = Decimal(u) + Decimal(n) / Decimal(1_000_000_000)
                        div_by_figi[figi] = div_by_figi.get(figi, Decimal("0")) + amount
                        div_by_acc_figi[(acc.id, figi)] = div_by_acc_figi.get((acc.id, figi), Decimal("0")) + amount
                        total_div_gross += amount
                    elif item.type == 23:  # COUPON
                        u = getattr(item.payment, "units", 0)
                        n = getattr(item.payment, "nano", 0)
                        total_coupon_gross += Decimal(u) + Decimal(n) / Decimal(1_000_000_000)
                    elif item.type in (22, 7, 18):  # SELL, SELL_CARD, SELL_MARGIN
                        y = getattr(item, "yield_", None)
                        if y is not None:
                            u = getattr(y, "units", 0)
                            n = getattr(y, "nano", 0)
                            total_sale_profit += Decimal(u) + Decimal(n) / Decimal(1_000_000_000)
                    c = getattr(item, "commission", None)
                    if c is not None:
                        u = getattr(c, "units", 0)
                        n = getattr(c, "nano", 0)
                        total_commission += Decimal(u) + Decimal(n) / Decimal(1_000_000_000)
                    if item.type in (1, 54, 51, 60):  # INPUT, INPUT_ACQUIRING, INPUT_SWIFT, INP_MULTI
                        u = getattr(item.payment, "units", 0)
                        n = getattr(item.payment, "nano", 0)
                        total_deposits += Decimal(u) + Decimal(n) / Decimal(1_000_000_000)
                if not resp.has_next:
                    break
                cursor = resp.next_cursor

        # ticker → total dividends (only tickers still in portfolio)
        ticker_to_div: dict[str, Decimal] = {}
        for figi, amount in div_by_figi.items():
            ticker = figi_to_ticker.get(figi, "")
            if ticker:
                ticker_to_div[ticker] = ticker_to_div.get(ticker, Decimal("0")) + amount

        DIV_TAX = Decimal("0.87")

        # ── Per-account tables ──
        total_value = Decimal("0")
        total_yield = Decimal("0")
        total_daily_yield = Decimal("0")
        for acc in accounts:
            if acc.type not in ("ACCOUNT_TYPE_TINKOFF", "ACCOUNT_TYPE_TINKOFF_IIS"):
                continue

            print(f"\n{acc.name}")
            summary = client.portfolio_summary(acc.id)
            portfolio = client.get_portfolio(acc.id)

            print(f"  {'Тикер':<10} {'Кол-во':<10} {'Средняя':<12} {'Текущая':<14} {'Дивиденды':<12} {'Доход':<12} {'За день':<12}")
            for pos in portfolio.positions:
                if pos.ticker.startswith("RUB"):
                    continue
                yield_val = pos.expected_yield
                daily_yield = pos.daily_yield
                div_gross = div_by_acc_figi.get((acc.id, pos.figi), Decimal("0"))
                div_net = div_gross * DIV_TAX
                adj_yield = yield_val + div_net
                print(f"  {pos.ticker:<10} {pos.quantity:<10.2f} {pos.average_price:<12.2f} {pos.current_price:<14.2f} {_cval(div_net, 12)} {_cval(adj_yield, 12)} {_cval(daily_yield, 12)}")
                total_yield += yield_val

            print(f"  Стоимость: {summary.total_value:,.2f} руб")
            total_value += summary.total_value
            total_daily_yield += sum(
                (pos.daily_yield for pos in portfolio.positions),
                Decimal("0"),
            )

        # ── Aggregated table (Мой капитал) ──
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
        print(f"  {'Тикер':<10} {'Кол-во':<10} {'Средняя':<12} {'Текущая':<14} {'Дивиденды':<12} {'Доход':<12} {'За день':<12}")
        for ticker, agg in aggregated.items():
            avg_price = agg["total_cost"] / agg["quantity"] if agg["quantity"] else Decimal("0")
            div_gross = ticker_to_div.get(ticker, Decimal("0"))
            div_net = div_gross * DIV_TAX
            adj_yield = agg["total_yield"] + div_net
            print(f"  {ticker:<10} {agg['quantity']:<10.2f} {avg_price:<12.2f} {agg['current_price']:<14.2f} {_cval(div_net, 12)} {_cval(adj_yield, 12)} {_cval(agg['total_daily_yield'], 12)}")
            total_agg_value += agg["current_price"] * agg["quantity"]

        print(f"  Стоимость: {total_agg_value:,.2f} руб")

        dividend_tax = total_div_gross * DIV_TAX
        print(f"\n  Суммарная стоимость: {total_value:,.2f} руб")
        coupon_tax = total_coupon_gross * DIV_TAX
        total_yield += dividend_tax + total_coupon_gross + total_sale_profit - total_commission
        print(f"  Суммарный доход:    {_cval(total_yield, comma=True)} руб")
        print(f"  Доход за день:      {_cval(total_daily_yield, comma=True)} руб")

        print(f"  Дивиденды получено: {_cval(dividend_tax, comma=True)} руб")
        print(f"  Купонов получено:   {_cval(total_coupon_gross, comma=True)} руб")
        print(f"  Прибыль от продаж:  {_cval(total_sale_profit, comma=True)} руб")
        print(f"  Уплачено комиссий:  {_cval(total_commission, comma=True)} руб")
        print(f"  Пополнения:         {_cval(total_deposits, comma=True)} руб")

        index_data = fetch_moex_index()
        if index_data:
            value, change_pct = index_data
            color = GREEN if change_pct >= 0 else RED
            print(f"  Индекс МосБиржи:    {color}{int(value)} ({change_pct:+.2f}%){RESET}")

if __name__ == "__main__":
    main()

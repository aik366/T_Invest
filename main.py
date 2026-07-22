from __future__ import annotations

import os
import warnings

import certifi

warnings.simplefilter("ignore", DeprecationWarning)

os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
os.environ["SSL_TBANK_VERIFY"] = "true"
from datetime import datetime, timezone
from decimal import Decimal

from t_tech.invest import Client
from t_tech.invest.schemas import (
    GetOperationsByCursorRequest,
    InstrumentIdType,
    OperationState,
    OperationType,
)

from invest_sdk.bootstrap import create_client

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
PURPLE = "\033[96m"
ORANGE = "\033[91m"
RESET = "\033[0m"


def _cval(val: Decimal, width: int = 0, comma: bool = False) -> str:
    color = GREEN if val >= 0 else RED
    fmt = f"{val:+,.2f}" if comma else f"{val:<+{width}.2f}"
    return f"{color}{fmt}{RESET}"


from t_tech.invest.schemas import CandleInterval
from datetime import timedelta

def _get_price_change(client, ticker: str, class_code: str = "") -> tuple[float | None, float | None]:
    try:
        response = client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            id=ticker,
            class_code=class_code,
        )
    except Exception:
        return None, None
    instrument = response.instrument
    if instrument is None:
        return None, None

    ob = client.market_data.get_order_book(figi=instrument.figi, depth=1)
    value = ob.last_price.units + ob.last_price.nano / 1_000_000_000

    # Получаем цену закрытия предыдущего дня из дневных свечей
    close = None
    try:
        now = datetime.now(timezone.utc)
        candles_resp = client.market_data.get_candles(
            figi=instrument.figi,
            from_=now - timedelta(days=10),
            to=now,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        )
        if candles_resp.candles:
            # Ищем последнюю завершенную свечу (предыдущий торговый день)
            for candle in reversed(candles_resp.candles):
                if candle.time.date() < now.date():
                    close = candle.close.units + candle.close.nano / 1_000_000_000
                    break
    except Exception:
        pass

    # Fallback на close_price из стакана, если свечи не получились
    if close is None or close == 0:
        close = ob.close_price.units + ob.close_price.nano / 1_000_000_000

    change_pct = (value - close) / close * 100 if close else 0
    return value, change_pct


def print_market_price(client, ticker: str, class_code: str = "", fmt_int: bool = False, label: str = "") -> None:
    value, change_pct = _get_price_change(client, ticker, class_code)
    if value is None:
        print(f"  {label or ticker:<20} не найден")
        return
    color = GREEN if change_pct >= 0 else RED
    val_str = f"{int(value)}" if fmt_int else f"{value:.2f}"
    print(f"  {label or ticker:<20} {color}{val_str} ({change_pct:+.2f}%){RESET}")


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

        # ── Fetch last & close prices for daily change ──
        last_by_figi: dict[str, Decimal] = {}
        close_by_figi: dict[str, Decimal] = {}
        for figi in figi_to_ticker:
            try:
                ob = client._sdk.market_data.get_order_book(figi=figi, depth=1)
                last_by_figi[figi] = Decimal(ob.last_price.units) + Decimal(ob.last_price.nano) / Decimal(1_000_000_000)
                close_by_figi[figi] = Decimal(ob.close_price.units) + Decimal(ob.close_price.nano) / Decimal(1_000_000_000)
            except Exception:
                pass

        # ── Per-account tables ──
        total_value = Decimal("0")
        total_yield = Decimal("0")
        total_daily_yield = Decimal("0")
        for acc in accounts:
            if acc.type not in ("ACCOUNT_TYPE_TINKOFF", "ACCOUNT_TYPE_TINKOFF_IIS"):
                continue

            print(f"\n{PURPLE}{acc.name}{RESET}")
            summary = client.portfolio_summary(acc.id)
            portfolio = client.get_portfolio(acc.id)

            print(f"  {YELLOW}{'Тикер':<10} {'Кол-во':<10} {'Средняя':<12} {'Текущая':<12} {'Дивиденды':<12} {'Доход':<12} {'За день':<12}{RESET}")
            for pos in portfolio.positions:
                if pos.ticker.startswith("RUB"):
                    continue
                yield_val = pos.expected_yield
                daily_yield = pos.daily_yield              
                div_gross = div_by_acc_figi.get((acc.id, pos.figi), Decimal("0"))
                div_net = div_gross * DIV_TAX
                adj_yield = yield_val + div_net
                last = last_by_figi.get(pos.figi, pos.current_price)
                print(f"  {pos.ticker:<10} {pos.quantity:<10.2f} {pos.average_price:<12.2f} {last:<12.2f} {_cval(div_net, 12)} {_cval(adj_yield, 12)} {_cval(daily_yield, 12)}")
                total_yield += yield_val

            print(f"  Стоимость: {BLUE}{summary.total_value:,.2f}{RESET} руб")
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
                        "figi": pos.figi,
                    }
                agg = aggregated[pos.ticker]
                agg["quantity"] += pos.quantity
                agg["total_cost"] += pos.average_price * pos.quantity
                agg["total_yield"] += pos.expected_yield
                agg["total_daily_yield"] += pos.daily_yield

        print(f"\n{PURPLE}Мой капитал{RESET}")
        print(f"  {YELLOW}{'Тикер':<10} {'Кол-во':<10} {'Средняя':<12} {'Текущая':<12} {'Дивиденды':<12} {'Доход':<12} {'За день':<12}{RESET}")
        list_ticer = []
        for ticker, agg in aggregated.items():
            avg_price = agg["total_cost"] / agg["quantity"] if agg["quantity"] else Decimal("0")
            div_gross = ticker_to_div.get(ticker, Decimal("0"))
            div_net = div_gross * DIV_TAX
            adj_yield = agg["total_yield"] + div_net
            last = last_by_figi.get(agg['figi'], agg['current_price'])
            print(f"  {ticker:<10} {agg['quantity']:<10.2f} {avg_price:<12.2f} {last:<12.2f} {_cval(div_net, 12)} {_cval(adj_yield, 12)} {_cval(agg['total_daily_yield'], 12)}")
            list_ticer.append(ticker)

        print(f"  Стоимость: {BLUE}{total_value:,.2f}{RESET} руб")

        dividend_tax = total_div_gross * DIV_TAX
        print(f"\n  Суммарная стоимость: {BLUE}{total_value:,.2f}{RESET} руб")
        coupon_tax = total_coupon_gross * DIV_TAX
        total_yield += dividend_tax + total_coupon_gross + total_sale_profit - total_commission
        print(f"  Суммарный доход:    {_cval(total_yield, comma=True)} руб")
        print(f"  Доход за день:      {_cval(total_daily_yield, comma=True)} руб")

        print(f"  Дивиденды получено: {_cval(dividend_tax, comma=True)} руб")
        print(f"  Купонов получено:   {_cval(total_coupon_gross, comma=True)} руб")
        print(f"  Прибыль от продаж:  {_cval(total_sale_profit, comma=True)} руб")
        print(f"  Уплачено комиссий:  {_cval(total_commission, comma=True)} руб")
        print(f"  Пополнения:         {_cval(total_deposits, comma=True)} руб\n")

        with Client(token) as moex_client:
            print_market_price(moex_client, "IMOEXF", "SPBFUT", fmt_int=True, label="МосБиржа")
            for ticer in list_ticer:
                print_market_price(moex_client, ticer, "TQBR")

if __name__ == "__main__":
    main()
    num = 1
    while num:
        num = int(input(f"\n  Для выхода 0: \n  Обновить   1: "))
        if num:
            main()

"""Интеграционный тест: проверка маппинга protobuf → модели.

Запуск:
    $env:INVEST_TOKEN="токен"
    python -m invest_sdk.tests.integration_test

    # Для песочницы:
    $env:INVEST_SANDBOX_TOKEN="токен_песочницы"
    python -m invest_sdk.tests.integration_test --sandbox
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from invest_sdk.bootstrap import create_client


def format_money(amount: Decimal, currency: str = "rub") -> str:
    return f"{amount:,.2f} {currency.upper()}"


def test_accounts(client) -> int:
    """Проверить get_accounts(). Вернуть количество аккаунтов."""
    print("\n=== 1. Получение счетов (get_accounts) ===")
    accounts = client.get_accounts()
    print(f"  Найдено счетов: {len(accounts)}")

    if not accounts:
        print("  ! Нет доступных счетов")
        return 0

    for acc in accounts:
        print(f"  - {acc.id}: {acc.name} ({acc.type}, {acc.status})")
        assert isinstance(acc.id, str), "id должен быть строкой"
        assert isinstance(acc.name, str), "name должен быть строкой"
        assert acc.id, "id не должен быть пустым"

    print("  [OK] get_accounts работает корректно")
    return len(accounts)


def test_portfolio(client, account_id: str) -> None:
    """Проверить portfolio_summary() для указанного счёта."""
    print(f"\n=== 2. Сводка портфеля (portfolio_summary) для {account_id} ===")
    try:
        summary = client.portfolio_summary(account_id)
        print(f"  Инвестировано:     {format_money(summary.total_invested)}")
        print(f"  Стоимость:         {format_money(summary.total_value)}")
        print(f"  Доход:             {format_money(summary.total_yield)}")
        print(f"  Доходность:        {summary.total_yield_percent:.2f}%")
        print(f"  Позиций:           {summary.position_count}")
        print(f"  Прибыльных:        {summary.profitable_count}")
        print(f"  Убыточных:         {summary.unprofitable_count}")

        assert isinstance(summary.total_value, Decimal)
        assert isinstance(summary.position_count, int)
        print("  [OK] portfolio_summary работает корректно")
    except Exception as e:
        print(f"  ! Ошибка portfolio_summary: {e}")
        traceback.print_exc()


def test_positions(client, account_id: str) -> None:
    """Проверить get_portfolio() и детальные позиции."""
    print(f"\n=== 3. Детальные позиции портфеля ===")
    portfolio = client.get_portfolio(account_id)
    print(f"  Всего позиций: {len(portfolio.positions)}")
    print(f"  Общая стоимость: {format_money(portfolio.total_value)}")
    print(f"  Валюта портфеля: {portfolio.currency}")

    for pos in portfolio.positions[:10]:
        print(f"  - {pos.ticker:>8} | {pos.name:<20} | "
              f"qty={pos.quantity:<8.2f} | "
              f"avg={pos.average_price:<10.2f} | "
              f"cur={pos.current_price:<10.2f} | "
              f"yield={pos.expected_yield:<10.2f}")
        assert isinstance(pos.ticker, str)
        assert isinstance(pos.quantity, Decimal)
        assert isinstance(pos.average_price, Decimal)
        assert isinstance(pos.current_price, Decimal)
        assert isinstance(pos.expected_yield, Decimal)

    print("  [OK] get_portfolio работает корректно")


def test_instruments(client) -> None:
    """Проверить получение инструментов."""
    print("\n=== 4. Получение инструментов ===")
    try:
        shares = client.get_shares("INSTRUMENT_STATUS_BASE")
        print(f"  Акций: {len(shares)}")

        etfs = client.get_etfs()
        print(f"  ETF: {len(etfs)}")

        bonds = client.get_bonds()
        print(f"  Облигаций: {len(bonds)}")

        if shares:
            sample = shares[0]
            print(f"  Пример: {sample.ticker} ({sample.name})")
            assert isinstance(sample.ticker, str)
            assert isinstance(sample.figi, str)
            assert isinstance(sample.currency, str)
            print("  [OK] get_instruments работает корректно")
    except Exception as e:
        print(f"  ! Ошибка при получении инструментов: {e}")


def test_order_book(client) -> None:
    """Проверить получение стакана."""
    print("\n=== 5. Получение стакана ===")
    shares = client.get_shares()
    if not shares:
        print("  ! Нет акций для теста стакана")
        return

    share = shares[0]
    try:
        ob = client.get_order_book(figi=share.figi, depth=5)
        print(f"  FIGI: {ob.figi}")
        print(f"  Глубина: {ob.depth}")
        print(f"  Last price: {ob.last_price}")
        print(f"  Bids: {len(ob.bids)}, Asks: {len(ob.asks)}")
        if ob.bids:
            print(f"  Best bid: {ob.bids[0][0]} x {ob.bids[0][1]}")
        if ob.asks:
            print(f"  Best ask: {ob.asks[0][0]} x {ob.asks[0][1]}")
        assert isinstance(ob.last_price, Decimal)
        print("  [OK] get_order_book работает корректно")
    except Exception as e:
        print(f"  ! Ошибка стакана: {e}")


def test_candles(client) -> None:
    """Проверить получение свечей."""
    print("\n=== 6. Получение свечей ===")
    shares = client.get_shares()
    if not shares:
        print("  ! Нет акций для теста свечей")
        return

    share = shares[0]
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    try:
        candles = client.get_candles(
            figi=share.figi,
            from_=week_ago,
            to=now,
            interval="CANDLE_INTERVAL_DAY",
        )
        print(f"  Свечей за 7 дней: {len(candles)}")
        if candles:
            c = candles[0]
            print(f"  Первая: {c.time} O={c.open} H={c.high} L={c.low} C={c.close} V={c.volume}")
            assert isinstance(c.open, Decimal)
            assert isinstance(c.close, Decimal)
            assert isinstance(c.volume, int)
            print("  [OK] get_candles работает корректно")
    except Exception as e:
        print(f"  ! Ошибка свечей: {e}")


def test_user_info(client) -> None:
    """Проверить получение информации о пользователе."""
    print("\n=== 7. Информация о пользователе ===")
    try:
        info = client.get_user_info()
        print(f"  Тариф: {info.tariff}")
        print(f"  Квалифицированный инвестор: {info.qualified_status}")
        print(f"  Премиум статус: {info.premium_status}")
        print("  [OK] get_user_info работает корректно")
    except Exception as e:
        print(f"  ! Ошибка: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Integration test for invest_sdk")
    parser.add_argument("--sandbox", action="store_true", help="Use sandbox API")
    parser.add_argument("--token", type=str, default=None, help="API token")
    args = parser.parse_args()

    token = args.token or os.environ.get(
        "INVEST_SANDBOX_TOKEN" if args.sandbox else "INVEST_TOKEN",
        "",
    )
    if not token:
        print("Ошибка: не задан токен.")
        print("Установите переменную окружения INVEST_TOKEN или INVEST_SANDBOX_TOKEN")
        sys.exit(1)

    env_type = "SANDBOX" if args.sandbox else "PRODUCTION"
    print(f"Запуск интеграционного теста в режиме: {env_type}")
    print(f"Токен: {token[:4]}...{token[-4:]}")

    try:
        client = create_client(token, use_sandbox=args.sandbox, cache_ttl=10)
    except Exception as e:
        print(f"Ошибка создания клиента: {e}")
        traceback.print_exc()
        sys.exit(1)

    with client:
        num_accounts = test_accounts(client)
        if num_accounts == 0:
            print("\nНет счетов для дальнейших тестов.")
            return

        accounts = client.get_accounts()
        account_id = accounts[0].id

        test_portfolio(client, account_id)
        test_positions(client, account_id)
        test_user_info(client)
        test_instruments(client)
        test_order_book(client)
        test_candles(client)

    print("\n=== Интеграционный тест завершён ===")


if __name__ == "__main__":
    main()

"""Пример базового использования библиотеки invest_sdk.

Перед запуском установите токен:
    $env:INVEST_TOKEN="ваш_токен"

Запуск:
    python -m invest_sdk.examples.basic_usage
"""

from __future__ import annotations

import os

from invest_sdk.bootstrap import create_client


def main() -> None:
    token = os.environ.get("INVEST_TOKEN", "")
    if not token:
        print("Установите переменную окружения INVEST_TOKEN")
        return

    with create_client(token, use_sandbox=True) as client:
        # Получить список счетов
        accounts = client.get_accounts()
        print(f"Найдено счетов: {len(accounts)}")

        if accounts:
            # Отрисовать сводку по первому счёту
            summary = client.portfolio_summary(accounts[0].id)
            print(f"Стоимость портфеля: {summary.total_value}")
            print(f"Доходность: {summary.total_yield_percent:.2f}%")
            print(f"Позиций: {summary.position_count}")


if __name__ == "__main__":
    main()

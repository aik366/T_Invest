from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TextIO


class Printer:
    """Форматирование и вывод данных.

    Только отображение. Никакой математики. Никаких вычислений.
    Никакого Decimal в логике форматирования.
    """

    def __init__(self, output: TextIO | None = None) -> None:
        self._output = output

    def _write(self, text: str) -> None:
        if self._output is not None:
            self._output.write(text + "\n")
        else:
            print(text)

    def print_accounts(self, accounts: Sequence[dict]) -> None:
        """Вывести список счетов."""
        if not accounts:
            self._write("Нет доступных счетов.")
            return

        self._write(f"{'ID':<40} {'Название':<30} {'Тип':<20} {'Статус':<15}")
        self._write("-" * 105)
        for acc in accounts:
            self._write(
                f"{acc.get('id', ''):<40} "
                f"{acc.get('name', ''):<30} "
                f"{acc.get('type', ''):<20} "
                f"{acc.get('status', ''):<15}"
            )
        self._write("")

    def print_portfolio_summary(self, data: dict) -> None:
        """Вывести сводку по портфелю."""
        self._write("=== Сводка по портфелю ===")
        self._write(f"Общая стоимость: {data.get('total_value', 'N/A')}")
        self._write(f"Инвестировано: {data.get('total_invested', 'N/A')}")
        self._write(f"Доход: {data.get('total_yield', 'N/A')}")
        self._write(f"Доходность: {data.get('total_yield_percent', 'N/A')}%")
        self._write(f"Позиций: {data.get('position_count', 0)}")
        self._write(
            f"Прибыльных: {data.get('profitable_count', 0)} | "
            f"Убыточных: {data.get('unprofitable_count', 0)}"
        )
        self._write(f"Диверсификация: {data.get('diversification_score', 'N/A')}%")
        self._write("")

    def print_positions(self, positions: Sequence[dict]) -> None:
        """Вывести список позиций."""
        if not positions:
            self._write("Нет позиций.")
            return

        self._write(
            f"{'Тикер':<10} {'Название':<25} {'Кол-во':<12} "
            f"{'Ср. цена':<14} {'Цена':<14} {'Стоимость':<14} {'Доход':<14}"
        )
        self._write("-" * 103)

        for pos in positions:
            self._write(
                f"{pos.get('ticker', ''):<10} "
                f"{pos.get('name', ''):<25} "
                f"{str(pos.get('quantity', '')):<12} "
                f"{str(pos.get('average_price', '')):<14} "
                f"{str(pos.get('current_price', '')):<14} "
                f"{str(pos.get('total_value', '')):<14} "
                f"{str(pos.get('expected_yield', '')):<14}"
            )
        self._write("")

    def print_candles(self, candles: Sequence[dict]) -> None:
        """Вывести свечи."""
        if not candles:
            self._write("Нет данных свечей.")
            return

        self._write(
            f"{'Дата':<25} {'Open':<14} {'High':<14} {'Low':<14} "
            f"{'Close':<14} {'Volume':<12}"
        )
        self._write("-" * 93)

        for c in candles:
            self._write(
                f"{str(c.get('time', '')):<25} "
                f"{str(c.get('open', '')):<14} "
                f"{str(c.get('high', '')):<14} "
                f"{str(c.get('low', '')):<14} "
                f"{str(c.get('close', '')):<14} "
                f"{str(c.get('volume', '')):<12}"
            )
        self._write("")

    def print_instruments(self, instruments: Sequence[dict]) -> None:
        """Вывести список инструментов."""
        if not instruments:
            self._write("Нет инструментов.")
            return

        self._write(
            f"{'Тикер':<10} {'Название':<35} {'Тип':<12} "
            f"{'Валюта':<8} {'Лот':<6}"
        )
        self._write("-" * 71)

        for inst in instruments:
            self._write(
                f"{inst.get('ticker', ''):<10} "
                f"{inst.get('name', ''):<35} "
                f"{inst.get('instrument_type', ''):<12} "
                f"{inst.get('currency', ''):<8} "
                f"{str(inst.get('lot', '')):<6}"
            )
        self._write("")

    def print_order_book(self, data: dict) -> None:
        """Вывести стакан."""
        self._write(f"FIGI: {data.get('figi', 'N/A')}")
        self._write(f"Глубина: {data.get('depth', 0)}")
        self._write(f"Последняя цена: {data.get('last_price', 'N/A')}")
        self._write(f"Цена закрытия: {data.get('close_price', 'N/A')}")
        self._write("")

        asks = data.get("asks", [])
        bids = data.get("bids", [])

        if asks:
            self._write("=== АСК (продажа) ===")
            self._write(f"{'Цена':<20} {'Объём':<12}")
            for price, qty in asks[:5]:
                self._write(f"{str(price):<20} {str(qty):<12}")
            self._write("")

        if bids:
            self._write("=== БИД (покупка) ===")
            self._write(f"{'Цена':<20} {'Объём':<12}")
            for price, qty in bids[:5]:
                self._write(f"{str(price):<20} {str(qty):<12}")
            self._write("")

    def print_statistics(self, stats: dict) -> None:
        """Вывести статистику."""
        self._write("=== Статистика ===")
        for key, value in stats.items():
            key_display = key.replace("_", " ").capitalize()
            self._write(f"{key_display:<25}: {value}")
        self._write("")

    def print_message(self, message: str) -> None:
        """Вывести простое сообщение."""
        self._write(message)

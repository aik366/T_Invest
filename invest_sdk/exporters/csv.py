from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvExporter:
    """Экспорт данных в CSV."""

    @staticmethod
    def export(
        data: list[dict[str, Any]],
        file_path: str | Path,
        *,
        fieldnames: list[str] | None = None,
        delimiter: str = ",",
    ) -> Path:
        """Экспортировать список словарей в CSV файл.

        Args:
            data: Данные для экспорта.
            file_path: Путь к файлу.
            fieldnames: Имена полей (по умолчанию — ключи первого элемента).
            delimiter: Разделитель.

        Returns:
            Путь к созданному файлу.
        """
        path = Path(file_path)
        fieldnames = fieldnames or (list(data[0].keys()) if data else [])

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=fieldnames, delimiter=delimiter
            )
            writer.writeheader()
            writer.writerows(data)

        return path

    @staticmethod
    def export_positions(
        positions: list[dict[str, Any]],
        file_path: str | Path,
    ) -> Path:
        """Экспортировать позиции портфеля в CSV."""
        fields = [
            "ticker", "name", "instrument_type", "quantity",
            "average_price", "current_price", "total_value",
            "expected_yield", "currency",
        ]
        return CsvExporter.export(
            positions, file_path, fieldnames=fields
        )

    @staticmethod
    def export_candles(
        candles: list[dict[str, Any]],
        file_path: str | Path,
    ) -> Path:
        """Экспортировать свечи в CSV."""
        fields = [
            "time", "open", "high", "low", "close",
            "volume", "interval", "is_complete",
        ]
        return CsvExporter.export(
            candles, file_path, fieldnames=fields
        )

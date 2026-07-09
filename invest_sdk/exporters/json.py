from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


class _CustomEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class JsonExporter:
    """Экспорт данных в JSON."""

    @staticmethod
    def export(
        data: object,
        file_path: str | Path,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> Path:
        """Экспортировать данные в JSON файл.

        Args:
            data: Данные для экспорта.
            file_path: Путь к файлу.
            indent: Отступ для форматирования.
            ensure_ascii: Экранировать не-ASCII символы.

        Returns:
            Путь к созданному файлу.
        """
        path = Path(file_path)
        with path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                cls=_CustomEncoder,
                indent=indent,
                ensure_ascii=ensure_ascii,
            )
        return path

    @staticmethod
    def export_portfolio(
        portfolio_data: dict[str, Any],
        file_path: str | Path,
    ) -> Path:
        """Экспортировать портфель в JSON."""
        return JsonExporter.export(portfolio_data, file_path)

    @staticmethod
    def export_candles(
        candles_data: list[dict[str, Any]],
        file_path: str | Path,
    ) -> Path:
        """Экспортировать свечи в JSON."""
        return JsonExporter.export(candles_data, file_path)

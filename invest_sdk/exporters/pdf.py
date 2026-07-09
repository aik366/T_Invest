from __future__ import annotations

from pathlib import Path
from typing import Any


class PdfExporter:
    """Экспорт данных в PDF.

    Requires: reportlab
    """

    @staticmethod
    def export(
        data: list[dict[str, Any]],
        file_path: str | Path,
        *,
        title: str = "Report",
    ) -> Path:
        """Экспортировать список словарей в PDF файл.

        Args:
            data: Данные для экспорта.
            file_path: Путь к файлу.
            title: Заголовок отчёта.

        Returns:
            Путь к созданному файлу.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate,
                Table,
                TableStyle,
                Paragraph,
            )
        except ImportError:
            msg = "PdfExporter requires reportlab. Install it with: pip install reportlab"
            raise ImportError(msg) from None

        path = Path(file_path)
        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(title, styles["Title"]))

        if data:
            fieldnames = list(data[0].keys())
            table_data = [fieldnames]

            for row in data:
                table_data.append(
                    [str(row.get(field, "")) for field in fieldnames]
                )

            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ]
                )
            )
            elements.append(table)

        doc.build(elements)
        return path

    @staticmethod
    def export_portfolio(
        portfolio_data: list[dict[str, Any]],
        file_path: str | Path,
    ) -> Path:
        """Экспортировать портфель в PDF."""
        return PdfExporter.export(
            portfolio_data, file_path, title="Portfolio Report"
        )

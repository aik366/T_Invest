from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any


class Chart:
    """Построение графиков.

    Requires: matplotlib
    """

    @staticmethod
    def _check_deps() -> None:
        try:
            import matplotlib  # noqa: F401
            import matplotlib.pyplot  # noqa: F401
        except ImportError:
            msg = "Chart requires matplotlib. Install it with: pip install matplotlib"
            raise ImportError(msg) from None

    @staticmethod
    def candlestick(
        candles_data: Sequence[dict[str, Any]],
        file_path: str | Path,
        *,
        title: str = "Candlestick Chart",
        figsize: tuple[int, int] = (12, 6),
    ) -> Path:
        """Построить график свечей.

        Args:
            candles_data: Список словарей с ключами time, open, high, low, close.
            file_path: Путь для сохранения.
            title: Заголовок графика.
            figsize: Размер фигуры (ширина, высота).

        Returns:
            Путь к сохранённому файлу.
        """
        Chart._check_deps()
        import matplotlib.pyplot as plt
        from matplotlib.dates import date2num

        times = [
            c.get("time", c.get("date", "")) for c in candles_data
        ]
        opens = [float(c.get("open", 0)) for c in candles_data]
        highs = [float(c.get("high", 0)) for c in candles_data]
        lows = [float(c.get("low", 0)) for c in candles_data]
        closes = [float(c.get("close", 0)) for c in candles_data]

        fig, ax = plt.subplots(figsize=figsize)

        for i in range(len(candles_data)):
            color = "green" if closes[i] >= opens[i] else "red"
            ax.plot(
                [date2num(times[i]), date2num(times[i])],
                [lows[i], highs[i]],
                color=color,
                linewidth=1,
            )
            ax.plot(
                [date2num(times[i]), date2num(times[i])],
                [opens[i], closes[i]],
                color=color,
                linewidth=4,
            )

        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        path = Path(file_path)
        fig.savefig(str(path), dpi=150)
        plt.close(fig)
        return path

    @staticmethod
    def line(
        data: Sequence[tuple[object, float]],
        file_path: str | Path,
        *,
        title: str = "Line Chart",
        xlabel: str = "X",
        ylabel: str = "Y",
        figsize: tuple[int, int] = (12, 6),
    ) -> Path:
        """Построить линейный график.

        Args:
            data: Последовательность кортежей (x, y).
            file_path: Путь для сохранения.
            title: Заголовок.
            xlabel: Подпись оси X.
            ylabel: Подпись оси Y.
            figsize: Размер фигуры.

        Returns:
            Путь к сохранённому файлу.
        """
        Chart._check_deps()
        import matplotlib.pyplot as plt

        x_vals = [d[0] for d in data]
        y_vals = [d[1] for d in data]

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x_vals, y_vals, linewidth=1.5)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        path = Path(file_path)
        fig.savefig(str(path), dpi=150)
        plt.close(fig)
        return path

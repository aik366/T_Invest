from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple

from invest_sdk.models import Candle, Portfolio, PortfolioPosition
from invest_sdk.utils import percent_of, safe_div


class PortfolioSummary(NamedTuple):
    """Сводка по портфелю."""

    total_invested: Decimal
    total_value: Decimal
    total_yield: Decimal
    total_yield_percent: Decimal
    position_count: int
    profitable_count: int
    unprofitable_count: int


class PositionAllocation(NamedTuple):
    """Распределение позиции в портфеле."""

    instrument_type: str
    total_value: Decimal
    percent: Decimal


class CandleStats(NamedTuple):
    """Статистика по свечам."""

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    mean: Decimal
    std: Decimal
    volatility: Decimal
    change: Decimal
    change_percent: Decimal


class Statistics:
    """Выполняет вычисления, аналитику, агрегирование.

    Не знает про SDK.
    Работает только с моделями из invest_sdk.models.
    """

    @staticmethod
    def portfolio_summary(portfolio: Portfolio) -> PortfolioSummary:
        """Сформировать сводку по портфелю."""
        total_invested = sum(
            (pos.average_price * pos.quantity for pos in portfolio.positions),
            Decimal("0"),
        )
        total_value = portfolio.total_value
        total_yield = portfolio.total_yield
        total_yield_percent = percent_of(total_yield, total_invested)

        profitable = sum(
            1
            for pos in portfolio.positions
            if pos.expected_yield >= Decimal("0")
        )
        unprofitable = len(portfolio.positions) - profitable

        return PortfolioSummary(
            total_invested=total_invested,
            total_value=total_value,
            total_yield=total_yield,
            total_yield_percent=total_yield_percent,
            position_count=len(portfolio.positions),
            profitable_count=profitable,
            unprofitable_count=unprofitable,
        )

    @staticmethod
    def position_allocations(
        portfolio: Portfolio,
    ) -> list[PositionAllocation]:
        """Рассчитать распределение по типам инструментов."""
        by_type: dict[str, Decimal] = {}
        for pos in portfolio.positions:
            typ = pos.instrument_type or "unknown"
            by_type[typ] = by_type.get(typ, Decimal("0")) + pos.total_value

        total = portfolio.total_value
        return sorted(
            [
                PositionAllocation(
                    instrument_type=typ,
                    total_value=val,
                    percent=percent_of(val, total),
                )
                for typ, val in by_type.items()
            ],
            key=lambda x: x.total_value,
            reverse=True,
        )

    @staticmethod
    def candle_statistics(candles: Sequence[Candle]) -> CandleStats:
        """Рассчитать статистику по списку свечей."""
        if not candles:
            return CandleStats(
                open=Decimal("0"),
                high=Decimal("0"),
                low=Decimal("0"),
                close=Decimal("0"),
                mean=Decimal("0"),
                std=Decimal("0"),
                volatility=Decimal("0"),
                change=Decimal("0"),
                change_percent=Decimal("0"),
            )

        opens = [c.open for c in candles]
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        first_open = opens[0]
        last_close = closes[-1]
        _max = max(highs)
        _min = min(lows)

        n = len(closes)
        mean = sum(closes) / Decimal(str(n))

        variance = (
            sum((c - mean) ** 2 for c in closes) / Decimal(str(n))
        )
        std = variance.sqrt() if variance >= Decimal("0") else Decimal("0")

        change = last_close - first_open
        change_percent = percent_of(change, first_open)

        daily_returns: list[Decimal] = []
        for i in range(1, len(closes)):
            prev = closes[i - 1]
            if prev != Decimal("0"):
                daily_returns.append(
                    (closes[i] - prev) / prev * Decimal("100")
                )

        volatility = (
            (
                sum(r ** 2 for r in daily_returns) / Decimal(str(len(daily_returns)))
            ).sqrt()
            if daily_returns
            else Decimal("0")
        )

        return CandleStats(
            open=first_open,
            high=_max,
            low=_min,
            close=last_close,
            mean=mean,
            std=std,
            volatility=volatility,
            change=change,
            change_percent=change_percent,
        )

    @staticmethod
    def total_profit_loss(positions: Sequence[PortfolioPosition]) -> Decimal:
        """Суммарная прибыль/убыток по позициям."""
        return sum(
            (pos.current_price - pos.average_price) * pos.quantity
            for pos in positions
        )

    @staticmethod
    def profitable_positions(
        positions: Sequence[PortfolioPosition],
    ) -> list[PortfolioPosition]:
        """Отфильтровать прибыльные позиции."""
        return [
            pos
            for pos in positions
            if pos.expected_yield >= Decimal("0")
        ]

    @staticmethod
    def unprofitable_positions(
        positions: Sequence[PortfolioPosition],
    ) -> list[PortfolioPosition]:
        """Отфильтровать убыточные позиции."""
        return [
            pos
            for pos in positions
            if pos.expected_yield < Decimal("0")
        ]

    @staticmethod
    def top_positions(
        positions: Sequence[PortfolioPosition],
        top_n: int = 5,
    ) -> list[PortfolioPosition]:
        """Топ N позиций по стоимости."""
        return sorted(
            positions,
            key=lambda pos: pos.total_value,
            reverse=True,
        )[:top_n]

    @staticmethod
    def diversification_score(
        positions: Sequence[PortfolioPosition],
    ) -> Decimal:
        """Индекс диверсификации (0-100).

        Чем больше разных инструментов с равномерным распределением,
        тем выше показатель.
        """
        if not positions:
            return Decimal("0")

        total = sum((pos.total_value for pos in positions), Decimal("0"))
        if total == Decimal("0"):
            return Decimal("0")

        shares = [
            pos.total_value / total for pos in positions
        ]
        hhi = sum(s ** 2 for s in shares)

        max_concentration = Decimal("1")
        n = Decimal(str(len(positions)))
        min_hhi = Decimal("1") / n if n > 0 else Decimal("1")

        if max_concentration == min_hhi:
            return Decimal("100")
        score = (Decimal("1") - (hhi - min_hhi) / (max_concentration - min_hhi)) * Decimal("100")
        return max(Decimal("0"), min(Decimal("100"), score))

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from invest_sdk.models import Portfolio, PortfolioPosition


class PortfolioService:
    """Сервис для получения данных о портфеле.

    Единственный слой, который напрямую вызывает SDK.
    """

    def __init__(self, sdk_services: object) -> None:
        self._sdk = sdk_services

    def get_portfolio(self, account_id: str) -> Portfolio:
        """Получить полную информацию о портфеле."""
        from t_tech.invest.schemas import PortfolioResponse

        response: PortfolioResponse = self._sdk.operations.get_portfolio(
            account_id=account_id
        )

        positions = list(self._build_positions(response))
        total_value = _money_value_to_decimal(
            response.total_amount_shares
        ) + _money_value_to_decimal(
            response.total_amount_bonds
        ) + _money_value_to_decimal(
            response.total_amount_etf
        ) + _money_value_to_decimal(
            response.total_amount_currencies
        ) + _money_value_to_decimal(
            response.total_amount_futures
        )

        total_yield = _quotation_to_decimal(response.expected_yield)
        total_yield_percent = Decimal("0")
        if total_value != Decimal("0"):
            total_yield_percent = _quotation_to_decimal(
                response.expected_yield
            ) / total_value * Decimal("100")

        currency = (
            response.total_amount_shares.currency.lower() or "rub"
        )

        return Portfolio(
            account_id=account_id,
            total_value=total_value,
            total_yield=total_yield,
            total_yield_percent=total_yield_percent,
            positions=positions,
            currency=currency,
            expected_yield=total_yield,
        )

    def _build_positions(
        self, response: object
    ) -> list[PortfolioPosition]:
        result: list[PortfolioPosition] = []
        for pos in response.positions:
            avg_price = (
                _money_value_to_decimal(pos.average_position_price_fifo)
                or _money_value_to_decimal(pos.average_position_price)
                or _quotation_to_decimal(pos.average_position_price_pt)
                or Decimal("0")
            )
            qty = _quotation_to_decimal(pos.quantity)
            cur_price = _money_value_to_decimal(pos.current_price)
            result.append(
                PortfolioPosition(
                    figi=pos.figi or pos.instrument_uid or "",
                    instrument_uid=pos.instrument_uid or "",
                    instrument_type=pos.instrument_type or "",
                    ticker=pos.ticker or "",
                    name=pos.ticker or "",
                    quantity=qty,
                    average_price=avg_price,
                    current_price=cur_price,
                    total_value=cur_price * qty,
                    expected_yield=_quotation_to_decimal(
                        pos.expected_yield
                    ),
                    currency=(
                        pos.current_price.currency.lower()
                        if pos.current_price
                        else "rub"
                    ),
                    lot=_quotation_units(pos.quantity_lots),
                    blocked=bool(pos.blocked),
                    var_margin=_money_value_to_decimal(pos.var_margin)
                    if pos.var_margin
                    else None,
                    current_nkd=_money_value_to_decimal(pos.current_nkd)
                    if pos.current_nkd
                    else None,
                    daily_yield=_money_value_to_decimal(pos.daily_yield)
                    if pos.daily_yield
                    else Decimal("0"),
                )
            )
        return result

    def get_positions(self, account_id: str) -> dict:
        """Получить позиции по счёту (деньги, бумаги, лимиты)."""
        response = self._sdk.operations.get_positions(account_id=account_id)
        return {
            "money": [
                {
                    "currency": m.currency.lower() if m.currency else "rub",
                    "units": m.units,
                    "nano": m.nano,
                }
                for m in response.money
            ],
            "securities": [
                {
                    "figi": s.figi or "",
                    "instrument_uid": s.instrument_uid or "",
                    "balance": s.balance,
                    "blocked": s.blocked,
                }
                for s in response.securities
            ],
            "futures": [
                {
                    "figi": f.figi or "",
                    "instrument_uid": f.instrument_uid or "",
                    "balance": f.balance,
                    "blocked": f.blocked,
                }
                for f in response.futures
            ],
        }

    def get_withdraw_limits(self, account_id: str) -> dict:
        """Получить лимиты вывода средств."""
        response = self._sdk.operations.get_withdraw_limits(
            account_id=account_id
        )
        return {
            "money": [
                {
                    "currency": m.currency.lower() if m.currency else "rub",
                    "units": m.units,
                    "nano": m.nano,
                }
                for m in response.money
            ],
            "blocked": [
                {
                    "currency": b.currency.lower() if b.currency else "rub",
                    "units": b.units,
                    "nano": b.nano,
                }
                for b in response.blocked
            ],
            "blocked_guarantee": [
                {
                    "currency": bg.currency.lower() if bg.currency else "rub",
                    "units": bg.units,
                    "nano": bg.nano,
                }
                for bg in response.blocked_guarantee
            ],
        }


def _quotation_units(q: object) -> int:
    if q is None:
        return 0
    return getattr(q, "units", 0) or 0


def _quotation_to_decimal(q: object) -> Decimal:
    if q is None:
        return Decimal("0")
    return Decimal(getattr(q, "units", 0)) + Decimal(getattr(q, "nano", 0)) / Decimal(
        1_000_000_000
    )


def _money_value_to_decimal(mv: object) -> Decimal:
    if mv is None:
        return Decimal("0")
    return Decimal(getattr(mv, "units", 0)) + Decimal(getattr(mv, "nano", 0)) / Decimal(
        1_000_000_000
    )

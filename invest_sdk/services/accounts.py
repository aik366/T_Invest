from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from invest_sdk.models import Account, AccountValue, UserInfo


class AccountService:
    """Сервис для работы со счетами и пользовательской информацией.

    Единственный слой, который напрямую вызывает SDK.

    Note:
        Все публичные методы возвращают только модели из invest_sdk.models.
    """

    def __init__(self, sdk_services: object) -> None:
        self._sdk = sdk_services

    def get_accounts(self) -> Sequence[Account]:
        """Получить список всех доступных счетов."""
        from t_tech.invest.schemas import AccountStatus, AccountType, AccessLevel

        response = self._sdk.users.get_accounts()
        result: list[Account] = []
        for acc in response.accounts:
            result.append(
                Account(
                    id=acc.id,
                    name=acc.name,
                    type=AccountType(acc.type).name if acc.type else "",
                    status=AccountStatus(acc.status).name if acc.status else "",
                    opened_date=acc.opened_date,
                    closed_date=acc.closed_date,
                    access_level=AccessLevel(acc.access_level).name if acc.access_level else "",
                )
            )
        return result

    def get_info(self) -> UserInfo:
        """Получить информацию о пользователе."""
        response = self._sdk.users.get_info()
        return UserInfo(
            premium_status="premium" if response.prem_status else "",
            qualified_status="qualified" if response.qual_status else "",
            tariff=response.tariff or "",
            promo_status="",
        )

    def get_margin_attributes(self, account_id: str) -> dict:
        """Получить маржинальные показатели по счёту."""
        response = self._sdk.users.get_margin_attributes(account_id=account_id)
        return {
            "liquid_portfolio": _money_value_to_dict(response.liquid_portfolio),
            "starting_margin": _money_value_to_dict(response.starting_margin),
            "minimal_margin": _money_value_to_dict(response.minimal_margin),
            "enough": response.enough,
        }

    def get_user_tariff(self) -> dict:
        """Получить информацию о тарифе пользователя."""
        response = self._sdk.users.get_user_tariff()
        limits = {"unary_limits": [], "stream_limits": []}
        for ul in response.unary_limits:
            limits["unary_limits"].append(
                {
                    "limit": ul.limit,
                    "api_trade_available": ul.api_trade_available,
                    "method": ul.method or "",
                    "day_interval": ul.day_interval,
                }
            )
        for sl in response.stream_limits:
            limits["stream_limits"].append(
                {
                    "limit": sl.limit,
                    "api_trade_available": sl.api_trade_available,
                    "streams": list(sl.streams),
                    "day_interval": sl.day_interval,
                }
            )
        return limits

    def get_account_values(self, account_id: str) -> list[AccountValue]:
        """Получить стоимость счёта в разрезе валют."""
        from t_tech.invest.schemas import GetAccountValuesRequest

        request = GetAccountValuesRequest(account_id=account_id)
        response = self._sdk.users.get_account_values(request=request)
        result: list[AccountValue] = []
        for val in response.values:
            blocked = val.blocked or val.total_blocked or 0
            total_from_api = val.total or val.total_value or 0
            result.append(
                AccountValue(
                    currency=val.currency.lower() or "rub",
                    total_value=_units_nano_to_decimal(getattr(total_from_api, "units", 0), getattr(total_from_api, "nano", 0)),
                    total_blocked=_units_nano_to_decimal(getattr(blocked, "units", 0), getattr(blocked, "nano", 0)) if hasattr(blocked, "units") else Decimal(str(blocked)),
                )
            )
        return result


def _money_value_to_dict(mv: object) -> dict:
    if mv is None:
        return {"currency": "", "units": 0, "nano": 0}
    return {
        "currency": getattr(mv, "currency", "") or "",
        "units": getattr(mv, "units", 0) or 0,
        "nano": getattr(mv, "nano", 0) or 0,
    }


def _units_nano_to_decimal(units: int, nano: int) -> Decimal:
    return Decimal(units) + Decimal(nano) / Decimal(1_000_000_000)

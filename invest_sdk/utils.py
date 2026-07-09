from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")

MOSCOW_TZ = timezone(timedelta(hours=3))


def utc_to_moscow(dt: datetime) -> datetime:
    """Конвертировать UTC datetime в московское время."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MOSCOW_TZ)


def moscow_now() -> datetime:
    """Текущее время в Москве."""
    return datetime.now(MOSCOW_TZ)


def str_to_decimal(value: str | None) -> Decimal:
    """Безопасно преобразовать строку в Decimal."""
    if value is None:
        return Decimal("0")
    return Decimal(value.strip())


def percent_of(part: Decimal, total: Decimal) -> Decimal:
    """Вычислить процент part от total."""
    if total == Decimal("0"):
        return Decimal("0")
    return (part / total) * Decimal("100")


def safe_div(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Безопасное деление с возвратом 0 при делении на 0."""
    if denominator == Decimal("0"):
        return Decimal("0")
    return numerator / denominator


def singleton(cls: type[_R]) -> Callable[..., _R]:
    """Декоратор для создания singleton класса."""
    instances: dict[type, _R] = {}

    @wraps(cls)
    def get_instance(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def chunks[T](seq: list[T], size: int):
    """Разбить последовательность на куски указанного размера."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]

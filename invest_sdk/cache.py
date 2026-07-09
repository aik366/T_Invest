from __future__ import annotations

from collections.abc import Callable, Hashable
from datetime import datetime, timedelta
from functools import wraps
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")


class TTLCache:
    """Кэш с временем жизни (TTL).

    Хранит результаты вызовов функций в памяти.
    Ничего не знает о Printer, Statistics, UI.
    """

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        self._default_ttl = timedelta(seconds=default_ttl_seconds)
        self._store: dict[Hashable, tuple[datetime, object]] = {}

    def get(self, key: Hashable) -> object | None:
        """Получить значение из кэша.

        Возвращает None если ключ отсутствует или истёк TTL.
        """
        if key not in self._store:
            return None
        created_at, value = self._store[key]
        if datetime.now() - created_at > self._default_ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: Hashable, value: object) -> None:
        """Сохранить значение в кэш."""
        self._store[key] = (datetime.now(), value)

    def invalidate(self, key: Hashable) -> None:
        """Инвалидировать ключ."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Полностью очистить кэш."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    @property
    def size(self) -> int:
        """Количество записей в кэше."""
        return len(self._store)


def cached(
    ttl_seconds: int | None = None,
    key_builder: Callable[..., Hashable] | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Декоратор для кэширования результатов функций.

    Args:
        ttl_seconds: Время жизни кэша в секундах.
        key_builder: Функция для построения ключа кэша.

    Usage:
        @cached(ttl_seconds=60)
        def expensive_function(param: str) -> str: ...
    """
    cache: TTLCache = TTLCache(ttl_seconds or 300)

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if key_builder is not None:
                key = key_builder(*args, **kwargs)
            else:
                key = (func.__name__, args, tuple(sorted(kwargs.items())))
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result  # type: ignore[return-value]
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator

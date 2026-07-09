from __future__ import annotations

from decimal import Decimal

import pytest

from invest_sdk.cache import TTLCache, cached


class TestTTLCache:
    def test_set_and_get(self) -> None:
        cache = TTLCache(default_ttl_seconds=300)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing(self) -> None:
        cache = TTLCache(default_ttl_seconds=300)
        assert cache.get("nonexistent") is None

    def test_invalidate(self) -> None:
        cache = TTLCache(default_ttl_seconds=300)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self) -> None:
        cache = TTLCache(default_ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size == 0

    def test_size(self) -> None:
        cache = TTLCache(default_ttl_seconds=300)
        assert cache.size == 0
        cache.set("key1", "value1")
        assert cache.size == 1

    def test_hashable_key(self) -> None:
        cache = TTLCache(default_ttl_seconds=300)
        cache.set(42, "answer")
        cache.set((1, 2), "tuple")
        assert cache.get(42) == "answer"
        assert cache.get((1, 2)) == "tuple"


class TestCachedDecorator:
    def test_cached_function(self) -> None:
        call_count = 0

        @cached(ttl_seconds=60)
        def compute(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * x

        assert compute(5) == 25
        assert call_count == 1
        assert compute(5) == 25
        assert call_count == 1
        assert compute(10) == 100
        assert call_count == 2
        assert compute(10) == 100
        assert call_count == 2

    def test_cached_with_custom_key(self) -> None:
        call_count = 0

        @cached(ttl_seconds=60, key_builder=lambda x: x % 2)
        def compute(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * x

        compute(5)
        assert call_count == 1
        compute(7)
        assert call_count == 1
        compute(6)
        assert call_count == 2

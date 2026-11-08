"""Shared primitives, types, and constants for PyIDM."""

from __future__ import annotations

import enum
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Type-safe Result container representing success or failure without exceptions."""

    def __init__(self, value: T | None, error: E | None, is_ok: bool) -> None:
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @classmethod
    def ok(cls, value: T) -> Result[T, E]:
        return cls(value=value, error=None, is_ok=True)

    @classmethod
    def err(cls, error: E) -> Result[T, E]:
        return cls(value=None, error=error, is_ok=False)

    @property
    def is_ok(self) -> bool:
        return self._is_ok

    @property
    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self) -> T:
        if not self._is_ok:
            raise ValueError(f"Called unwrap on Err Result: {self._error}")
        assert self._value is not None
        return self._value

    def error(self) -> E:
        if self._is_ok:
            raise ValueError("Called error on Ok Result")
        assert self._error is not None
        return self._error

    def unwrap_or(self, default: T) -> T:
        return self._value if self._is_ok and self._value is not None else default


class Priority(enum.IntEnum):
    """Execution priority levels for downloads and queues."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


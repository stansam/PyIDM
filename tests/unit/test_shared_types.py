"""Unit tests for Result container and shared primitives."""

import pytest

from app.shared.types import Priority, Result


def test_result_ok() -> None:
    res: Result[int, str] = Result.ok(42)
    assert res.is_ok is True
    assert res.is_err is False
    assert res.unwrap() == 42
    assert res.unwrap_or(0) == 42


def test_result_err() -> None:
    res: Result[int, str] = Result.err("failure")
    assert res.is_ok is False
    assert res.is_err is True
    assert res.error() == "failure"
    assert res.unwrap_or(100) == 100

    with pytest.raises(ValueError, match="Called unwrap on Err Result"):
        res.unwrap()


def test_priority_ordering() -> None:
    assert Priority.LOW < Priority.NORMAL < Priority.HIGH < Priority.URGENT


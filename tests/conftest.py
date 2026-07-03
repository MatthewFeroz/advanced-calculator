"""Shared pytest fixtures and helpers for the test suite."""

from decimal import Decimal

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


@pytest.fixture
def config(tmp_path):
    """A small, predictable configuration that writes files to a temp folder."""
    return CalculatorConfig(
        base_dir=tmp_path,
        max_history_size=3,
        auto_save=False,
        precision=4,
        max_input_value=Decimal("1000"),
    )


@pytest.fixture
def calculator(config):
    """A calculator wired to the small test configuration above."""
    return Calculator(config)


def feed_input(monkeypatch, values):
    """Replace `input()` so REPL tests can script what the user types.

    Each entry in `values` is returned in order. If an entry is an
    exception class (like KeyboardInterrupt), it is raised instead, which
    lets tests simulate Ctrl+C and Ctrl+D.
    """
    iterator = iter(values)

    def fake_input(prompt=""):
        value = next(iterator)
        if isinstance(value, type) and issubclass(value, BaseException):
            raise value
        return value

    monkeypatch.setattr("builtins.input", fake_input)

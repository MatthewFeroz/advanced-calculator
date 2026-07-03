"""Tests for the logging and auto-save observers."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.calculation import Calculation
from app.history import AutoSaveObserver, LoggingObserver


@pytest.fixture
def calculation():
    return Calculation(
        operation="add",
        operand1=Decimal("1"),
        operand2=Decimal("2"),
        result=Decimal("3"),
        timestamp=datetime(2026, 1, 1, 9, 0, 0),
    )


def test_logging_observer_writes_log_record(calculation, caplog):
    with caplog.at_level("INFO"):
        LoggingObserver().update(calculation)
    assert "Calculation performed" in caplog.text
    assert "add(1, 2) = 3" in caplog.text


def test_logging_observer_requires_a_calculation():
    with pytest.raises(AttributeError):
        LoggingObserver().update(None)


def test_autosave_observer_saves_when_enabled(calculation):
    calculator = SimpleNamespace(
        config=SimpleNamespace(auto_save=True), save_history=Mock()
    )
    AutoSaveObserver(calculator).update(calculation)
    calculator.save_history.assert_called_once()


def test_autosave_observer_skips_when_disabled(calculation):
    calculator = SimpleNamespace(
        config=SimpleNamespace(auto_save=False), save_history=Mock()
    )
    AutoSaveObserver(calculator).update(calculation)
    calculator.save_history.assert_not_called()


def test_autosave_observer_requires_a_calculation():
    calculator = SimpleNamespace(
        config=SimpleNamespace(auto_save=True), save_history=Mock()
    )
    with pytest.raises(AttributeError):
        AutoSaveObserver(calculator).update(None)


def test_autosave_observer_rejects_incomplete_calculator():
    """Objects without config/save_history cannot be observed."""
    with pytest.raises(TypeError, match="must expose"):
        AutoSaveObserver(object())

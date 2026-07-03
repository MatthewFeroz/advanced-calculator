"""Tests for the Memento snapshots used by undo/redo."""

from datetime import datetime
from decimal import Decimal

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento


def _sample_calculation():
    return Calculation(
        operation="add",
        operand1=Decimal("1"),
        operand2=Decimal("2"),
        result=Decimal("3"),
        timestamp=datetime(2026, 1, 1, 9, 0, 0),
    )


def test_memento_round_trips_through_dict():
    """A snapshot should survive being serialized and rebuilt unchanged."""
    memento = CalculatorMemento(history=[_sample_calculation()])
    restored = CalculatorMemento.from_dict(memento.to_dict())
    assert restored.history == memento.history
    assert restored.timestamp == memento.timestamp


def test_empty_history_snapshot():
    """Snapshotting an empty history is valid (used right after startup)."""
    memento = CalculatorMemento(history=[])
    assert CalculatorMemento.from_dict(memento.to_dict()).history == []

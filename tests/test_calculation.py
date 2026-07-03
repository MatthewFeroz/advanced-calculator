"""Tests for the Calculation record."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.calculation import Calculation
from app.exceptions import OperationError


@pytest.fixture
def calculation():
    return Calculation(
        operation="add",
        operand1=Decimal("2"),
        operand2=Decimal("3"),
        result=Decimal("5"),
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )


def test_str_shows_full_equation(calculation):
    assert str(calculation) == "add(2, 3) = 5"


def test_to_dict_produces_csv_ready_strings(calculation):
    """Serialized rows should be all strings so pandas writes them cleanly."""
    row = calculation.to_dict()
    assert row == {
        "operation": "add",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": "2026-01-01T12:00:00",
    }


def test_round_trip_through_dict(calculation):
    """Saving then loading should reproduce the same calculation."""
    restored = Calculation.from_dict(calculation.to_dict())
    assert restored == calculation


@pytest.mark.parametrize(
    "bad_row",
    [
        {"operation": "add"},  # missing fields
        {"operation": "add", "operand1": "x", "operand2": "3", "result": "5",
         "timestamp": "2026-01-01T12:00:00"},  # non-numeric operand
        {"operation": "add", "operand1": "2", "operand2": "3", "result": "5",
         "timestamp": "not-a-date"},  # bad timestamp
    ],
)
def test_from_dict_rejects_malformed_rows(bad_row):
    """Corrupt CSV rows should raise OperationError, not crash the app."""
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(bad_row)


def test_timestamp_defaults_to_now():
    calculation = Calculation("add", Decimal("1"), Decimal("1"), Decimal("2"))
    assert isinstance(calculation.timestamp, datetime)

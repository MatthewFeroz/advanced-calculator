"""Tests for user input validation."""

from decimal import Decimal

import pytest

from app.input_validators import InputValidator
from app.exceptions import ValidationError


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("5", Decimal("5")),
        ("  3.25  ", Decimal("3.25")),
        (-2, Decimal("-2")),
        (1.5, Decimal("1.5")),
        ("1e2", Decimal("100")),
    ],
)
def test_valid_numbers_become_decimals(config, raw, expected):
    assert InputValidator.validate_number(raw, config) == expected


@pytest.mark.parametrize(
    "raw,message",
    [
        ("", "required"),
        ("   ", "required"),
        ("abc", "Invalid number"),
        ("1/2", "Invalid number"),
        ("inf", "finite"),
        ("nan", "finite"),
        ("100000", "maximum"),
    ],
)
def test_invalid_numbers_raise_validation_error(config, raw, message):
    """Anything that is not a usable number should be rejected with a reason."""
    with pytest.raises(ValidationError, match=message):
        InputValidator.validate_number(raw, config)

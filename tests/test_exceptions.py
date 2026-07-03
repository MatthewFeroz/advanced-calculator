"""Tests for the custom exception hierarchy."""

import pytest

from app.exceptions import (
    CalculatorError,
    ConfigurationError,
    OperationError,
    ValidationError,
)


@pytest.mark.parametrize(
    "exception_class",
    [ConfigurationError, OperationError, ValidationError],
)
def test_specific_errors_inherit_from_calculator_error(exception_class):
    """Every specific error should be catchable as a CalculatorError."""
    assert issubclass(exception_class, CalculatorError)


def test_calculator_error_carries_message():
    """The base error should keep the message it was raised with."""
    with pytest.raises(CalculatorError, match="something broke"):
        raise CalculatorError("something broke")

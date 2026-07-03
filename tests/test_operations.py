"""Tests for arithmetic operations and the operation factory."""

from decimal import Decimal

import pytest

from app.exceptions import OperationError, ValidationError
from app.operations import (
    AbsoluteDifference,
    Addition,
    Division,
    IntegerDivision,
    Modulus,
    Multiplication,
    Operation,
    OperationFactory,
    Percentage,
    Power,
    Root,
    Subtraction,
)


@pytest.mark.parametrize(
    "operation,left,right,expected",
    [
        (Addition(), "2", "3", Decimal("5")),
        (Addition(), "-2", "3", Decimal("1")),
        (Subtraction(), "2", "3", Decimal("-1")),
        (Multiplication(), "2", "3", Decimal("6")),
        (Multiplication(), "2.5", "4", Decimal("10.0")),
        (Division(), "6", "3", Decimal("2")),
        (Power(), "2", "3", Decimal("8.0")),
        (Power(), "5", "0", Decimal("1.0")),
        (Root(), "9", "2", Decimal("3.0")),
        (Root(), "27", "3", Decimal("3.0")),
        (Modulus(), "7", "3", Decimal("1")),
        (Modulus(), "10", "5", Decimal("0")),
        (IntegerDivision(), "7", "2", Decimal("3")),
        (IntegerDivision(), "9", "3", Decimal("3")),
        (Percentage(), "50", "200", Decimal("25")),
        (Percentage(), "1", "3", Decimal("1") / Decimal("3") * 100),
        (AbsoluteDifference(), "3", "10", Decimal("7")),
        (AbsoluteDifference(), "10", "3", Decimal("7")),
        (AbsoluteDifference(), "-5", "5", Decimal("10")),
    ],
)
def test_operations_execute(operation, left, right, expected):
    """Every operation should produce the mathematically correct result."""
    assert operation.execute(Decimal(left), Decimal(right)) == expected


@pytest.mark.parametrize(
    "operation,left,right,message",
    [
        (Division(), "1", "0", "Division by zero"),
        (Power(), "2", "-1", "Negative exponents"),
        (Root(), "-9", "2", "negative"),
        (Root(), "9", "0", "Zero root"),
        (Modulus(), "5", "0", "Modulus by zero"),
        (IntegerDivision(), "5", "0", "Integer division by zero"),
        (Percentage(), "5", "0", "percentage of zero"),
    ],
)
def test_operation_validation_errors(operation, left, right, message):
    """Impossible math should raise ValidationError with a clear reason."""
    with pytest.raises(ValidationError, match=message):
        operation.execute(Decimal(left), Decimal(right))


def test_operation_base_is_abstract():
    """The Operation base class should not be instantiated directly."""
    with pytest.raises(TypeError):
        Operation()


def test_operation_str_uses_command():
    assert str(Modulus()) == "modulus"


def test_describe_returns_docstring_first_line():
    """Descriptions come straight from each class docstring."""
    assert Percentage.describe() == "Work out what percent the first number is of the second."
    assert OperationFactory.describe("abs_diff").startswith("Find the distance")


def test_describe_rejects_unknown_operation():
    with pytest.raises(OperationError, match="Unknown operation"):
        OperationFactory.describe("nope")


def test_factory_lists_all_ten_operations():
    """All mandatory operations should be registered in the factory."""
    expected = {
        "add", "subtract", "multiply", "divide", "power",
        "root", "modulus", "int_divide", "percent", "abs_diff",
    }
    assert expected.issubset(set(OperationFactory.commands()))


def test_factory_creates_operations_case_insensitively():
    assert isinstance(OperationFactory.create(" ADD "), Addition)
    assert isinstance(OperationFactory.create("Percent"), Percentage)


def test_factory_rejects_unknown_operation():
    with pytest.raises(OperationError, match="Unknown operation"):
        OperationFactory.create("cube")


def test_factory_registers_new_operation():
    """New operations can be plugged in without touching existing code."""

    class Average(Operation):
        """Average of two numbers."""

        command = "average"

        def execute(self, left, right):
            return (left + right) / 2

    OperationFactory.register("average", Average)
    assert isinstance(OperationFactory.create("average"), Average)


def test_factory_rejects_non_operation_class():
    with pytest.raises(TypeError, match="inherit"):
        OperationFactory.register("bad", dict)

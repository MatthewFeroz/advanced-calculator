"""Arithmetic operations and the factory that creates them.

Each operation is a small "strategy" class with one job: take two
numbers and return a result. The `OperationFactory` at the bottom maps
command names (like "modulus") to these classes, so the rest of the app
never needs a giant if/else chain to pick an operation.

The first line of each operation's docstring doubles as its description
in the REPL's help menu, so adding a new operation here automatically
updates the help text.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import ClassVar

from app.exceptions import OperationError, ValidationError


class Operation(ABC):
    """Base class every arithmetic operation builds on."""

    command: ClassVar[str] = "operation"

    def validate(self, left: Decimal, right: Decimal) -> None:
        """Check the operands before running; subclasses add their own rules."""

    @abstractmethod
    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        """Run the operation and return the result."""
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def describe(cls) -> str:
        """Return a short human-friendly description (the docstring's first line)."""
        return (cls.__doc__ or cls.command).strip().splitlines()[0]

    def __str__(self) -> str:
        return self.command


class Addition(Operation):
    """Add two numbers together."""

    command = "add"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return left + right


class Subtraction(Operation):
    """Subtract the second number from the first."""

    command = "subtract"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return left - right


class Multiplication(Operation):
    """Multiply two numbers together."""

    command = "multiply"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return left * right


class Division(Operation):
    """Divide the first number by the second."""

    command = "divide"

    def validate(self, left: Decimal, right: Decimal) -> None:
        super().validate(left, right)
        if right == 0:
            raise ValidationError("Division by zero is not allowed")

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return left / right


class Power(Operation):
    """Raise the first number to the power of the second."""

    command = "power"

    def validate(self, left: Decimal, right: Decimal) -> None:
        super().validate(left, right)
        if right < 0:
            raise ValidationError("Negative exponents are not supported")

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return Decimal(str(float(left) ** float(right)))


class Root(Operation):
    """Take the nth root of the first number (second number is n)."""

    command = "root"

    def validate(self, left: Decimal, right: Decimal) -> None:
        super().validate(left, right)
        if left < 0:
            raise ValidationError("Cannot calculate root of a negative number")
        if right == 0:
            raise ValidationError("Zero root is undefined")

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return Decimal(str(float(left) ** (1 / float(right))))


class Modulus(Operation):
    """Find the remainder after dividing the first number by the second."""

    command = "modulus"

    def validate(self, left: Decimal, right: Decimal) -> None:
        super().validate(left, right)
        if right == 0:
            raise ValidationError("Modulus by zero is not allowed")

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return left % right


class IntegerDivision(Operation):
    """Divide and keep only the whole-number part of the answer."""

    command = "int_divide"

    def validate(self, left: Decimal, right: Decimal) -> None:
        super().validate(left, right)
        if right == 0:
            raise ValidationError("Integer division by zero is not allowed")

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return left // right


class Percentage(Operation):
    """Work out what percent the first number is of the second."""

    command = "percent"

    def validate(self, left: Decimal, right: Decimal) -> None:
        super().validate(left, right)
        if right == 0:
            raise ValidationError("Cannot take a percentage of zero")

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return (left / right) * Decimal("100")


class AbsoluteDifference(Operation):
    """Find the distance between two numbers (always zero or positive)."""

    command = "abs_diff"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        self.validate(left, right)
        return abs(left - right)


class OperationFactory:
    """Factory that builds operation objects from their command names.

    Keeping the name-to-class map in one place means the REPL, the help
    menu, and the tests all stay in sync automatically when an operation
    is added or removed.
    """

    _operations: ClassVar[dict[str, type[Operation]]] = {
        "add": Addition,
        "subtract": Subtraction,
        "multiply": Multiplication,
        "divide": Division,
        "power": Power,
        "root": Root,
        "modulus": Modulus,
        "int_divide": IntegerDivision,
        "percent": Percentage,
        "abs_diff": AbsoluteDifference,
    }

    @classmethod
    def commands(cls) -> tuple[str, ...]:
        """Return every supported operation command name."""
        return tuple(cls._operations)

    @classmethod
    def describe(cls, name: str) -> str:
        """Return the one-line description of an operation, for the help menu."""
        operation_class = cls._operations.get(name.strip().lower())
        if operation_class is None:
            raise OperationError(f"Unknown operation: {name}")
        return operation_class.describe()

    @classmethod
    def register(cls, name: str, operation_class: type[Operation]) -> None:
        """Add a brand-new operation to the factory at runtime."""
        if not issubclass(operation_class, Operation):
            raise TypeError("operation_class must inherit from Operation")
        cls._operations[name.strip().lower()] = operation_class

    @classmethod
    def create(cls, name: str) -> Operation:
        """Build the operation object matching what the user typed."""
        operation_class = cls._operations.get(name.strip().lower())
        if operation_class is None:
            raise OperationError(f"Unknown operation: {name}")
        return operation_class()

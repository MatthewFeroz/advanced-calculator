"""Custom exceptions for the calculator.

Every error the calculator raises on purpose comes from this small family
of exception classes. Because they all share one base class, the REPL can
catch `CalculatorError` in a single place and show the user a friendly
message instead of crashing.
"""


class CalculatorError(Exception):
    """The parent of every calculator-specific error."""


class ConfigurationError(CalculatorError):
    """Raised when a setting in the .env file (or a default) is invalid."""


class OperationError(CalculatorError):
    """Raised when a calculation or history action cannot be completed."""


class ValidationError(CalculatorError):
    """Raised when the user types something that is not a usable number."""

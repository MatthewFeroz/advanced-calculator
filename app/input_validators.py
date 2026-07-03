"""Helpers that check user input before it reaches an operation.

Users can type anything at the REPL prompt, so every value goes through
`InputValidator.validate_number` first. It turns the raw text into a
`Decimal` (which avoids floating-point surprises) and rejects values
that are empty, not numbers, infinite, or larger than the configured
maximum.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError


class InputValidator:
    """Validate and normalize numbers typed by the user."""

    @staticmethod
    def validate_number(value: Any, config: CalculatorConfig) -> Decimal:
        """Return `value` as a Decimal, or raise ValidationError explaining why not."""
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                raise ValidationError("A number is required")
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError(f"Invalid number: {value}") from exc
        if not number.is_finite():
            raise ValidationError("Number must be finite")
        if abs(number) > config.max_input_value:
            raise ValidationError(f"Value exceeds maximum allowed: {config.max_input_value}")
        return number

"""The Calculation record stored in history.

A `Calculation` is a simple snapshot of one finished sum: which
operation ran, the two numbers that went in, the result, and when it
happened. It knows how to turn itself into a plain dictionary (for
saving to CSV with pandas) and how to rebuild itself from one (for
loading history back in).
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.exceptions import OperationError


@dataclass
class Calculation:
    """One completed calculation, ready to be shown or saved."""

    operation: str
    operand1: Decimal
    operand2: Decimal
    result: Decimal
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, str]:
        """Turn this calculation into a row of plain strings for the CSV file."""
        return {
            "operation": self.operation,
            "operand1": str(self.operand1),
            "operand2": str(self.operand2),
            "result": str(self.result),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Calculation":
        """Rebuild a calculation from a CSV row, or explain what was wrong with it."""
        try:
            return cls(
                operation=str(data["operation"]),
                operand1=Decimal(str(data["operand1"])),
                operand2=Decimal(str(data["operand2"])),
                result=Decimal(str(data["result"])),
                timestamp=datetime.fromisoformat(str(data["timestamp"])),
            )
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise OperationError(f"Invalid calculation data: {exc}") from exc

    def __str__(self) -> str:
        return f"{self.operation}({self.operand1}, {self.operand2}) = {self.result}"

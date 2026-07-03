"""Memento objects that power undo and redo.

The Memento pattern works like a save point in a game: before the
history changes, the calculator tucks away a `CalculatorMemento` holding
a copy of the history as it was. Undo pops the most recent save point
and restores it; redo does the same in the other direction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.calculation import Calculation


@dataclass
class CalculatorMemento:
    """A frozen copy of the calculator's history at one moment in time."""

    history: list[Calculation]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Turn this snapshot into plain data (useful for saving or debugging)."""
        return {
            "history": [calculation.to_dict() for calculation in self.history],
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalculatorMemento":
        """Rebuild a snapshot from plain data."""
        return cls(
            history=[Calculation.from_dict(item) for item in data["history"]],
            timestamp=datetime.fromisoformat(str(data["timestamp"])),
        )

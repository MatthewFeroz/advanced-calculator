"""The Calculator facade — the one object the REPL talks to.

This class wires every other piece together: it validates input, asks
the `OperationFactory` for the right operation, rounds the result to the
configured precision, records the calculation in history, snapshots the
old history for undo (Memento pattern), and tells its observers about
the new calculation (Observer pattern). It also saves and loads history
as CSV using pandas.
"""

from decimal import Decimal, ROUND_HALF_UP
import logging
from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError
from app.history import AutoSaveObserver, HistoryObserver, LoggingObserver
from app.input_validators import InputValidator
from app.logger import configure_logging
from app.operations import Operation, OperationFactory


class Calculator:
    """Coordinates operations, history, undo/redo, observers, and storage."""

    history_columns = ["operation", "operand1", "operand2", "result", "timestamp"]

    def __init__(self, config: CalculatorConfig | None = None) -> None:
        self.config = config or CalculatorConfig()
        self.config.history_dir.mkdir(parents=True, exist_ok=True)
        configure_logging(self.config)
        self.history: list[Calculation] = []
        self.undo_stack: list[CalculatorMemento] = []
        self.redo_stack: list[CalculatorMemento] = []
        self.operation_strategy: Operation | None = None
        # Every calculator logs its calculations; auto-saving is optional.
        self.observers: list[HistoryObserver] = [LoggingObserver()]
        if self.config.auto_save:
            self.observers.append(AutoSaveObserver(self))
        self.load_history()

    # ----- Observer management -------------------------------------------

    def add_observer(self, observer: HistoryObserver) -> None:
        """Start notifying one more observer about new calculations."""
        self.observers.append(observer)

    def remove_observer(self, observer: HistoryObserver) -> None:
        """Stop notifying an observer."""
        self.observers.remove(observer)

    def notify_observers(self, calculation: Calculation) -> None:
        """Tell every registered observer that a calculation just finished."""
        for observer in self.observers:
            observer.update(calculation)

    # ----- Performing calculations ---------------------------------------

    def set_operation(self, operation: Operation) -> None:
        """Choose which operation `perform_operation` will run next."""
        self.operation_strategy = operation

    def calculate(self, operation_name: str, operand1, operand2) -> Decimal:
        """Look up an operation by name and run it — the REPL's main entry point."""
        self.set_operation(OperationFactory.create(operation_name))
        return self.perform_operation(operand1, operand2)

    def perform_operation(self, operand1, operand2) -> Decimal:
        """Validate the inputs, run the chosen operation, and record the result."""
        if self.operation_strategy is None:
            raise OperationError("No operation set")
        left = InputValidator.validate_number(operand1, self.config)
        right = InputValidator.validate_number(operand2, self.config)
        result = self._round(self.operation_strategy.execute(left, right))
        calculation = Calculation(str(self.operation_strategy), left, right, result)
        # Save the old history first so this step can be undone.
        self._remember()
        self.redo_stack.clear()
        self.history.append(calculation)
        self.history = self.history[-self.config.max_history_size:]
        self.notify_observers(calculation)
        return result

    def _round(self, value: Decimal) -> Decimal:
        """Round a result to the configured number of decimal places."""
        quantum = Decimal("1").scaleb(-self.config.precision)
        return value.quantize(quantum, rounding=ROUND_HALF_UP).normalize()

    def _remember(self) -> None:
        """Push a Memento snapshot of the current history onto the undo stack."""
        self.undo_stack.append(CalculatorMemento(self.history.copy()))

    # ----- History persistence with pandas --------------------------------

    def get_history_dataframe(self) -> pd.DataFrame:
        """Return the history as a pandas DataFrame, one row per calculation."""
        rows = [calculation.to_dict() for calculation in self.history]
        return pd.DataFrame(rows, columns=self.history_columns)

    def save_history(self) -> Path:
        """Write the history to the configured CSV file and return its path."""
        self.config.history_dir.mkdir(parents=True, exist_ok=True)
        self.get_history_dataframe().to_csv(
            self.config.history_file,
            index=False,
            encoding=self.config.default_encoding,
        )
        logging.info("History saved to %s", self.config.history_file)
        return self.config.history_file

    def load_history(self) -> int:
        """Read history back from CSV; returns how many entries were loaded."""
        if not self.config.history_file.exists():
            self.history = []
            return 0
        try:
            frame = pd.read_csv(self.config.history_file, encoding=self.config.default_encoding)
            self.history = [
                Calculation.from_dict(row)
                for row in frame.to_dict(orient="records")
            ][-self.config.max_history_size:]
            self.undo_stack.clear()
            self.redo_stack.clear()
            logging.info("Loaded %d calculation(s) from history", len(self.history))
            return len(self.history)
        except Exception as exc:
            logging.error("Failed to load history: %s", exc)
            raise OperationError(f"Failed to load history: {exc}") from exc

    # ----- History display and undo/redo ----------------------------------

    def show_history(self) -> list[str]:
        """Return the history as readable strings like 'add(2, 3) = 5'."""
        return [str(calculation) for calculation in self.history]

    def clear_history(self) -> None:
        """Empty the history (the old state is kept so `undo` can restore it)."""
        self._remember()
        self.redo_stack.clear()
        self.history.clear()
        logging.info("History cleared")

    def undo(self) -> bool:
        """Go back to the previous history state; returns False if there is none."""
        if not self.undo_stack:
            return False
        self.redo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = self.undo_stack.pop().history.copy()
        logging.info("Undo performed")
        return True

    def redo(self) -> bool:
        """Re-apply a state that was just undone; returns False if there is none."""
        if not self.redo_stack:
            return False
        self.undo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = self.redo_stack.pop().history.copy()
        logging.info("Redo performed")
        return True

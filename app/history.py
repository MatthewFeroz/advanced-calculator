"""Observers that react whenever a calculation finishes.

This is the Observer pattern: the calculator does not know or care what
happens after a calculation — it just tells its list of observers
"something happened". Each observer then does its own job:

- `LoggingObserver` writes the calculation to the log file.
- `AutoSaveObserver` saves the whole history to CSV (when auto-save is on).

New behaviors (emailing results, playing a sound, ...) can be added by
writing a new observer, without touching the calculator itself.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any

from app.calculation import Calculation


class HistoryObserver(ABC):
    """The interface every observer must follow."""

    @abstractmethod
    def update(self, calculation: Calculation) -> None:
        """Called by the calculator each time a calculation completes."""
        raise NotImplementedError  # pragma: no cover


class LoggingObserver(HistoryObserver):
    """Writes every finished calculation to the application log."""

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("calculation is required")
        logging.info("Calculation performed: %s", calculation)


class AutoSaveObserver(HistoryObserver):
    """Saves the history file automatically after each calculation."""

    def __init__(self, calculator: Any) -> None:
        # The observer only needs two things from the calculator: its
        # config (to check the auto_save flag) and its save method.
        if not hasattr(calculator, "config") or not hasattr(calculator, "save_history"):
            raise TypeError("calculator must expose config and save_history")
        self.calculator = calculator

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("calculation is required")
        if getattr(self.calculator.config, "auto_save"):
            self.calculator.save_history()
            logging.info("History auto-saved")

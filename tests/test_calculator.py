"""Tests for the Calculator facade: calculations, history, undo/redo, persistence."""

from decimal import Decimal

import pandas as pd
import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver
from app.operations import Addition


def test_calculator_starts_with_empty_history(calculator):
    assert calculator.history == []
    assert calculator.show_history() == []
    assert list(calculator.get_history_dataframe().columns) == calculator.history_columns


def test_observer_add_and_remove(calculator):
    observer = AutoSaveObserver(calculator)
    calculator.add_observer(observer)
    assert observer in calculator.observers
    calculator.remove_observer(observer)
    assert observer not in calculator.observers


def test_perform_operation_requires_a_strategy(calculator):
    with pytest.raises(OperationError, match="No operation"):
        calculator.perform_operation(1, 2)


def test_calculate_records_history_and_rounds(calculator):
    """Results should be rounded to the configured precision (4 places here)."""
    result = calculator.calculate("divide", "1", "3")
    assert result == Decimal("0.3333")
    assert calculator.show_history() == ["divide(1, 3) = 0.3333"]


@pytest.mark.parametrize(
    "operation,left,right,expected",
    [
        ("modulus", "7", "3", Decimal("1")),
        ("int_divide", "7", "2", Decimal("3")),
        ("percent", "50", "200", Decimal("25")),
        ("abs_diff", "3", "10", Decimal("7")),
    ],
)
def test_calculate_supports_new_operations(calculator, operation, left, right, expected):
    assert calculator.calculate(operation, left, right) == expected


def test_calculate_rejects_bad_input(calculator):
    with pytest.raises(ValidationError, match="Invalid number"):
        calculator.calculate("add", "two", "3")


def test_set_operation_then_perform(calculator):
    calculator.set_operation(Addition())
    assert calculator.perform_operation("2", "3") == Decimal("5")


def test_history_respects_max_size(config):
    """Old entries fall off once the configured limit is reached."""
    limited = Calculator(
        CalculatorConfig(
            base_dir=config.base_dir,
            max_history_size=2,
            auto_save=False,
            precision=2,
            max_input_value=100,
        )
    )
    limited.calculate("add", 1, 1)
    limited.calculate("add", 2, 2)
    limited.calculate("add", 3, 3)
    assert [entry.operand1 for entry in limited.history] == [Decimal("2"), Decimal("3")]


def test_undo_redo_and_clear(calculator):
    assert calculator.undo() is False
    assert calculator.redo() is False
    calculator.calculate("add", 1, 1)
    calculator.calculate("add", 2, 2)
    assert calculator.undo() is True
    assert calculator.show_history() == ["add(1, 1) = 2"]
    assert calculator.redo() is True
    assert len(calculator.history) == 2
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo() is True
    assert len(calculator.history) == 2


def test_new_calculation_clears_redo_stack(calculator):
    """After undoing, doing a fresh calculation should forget the redo path."""
    calculator.calculate("add", 1, 1)
    calculator.undo()
    calculator.calculate("add", 5, 5)
    assert calculator.redo() is False


def test_save_and_load_history(config):
    first = Calculator(config)
    first.calculate("multiply", 3, 4)
    path = first.save_history()
    assert path.exists()
    second = Calculator(config)
    assert second.show_history() == ["multiply(3, 4) = 12"]


def test_autosave_writes_history_file(tmp_path):
    config = CalculatorConfig(base_dir=tmp_path, auto_save=True, precision=2)
    calculator = Calculator(config)
    calculator.calculate("add", 1, 2)
    assert config.history_file.exists()


def test_load_history_rejects_malformed_file(config):
    config.history_dir.mkdir(parents=True)
    config.history_file.write_text("bad,data\n1,2\n", encoding=config.default_encoding)
    with pytest.raises(OperationError, match="Failed to load history"):
        Calculator(config)


def test_load_history_keeps_only_newest_entries(config):
    """Loading trims the file down to the configured history size (3 here)."""
    rows = pd.DataFrame(
        [
            {
                "operation": "add",
                "operand1": i,
                "operand2": i,
                "result": i + i,
                "timestamp": "2026-01-01T00:00:00",
            }
            for i in range(5)
        ]
    )
    config.history_dir.mkdir(parents=True)
    rows.to_csv(config.history_file, index=False)
    loaded = Calculator(config)
    assert len(loaded.history) == 3
    assert loaded.history[0].operand1 == Decimal("2")


def test_calculations_are_logged(config):
    """The LoggingObserver should write each calculation to the log file."""
    calculator = Calculator(config)
    calculator.calculate("add", 2, 3)
    import logging

    logging.shutdown()
    contents = config.log_file.read_text(encoding=config.default_encoding)
    assert "Calculation performed: add(2, 3) = 5" in contents

"""Tests for the color-coded REPL and its dynamic help menu."""

from types import SimpleNamespace
from unittest.mock import Mock
import runpy

import pytest

import main
from app.calculator import Calculator
from app.calculator_repl import (
    _COMMANDS,
    ExitREPL,
    _prompt,
    _read_operand,
    build_help,
    calculator_repl,
    command,
)
from app.operations import OperationFactory
from tests.conftest import feed_input


def test_prompt_returns_stripped_input(monkeypatch):
    feed_input(monkeypatch, ["  hello  "])
    assert _prompt("? ") == "hello"


def test_prompt_eof_raises_exit(monkeypatch):
    """Ctrl+D at the prompt should end the REPL cleanly."""
    feed_input(monkeypatch, [EOFError])
    with pytest.raises(ExitREPL):
        _prompt("? ")


def test_read_operand_can_cancel(monkeypatch):
    feed_input(monkeypatch, ["cancel"])
    assert _read_operand("number: ") is None


def test_help_menu_is_built_dynamically():
    """Every operation and every registered command should appear in help."""
    help_text = build_help()
    for name in OperationFactory.commands():
        assert name in help_text
    for name in ["history", "clear", "undo", "redo", "save", "load", "help", "exit"]:
        assert name in help_text


def test_new_command_appears_in_help_automatically():
    """The Decorator pattern should pick up new commands with zero manual edits."""

    @command("greet", "Say hello to the user")
    def _cmd_greet(calc):
        print("hello")  # pragma: no cover

    try:
        assert "greet" in _COMMANDS
        assert "Say hello to the user" in build_help()
    finally:
        del _COMMANDS["greet"]


def test_repl_help_blank_unknown_and_exit(monkeypatch, capsys, calculator):
    feed_input(monkeypatch, ["", "help", "wat", "exit"])
    calculator_repl(calculator)
    output = capsys.readouterr().out
    assert "Available commands" in output
    assert "Unknown command" in output
    assert "Goodbye" in output


def test_repl_operation_history_save_load_clear(monkeypatch, capsys, config):
    calculator = Calculator(config)
    feed_input(
        monkeypatch,
        ["add", "2", "3", "history", "save", "clear", "load", "history", "exit"],
    )
    calculator_repl(calculator)
    output = capsys.readouterr().out
    assert "Result: 5" in output
    assert "Calculation History" in output
    assert "Loaded 1 calculation" in output


@pytest.mark.parametrize(
    "operation,left,right,expected",
    [
        ("modulus", "7", "3", "Result: 1"),
        ("int_divide", "7", "2", "Result: 3"),
        ("percent", "50", "200", "Result: 25"),
        ("abs_diff", "3", "10", "Result: 7"),
    ],
)
def test_repl_runs_new_operations(monkeypatch, capsys, calculator, operation, left, right, expected):
    feed_input(monkeypatch, [operation, left, right, "exit"])
    calculator_repl(calculator)
    assert expected in capsys.readouterr().out


def test_repl_undo_and_redo(monkeypatch, capsys, calculator):
    feed_input(monkeypatch, ["undo", "add", "1", "1", "undo", "redo", "exit"])
    calculator_repl(calculator)
    output = capsys.readouterr().out
    assert "Nothing to undo" in output
    assert "Operation undone" in output
    assert "Operation redone" in output


def test_repl_cancel_first_operand(monkeypatch, capsys, calculator):
    feed_input(monkeypatch, ["add", "cancel", "exit"])
    calculator_repl(calculator)
    assert "Operation cancelled" in capsys.readouterr().out


def test_repl_cancel_second_operand(monkeypatch, capsys, calculator):
    feed_input(monkeypatch, ["add", "1", "cancel", "exit"])
    calculator_repl(calculator)
    assert "Operation cancelled" in capsys.readouterr().out


def test_repl_prints_calculator_errors(monkeypatch, capsys, calculator):
    """Math errors should be shown to the user, not crash the REPL."""
    feed_input(monkeypatch, ["divide", "1", "0", "exit"])
    calculator_repl(calculator)
    assert "Division by zero" in capsys.readouterr().out


def test_repl_prints_validation_errors(monkeypatch, capsys, calculator):
    feed_input(monkeypatch, ["add", "abc", "3", "exit"])
    calculator_repl(calculator)
    assert "Invalid number" in capsys.readouterr().out


def test_repl_keyboard_interrupt_continues(monkeypatch, capsys, calculator):
    """Ctrl+C cancels the current entry but keeps the calculator running."""
    feed_input(monkeypatch, [KeyboardInterrupt, "exit"])
    calculator_repl(calculator)
    output = capsys.readouterr().out
    assert "Operation cancelled" in output
    assert "Goodbye" in output


def test_repl_eof_exits(monkeypatch, capsys, calculator):
    feed_input(monkeypatch, [EOFError])
    calculator_repl(calculator)
    assert "Goodbye" in capsys.readouterr().out


def test_repl_can_construct_its_own_calculator(monkeypatch, capsys):
    """Calling calculator_repl() with no argument should build a Calculator."""
    fake = SimpleNamespace(
        show_history=Mock(return_value=[]),
        save_history=Mock(),
        clear_history=Mock(),
        undo=Mock(return_value=False),
        redo=Mock(return_value=False),
        load_history=Mock(return_value=0),
        calculate=Mock(return_value=3),
    )
    monkeypatch.setattr("app.calculator_repl.Calculator", Mock(return_value=fake))
    feed_input(monkeypatch, ["exit"])
    calculator_repl()
    fake.save_history.assert_called_once()
    assert "Goodbye" in capsys.readouterr().out


def test_main_calls_repl(monkeypatch):
    repl = Mock()
    monkeypatch.setattr(main, "calculator_repl", repl)
    main.main()
    repl.assert_called_once()


def test_main_module_guard_runs_repl(monkeypatch):
    repl = Mock()
    monkeypatch.setattr("app.calculator_repl.calculator_repl", repl)
    runpy.run_module("main", run_name="__main__")
    repl.assert_called_once()

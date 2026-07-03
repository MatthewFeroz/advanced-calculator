"""The interactive command-line interface (REPL) with color-coded output.

Two of the assignment's optional features live here:

1. Color-coded output (colorama): results print in green, errors in red,
   warnings in yellow, and informational text in cyan, so the user can
   tell at a glance whether something worked.

2. A dynamic help menu (Decorator pattern): every non-math command is
   registered with the `@command` decorator, which stores its name and a
   one-line description in a registry. The help menu is built from that
   registry plus the OperationFactory, so adding a new command or
   operation updates `help` automatically — no manual edits needed.
"""

from typing import Callable

from colorama import Fore, Style, init as colorama_init

from app.calculator import Calculator
from app.exceptions import CalculatorError
from app.operations import OperationFactory

# Make colors reset automatically after each print, and work on Windows too.
colorama_init(autoreset=True)


class ExitREPL(Exception):
    """Raised internally to end the REPL loop cleanly."""


# ----- Color helpers -------------------------------------------------------


def print_success(message: str) -> None:
    """Show good news (results, saves) in green."""
    print(Fore.GREEN + message)


def print_error(message: str) -> None:
    """Show errors in red so they stand out."""
    print(Fore.RED + message)


def print_warning(message: str) -> None:
    """Show gentle warnings (nothing to undo, etc.) in yellow."""
    print(Fore.YELLOW + message)


def print_info(message: str) -> None:
    """Show neutral information in cyan."""
    print(Fore.CYAN + message)


# ----- Dynamic command registry (Decorator pattern) ------------------------

# Maps a command name to (handler function, one-line help description).
_COMMANDS: dict[str, tuple[Callable[[Calculator], None], str]] = {}


def command(name: str, description: str) -> Callable:
    """Decorator that registers a REPL command and its help text.

    Any function decorated with `@command("name", "what it does")` is
    automatically callable from the prompt and listed in the help menu.
    """

    def decorator(func: Callable[[Calculator], None]) -> Callable[[Calculator], None]:
        _COMMANDS[name] = (func, description)
        return func

    return decorator


def build_help() -> str:
    """Assemble the help menu from the registries — never written by hand."""
    lines = [Fore.CYAN + Style.BRIGHT + "Available commands:" + Style.RESET_ALL]
    lines.append(Fore.MAGENTA + "  Operations (each asks for two numbers):" + Style.RESET_ALL)
    for name in OperationFactory.commands():
        lines.append(f"    {name:<12} {OperationFactory.describe(name)}")
    lines.append(Fore.MAGENTA + "  Other commands:" + Style.RESET_ALL)
    for name, (_, description) in _COMMANDS.items():
        lines.append(f"    {name:<12} {description}")
    return "\n".join(lines)


# ----- Registered commands --------------------------------------------------


@command("history", "Show every calculation stored in history")
def _cmd_history(calc: Calculator) -> None:
    history = calc.show_history()
    if not history:
        print_warning("No calculations in history.")
        return
    print_info("Calculation History:")
    for index, entry in enumerate(history, start=1):
        print(f"{index}. {entry}")


@command("clear", "Delete all calculations from history")
def _cmd_clear(calc: Calculator) -> None:
    calc.clear_history()
    print_success("History cleared.")


@command("undo", "Undo the last calculation")
def _cmd_undo(calc: Calculator) -> None:
    if calc.undo():
        print_success("Operation undone.")
    else:
        print_warning("Nothing to undo.")


@command("redo", "Redo the last undone calculation")
def _cmd_redo(calc: Calculator) -> None:
    if calc.redo():
        print_success("Operation redone.")
    else:
        print_warning("Nothing to redo.")


@command("save", "Save calculation history to the CSV file")
def _cmd_save(calc: Calculator) -> None:
    calc.save_history()
    print_success("History saved.")


@command("load", "Load calculation history from the CSV file")
def _cmd_load(calc: Calculator) -> None:
    count = calc.load_history()
    print_success(f"Loaded {count} calculation(s).")


@command("help", "Show this help menu")
def _cmd_help(calc: Calculator) -> None:
    print(build_help())


@command("exit", "Save history and quit the calculator")
def _cmd_exit(calc: Calculator) -> None:
    calc.save_history()
    print_success("History saved.")
    raise ExitREPL


# ----- Input helpers ---------------------------------------------------------


def _prompt(message: str) -> str:
    """Read one line from the user; Ctrl+D quietly ends the REPL."""
    try:
        return input(message).strip()
    except EOFError as exc:
        raise ExitREPL from exc


def _read_operand(label: str) -> str | None:
    """Ask for one number; returns None if the user types 'cancel'."""
    value = _prompt(label)
    if value.lower() == "cancel":
        return None
    return value


def _run_operation(calc: Calculator, operation_name: str) -> None:
    """Collect two numbers from the user and show the colored result."""
    print_info("Enter numbers, or type 'cancel' to abort.")
    left = _read_operand("First number: ")
    if left is None:
        print_warning("Operation cancelled.")
        return
    right = _read_operand("Second number: ")
    if right is None:
        print_warning("Operation cancelled.")
        return
    result = calc.calculate(operation_name, left, right)
    print_success(f"Result: {result}")


# ----- The main loop ----------------------------------------------------------


def calculator_repl(calculator: Calculator | None = None) -> None:
    """Read a command, run it, print the outcome — repeat until exit."""
    calc = calculator or Calculator()
    print_info("Advanced Calculator started. Type 'help' for commands.")
    operations = set(OperationFactory.commands())

    while True:
        try:
            command_name = _prompt("\nEnter command: ").lower()
            if command_name == "":
                continue
            if command_name in _COMMANDS:
                handler, _ = _COMMANDS[command_name]
                handler(calc)
            elif command_name in operations:
                _run_operation(calc, command_name)
            else:
                print_error(f"Unknown command: {command_name}. Type 'help' for commands.")
        except KeyboardInterrupt:
            # Ctrl+C cancels the current action but keeps the REPL alive.
            print_warning("\nOperation cancelled.")
        except ExitREPL:
            print_info("\nGoodbye!")
            break
        except CalculatorError as exc:
            # Any calculator-specific problem is reported in red, never a crash.
            print_error(f"Error: {exc}")

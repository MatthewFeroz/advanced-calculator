"""The interactive command-line interface (REPL) with color-coded output.

Three of the assignment's optional features live here:

1. Color-coded output (colorama): results print in green, errors in red,
   warnings in yellow, and informational text in cyan, so the user can
   tell at a glance whether something worked.

2. A dynamic help menu (Decorator pattern): every non-math command is
   registered with the `@command` decorator, which stores its class and a
   one-line description in a registry. The help menu is built from that
   registry plus the OperationFactory, so adding a new command or
   operation updates `help` automatically — no manual edits needed.

3. The Command pattern: every request the user can make is wrapped up as
   an object with an `execute()` method. `OperationCommand` even carries
   its two operands inside it, which means requests can be parameterized,
   stored in a list, and run later — a queue of pending work.
"""

from abc import ABC, abstractmethod
import itertools

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


# ----- Rainbow mode ---------------------------------------------------------


class DisplaySettings:
    """User-togglable display preferences for the REPL."""

    def __init__(self) -> None:
        self.rainbow = False


# One shared settings object for the whole REPL session.
settings = DisplaySettings()

# The color wheel that rainbow mode cycles through, character by character.
RAINBOW_COLORS = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]


def rainbow_text(text: str) -> str:
    """Paint each character of `text` the next color of the rainbow."""
    colored = "".join(
        color + char for color, char in zip(itertools.cycle(RAINBOW_COLORS), text)
    )
    return colored + Style.RESET_ALL


def print_result(message: str) -> None:
    """Show a calculation result — green normally, rainbow when toggled on."""
    if settings.rainbow:
        print(rainbow_text(message))
    else:
        print_success(message)


# ----- Command pattern base + dynamic registry (Decorator pattern) ---------


class ReplCommand(ABC):
    """A user request wrapped up as an object (the Command pattern).

    Because every request is an object with one `execute` method, commands
    can be created in one place, handed around, put in a queue, and run
    later — the REPL loop never needs to know what each one actually does.
    """

    @abstractmethod
    def execute(self, calc: Calculator) -> None:
        """Carry out the request against the given calculator."""
        raise NotImplementedError  # pragma: no cover


# Maps a command name to (command class, one-line help description).
_COMMANDS: dict[str, tuple[type[ReplCommand], str]] = {}


def command(name: str, description: str):
    """Decorator that registers a command class and its help text.

    Any class decorated with `@command("name", "what it does")` is
    automatically callable from the prompt and listed in the help menu.
    """

    def decorator(cls: type[ReplCommand]) -> type[ReplCommand]:
        _COMMANDS[name] = (cls, description)
        return cls

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


# ----- Concrete commands -----------------------------------------------------


class OperationCommand(ReplCommand):
    """A math request with its operands packaged inside it.

    This is the parameterized command: `OperationCommand("add", "2", "3")`
    fully describes one calculation, so a list of these objects is a queue
    of pending calculations that can be executed whenever you like.
    """

    def __init__(self, operation_name: str, left: str, right: str) -> None:
        self.operation_name = operation_name
        self.left = left
        self.right = right

    def execute(self, calc: Calculator) -> None:
        result = calc.calculate(self.operation_name, self.left, self.right)
        print_result(f"Result: {result}")


@command("history", "Show every calculation stored in history")
class HistoryCommand(ReplCommand):
    """Print the numbered calculation history."""

    def execute(self, calc: Calculator) -> None:
        history = calc.show_history()
        if not history:
            print_warning("No calculations in history.")
            return
        print_info("Calculation History:")
        for index, entry in enumerate(history, start=1):
            print(f"{index}. {entry}")


@command("clear", "Delete all calculations from history")
class ClearCommand(ReplCommand):
    """Empty the history (still undoable)."""

    def execute(self, calc: Calculator) -> None:
        calc.clear_history()
        print_success("History cleared.")


@command("undo", "Undo the last calculation")
class UndoCommand(ReplCommand):
    """Step the history back to its previous state."""

    def execute(self, calc: Calculator) -> None:
        if calc.undo():
            print_success("Operation undone.")
        else:
            print_warning("Nothing to undo.")


@command("redo", "Redo the last undone calculation")
class RedoCommand(ReplCommand):
    """Re-apply the most recently undone change."""

    def execute(self, calc: Calculator) -> None:
        if calc.redo():
            print_success("Operation redone.")
        else:
            print_warning("Nothing to redo.")


@command("save", "Save calculation history to the CSV file")
class SaveCommand(ReplCommand):
    """Write the history CSV on demand."""

    def execute(self, calc: Calculator) -> None:
        calc.save_history()
        print_success("History saved.")


@command("load", "Load calculation history from the CSV file")
class LoadCommand(ReplCommand):
    """Read the history CSV back in."""

    def execute(self, calc: Calculator) -> None:
        count = calc.load_history()
        print_success(f"Loaded {count} calculation(s).")


@command("rainbow", "Toggle rainbow-colored results on or off")
class RainbowCommand(ReplCommand):
    """Flip rainbow mode — purely for fun."""

    def execute(self, calc: Calculator) -> None:
        settings.rainbow = not settings.rainbow
        if settings.rainbow:
            print(rainbow_text("Rainbow mode ON! Results will now sparkle."))
        else:
            print_info("Rainbow mode off. Results are green again.")


@command("help", "Show this help menu")
class HelpCommand(ReplCommand):
    """Print the dynamically generated help menu."""

    def execute(self, calc: Calculator) -> None:
        print(build_help())


@command("exit", "Save history and quit the calculator")
class ExitCommand(ReplCommand):
    """Save everything, then stop the loop."""

    def execute(self, calc: Calculator) -> None:
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


def _build_operation_command(operation_name: str) -> OperationCommand | None:
    """Collect two numbers and wrap them in a parameterized command object."""
    print_info("Enter numbers, or type 'cancel' to abort.")
    left = _read_operand("First number: ")
    if left is None:
        print_warning("Operation cancelled.")
        return None
    right = _read_operand("Second number: ")
    if right is None:
        print_warning("Operation cancelled.")
        return None
    return OperationCommand(operation_name, left, right)


# ----- The main loop ----------------------------------------------------------


def calculator_repl(calculator: Calculator | None = None) -> None:
    """Read a command, turn it into a command object, execute it — repeat."""
    calc = calculator or Calculator()
    print_info("Advanced Calculator started. Type 'help' for commands.")
    operations = set(OperationFactory.commands())

    while True:
        try:
            command_name = _prompt("\nEnter command: ").lower()
            if command_name == "":
                continue
            if command_name in _COMMANDS:
                command_class, _ = _COMMANDS[command_name]
                command_class().execute(calc)
            elif command_name in operations:
                operation_command = _build_operation_command(command_name)
                if operation_command is not None:
                    operation_command.execute(calc)
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

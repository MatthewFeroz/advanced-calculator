"""Program entry point — run `python main.py` to start the calculator."""

from app.calculator_repl import calculator_repl


def main() -> None:
    """Start the advanced calculator REPL."""
    calculator_repl()


if __name__ == "__main__":
    main()

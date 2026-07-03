# Advanced Calculator

A command-line calculator built for IS601 that goes well beyond basic math.
It supports ten arithmetic operations, keeps a full calculation history with
undo/redo, saves that history to CSV automatically, logs everything it does,
and prints color-coded output so you can tell results, warnings, and errors
apart at a glance.

## Features

- **Ten operations** — `add`, `subtract`, `multiply`, `divide`, `power`,
  `root`, `modulus`, `int_divide`, `percent`, and `abs_diff`, created through
  a **Factory pattern** so new operations plug in without changing the REPL.
- **Undo / redo** — implemented with the **Memento pattern**: every change to
  history is snapshotted first, so you can step backward and forward safely.
- **Observers** — the **Observer pattern** notifies a `LoggingObserver`
  (writes each calculation to the log file) and an `AutoSaveObserver`
  (saves history to CSV with pandas after every calculation).
- **Configuration via `.env`** — directories, history size, precision,
  auto-save, input limits, and encoding are all configurable with
  python-dotenv, with sensible defaults when a value is missing.
- **Robust error handling** — custom exceptions (`ValidationError`,
  `OperationError`, `ConfigurationError`) mean bad input produces a helpful
  red message instead of a crash.
- **Color-coded output** *(optional feature)* — colorama prints results in
  green, warnings in yellow, errors in red, and information in cyan.
- **Dynamic help menu** *(optional feature)* — commands register themselves
  with a `@command` decorator and operations describe themselves through
  their docstrings, so `help` always reflects exactly what is available.
- **Command pattern** *(optional feature)* — every user request is wrapped
  in a command object with an `execute()` method. `OperationCommand` carries
  its two operands inside it, so requests are fully parameterized and can be
  held in a queue and executed later.

## Project Structure

```
advanced-calculator/
├── app/
│   ├── calculator.py          # Facade tying everything together
│   ├── calculation.py         # One history record + CSV serialization
│   ├── calculator_config.py   # .env-driven configuration
│   ├── calculator_memento.py  # Undo/redo snapshots (Memento pattern)
│   ├── calculator_repl.py     # Color-coded REPL + dynamic help
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── history.py             # Logging & auto-save observers
│   ├── input_validators.py    # User input validation
│   ├── logger.py              # Central logging setup
│   └── operations.py          # Ten operations + OperationFactory
├── tests/                     # pytest suite (100% coverage)
├── .github/workflows/         # CI pipeline
├── .env.example               # Configuration template
├── requirements.txt
└── main.py                    # Entry point
```

## Installation

```bash
git clone <your-repo-url>
cd advanced-calculator

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy the template and adjust any values you want to change:

```bash
cp .env.example .env
```

| Variable | Purpose | Default |
| --- | --- | --- |
| `CALCULATOR_LOG_DIR` | Folder for log files | `logs/` |
| `CALCULATOR_HISTORY_DIR` | Folder for the history CSV | `history/` |
| `CALCULATOR_MAX_HISTORY_SIZE` | Max history entries kept | `100` |
| `CALCULATOR_AUTO_SAVE` | Save history after every calculation | `true` |
| `CALCULATOR_PRECISION` | Decimal places in results | `10` |
| `CALCULATOR_MAX_INPUT_VALUE` | Largest accepted input | `1e999` |
| `CALCULATOR_DEFAULT_ENCODING` | Encoding for file reads/writes | `utf-8` |

Every variable is optional — the calculator runs with the defaults above if
`.env` is missing. Invalid values are rejected at startup with a clear
`ConfigurationError`.

## Usage

```bash
python main.py
```

Type a command at the prompt. Operations ask for two numbers (type `cancel`
to abort an entry):

```
Enter command: percent
Enter numbers, or type 'cancel' to abort.
First number: 50
Second number: 200
Result: 25
```

| Command | What it does |
| --- | --- |
| `add`, `subtract`, `multiply`, `divide` | Basic arithmetic |
| `power`, `root` | Exponents and nth roots |
| `modulus`, `int_divide` | Remainder and whole-number division |
| `percent` | What percent the first number is of the second |
| `abs_diff` | Absolute difference between two numbers |
| `history` | Show every stored calculation |
| `clear` | Delete the history (undoable) |
| `undo` / `redo` | Step backward / forward through history changes |
| `save` / `load` | Write / read the history CSV manually |
| `help` | Show the (dynamically generated) command list |
| `exit` | Save history and quit |

`Ctrl+C` cancels the current entry without quitting; `Ctrl+D` exits.

## Testing

```bash
pytest                          # runs the suite with coverage enforcement
```

The pytest configuration (`pytest.ini`) measures branch coverage over the
`app` package and `main.py`, writes an HTML report to `htmlcov/`, and fails
the run if coverage falls below **90%** (the suite currently sits at 100%).

## Continuous Integration

Every push and pull request to `main` triggers the GitHub Actions workflow
in `.github/workflows/python-app.yml`, which checks out the code, sets up
Python, installs the dependencies, and runs the full pytest suite with the
same 90% coverage gate. A red build means either a failing test or a
coverage drop.

## Logging

All events — startup, every calculation, saves, loads, undo/redo, and
errors — are written to the file named by `CALCULATOR_LOG_FILE`
(default `logs/calculator.log`) with timestamps and severity levels
(INFO, WARNING, ERROR).

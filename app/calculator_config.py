"""Configuration loaded from the environment.

Settings for the calculator (where files go, how many history entries to
keep, how precise results are, and so on) come from a `.env` file read by
python-dotenv. Every setting has a sensible default, so the calculator
still works even when the `.env` file is missing. All values are checked
in `validate()` so a bad setting fails loudly at startup instead of
causing confusing behavior later.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import codecs
import os

from dotenv import load_dotenv

from app.exceptions import ConfigurationError

# Pull variables from the .env file into the process environment once,
# when this module is first imported.
load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    """Read an environment variable and turn it into True or False."""
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean value")


@dataclass(frozen=True)
class CalculatorConfig:
    """A frozen bundle of validated runtime settings.

    Each argument can be passed directly (handy for tests) or left as
    None, in which case the matching environment variable is used, and
    if that is missing too, a built-in default takes over.
    """

    base_dir: Path
    max_history_size: int
    auto_save: bool
    precision: int
    max_input_value: Decimal
    default_encoding: str

    def __init__(
        self,
        base_dir: Path | str | None = None,
        max_history_size: int | None = None,
        auto_save: bool | None = None,
        precision: int | None = None,
        max_input_value: Decimal | int | float | str | None = None,
        default_encoding: str | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parent.parent
        selected_base = base_dir or os.getenv("CALCULATOR_BASE_DIR") or project_root
        selected_history = max_history_size
        if selected_history is None:
            selected_history = int(os.getenv("CALCULATOR_MAX_HISTORY_SIZE", "100"))
        selected_precision = precision
        if selected_precision is None:
            selected_precision = int(os.getenv("CALCULATOR_PRECISION", "10"))
        selected_max = max_input_value
        if selected_max is None:
            selected_max = os.getenv("CALCULATOR_MAX_INPUT_VALUE", "1e999")
        selected_encoding = default_encoding or os.getenv("CALCULATOR_DEFAULT_ENCODING", "utf-8")

        # The dataclass is frozen, so fields are set through object.__setattr__.
        object.__setattr__(self, "base_dir", Path(selected_base).resolve())
        object.__setattr__(self, "max_history_size", selected_history)
        object.__setattr__(
            self,
            "auto_save",
            auto_save if auto_save is not None else _env_bool("CALCULATOR_AUTO_SAVE", True),
        )
        object.__setattr__(self, "precision", selected_precision)
        try:
            parsed_max = Decimal(str(selected_max))
        except InvalidOperation as exc:
            raise ConfigurationError("max_input_value must be numeric") from exc
        object.__setattr__(self, "max_input_value", parsed_max)
        object.__setattr__(self, "default_encoding", selected_encoding)
        self.validate()

    @property
    def log_dir(self) -> Path:
        """Folder where log files are written."""
        return Path(os.getenv("CALCULATOR_LOG_DIR", str(self.base_dir / "logs"))).resolve()

    @property
    def log_file(self) -> Path:
        """Full path of the application log file."""
        return Path(os.getenv("CALCULATOR_LOG_FILE", str(self.log_dir / "calculator.log"))).resolve()

    @property
    def history_dir(self) -> Path:
        """Folder where the CSV history file is written."""
        return Path(os.getenv("CALCULATOR_HISTORY_DIR", str(self.base_dir / "history"))).resolve()

    @property
    def history_file(self) -> Path:
        """Full path of the calculation history CSV file."""
        return Path(
            os.getenv("CALCULATOR_HISTORY_FILE", str(self.history_dir / "calculator_history.csv"))
        ).resolve()

    def validate(self) -> None:
        """Reject settings that would break the calculator at runtime."""
        try:
            codecs.lookup(self.default_encoding)
        except LookupError as exc:
            raise ConfigurationError("default_encoding must be a valid codec") from exc
        if self.max_history_size <= 0:
            raise ConfigurationError("max_history_size must be positive")
        if self.precision <= 0:
            raise ConfigurationError("precision must be positive")
        if not self.max_input_value.is_finite() or self.max_input_value <= 0:
            raise ConfigurationError("max_input_value must be a positive finite number")

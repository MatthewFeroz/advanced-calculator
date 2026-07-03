"""Tests for environment-driven configuration."""

from decimal import Decimal

import pytest

from app.calculator_config import CalculatorConfig, _env_bool
from app.exceptions import ConfigurationError


def test_explicit_arguments_win(tmp_path):
    """Values passed directly should be used as-is."""
    config = CalculatorConfig(
        base_dir=tmp_path,
        max_history_size=5,
        auto_save=False,
        precision=2,
        max_input_value="100",
        default_encoding="utf-8",
    )
    assert config.base_dir == tmp_path.resolve()
    assert config.max_history_size == 5
    assert config.auto_save is False
    assert config.precision == 2
    assert config.max_input_value == Decimal("100")


def test_environment_variables_fill_in_defaults(tmp_path, monkeypatch):
    """When arguments are omitted, matching env vars should be used."""
    monkeypatch.setenv("CALCULATOR_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_MAX_HISTORY_SIZE", "7")
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "false")
    monkeypatch.setenv("CALCULATOR_PRECISION", "3")
    monkeypatch.setenv("CALCULATOR_MAX_INPUT_VALUE", "500")
    monkeypatch.setenv("CALCULATOR_DEFAULT_ENCODING", "utf-8")
    config = CalculatorConfig()
    assert config.base_dir == tmp_path.resolve()
    assert config.max_history_size == 7
    assert config.auto_save is False
    assert config.precision == 3
    assert config.max_input_value == Decimal("500")


def test_directory_and_file_paths_derive_from_base(tmp_path):
    """Log and history paths should live under the base directory by default."""
    config = CalculatorConfig(base_dir=tmp_path, auto_save=False)
    assert config.log_dir == (tmp_path / "logs").resolve()
    assert config.log_file == (tmp_path / "logs" / "calculator.log").resolve()
    assert config.history_dir == (tmp_path / "history").resolve()
    assert config.history_file == (tmp_path / "history" / "calculator_history.csv").resolve()


def test_directory_env_overrides(tmp_path, monkeypatch):
    """CALCULATOR_LOG_DIR and CALCULATOR_HISTORY_DIR should win when set."""
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "mylogs"))
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "myhistory"))
    config = CalculatorConfig(base_dir=tmp_path, auto_save=False)
    assert config.log_dir == (tmp_path / "mylogs").resolve()
    assert config.history_dir == (tmp_path / "myhistory").resolve()


@pytest.mark.parametrize("raw,expected", [("1", True), ("yes", True), ("off", False), ("0", False)])
def test_env_bool_accepts_common_spellings(monkeypatch, raw, expected):
    monkeypatch.setenv("SOME_FLAG", raw)
    assert _env_bool("SOME_FLAG", not expected) is expected


def test_env_bool_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_FLAG", raising=False)
    assert _env_bool("SOME_FLAG", True) is True


def test_env_bool_rejects_garbage(monkeypatch):
    monkeypatch.setenv("SOME_FLAG", "maybe")
    with pytest.raises(ConfigurationError, match="boolean"):
        _env_bool("SOME_FLAG", True)


@pytest.mark.parametrize(
    "kwargs,message",
    [
        ({"max_history_size": 0}, "max_history_size"),
        ({"precision": -1}, "precision"),
        ({"max_input_value": "-5"}, "max_input_value"),
        ({"max_input_value": "not-a-number"}, "numeric"),
        ({"default_encoding": "no-such-codec"}, "codec"),
    ],
)
def test_invalid_settings_raise_configuration_error(tmp_path, kwargs, message):
    """Bad values should fail fast with a clear message."""
    with pytest.raises(ConfigurationError, match=message):
        CalculatorConfig(base_dir=tmp_path, auto_save=False, **kwargs)

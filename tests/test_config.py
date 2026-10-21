from pathlib import Path
import subprocess
import sys

import pytest

from app.settings.config import ConfigError, load_config


def test_missing_default_file_uses_prd_defaults_without_secrets(tmp_path):
    config = load_config(tmp_path, environ={})
    assert config.similarity_threshold == .60
    assert config.liveness_enabled and config.liveness_threshold == .85
    assert config.recognition_timeout == 3 and config.duplicate_window == 60
    assert not config.env_loaded and config.database.password == ""
    assert config.model_dir == tmp_path / "resources/models"


def test_config_precedence_paths_and_private_repr(tmp_path):
    path = tmp_path / ".env"
    path.write_text("STARGATE_DB_PORT=5432\nSTARGATE_DB_PASSWORD=hidden-one\n"
                    "STARGATE_DB_MIGRATION_PASSWORD=hidden-two\nSTARGATE_MODEL_DIR=weights\n"
                    "STARGATE_LIVENESS_ENABLED=false\nSTARGATE_LOG_LEVEL=debug\n")
    config = load_config(tmp_path, environ={"STARGATE_DB_PORT": "55433", "OTHER": "ignored"})
    assert config.database.port == 55433
    assert config.database.password == "hidden-one" and config.env_loaded
    assert config.model_dir == tmp_path / "weights"
    assert not config.liveness_enabled and config.log_level == "DEBUG"
    assert "hidden-one" not in repr(config) and "hidden-two" not in repr(config)
    assert set(config.secrets) == {"hidden-one", "hidden-two"}


@pytest.mark.parametrize("key,value", [
    ("DB_PORT", "secret-value"), ("DB_PORT", "0"), ("DB_PORT", "65536"),
    ("SIMILARITY_THRESHOLD", "nan"), ("LIVENESS_THRESHOLD", "1.01"),
    ("RECOGNITION_TIMEOUT", "0"), ("RECOGNITION_TIMEOUT", "inf"),
    ("DUPLICATE_WINDOW", "1.5"), ("LIVENESS_ENABLED", "maybe"),
    ("TIMEZONE", "Invalid/SecretZone"), ("LOG_LEVEL", "secret-value"),
])
def test_invalid_config_is_rejected_without_echoing_input(tmp_path, key, value):
    with pytest.raises(ConfigError) as error:
        load_config(tmp_path, environ={f"STARGATE_{key}": value})
    assert "secret-value" not in str(error.value)
    assert "Invalid/SecretZone" not in str(error.value)


def test_explicit_missing_config_directory_and_bad_encoding(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path, tmp_path / "absent", environ={})
    with pytest.raises(ConfigError):
        load_config(tmp_path, tmp_path, environ={})
    path = tmp_path / ".env"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(ConfigError):
        load_config(tmp_path, environ={})
    path.write_text('STARGATE_DB_PASSWORD="unterminated-secret\n')
    with pytest.raises(ConfigError) as error:
        load_config(tmp_path, environ={})
    assert "unterminated-secret" not in str(error.value)


def test_cli_validates_without_gui_or_leaking_config(tmp_path):
    path = tmp_path / "custom.env"
    path.write_text("STARGATE_DB_PASSWORD=keep-private\n")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "main.py"), "--check-config",
                             "--config", str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and "valid" in result.stdout
    assert "keep-private" not in result.stdout + result.stderr
    path.write_text("STARGATE_DB_PORT=keep-private\n")
    result = subprocess.run([sys.executable, str(root / "main.py"), "--check-config",
                             "--config", str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 2 and "DB_PORT" in result.stderr
    assert "keep-private" not in result.stdout + result.stderr

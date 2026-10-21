"""Validated configuration without changing global environment or loading AI."""
from dataclasses import dataclass, field
from io import StringIO
import math
import os
from pathlib import Path
from typing import Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import dotenv_values
from dotenv.parser import parse_stream


class ConfigError(ValueError):
    """Contains field names and safe guidance, never rejected values."""


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "127.0.0.1"
    port: int = 55432
    name: str = "stargate_dev"
    user: str = "stargate_app"
    password: str = field(default="", repr=False)


@dataclass(frozen=True)
class AppConfig:
    root: Path
    model_dir: Path
    log_dir: Path
    database: DatabaseConfig
    timezone: str = "Asia/Jakarta"
    similarity_threshold: float = 0.60
    liveness_enabled: bool = True
    liveness_threshold: float = 0.85
    recognition_timeout: float = 3.0
    duplicate_window: int = 60
    max_face_size: str = "Auto"
    check_in_start: str = "Shift"
    auto_checkout: bool = False
    log_level: str = "INFO"
    env_loaded: bool = False
    camera_max_streams: int = 2
    camera_open_timeout: float = 5.0
    camera_read_timeout: float = 3.0
    camera_reconnect_attempts: int = 2
    secrets: tuple[str, ...] = field(default=(), repr=False)
    bundle_root: Path | None = None
    config_file: Path | None = field(default=None, repr=False)

    @property
    def resource_root(self):
        return self.bundle_root or self.root


def load_config(root: Path, env_file: Path | None = None,
                environ: Mapping[str, str] | None = None, *, bundle_root: Path | None = None) -> AppConfig:
    root = root.resolve()
    explicit = env_file is not None
    path = Path(env_file) if explicit else root / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        if explicit:
            raise ConfigError("File konfigurasi yang dipilih tidak ditemukan.")
    elif not path.is_file():
        raise ConfigError("Konfigurasi harus berupa berkas .env.")
    else:
        try:
            content = path.read_text(encoding="utf-8")
            if any(binding.error for binding in parse_stream(StringIO(content))):
                raise ConfigError("File konfigurasi memiliki sintaks tidak valid.")
            values = {key: value for key, value in
                      dotenv_values(stream=StringIO(content), interpolate=False).items()
                      if value is not None}
        except (OSError, UnicodeError):
            raise ConfigError("File konfigurasi tidak dapat dibaca sebagai UTF-8.") from None
    system = os.environ if environ is None else environ
    values.update({key: value for key, value in system.items()
                   if key.startswith("STARGATE_")})

    def value(name, default):
        return values.get(f"STARGATE_{name}", default)

    def integer(name, default, minimum, maximum):
        try:
            result = int(value(name, str(default)))
            if not minimum <= result <= maximum:
                raise ValueError
            return result
        except (ValueError, TypeError):
            raise ConfigError(f"STARGATE_{name} harus bilangan bulat {minimum} sampai {maximum}.") from None

    def number(name, default, minimum, maximum):
        try:
            result = float(value(name, str(default)))
            if not math.isfinite(result) or not minimum <= result <= maximum:
                raise ValueError
            return result
        except (ValueError, TypeError):
            raise ConfigError(f"STARGATE_{name} harus angka {minimum} sampai {maximum}.") from None

    def folder(name, default):
        result = Path(value(name, default)).expanduser()
        return (root / result).resolve() if not result.is_absolute() else result.resolve()

    timezone = value("TIMEZONE", "Asia/Jakarta")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ConfigError("STARGATE_TIMEZONE harus zona waktu IANA yang valid.") from None
    enabled = value("LIVENESS_ENABLED", "true").lower()
    if enabled not in {"true", "false", "1", "0"}:
        raise ConfigError("STARGATE_LIVENESS_ENABLED harus true atau false.")
    level = value("LOG_LEVEL", "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigError("STARGATE_LOG_LEVEL tidak valid.")
    return AppConfig(
        root=root, bundle_root=bundle_root, config_file=path.resolve(),
        model_dir=folder("MODEL_DIR", str(bundle_root / "resources/models") if bundle_root else "resources/models"),
        log_dir=folder("LOG_DIR", "logs"),
        database=DatabaseConfig(host=value("DB_HOST", "127.0.0.1"),
                                port=integer("DB_PORT", 55432, 1, 65535),
                                name=value("DB_NAME", "stargate_dev"),
                                user=value("DB_USER", "stargate_app"),
                                password=value("DB_PASSWORD", "")),
        timezone=timezone, similarity_threshold=number("SIMILARITY_THRESHOLD", .60, 0, 1),
        liveness_enabled=enabled in {"true", "1"},
        liveness_threshold=number("LIVENESS_THRESHOLD", .85, 0, 1),
        recognition_timeout=number("RECOGNITION_TIMEOUT", 3, .01, 300),
        duplicate_window=integer("DUPLICATE_WINDOW", 60, 1, 86400), log_level=level,
        env_loaded=path.is_file(),
        camera_max_streams=integer("CAMERA_MAX_STREAMS", 2, 1, 4),
        camera_open_timeout=number("CAMERA_OPEN_TIMEOUT", 5, .25, 30),
        camera_read_timeout=number("CAMERA_READ_TIMEOUT", 3, .25, 30),
        camera_reconnect_attempts=integer("CAMERA_RECONNECT_ATTEMPTS", 2, 0, 3),
        secrets=tuple(v for k, v in values.items()
                      if v and any(word in k.upper() for word in ("PASSWORD", "SECRET", "TOKEN"))),
    )

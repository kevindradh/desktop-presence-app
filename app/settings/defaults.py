import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.database import DataValidationError


DEFAULT_SETTINGS = {
    "similarity_threshold": 0.60, "max_face_size": "Auto", "recognition_timeout": 3.0,
    "anti_spoof_enabled": True, "anti_spoof_threshold": 0.85,
    "duplicate_window": 60, "check_in_start": "Shift", "auto_checkout": False,
    "timezone": "Asia/Jakarta", "session_timeout_minutes": 15,
    "account_lockout_attempts": 5, "account_lockout_minutes": 15,
}


def validate_setting(key, value):
    valid = False
    if key in {"similarity_threshold", "anti_spoof_threshold", "recognition_timeout"}:
        valid = type(value) in {float, int} and math.isfinite(value)
        if valid:
            valid = 0 <= value <= 1 if key != "recognition_timeout" else 0 < value <= 300
    elif key in {"duplicate_window", "session_timeout_minutes", "account_lockout_attempts",
                 "account_lockout_minutes"}:
        valid = type(value) is int and 1 <= value <= 86400
    elif key in {"anti_spoof_enabled", "auto_checkout"}:
        valid = type(value) is bool
    elif key in {"max_face_size", "check_in_start"}:
        valid = value == DEFAULT_SETTINGS[key]
    elif key == "timezone" and isinstance(value, str):
        try:
            ZoneInfo(value)
            valid = True
        except (ZoneInfoNotFoundError, ValueError):
            pass
    if not valid:
        raise DataValidationError("Nama atau nilai pengaturan tidak valid.")
    return value

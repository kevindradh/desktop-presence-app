"""Rotating local diagnostic log. Business audit is implemented in Stage 3."""
import copy
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import traceback
from app.services.private_files import restrict_path


def redact(message: str, secrets: tuple[str, ...] = ()) -> str:
    # Drop biometric payload messages rather than guessing the vector format.
    if re.search(r"\b(embedding|face_vector|biometric_vector)\b", message, re.I):
        return "[REDACTED: biometric payload]"
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"\b(?:rtsp|rtsps|postgresql|postgres)://[^\s]+", "[REDACTED URL]",
                     message, flags=re.I)
    message = re.sub(r"(?i)(?<!\w)[\"']?([a-z0-9_]*(?:password|passwd|pwd|token|secret))"
                     r"[\"']?\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)",
                     r"\1=[REDACTED]", message)
    # Defensive fallback for an accidentally logged dense numeric vector.
    message = re.sub(r"\[\s*(?:[-+\d.eE]+[\s,]+){8,}[-+\d.eE]+\s*\]",
                     "[REDACTED VECTOR]", message)
    return message


class PrivateFormatter(logging.Formatter):
    def __init__(self, secrets=()):
        super().__init__("%(asctime)s %(levelname)s %(name)s %(message)s")
        self.secrets = secrets

    def formatException(self, info):
        # Exception text and source lines may contain passwords or face arrays.
        kind, _, tb = info
        frames = traceback.extract_tb(tb)
        return "\n".join([f"Exception type: {kind.__name__}"] + [
            f"  {Path(frame.filename).name}:{frame.lineno} in {frame.name}" for frame in frames])

    def format(self, record):
        safe = copy.copy(record)
        safe.msg = redact(record.getMessage(), self.secrets)
        safe.args = ()
        safe.exc_text = None
        safe.stack_info = None
        return super().format(safe)


class PrivateRotatingHandler(RotatingFileHandler):
    def _open(self):
        fd = os.open(self.baseFilename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        try:
            restrict_path(self.baseFilename)
        except OSError:
            os.close(fd)
            raise
        return os.fdopen(fd, "a", encoding="utf-8")


def configure_logging(log_dir: Path, level="INFO", secrets=(),
                      max_bytes=1_048_576, backup_count=5) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    logger = logging.getLogger("stargate")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(level)
    logger.propagate = False
    handler = PrivateRotatingHandler(log_dir / "stargate.log", maxBytes=max_bytes,
                                     backupCount=backup_count, encoding="utf-8")
    handler.setFormatter(PrivateFormatter(secrets))
    logger.addHandler(handler)
    return logger

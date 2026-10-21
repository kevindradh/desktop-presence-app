from tests.permissions import assert_private_path
import io
import logging
from pathlib import Path

from app.services.diagnostic_logging import PrivateFormatter, configure_logging, redact


def test_redaction_covers_credentials_urls_biometrics():
    message = 'connect rtsp://person:p@camera/live postgresql://user:p@server/db password="two words" token=abc'
    result = redact(message, ("known-secret",))
    for forbidden in ["person:p", "user:p", "two words", "abc"]:
        assert forbidden not in result
    assert "known-secret" not in redact("arbitrary known-secret", ("known-secret",))
    assert "0.123" not in redact("embedding=[0.123, 1, 2]")
    assert "0.123" not in redact("result [0.123, 1, 2, 3, 4, 5, 6, 7, 8, 9]")
    assert "sensitive-value" not in redact("STARGATE_DB_PASSWORD=sensitive-value")
    assert "two words" not in redact("{'password': 'two words'}")


def test_exception_trace_does_not_leak_message_source_or_cached_traceback():
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(PrivateFormatter())
    logger = logging.Logger("isolated")
    logger.addHandler(handler)
    try:
        raise RuntimeError("exception-secret-without-keyword")
    except RuntimeError:
        logger.exception("Operation failed")
    text = buffer.getvalue()
    assert "RuntimeError" in text and "test_diagnostic_logging.py" in text
    assert "exception-secret-without-keyword" not in text


def test_rotation_permissions_and_reconfiguration(tmp_path):
    logger = configure_logging(tmp_path, secrets=("sensitive-value",), max_bytes=180, backup_count=2)
    for n in range(20):
        logger.info("message %s sensitive-value", n)
    logger.handlers[0].flush()
    files = list(tmp_path.glob("stargate.log*"))
    assert len(files) == 3
    assert all("sensitive-value" not in path.read_text() for path in files)
    for path in files: assert_private_path(path)
    logger = configure_logging(tmp_path)
    assert len(logger.handlers) == 1 and not logger.propagate
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

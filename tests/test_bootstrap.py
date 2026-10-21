"""Real entrypoint/event loop in isolated processes; dialogs intercepted for CI."""
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("mode", ["success", "slot_error", "invalid_config", "unwritable_log"])
def test_bootstrap_startup_error_routing_and_shutdown(tmp_path, mode):
    root = Path(__file__).resolve().parents[1]
    log_dir = tmp_path / "logs"
    if mode == "unwritable_log":
        log_dir.write_text("Existing file blocks directory creation")
    config = tmp_path / "test.env"
    config.write_text(f"STARGATE_LOG_DIR={log_dir}\n" + (
        "STARGATE_DB_PORT=synthetic-secret-value\n" if mode == "invalid_config" else ""))
    code = r'''
import logging,sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication,QMessageBox
from app.bootstrap import main
mode=sys.argv[1]
messages=[]
observations=[]
QMessageBox.critical=lambda parent,title,message: messages.append(message)
original_exec=QApplication.exec
def event_loop(application):
    if mode == 'slot_error':
        def fail():
            raise RuntimeError('synthetic-secret-value')
        def check_banner():
            windows=[w for w in application.topLevelWidgets() if hasattr(w,'error_banner')]
            observations.append(len(windows)==1 and windows[0].error_banner.isVisible()
                and 'synthetic-secret-value' not in windows[0].error_message.text())
        QTimer.singleShot(10,fail)
        QTimer.singleShot(60,check_banner)
    QTimer.singleShot(150,application.closeAllWindows)
    return original_exec()
QApplication.exec=event_loop
hook=sys.excepthook
result=main(['--config',sys.argv[2]])
assert sys.excepthook is hook
assert result == (2 if mode in ('invalid_config','unwritable_log') else 0)
assert bool(messages) == (mode in ('invalid_config','unwritable_log'))
assert not logging.getLogger('stargate').handlers
assert all('synthetic-secret-value' not in message for message in messages)
if mode == 'slot_error':
    assert observations == [True]
'''
    completed = subprocess.run([sys.executable, "-c", code, mode, str(config)],
                               cwd=root, capture_output=True, text=True, timeout=10)
    assert completed.returncode == 0, completed.stderr
    assert "synthetic-secret-value" not in completed.stdout + completed.stderr
    if log_dir.is_dir():
        text = (log_dir / "stargate.log").read_text()
        assert "opened" in text and "closed cleanly" in text
        assert "synthetic-secret-value" not in text
        if mode == "slot_error":
            assert "RuntimeError" in text and "ref=" in text

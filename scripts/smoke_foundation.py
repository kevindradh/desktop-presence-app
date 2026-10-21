"""Exercise Stage 2 UI/task lifecycle without real cameras, AI or database access."""
import argparse
import json
import logging
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/testing/evidence/stage-02-smoke.json")
    parser.add_argument("--screenshots", type=Path,
                        default=ROOT / "docs/testing/evidence")
    args = parser.parse_args()
    if not args.visible:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    from app.services.diagnostic_logging import configure_logging
    from app.services.errors import ErrorReporter
    from app.settings.config import load_config
    from app.ui.main_window import MainWindow, ROUTES
    from app.ui.theme import apply_theme
    from app.services.auth import Principal
    from app.models.entities import Role

    application = QApplication([])
    application.setQuitOnLastWindowClosed(False)
    apply_theme(application)
    config = load_config(ROOT)
    logger = configure_logging(config.log_dir, config.log_level, config.secrets)
    reporter = ErrorReporter(logger)
    # Explicit test double only; production entrypoint always creates SessionWindow.
    window = MainWindow(config, logger, reporter,
        Principal(0, "synthetic", "Penguji fondasi", Role.SUPER_ADMIN, False),
        lambda route: window.show_route(route))
    report = {"stage": 2, "mode": "native" if args.visible else "offscreen", "checks": {},
              "scope": "Synthetic tasks only; no camera/model/database activity"}

    def wait(predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            application.processEvents()
            if predicate():
                return
            QTest.qWait(10)
        raise AssertionError("UI condition timed out")

    def scenario():
        try:
            wait(lambda: window.heartbeat_count > 0)
            args.screenshots.mkdir(parents=True, exist_ok=True)
            assert window.grab().save(str(args.screenshots / "stage-02-dashboard.png"))
            for index, (route, title, _) in enumerate(ROUTES):
                window.navigate(route)
                assert window.pages.currentIndex() == index and window.heading.text() == title
            report["checks"]["navigation"] = {"status": "PASS", "page_count": len(ROUTES)}
            window.navigate("diagnostics")
            count = window.heartbeat_count
            QTest.mouseClick(window.diagnostics.run_button, Qt.MouseButton.LeftButton)
            assert window.tasks.busy
            window.navigate("members")
            wait(lambda: window.heartbeat_count >= count + 2)
            assert window.heading.text() == "Anggota" and window.tasks.busy
            window.navigate("diagnostics")
            wait(lambda: not window.tasks.busy)
            assert window.diagnostics.progress.value() == 100
            assert "Pemeriksaan selesai" in window.diagnostics.result.text()
            report["checks"]["success_and_responsiveness"] = {"status": "PASS",
                "ui_ticks_during_task": window.heartbeat_count - count}
            QTest.mouseClick(window.diagnostics.fail_button, Qt.MouseButton.LeftButton)
            wait(lambda: not window.tasks.busy)
            assert window.error_banner.isVisible() and "Referensi:" in window.error_message.text()
            assert window.grab().save(str(args.screenshots / "stage-02-diagnostic-error.png"))
            report["checks"]["safe_worker_error"] = {"status": "PASS"}
            QTest.mouseClick(window.diagnostics.run_button, Qt.MouseButton.LeftButton)
            assert not window.error_banner.isVisible()
            QTest.mouseClick(window.diagnostics.cancel_button, Qt.MouseButton.LeftButton)
            wait(lambda: not window.tasks.busy)
            assert "dibatalkan" in window.diagnostics.result.text()
            report["checks"]["cancel_and_retry"] = {"status": "PASS"}
            QTest.mouseClick(window.diagnostics.run_button, Qt.MouseButton.LeftButton)
            before_close = time.monotonic()
            window.close()
            wait(lambda: not window.isVisible() and not window.tasks.busy, timeout=2)
            report["checks"]["close_while_running"] = {"status": "PASS",
                "seconds": round(time.monotonic() - before_close, 3)}
        except Exception as error:
            report["checks"]["scenario"] = {"status": "FAIL", "error_type": type(error).__name__}
        finally:
            window.tasks.cancel()
            try:
                wait(lambda: not window.tasks.busy, timeout=2)
            except AssertionError:
                report["checks"]["cleanup"] = {"status": "FAIL"}
                # Keep the event loop alive for safe cooperative cleanup.
                window.tasks.settled.connect(application.quit)
            window.close()
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n")
            for name, item in report["checks"].items():
                print(f"{name}: {item['status']}", flush=True)
            if not window.tasks.busy:
                application.quit()

    window.show()
    QTimer.singleShot(0, scenario)
    application.exec()
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    return 0 if report["checks"] and all(
        item["status"] == "PASS" for item in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

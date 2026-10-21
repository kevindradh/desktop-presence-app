import logging
from threading import get_ident

import pytest
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtTest import QTest

from app.services.errors import ErrorReporter
from app.services.tasks import TaskController
from app.settings.config import load_config
from app.ui.main_window import MainWindow, ROUTES
from app.ui.theme import apply_theme
from app.services.auth import Principal
from app.models.entities import Role


@pytest.fixture
def reporter(qt_app):
    logger = logging.Logger("test-errors")
    logger.addHandler(logging.NullHandler())
    return ErrorReporter(logger)


def test_worker_runs_off_ui_thread_and_keeps_event_loop_responsive(qt_app, reporter, wait_until):
    controller = TaskController(reporter)
    main_thread = get_ident()
    results, progress, ticks = [], [], []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start(5)
    controller.succeeded.connect(results.append)
    controller.progress.connect(progress.append)
    def task(ctx):
        for _ in range(10):
            ctx.pause(.01)
        ctx.progress(100)
        return get_ident()
    assert controller.start(task)
    assert not controller.start(task)  # A second task must not overwrite a running worker.
    wait_until(lambda: not controller.busy)
    timer.stop()
    assert len(results) == 1 and results[0] != main_thread
    assert progress == [100] and len(ticks) >= 3


def test_worker_failure_and_cancel_can_be_reused(qt_app, reporter, wait_until):
    controller = TaskController(reporter)
    errors, cancelled, result = [], [], []
    reporter.occurred.connect(errors.append)
    controller.cancelled.connect(lambda: cancelled.append(1))
    controller.succeeded.connect(result.append)
    def fail(ctx):
        raise RuntimeError("private-error-value")
    controller.start(fail)
    wait_until(lambda: not controller.busy)
    assert len(errors) == 1 and "private-error-value" not in errors[0].message
    assert len(errors[0].reference) == 10
    controller.start(lambda ctx: ctx.pause(30))
    controller.cancel()
    wait_until(lambda: not controller.busy, timeout=1000)
    assert cancelled and not result
    assert controller.start(lambda ctx: "recovered")
    wait_until(lambda: not controller.busy)
    assert result == ["recovered"]


@pytest.fixture
def window(qt_app, tmp_path, reporter, wait_until):
    apply_theme(qt_app)
    view = MainWindow(load_config(tmp_path, environ={}), logging.Logger("test-window"), reporter,
        Principal(1, "synthetic", "Penguji", Role.SUPER_ADMIN, False), lambda route: view.show_route(route))
    view.show()
    yield view
    view.tasks.cancel()
    wait_until(lambda: not view.tasks.busy)
    view.close()
    view.deleteLater()
    qt_app.processEvents()


def test_navigation_buttons_and_keyboard(window, wait_until):
    assert window.pages.count() == len(ROUTES)
    for index, (key, title, _) in enumerate(ROUTES):
        window.navigate(key)
        assert window.pages.currentIndex() == index and window.heading.text() == title
    window.navigation.setFocus()
    window.navigate("members")
    QTest.keyClick(window.navigation, Qt.Key.Key_Down)
    assert window.heading.text() == "Grup"
    window.navigate("dashboard")
    from PyQt6.QtWidgets import QPushButton
    button = next(b for b in window.pages.currentWidget().findChildren(QPushButton)
                  if b.text() == "Lihat anggota")
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert window.heading.text() == "Anggota"
    wait_until(lambda: window.heartbeat_count >= 1)


def test_diagnostic_failure_retry_cancel_and_safe_close(window, reporter, wait_until):
    window.navigate("diagnostics")
    QTest.mouseClick(window.diagnostics.run_button, Qt.MouseButton.LeftButton)
    assert window.tasks.busy and not window.diagnostics.run_button.isEnabled()
    count = window.heartbeat_count
    window.navigate("members")
    wait_until(lambda: window.heartbeat_count > count)
    QTest.mouseClick(window.diagnostics.cancel_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.tasks.busy)
    assert "dibatalkan" in window.diagnostics.result.text()
    window.tasks.start(lambda ctx: (_ for _ in ()).throw(ValueError("private-ui-error")))
    wait_until(lambda: not window.tasks.busy)
    assert window.error_banner.isVisible()
    assert "private-ui-error" not in window.error_message.text()
    assert "Referensi:" in window.error_message.text()
    window._run_diagnostic(False)
    assert not window.error_banner.isVisible()
    window.close()
    wait_until(lambda: not window.isVisible(), timeout=1500)
    assert not window.tasks.busy and not window.timer.isActive()


def test_worker_repeated_reuse_finishes_cleanup_before_next_task(qt_app, reporter, wait_until):
    controller = TaskController(reporter)
    results, ticks = [], []
    heartbeat = QTimer()
    heartbeat.setInterval(1)
    heartbeat.timeout.connect(lambda: ticks.append(1))
    heartbeat.start()
    controller.succeeded.connect(results.append)
    for index in range(100):
        assert controller.start(lambda ctx, index=index: index)
        wait_until(lambda: not controller.busy)
        assert not controller._join_timer.isActive()
    heartbeat.stop()
    assert results == list(range(100)) and ticks
    assert controller._worker is None and controller._thread is None

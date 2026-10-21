"""UI + real database. Synthetic accounts only, native/offscreen compatible."""
import logging
import os
from datetime import timedelta
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit

from app.models.entities import Role
from app.services.auth import AuthService
from app.services.credential_store import CredentialStore, CredentialStoreError
from app.services.database import DatabaseUnavailable
from app.services.errors import ErrorReporter
from app.settings.config import load_config
from app.ui.session_window import SessionWindow
from app.ui.theme import apply_theme
from tests.test_auth import auth, add_role, OLD, NEW
from tests.test_credentials import MemoryKeyring
from tests.test_database import store

pytestmark = pytest.mark.database


@pytest.fixture
def views(qt_app, wait_until, tmp_path):
    windows = []
    apply_theme(qt_app)
    def create(service, credentials=None):
        logger = logging.Logger("session-ui")
        logger.addHandler(logging.NullHandler())
        reporter = ErrorReporter(logger)
        config = load_config(tmp_path, environ={})
        credentials = credentials or CredentialStore(config, backend=MemoryKeyring())
        window = SessionWindow(config, logger, reporter, service, credentials)
        window.show()
        windows.append(window)
        wait_until(lambda: not window.jobs.tasks.busy, timeout=8000)
        return window
    yield create
    for window in windows:
        window.close()
        wait_until(lambda: not window.isVisible(), timeout=8000)
        assert not window.jobs.tasks.busy
        window.deleteLater()
    qt_app.processEvents()


def idle(window, wait_until):
    wait_until(lambda: not window.jobs.tasks.busy, timeout=10000)


def activate(window):
    # Native window activation is asynchronous; establish this precondition
    # before testing whether background session polling preserves input focus.
    window.raise_()
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window, 5000), 'Native test window did not become active'


def sign_in(window, username, password, wait_until, remember=False):
    window.username.setText(username)
    window.password.setText(password)
    window.remember.setChecked(remember)
    QTest.mouseClick(window.signin_button, Qt.MouseButton.LeftButton)
    idle(window, wait_until)


def change(window, old, new, wait_until):
    window.old_password.setText(old)
    window.new_password.setText(new)
    window.confirm_password.setText(new)
    QTest.mouseClick(window.change_button, Qt.MouseButton.LeftButton)
    idle(window, wait_until)


def screenshot(window, name):
    # Native proof requested explicitly through STARGATE_UI_EVIDENCE; no password fields populated.
    destination = os.environ.get("STARGATE_UI_EVIDENCE")
    if destination:
        path = Path(destination)
        path.mkdir(parents=True, exist_ok=True)
        assert window.grab().save(str(path / name))


def test_login_forced_change_remember_restart_logout_and_error_recovery(store, views, wait_until):
    from database.seed.defaults import seed_defaults
    with store.db.transaction() as session:
        seed_defaults(session)
    service = AuthService(store.db)
    service.bootstrap("root", "Pengelola Uji", OLD)
    view = views(service)
    screenshot(view, "stage-04-login.png")
    sign_in(view, "root", "wrong", wait_until)
    assert view.login is None and "tidak sesuai" in view.login_message.text()
    sign_in(view, "root", OLD, wait_until, remember=True)
    assert view.stack.currentWidget() is view.password_panel
    assert view.shell is None and not view.password.text()
    view.new_password.setText(NEW)
    view.confirm_password.setText("mismatch")
    view.change_password()
    assert "tidak sesuai" in view.password_message.text()
    change(view, OLD, NEW, wait_until)
    assert view.shell is not None and view.credentials.get()
    assert not view.new_password.text() and not view.old_password.text()
    screenshot(view, "stage-04-dashboard.png")
    credentials = view.credentials
    token = view.login.token
    view.close()
    wait_until(lambda: not view.isVisible(), timeout=5000)
    resumed = views(AuthService(store.db), credentials)
    assert resumed.login is not None and resumed.shell
    assert resumed.login.token != token
    resumed.logout()
    idle(resumed, wait_until)
    assert resumed.login is None and resumed.credentials.get() is None
    sign_in(resumed, "root", NEW, wait_until)
    assert resumed.shell is not None
    resumed.open_password()
    resumed._cancel_password()
    assert resumed.stack.currentWidget() is resumed.shell
    resumed.open_password()
    change(resumed, NEW, "Second-change-2026!", wait_until)
    assert resumed.shell is not None


@pytest.mark.parametrize("role", list(Role))
def test_role_navigation_and_direct_denial(auth, views, wait_until, role):
    service, admin, _ = auth
    _, login = add_role(service, admin, role)
    view = views(service)
    sign_in(view, login.principal.username, NEW, wait_until)
    routes = {route[0] for route in view.shell.routes}
    if role == Role.VIEWER:
        assert routes == {"reports"} and view.shell.heading.text() == "Laporan"
        screenshot(view, "stage-04-viewer.png")
    if role != Role.SUPER_ADMIN:
        assert "users" not in routes
        previous = view.shell.heading.text()
        view.navigate("users")
        idle(view, wait_until)
        assert view.shell.heading.text() == previous
        assert "izin" in view.error_message.text()
    else:
        assert "users" in routes
    for route in routes:
        view.shell.navigate(route)
        idle(view, wait_until)
        assert view.shell.routes[view.shell.pages.currentIndex()][0] == route


def test_users_form_create_edit_reset_and_deactivate(auth, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    view.navigate("users")
    idle(view, wait_until)
    page = view.shell.users_page
    assert page.table.rowCount() == 1
    page.username.setText("viewer-ui")
    page.fullname.setText("Pengguna UI")
    page.password.setText(OLD)
    page.role.setCurrentIndex(page.role.findData(Role.VIEWER.value))
    QTest.mouseClick(page.save_button, Qt.MouseButton.LeftButton)
    idle(view, wait_until)
    assert page.table.rowCount() == 2 and not page.password.text()
    index = next(i for i, row in enumerate(page.rows) if row.username == "viewer-ui")
    page.table.selectRow(index)
    assert page.selected_id is not None and not page.password.isEnabled()
    page.fullname.setText("Nama Diperbarui")
    page.save()
    idle(view, wait_until)
    assert any(row.fullname == "Nama Diperbarui" for row in page.rows)
    page.table.selectRow(next(i for i, row in enumerate(page.rows) if row.username == "viewer-ui"))
    temporary = []
    def close_secret():
        modal = QApplication.activeModalWidget()
        if modal is None:
            QTimer.singleShot(20, close_secret)
            return
        temporary.append(modal.findChild(QLineEdit).text())
        modal.reject()
    QTimer.singleShot(20, close_secret)
    page.reset()
    idle(view, wait_until)
    wait_until(lambda: len(temporary) == 1, timeout=5000)
    assert len(temporary) == 1 and len(temporary[0]) >= 12
    assert service.login("viewer-ui", temporary[0]).principal.must_change_password
    assert not page.findChildren(QLineEdit)[-1].text()
    temporary.clear()
    screenshot(view, "stage-04-users.png")
    page.active.setChecked(False)
    page.save()
    idle(view, wait_until)
    assert not next(row for row in page.rows if row.username == "viewer-ui").is_active
    page.new_button.click()
    assert page.selected_id is None and not page.username.text()


def test_idle_background_does_not_extend_session_and_database_failure_locks_ui(auth, views, wait_until, monkeypatch):
    service, _, now = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until, remember=True)
    now[0] += timedelta(minutes=15)
    view._touched = False
    view._check_session()
    idle(view, wait_until)
    assert view.login is None and view.shell is None
    # The local OS entry cannot bypass the server-revoked remember grant.
    restarted = views(service, view.credentials)
    assert restarted.login is None
    sign_in(restarted, "root", NEW, wait_until)
    monkeypatch.setattr(service, "inspect", lambda *a, **kw: (_ for _ in ()).throw(DatabaseUnavailable()))
    restarted._check_session()
    idle(restarted, wait_until)
    assert restarted.login is None and restarted.shell is None
    assert "Database" in restarted.login_message.text()


def test_keychain_unavailable_keeps_password_login_usable(auth, views, wait_until):
    service, _, _ = auth
    class Unavailable:
        def get(self):
            raise CredentialStoreError()
        def set(self, token):
            raise CredentialStoreError()
        def clear(self):
            pass
    view = views(service, Unavailable())
    assert "Ingat saya" in view.login_message.text()
    sign_in(view, "root", NEW, wait_until, remember=True)
    assert view.shell is not None
    assert "Sesi ini tetap" in view.error_message.text()


def test_close_waits_for_login_and_diagnostic_workers(auth, views, wait_until):
    service, _, _ = auth
    view = views(service)
    view.username.setText("root")
    view.password.setText(NEW)
    view.sign_in()
    view.close()
    wait_until(lambda: not view.isVisible(), timeout=8000)
    assert not view.jobs.tasks.busy
    another = views(service)
    sign_in(another, "root", NEW, wait_until)
    another.shell._run_diagnostic()
    assert another.shell.tasks.busy
    another.close()
    wait_until(lambda: not another.isVisible(), timeout=8000)
    assert not another.shell.tasks.busy


def test_first_run_setup_before_login_and_forced_logout(store, views, wait_until):
    from database.seed.defaults import seed_defaults
    from PyQt6.QtWidgets import QPushButton
    with store.db.transaction() as session:
        seed_defaults(session)
    service = AuthService(store.db)
    view = views(service)
    assert view.stack.currentWidget() is view.setup_panel
    assert not any('Super Admin' in button.text() for button in view.login_panel.findChildren(QPushButton))
    # Login cannot bypass first-run setup, including a direct call.
    sign_in(view, "first", OLD, wait_until)
    assert view.login is None and view.stack.currentWidget() is view.setup_panel
    def submit(confirm, password=OLD):
        view.setup_username.setText("first")
        view.setup_fullname.setText("Pengelola Pertama")
        view.setup_password.setText(password)
        view.setup_confirm.setText(confirm)
        view.setup_submit.click()
        idle(view, wait_until)
    submit("mismatch")
    assert "tidak sesuai" in view.setup_message.text()
    assert view.stack.currentWidget() is view.setup_panel
    submit("short", "short")
    assert "12" in view.setup_message.text() and service.bootstrap_required()
    submit(OLD)
    assert view.stack.currentWidget() is view.login_panel
    assert "dibuat" in view.login_message.text() and view.username.text() == "first"
    assert not view.setup_password.text() and not view.setup_confirm.text()
    assert not service.bootstrap_required()
    view.bootstrap()
    assert view.stack.currentWidget() is view.login_panel
    sign_in(view, "first", OLD, wait_until)
    assert view.stack.currentWidget() is view.password_panel
    view._cancel_password()
    idle(view, wait_until)
    assert view.login is None and view.stack.currentWidget() is view.login_panel
    restarted = views(service)
    assert restarted.stack.currentWidget() is restarted.login_panel


@pytest.mark.parametrize("has_admin", [False, True])
def test_startup_database_failure_blocks_setup_and_login_until_retry(store, views, wait_until, monkeypatch, has_admin):
    service = AuthService(store.db)
    if has_admin:
        service.bootstrap("existing", "Pengelola", OLD)
    check = service.bootstrap_required
    def unavailable():
        raise DatabaseUnavailable()
    monkeypatch.setattr(service, "bootstrap_required", unavailable)
    view = views(service)
    assert view.stack.currentWidget() is view.startup_panel
    assert view.startup_retry.isVisible() and "Database" in view.startup_message.text()
    view.bootstrap()
    sign_in(view, "existing", OLD, wait_until)
    assert view.login is None and view.stack.currentWidget() is view.startup_panel
    monkeypatch.setattr(service, "bootstrap_required", check)
    view.startup_retry.click()
    idle(view, wait_until)
    assert view.stack.currentWidget() is (view.login_panel if has_admin else view.setup_panel)


def test_first_run_setup_handles_admin_created_by_another_instance(store, views, wait_until):
    from sqlalchemy import select, func
    from app.models.entities import User
    service = AuthService(store.db)
    view = views(service)
    assert view.stack.currentWidget() is view.setup_panel
    service.bootstrap("other", "Pengelola dari jendela lain", OLD)
    view.setup_username.setText("first")
    view.setup_fullname.setText("Pengelola Pertama")
    view.setup_password.setText(OLD)
    view.setup_confirm.setText(OLD)
    view.setup_submit.click()
    idle(view, wait_until)
    assert view.stack.currentWidget() is view.login_panel and view.login is None
    assert "sudah tersedia" in view.login_message.text()
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert session.scalar(select(User.username)) == "other"


@pytest.mark.parametrize("forced", [True, False])
def test_password_inputs_keep_focus_and_accept_typing_during_session_checks(
        auth, views, wait_until, monkeypatch, forced):
    from threading import Event
    service, admin, _ = auth
    if forced:
        service.create_user(admin.token, "first-login", "Akun Pertama", Role.VIEWER, OLD)
    view = views(service)
    sign_in(view, "first-login" if forced else "root", OLD if forced else NEW, wait_until)
    if not forced:
        view.open_password()
    assert view.stack.currentWidget() is view.password_panel
    view.timer.stop()
    original = service.inspect
    started, release = Event(), Event()
    def slow_inspect(*args, **kwargs):
        started.set()
        release.wait(timeout=3)
        return original(*args, **kwargs)
    monkeypatch.setattr(service, "inspect", slow_inspect)
    activate(view)
    for field in (view.old_password, view.new_password, view.confirm_password):
        started.clear()
        release.clear()
        field.setFocus()
        wait_until(field.hasFocus)
        QTest.keyClicks(field, "before")
        view._check_session()
        try:
            wait_until(started.is_set)
            assert field.isEnabled(), "Session polling disabled the active password input"
            assert field.hasFocus(), "Session polling stole input focus"
            QTest.keyClicks(field, "-during")
        finally:
            release.set()
        idle(view, wait_until)
        assert field.hasFocus(), "Session polling completion changed input focus"
        QTest.keyClicks(field, "-after")
        assert field.text() == "before-during-after"
    assert view.login is not None


@pytest.mark.parametrize("session_valid", [True, False])
def test_user_save_waits_for_poll_and_is_discarded_if_session_fails(
        auth, views, wait_until, monkeypatch, session_valid):
    from threading import Event
    service, admin, _ = auth
    user, _ = add_role(service, admin, Role.VIEWER)
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    view.navigate("users")
    idle(view, wait_until)
    page = view.shell.users_page
    page.table.selectRow(next(i for i, row in enumerate(page.rows) if row.id == user.id))
    page.fullname.setText("Queued edit")
    view.timer.stop()
    original = service.inspect
    started, release = Event(), Event()
    def slow_inspect(*args, **kwargs):
        started.set()
        release.wait(timeout=3)
        if not session_valid:
            raise DatabaseUnavailable()
        return original(*args, **kwargs)
    monkeypatch.setattr(service, "inspect", slow_inspect)
    view._check_session()
    wait_until(started.is_set)
    try:
        page.save_button.click()
        assert view.jobs.queued is not None
        assert not page.save_button.isEnabled()
    finally:
        release.set()
    idle(view, wait_until)
    if session_valid:
        assert next(row for row in page.rows if row.id == user.id).fullname == "Queued edit"
    else:
        assert view.login is None and view.jobs.queued is None
        assert next(row for row in service.users(admin.token) if row.id == user.id).fullname != "Queued edit"

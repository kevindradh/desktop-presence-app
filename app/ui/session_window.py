"""Login/session coordinator. Expensive IO and bcrypt run outside the UI thread."""
from dataclasses import dataclass

from PyQt6.QtCore import QEvent, QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget)

from app.pages.users import UsersPage
from app.pages.administration import GroupsPage, MembersPage, ShiftsPage
from app.pages.devices import DevicesPage
from app.pages.settings import SettingsPage
from app.pages.attendance import AttendancePage
from app.pages.dashboard import DashboardPage
from app.services.dashboard import DashboardService
from app.pages.audit import AuditPage
from app.pages.backups import BackupsPage
from app.services.audit import AuditService
from app.services.backups import BackupService
from app.pages.reports import ReportsPage
from app.services.reports import ReportsService
from app.services.attendance import AttendanceService
from app.services.settings import SettingsService
from app.services.administration import AdministrationService
from app.services.cameras import CameraManager
from app.services.devices import DevicesService
from app.services.enrollment import EnrollmentService
from app.ui.enrollment import EnrollmentDialog
from app.services.auth import AuthError
from app.services.credential_store import CredentialStoreError
from app.services.database import DataConflict, DataValidationError, DatabaseUnavailable
from app.services.tasks import TaskController
from app.ui.main_window import MainWindow
from app.widgets.cards import text_label


EXPECTED = (AuthError, DataConflict, DataValidationError, DatabaseUnavailable, CredentialStoreError)


@dataclass(repr=False)
class Outcome:
    value: object = None
    error: str = ""


class Jobs(QObject):
    interaction_busy_changed = pyqtSignal(bool)

    def __init__(self, reporter, parent):
        super().__init__(parent)
        self.tasks = TaskController(reporter, self)
        self.tasks.succeeded.connect(self._result)
        self.tasks.settled.connect(self._settled)
        self.tasks.busy_changed.connect(self._busy_changed)
        self.callback = None
        self.result = None
        self.blocks_ui = True
        self.queued = None

    def _busy_changed(self, busy):
        if self.blocks_ui:
            self.interaction_busy_changed.emit(busy)

    def discard_queued(self):
        if self.queued is not None:
            self.queued = None
            self.interaction_busy_changed.emit(False)

    def run(self, operation, callback, *, blocks_ui=True):
        if self.tasks.busy:
            if blocks_ui and not self.blocks_ui and self.queued is None:
                self.queued = (operation, callback)
                self.interaction_busy_changed.emit(True)
                return True
            return False
        self.blocks_ui = blocks_ui
        self.result, self.callback = None, callback
        def work(ctx):
            try:
                return Outcome(value=operation())
            except EXPECTED as error:
                return Outcome(error=str(error))
        return self.tasks.start(work)

    def _result(self, result):
        self.result = result

    def _settled(self):
        callback, result = self.callback, self.result
        self.callback = self.result = None
        if callback:
            callback(result or Outcome(error="Proses tidak dapat diselesaikan. Silakan coba lagi."))
        if self.queued is not None and not self.tasks.busy:
            operation, callback = self.queued
            self.queued = None
            self.run(operation, callback)


def secret_field():
    field = QLineEdit()
    field.setEchoMode(QLineEdit.EchoMode.Password)
    field.setMaxLength(256)
    return field


class SessionWindow(QMainWindow):
    def __init__(self, config, logger, reporter, service, credential_store):
        super().__init__()
        self.config, self.logger, self.reporter = config, logger, reporter
        self.service, self.credentials = service, credential_store
        self.administration = AdministrationService(service, config.root)
        self.devices_service = DevicesService(service, config)
        self.settings_service = SettingsService(service)
        self.attendance_service = AttendanceService(service, config, self.devices_service)
        self.dashboard_service = DashboardService(service, config)
        self.reports_service = ReportsService(service, config)
        self.audit_service = AuditService(service)
        self.backup_service = BackupService(service, config.root, config_file=config.config_file, resource_root=config.resource_root)
        self._maintenance = False
        self._retired_shells = []
        self.retire_timer = QTimer(self)
        self.retire_timer.setInterval(50)
        self.retire_timer.timeout.connect(self._clean_retired)
        self.enrollment_service = EnrollmentService(service,config.root,storage_enabled=True,similarity_threshold=config.similarity_threshold)
        self.enrollment_dialog = None
        self.cameras = CameraManager(config, logger, self)
        QApplication.instance().aboutToQuit.connect(self.cameras.shutdown_now)
        self.login = None
        self.shell = None
        self._closing = False
        self._close_ready = False
        self._touched = False
        self._remember_requested = False
        self._entry_state = "checking"
        self.jobs = Jobs(reporter, self)
        self.jobs.interaction_busy_changed.connect(self._busy)
        self.setWindowTitle("StarGate")
        self.resize(1180, 820)
        self.setMinimumSize(1000, 740)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self._build_login()
        self._build_password()
        self._build_setup()
        self._build_startup()
        self.stack.setCurrentWidget(self.startup_panel)
        self.error_banner = self.statusBar()
        self.error_message = text_label("")
        self.statusBar().addWidget(self.error_message, 1)
        reporter.occurred.connect(self._error)
        QApplication.instance().installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._check_session)
        self.timer.start()
        self.checkout_timer = QTimer(self)
        self.checkout_timer.setInterval(10000)
        self.checkout_timer.timeout.connect(self._auto_checkout)
        self.checkout_timer.start()
        self.logger.info("Login window opened")
        QTimer.singleShot(0, self._initialize)

    def _panel(self, title, description=""):
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.addStretch()
        center = QHBoxLayout()
        center.addStretch()
        card = QWidget()
        card.setMaximumWidth(540)
        form = QVBoxLayout(card)
        form.setSpacing(18)
        brand = text_label("StarGate", "pageTitle")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setContentsMargins(0, 0, 0, 24)
        form.addWidget(brand)
        form.addWidget(text_label(title, "pageTitle"))
        if description:
            form.addWidget(text_label(description))
        center.addWidget(card, 1)
        center.addStretch()
        outer.addLayout(center)
        outer.addStretch()
        self.stack.addWidget(container)
        return container, form

    def _build_login(self):
        self.login_panel, body = self._panel("Masuk")
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.username, self.password = QLineEdit(), secret_field()
        self.username.setMaxLength(80)
        self.username.setAccessibleName("Username")
        self.password.setAccessibleName("Password")
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)
        body.addLayout(form)
        self.remember = QCheckBox("Ingat saya")
        body.addWidget(self.remember)
        self.signin_button = QPushButton("Masuk")
        self.signin_button.setProperty("variant", "primary")
        body.addWidget(self.signin_button)
        self.login_message = text_label("")
        body.addWidget(self.login_message)
        self.signin_button.clicked.connect(self.sign_in)
        self.password.returnPressed.connect(self.sign_in)

    def _build_startup(self):
        self.startup_panel, body = self._panel("Menyiapkan aplikasi")
        self.startup_message = text_label("Memeriksa akun pengelola…")
        self.startup_retry = QPushButton("Coba lagi")
        self.startup_retry.clicked.connect(self._initialize)
        self.startup_retry.hide()
        body.addWidget(self.startup_message)
        body.addWidget(self.startup_retry)

    def _build_setup(self):
        self.setup_panel, body = self._panel("Buat Super Admin",
            "Buat akun pengelola pertama untuk menggunakan aplikasi.")
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.setup_username, self.setup_fullname = QLineEdit(), QLineEdit()
        self.setup_password, self.setup_confirm = secret_field(), secret_field()
        self.setup_username.setMaxLength(80)
        for title, widget in (("Username", self.setup_username), ("Nama lengkap", self.setup_fullname),
                              ("Password", self.setup_password), ("Ulangi password", self.setup_confirm)):
            form.addRow(title, widget)
        body.addLayout(form)
        self.setup_submit = QPushButton("Buat akun")
        self.setup_submit.setProperty("variant", "primary")
        self.setup_close = QPushButton("Tutup aplikasi")
        self.setup_message = text_label("")
        body.addWidget(self.setup_submit)
        body.addWidget(self.setup_close)
        body.addWidget(self.setup_message)
        self.setup_submit.clicked.connect(self.bootstrap)
        self.setup_confirm.returnPressed.connect(self.bootstrap)
        self.setup_close.clicked.connect(self.close)

    def _build_password(self):
        self.password_panel, body = self._panel("Ganti password",
            "Password baru harus 12–72 byte UTF-8 dan berbeda dari password saat ini.")
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.old_password, self.new_password, self.confirm_password = (secret_field() for _ in range(3))
        form.addRow("Password saat ini", self.old_password)
        form.addRow("Password baru", self.new_password)
        form.addRow("Ulangi password baru", self.confirm_password)
        body.addLayout(form)
        self.change_button, self.cancel_change = QPushButton("Simpan password"), QPushButton("Kembali")
        body.addWidget(self.change_button)
        body.addWidget(self.cancel_change)
        self.password_message = text_label("")
        body.addWidget(self.password_message)
        self.change_button.clicked.connect(self.change_password)
        self.cancel_change.clicked.connect(self._cancel_password)

    def _busy(self, busy):
        self.login_panel.setEnabled(not busy)
        self.password_panel.setEnabled(not busy)
        self.setup_panel.setEnabled(not busy)
        self.startup_retry.setEnabled(not busy)
        if self.shell:
            self.shell.navigation.setEnabled(not busy)
            if self.shell.users_page:
                self.shell.users_page.setEnabled(not busy)
            self.shell.logout_button.setEnabled(not busy)
            self.shell.password_button.setEnabled(not busy)

    def _error(self, incident):
        self.error_message.setText(f"{incident.message} Referensi: {incident.reference}")

    def _message(self, text):
        self.error_message.setText(text)
        self.login_message.setText(text)
        self.password_message.setText(text)
        if self.shell and self.shell.users_page:
            self.shell.users_page.message.setText(text)

    def _initialize(self):
        if self.login or self._closing or self.jobs.tasks.busy:
            return
        self._entry_state = "checking"
        self.stack.setCurrentWidget(self.startup_panel)
        self.startup_message.setText("Memeriksa akun pengelola…")
        self.startup_retry.hide()
        def done(result):
            if self._closing:
                return
            if result.error:
                self.startup_message.setText(result.error)
                self.startup_retry.show()
            elif result.value:
                self._entry_state = "setup"
                self.stack.setCurrentWidget(self.setup_panel)
                self.setup_username.setFocus()
            else:
                self._entry_state = "login"
                self.stack.setCurrentWidget(self.login_panel)
                self._restore()
        self.jobs.run(self.service.bootstrap_required, done)

    def _restore(self):
        if self.login or self._closing or self._entry_state != "login":
            return
        def operation():
            token = self.credentials.get()
            if not token:
                return None
            try:
                result = self.service.resume(token)
            except AuthError:
                self.service.forget(token)
                self.credentials.clear()
                return None
            return result
        def done(result):
            if result.error:
                self._message(result.error)
            elif result.value:
                self._remember_requested = True
                self._accepted(result.value)
        self.jobs.run(operation, done)

    def sign_in(self):
        if self.jobs.tasks.busy or self._entry_state != "login":
            return
        username, password = self.username.text(), self.password.text()
        self.password.clear()
        self._remember_requested = self.remember.isChecked()
        def operation():
            # An explicit login replaces any remembered account on this workstation.
            try:
                previous = self.credentials.get()
            except CredentialStoreError:
                previous = None
            if previous:
                self.service.forget(previous)
            self.credentials.clear()
            return self.service.login(username, password)
        def done(result):
            if result.error:
                self._message(result.error)
            else:
                self._accepted(result.value)
        self.jobs.run(operation, done)

    def _accepted(self, login):
        self._entry_state = "login"
        self.login = login
        self._touched = False
        self._message("")
        if self._remember_requested:
            self._save_remember()
        else:
            self._open_shell()

    def _save_remember(self):
        def operation():
            grant = self.service.remember(self.login.token)
            try:
                self.credentials.set(grant.token)
            except CredentialStoreError:
                self.service.forget(grant.token)
                return "Ingat saya tidak tersedia. Sesi ini tetap dapat digunakan."
        def done(result):
            if result.error:
                self._return_login(result.error)
            else:
                self._open_shell()
                if result.value:
                    self._message(result.value)
        self.jobs.run(operation, done)

    def _discard_shell(self):
        self.reports_service.clear()
        self.stop_enrollment()
        self.stop_attendance()
        self.cameras.stop_all()
        shell, self.shell = self.shell, None
        if shell:
            self.stack.removeWidget(shell)
            shell.hide()
            shell.timer.stop()
            if shell.tasks.busy:
                shell.tasks.cancel()
            self._retired_shells.append(shell)
            self.retire_timer.start()

    def _clean_retired(self):
        for shell in list(self._retired_shells):
            if not shell.tasks.busy and not any(getattr(page, 'busy', False) for page in shell.administrative_pages.values()):
                self._retired_shells.remove(shell)
                shell.deleteLater()
        if not self._retired_shells:
            self.retire_timer.stop()

    def _open_shell(self):
        self._discard_shell()
        users = UsersPage(self) if self.login.principal.role.value == "SUPER_ADMIN" else None
        from app.services.auth import PERMISSIONS
        administrative_pages = {route: page(self) for route, page in (
            ("groups", GroupsPage), ("shifts", ShiftsPage), ("members", MembersPage), ("devices", DevicesPage), ("settings", SettingsPage), ("attendance", AttendancePage), ("dashboard", DashboardPage), ("reports", ReportsPage), ("audit", AuditPage), ("backup", BackupsPage))
            if route in PERMISSIONS[self.login.principal.role]}
        self.shell = MainWindow(self.config, self.logger, self.reporter, self.login.principal,
                                self.navigate, users_page=users, administrative_pages=administrative_pages)
        self.shell.setWindowFlags(Qt.WindowType.Widget)
        self.shell.password_button.clicked.connect(self.open_password)
        self.shell.logout_button.clicked.connect(self.logout)
        self.stack.addWidget(self.shell)
        self.stack.setCurrentWidget(self.shell)
        QTimer.singleShot(0, self._auto_checkout)

    def _auto_checkout(self):
        if self._maintenance or not self.login or not self.shell or self.stack.currentWidget() is not self.shell or self._closing or self.jobs.tasks.busy:
            return
        from app.services.auth import PERMISSIONS
        if 'attendance' not in PERMISSIONS[self.login.principal.role]:
            return
        token = self.login.token
        def done(result):
            if not self.login or self.login.token != token:
                return
            if result.error:
                self._handle_denial(result.error)
            elif result.value:
                self._message(f'{result.value} sesi ditutup otomatis sesuai akhir shift.')
        self.jobs.run(lambda: self.attendance_service.auto_checkout(token), done, blocks_ui=False)

    def navigate(self, route):
        if self._maintenance or not self.login or (self.jobs.tasks.busy and self.jobs.blocks_ui):
            return
        def done(result):
            if result.error:
                self._handle_denial(result.error)
            elif self.shell:
                if result.value.role != self.login.principal.role:
                    self._return_login("Hak akses berubah. Silakan masuk kembali.")
                    return
                self.shell.show_route(route)
                if route == "users":
                    self.refresh_users()
                elif route in self.shell.administrative_pages:
                    self.shell.administrative_pages[route].reload()
        self.jobs.run(lambda: self.service.authorize(self.login.token, route), done)

    def _handle_denial(self, error):
        if "Sesi berakhir" in error or error.startswith("Database "):
            self._return_login(error)
        else:
            self._message(error)

    def open_password(self):
        if (self.jobs.tasks.busy and self.jobs.blocks_ui) or not self.login:
            return
        self.cameras.stop_all()
        self.stop_attendance()
        self.stop_enrollment()
        self.old_password.clear()
        self.new_password.clear()
        self.confirm_password.clear()
        self.password_message.setText("")
        self.stack.setCurrentWidget(self.password_panel)

    def _cancel_password(self):
        self.stack.setCurrentWidget(self.shell)

    def change_password(self):
        if (self.jobs.tasks.busy and self.jobs.blocks_ui) or not self.login:
            return
        old, new = self.old_password.text(), self.new_password.text()
        if new != self.confirm_password.text():
            self.password_message.setText("Pengulangan password baru tidak sesuai.")
            return
        for field in (self.old_password, self.new_password, self.confirm_password):
            field.clear()
        token = self.login.token
        def operation():
            result = self.service.change_password(token, old, new)
            self.credentials.clear()
            return result
        def done(result):
            if result.error:
                self._handle_denial(result.error)
            else:
                self._accepted(result.value)
        self.jobs.run(operation, done)

    def bootstrap(self):
        if self.jobs.tasks.busy or self._closing or self._entry_state != "setup":
            return
        name, full = self.setup_username.text(), self.setup_fullname.text()
        value = self.setup_password.text()
        if value != self.setup_confirm.text():
            self.setup_message.setText("Pengulangan password tidak sesuai.")
            return
        self.setup_password.clear()
        self.setup_confirm.clear()
        self.setup_message.setText("")
        def operation():
            try:
                self.service.bootstrap(name, full, value)
            except (DataConflict, DataValidationError):
                # Another instance may have finished setup while this form was open.
                if not self.service.bootstrap_required():
                    return False
                raise
            return True
        def done(result):
            if self._closing:
                return
            if result.error:
                self.setup_message.setText(result.error)
            else:
                self.setup_username.clear()
                self.setup_fullname.clear()
                self._entry_state = "login"
                self.stack.setCurrentWidget(self.login_panel)
                if result.value:
                    self.username.setText(name)
                self._message("Super Admin dibuat. Silakan masuk." if result.value
                    else "Super Admin sudah tersedia. Silakan masuk dengan akun yang sudah dibuat.")
        self.jobs.run(operation, done)

    def refresh_users(self):
        if not self.login:
            return
        token = self.login.token
        def done(result):
            if result.error:
                self._handle_denial(result.error)
            elif self.shell and self.shell.users_page:
                self.shell.users_page.display(result.value)
        self.jobs.run(lambda: self.service.users(token), done)

    def _user_action(self, operation):
        def done(result):
            if result.error:
                self._handle_denial(result.error)
            else:
                self.refresh_users()
        self.jobs.run(operation, done)

    def create_user(self, *args):
        token = self.login.token
        self._user_action(lambda: self.service.create_user(token, *args))

    def update_user(self, *args):
        token = self.login.token
        self._user_action(lambda: self.service.update_user(token, *args))

    def reset_user(self, user_id):
        token = self.login.token
        def done(result):
            if result.error:
                self._handle_denial(result.error)
                return
            dialog = QDialog(self)
            dialog.setWindowTitle("Password hasil reset — tampil sekali")
            form = QFormLayout(dialog)
            form.addRow(text_label("Sampaikan password ini kepada pemilik akun. Pengguna dapat menggantinya melalui menu Ganti password."))
            value = QLineEdit(result.value.value)
            value.setReadOnly(True)
            form.addRow("Password baru", value)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(dialog.reject)
            form.addRow(buttons)
            def clear_secret():
                value.clear()
                dialog.deleteLater()
            dialog.finished.connect(clear_secret)
            # open() avoids a nested Cocoa modal event loop in a worker-result slot.
            dialog.open()
        self.jobs.run(lambda: self.service.reset_password(token, user_id), done)

    def logout(self):
        self.stop_enrollment()
        self.stop_attendance()
        if self._maintenance or not self.login or (self.jobs.tasks.busy and self.jobs.blocks_ui):
            return
        token = self.login.token
        self.cameras.stop_all()
        # Hide protected content immediately, even if DB is temporarily unavailable.
        self.stack.setCurrentWidget(self.login_panel)
        def operation():
            try:
                self.service.logout(token)
            finally:
                self.credentials.clear()
        def done(result):
            self._return_login(result.error or "Anda telah keluar.")
        self.jobs.run(operation, done)

    def _return_login(self, message):
        self._entry_state = "login"
        self.jobs.discard_queued()
        for dialog in self.findChildren(QDialog):
            dialog.reject()
        self.login = None
        self._discard_shell()
        self.password.clear()
        self.remember.setChecked(False)
        self.stack.setCurrentWidget(self.login_panel)
        self._message(message)

    def eventFilter(self, watched, event):
        if self.login and event.type() in {QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress,
                                            QEvent.Type.Wheel, QEvent.Type.TouchBegin}:
            if isinstance(watched, QWidget) and (watched is self or self.isAncestorOf(watched)):
                self._touched = True
        return super().eventFilter(watched, event)

    def _check_session(self):
        if self._maintenance or not self.login or self.jobs.tasks.busy or self._closing:
            return
        # Only real input renews idle time. Timer/worker progress never counts.
        touch, self._touched = self._touched, False
        token = self.login.token
        def done(result):
            if result.error:
                self._return_login(result.error)
            elif result.value.role != self.login.principal.role:
                self.logout()
        self.jobs.run(lambda: self.service.inspect(token, touch=touch), done, blocks_ui=False)

    def closeEvent(self, event):
        if self._close_ready:
            self.timer.stop()
            self.checkout_timer.stop()
            self.retire_timer.stop()
            if self.shell:
                self.shell.timer.stop()
            QApplication.instance().removeEventFilter(self)
            self.logger.info("Session window closed cleanly")
            event.accept()
            return
        self._closing = True
        self.timer.stop()
        self.checkout_timer.stop()
        self.cameras.stop_all()
        self.stop_enrollment()
        self.stop_attendance()
        self.setEnabled(False)
        if self.shell:
            for page in self.shell.administrative_pages.values():
                if hasattr(page, 'on_leave'):page.on_leave()
        if self.cameras.busy or (self.enrollment_dialog is not None and self.enrollment_dialog.busy):
            QTimer.singleShot(50, self.close)
            event.ignore()
            return
        if self.jobs.tasks.busy:
            QTimer.singleShot(50, self.close)
            event.ignore()
            return
        if self._retired_shells or (self.shell and any(getattr(page, 'busy', False) for page in self.shell.administrative_pages.values())):
            QTimer.singleShot(50, self.close)
            event.ignore()
            return
        if self.shell and self.shell.tasks.busy:
            self.shell.tasks.cancel()
            QTimer.singleShot(50, self.close)
            event.ignore()
            return
        if self.login:
            token = self.login.token
            self.login = None
            def done(result):
                self._close_ready = True
                self.close()
            self.jobs.run(lambda: self.service.close_session(token), done)
            event.ignore()
            return
        self._close_ready = True
        self.closeEvent(event)

    def stop_enrollment(self):
        if self.enrollment_dialog is not None:
            self.enrollment_dialog.reject()

    def open_enrollment(self,binding,fields,page):
        if not self.login or self._closing:
            self.enrollment_service.cancel(binding)
            return
        self.cameras.stop_all()
        self.stop_attendance()
        dialog=EnrollmentDialog(self,binding,fields)
        self.enrollment_dialog=dialog
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.saved.connect(page.changed)
        def finished(unused):
            if self.enrollment_dialog is dialog:
                self.enrollment_dialog=None
            dialog.deleteLater()
        dialog.finished.connect(finished)
        dialog.open()

    def stop_attendance(self):
        self.attendance_service.cancel_all()
        if self.shell:
            page = self.shell.administrative_pages.get('attendance')
            if page:
                page.stop()

from datetime import datetime
from functools import partial
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QTimer, Qt, pyqtSlot
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow,
                             QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

from app.pages.diagnostics import DiagnosticsPage
from app.pages.overview import OverviewPage, PlaceholderPage
from app.services.diagnostics import run_diagnostic
from app.services.tasks import TaskController
from app.widgets.cards import text_label
from app.widgets.toast import Toast


ROUTES = (
    ("dashboard", "Dashboard", "Ringkasan ruang kerja"),
    ("members", "Anggota", "Registrasi, data anggota, dan riwayat kehadiran."),
    ("groups", "Grup", "Pengelompokan anggota berdasarkan kelas atau bagian."),
    ("shifts", "Shift", "Jadwal, toleransi keterlambatan, dan aturan kehadiran."),
    ("devices", "Perangkat", "Pengaturan webcam dan kamera jaringan."),
    ("attendance", "Kehadiran", "Pencatatan masuk, keluar, dan istirahat menggunakan wajah."),
    ("reports", "Laporan", "Rekap kehadiran dan ekspor Excel maupun PDF."),
    ("settings", "Pengaturan", "Pengaturan pengenalan wajah dan kebijakan absensi."),
    ("users", "Pengguna", "Pengelolaan akun dan hak akses aplikasi."),
    ("audit", "Audit aktivitas", "Inspeksi aktivitas penting dan perubahan data."),
    ("backup", "Cadangan dan pemulihan", "Cadangan terenkripsi dan pemulihan data aplikasi."),
    ("diagnostics", "Pemeriksaan aplikasi", "Uji fondasi aplikasi tanpa mengubah data."),
)


class MainWindow(QMainWindow):
    def __init__(self, config, logger, reporter, principal, navigation_guard, *, users_page=None, administrative_pages=None, toast=None):
        super().__init__()
        from app.services.auth import PERMISSIONS
        self.principal = principal
        self.navigation_guard = navigation_guard
        self.routes = tuple(route for route in ROUTES if route[0] in PERMISSIONS[principal.role])
        self.users_page = users_page
        self.administrative_pages = administrative_pages or {}
        self.config, self.logger, self.reporter = config, logger, reporter
        self.toast = toast if toast is not None else Toast(self)
        self.setWindowTitle("StarGate")
        self.resize(1180, 820)
        self.setMinimumSize(1000, 740)
        self._closing = False
        self.heartbeat_count = 0
        self.tasks = TaskController(reporter, self)
        self._build_ui()
        self.tasks.progress.connect(self.diagnostics.progress.setValue)
        self.tasks.busy_changed.connect(self.diagnostics.set_busy)
        self.tasks.succeeded.connect(self.diagnostics.on_success)
        self.tasks.cancelled.connect(self.diagnostics.on_cancelled)
        self.tasks.settled.connect(self._on_settled)
        self.reporter.occurred.connect(self._on_error)
        self.diagnostics.requested.connect(self._run_diagnostic)
        self.diagnostics.cancel_requested.connect(self.tasks.cancel)
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._tick)
        self._tick()
        self.timer.start()
        self.show_route(self.routes[0][0])
        self.logger.info("Application shell opened")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(272)
        rail = QVBoxLayout(sidebar)
        rail.setContentsMargins(18, 30, 18, 20)
        rail.setSpacing(12)
        brand = text_label("StarGate", wrap=False)
        brand.setObjectName("brand")
        rail.addWidget(brand)
        hint = text_label("FACE RECOGNITION ATTENDANCE")
        hint.setObjectName("brandHint")
        rail.addWidget(hint)
        rail.addSpacing(20)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setAccessibleName("Navigasi utama")
        for _, title, _ in self.routes:
            self.navigation.addItem(title)
        self.navigation.currentRowChanged.connect(self._navigate_index)
        rail.addWidget(self.navigation, 1)
        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        foot = QVBoxLayout(footer)
        foot.setContentsMargins(15, 14, 15, 14)
        foot.addWidget(text_label(self.principal.fullname))
        foot.addWidget(text_label(self.principal.role.value.replace("_", " ")))
        self.password_button = QPushButton("Ganti password")
        self.logout_button = QPushButton("Keluar akun")
        foot.addWidget(self.password_button)
        foot.addWidget(self.logout_button)
        rail.addWidget(footer)
        row.addWidget(sidebar)
        workspace = QWidget()
        workspace.setObjectName("workspace")
        body = QVBoxLayout(workspace)
        body.setContentsMargins(32, 25, 32, 22)
        body.setSpacing(22)
        header = QHBoxLayout()
        self.heading = text_label("Dashboard", "pageTitle")
        header.addWidget(self.heading, 1)
        self.clock = text_label("", "muted", wrap=False)
        self.clock.setMinimumWidth(self.clock.fontMetrics().horizontalAdvance(
            "18 Oct 2026  20:00") + 18)
        header.addWidget(self.clock)
        body.addLayout(header)
        self.error_banner = self.toast
        self.error_message = self.toast.message
        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
        self.diagnostics = DiagnosticsPage()
        for key, title, description in self.routes:
            if key in self.administrative_pages:
                page = self.administrative_pages[key]
            elif key == "dashboard":
                page = OverviewPage(self.navigate)
            elif key == "diagnostics":
                page = self.diagnostics
            elif key == "users" and self.users_page is not None:
                page = self.users_page
            elif key in self.administrative_pages:
                page = self.administrative_pages[key]
            else:
                page = PlaceholderPage(title, description)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
        body.addWidget(self.pages, 1)
        row.addWidget(workspace, 1)

    def navigate(self, route):
        self.navigation_guard(route)

    def show_route(self, route):
        index = next((i for i, item in enumerate(self.routes) if item[0] == route), None)
        if index is None:
            return
        current = self.routes[self.pages.currentIndex()][0]
        if current != route:
            old_page = self.administrative_pages.get(current)
            if old_page is not None and hasattr(old_page, "on_leave"):
                old_page.on_leave()
        self.navigation.blockSignals(True)
        self.navigation.setCurrentRow(index)
        self.navigation.blockSignals(False)
        self.pages.setCurrentIndex(index)
        self.heading.setText(self.routes[index][1])
        self.logger.info("Page opened route=%s", route)

    @pyqtSlot(int)
    def _navigate_index(self, index):
        if 0 <= index < len(self.routes):
            self.navigate(self.routes[index][0])

    @pyqtSlot()
    def _tick(self):
        self.heartbeat_count += 1
        self.diagnostics.heartbeat.setText(f"Antarmuka aktif · {self.heartbeat_count}")
        self.clock.setText(datetime.now(ZoneInfo(self.config.timezone)).strftime("%d %b %Y  %H:%M"))

    @pyqtSlot(bool)
    def _run_diagnostic(self, fail=False):
        self.toast.dismiss()
        self.tasks.start(partial(run_diagnostic, fail=fail))

    @pyqtSlot(object)
    def _on_error(self, incident):
        text = f"{incident.message} Referensi: {incident.reference}"
        self.toast.show_message(text)

    @pyqtSlot()
    def _on_settled(self):
        if self._closing:
            self.close()

    def closeEvent(self, event):
        if self.tasks.busy:
            self._closing = True
            self.tasks.cancel()
            self.toast.show_message("Menunggu proses berhenti sebelum menutup aplikasi…")
            self.setEnabled(False)
            event.ignore()
            return
        self.timer.stop()
        self.logger.info("Application shell closed cleanly")
        event.accept()

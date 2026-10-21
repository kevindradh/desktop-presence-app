"""Viewer-only report sandbox: automatically prepared, no camera access."""
from PyQt6.QtWidgets import QLabel,QToolBar
from app.ui.attendance_demo import NoCredentials
from app.ui.session_window import SessionWindow
from database.attendance_demo import synthetic_camera


class ReportsDemo(SessionWindow):
    def __init__(self,config,logger,reporter,data):
        super().__init__(config,logger,reporter,data.auth,NoCredentials())
        self.reports_service.clock=data.clock.now
        self.cameras.capture_target=synthetic_camera
        self._accepted(data.login)
        self.setWindowTitle('StarGate - DEMO Laporan Tahap 12')
        self.checkout_timer.stop()
        toolbar=QToolBar('Demo laporan',self);toolbar.setMovable(False)
        notice=QLabel(' DEMO SINTETIS - Akun Viewer - 65 baris, dua halaman - Ekspor memuat seluruh hasil filter ')
        notice.setWordWrap(True);toolbar.addWidget(notice);self.addToolBar(toolbar)
        self.page=self.shell.administrative_pages['reports']
        self.auto_load=True
        self.page.tasks.settled.connect(self.prepared)

    def prepared(self):
        if self.auto_load and not self._closing:
            self.auto_load=False
            self.page.load()

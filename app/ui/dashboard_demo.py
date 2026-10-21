"""Fast Stage 11 review using a real shell and another service/terminal writer."""
import copy
from functools import partial
import multiprocessing as mp

from PyQt6.QtWidgets import QLabel, QPushButton, QToolBar
from app.services.attendance import AttendanceService
from app.services.auth import AuthService
from app.services.devices import DevicesService
from app.ui.attendance_demo import NoCredentials
from app.ui.session_window import SessionWindow
from database.attendance_demo import SyntheticTarget, begin, scan, synthetic_camera


class DashboardDemo(SessionWindow):
    def __init__(self, config, logger, reporter, data):
        super().__init__(config, logger, reporter, data.auth, NoCredentials())
        self.data=data
        self.dashboard_service.clock=data.clock.now
        self.attendance_service=data.service
        self.cameras.capture_target=synthetic_camera
        self._accepted(data.login)
        self.setWindowTitle('StarGate — DEMO Dashboard Tahap 11')
        self.choice=mp.get_context('spawn').Value('i',0)
        self.shell.administrative_pages['attendance'].target_factory=partial(SyntheticTarget,choice=self.choice)
        self.checkout_timer.stop()
        toolbar=QToolBar('Kontrol demo',self)
        toolbar.setMovable(False)
        toolbar.addWidget(QLabel(' DEMO SINTETIS • Database test • '))
        self.scan_button=QPushButton('Simulasikan check-in terminal lain')
        self.end_button=QPushButton('Majukan ke akhir shift')
        self.demo_status=QLabel('08:11 WIB • waktu simulasi')
        toolbar.addWidget(self.scan_button)
        toolbar.addWidget(self.end_button)
        toolbar.addWidget(self.demo_status)
        self.addToolBar(toolbar)
        self.scan_button.clicked.connect(self.external_scan)
        self.end_button.clicked.connect(self.finish_shift)

    def external_scan(self):
        if self.jobs.tasks.busy and (self.jobs.blocks_ui or self.jobs.queued is not None):
            self.demo_status.setText('Tunggu proses saat ini selesai, lalu coba lagi.')
            return
        other=copy.copy(self.data)
        other.auth=AuthService(self.data.auth.database)
        other.service=AttendanceService(other.auth,self.config,DevicesService(other.auth,self.config),clock=self.data.clock.now)
        self.scan_button.setEnabled(False)
        self.end_button.setEnabled(False)
        def operation():
            try:
                return scan(other,begin(other,'IN'))
            finally:
                other.service.cancel_all()
        def done(result):
            self.scan_button.setEnabled(True)
            self.end_button.setEnabled(True)
            self.demo_status.setText(result.error or result.value.message)
            # Intentionally no dashboard.reload(): its own polling must discover this commit.
        self.jobs.run(operation,done)

    def finish_shift(self):
        if self.jobs.tasks.busy:
            self.demo_status.setText('Tunggu proses saat ini selesai, lalu coba lagi.')
            return
        now=self.data.clock.now()
        self.data.clock.advance(max(0,(now.replace(hour=17,minute=0,second=0)-now).total_seconds()))
        self.demo_status.setText('Waktu absensi simulasi 17:00 WIB • tunggu pembaruan otomatis')

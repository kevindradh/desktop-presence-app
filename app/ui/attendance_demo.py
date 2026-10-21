"""User-driven synthetic attendance sandbox and one-click scenario runner."""
import json
import multiprocessing as mp
from datetime import datetime, timezone
from functools import partial
from zoneinfo import ZoneInfo

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget)

from app.services.tasks import TaskController
from app.ui.session_window import SessionWindow
from database.attendance_demo import SCENARIOS, SyntheticTarget, run_scenario, synthetic_camera


class NoCredentials:
    def get(self): return None
    def clear(self): pass
    def set(self, token):
        from app.services.credential_store import CredentialStoreError
        raise CredentialStoreError()


class AttendanceDemo(QMainWindow):
    def __init__(self, config, logger, reporter, data):
        super().__init__()
        self.config, self.data = config, data
        self.results = {}
        self.queue = []
        self.closing = False
        self.setWindowTitle('StarGate — DEMO Tahap 10 (data sintetis)')
        self.resize(1240, 880)
        body = QWidget()
        layout = QVBoxLayout(body)
        notice = QLabel('MODE DEMO • Data otomatis di database test terpisah • Kamera/wajah sintetis • Data kerja tidak diubah')
        notice.setWordWrap(True)
        notice.setStyleSheet('background:#fff0d9;color:#684719;padding:10px;')
        layout.addWidget(notice)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.setCentralWidget(body)

        panel = QWidget()
        column = QVBoxLayout(panel)
        hint = QLabel('Klik Jalankan semua. Setiap skenario menyiapkan data baru, menjalankan layanan absensi asli, dan memeriksa riwayat PostgreSQL.\nWaktu dimajukan dalam simulasi; Anda tidak perlu menunggu 60 detik atau mengganti jam komputer.')
        hint.setWordWrap(True)
        column.addWidget(hint)
        buttons = QHBoxLayout()
        self.run_all = QPushButton('Jalankan semua (9 skenario)')
        self.run_selected = QPushButton('Jalankan yang dipilih')
        self.export = QPushButton('Simpan hasil JSON')
        for button in (self.run_all, self.run_selected, self.export):
            buttons.addWidget(button)
        column.addLayout(buttons)
        self.table = QTableWidget(len(SCENARIOS), 3)
        self.table.setHorizontalHeaderLabels(['Skenario', 'Status', 'Ringkasan'])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        for index, (title, _) in enumerate(SCENARIOS):
            for field, text in enumerate((title, 'BELUM DIUJI', '')):
                self.table.setItem(index, field, QTableWidgetItem(text))
        self.table.setColumnWidth(0, 380)
        self.table.setColumnWidth(1, 130)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.selectRow(0)
        column.addWidget(self.table)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(180)
        column.addWidget(self.details)
        column.addWidget(QLabel('LULUS di sini membuktikan alur sintetis. Akurasi wajah, foto/replay, kamera dan speaker nyata tetap diuji terpisah.'))
        self.tabs.addTab(panel, 'Uji otomatis')

        interactive = QWidget()
        live = QVBoxLayout(interactive)
        controls = QHBoxLayout()
        self.face = QComboBox()
        self.face.addItems(['Peserta terdaftar (sintetis)', 'Wajah tidak dikenal', 'Spoof sintetis', 'Tidak ada wajah'])
        self.choice = mp.get_context('spawn').Value('i', 0)
        self.face.currentIndexChanged.connect(self.change_face)
        controls.addWidget(self.face)
        self.clock_label = QLabel()
        controls.addWidget(self.clock_label)
        self.advance = QPushButton('+61 detik simulasi')
        self.end_shift = QPushButton('Ke akhir shift (17:00)')
        controls.addWidget(self.advance)
        controls.addWidget(self.end_shift)
        live.addLayout(controls)
        guide = QLabel('Data anggota, lima embedding, shift dan dua kamera sudah siap. Pilih kamera, centang persetujuan, lalu Mulai absensi.\nUntuk scan berikutnya: pilih Tidak ada wajah selama >1 detik, klik +61 detik, lalu pilih peserta lagi. Setelah OUT, tutup/buka demo untuk sesi baru.')
        guide.setWordWrap(True)
        live.addWidget(guide)
        self.session = SessionWindow(config, logger, reporter, data.auth, NoCredentials())
        self.session.setWindowFlags(Qt.WindowType.Widget)
        self.session.attendance_service = data.service
        self.session.cameras.capture_target = synthetic_camera
        self.session._accepted(data.login)
        self.session.checkout_timer.stop()  # Controlled explicitly by demo time actions.
        self.page = self.session.shell.administrative_pages['attendance']
        self.page.target_factory = partial(SyntheticTarget, choice=self.choice)
        self.session.shell.show_route('attendance')
        self.page.reload()
        live.addWidget(self.session)
        self.tabs.addTab(interactive, 'Coba halaman Kehadiran')
        self.update_clock()
        self.advance.clicked.connect(lambda: self.advance_time(61))
        self.end_shift.clicked.connect(self.advance_to_end)

        self.tasks = TaskController(reporter, self)
        self.tasks.succeeded.connect(self.received)
        self.tasks.settled.connect(self.next_scenario)
        self.run_all.clicked.connect(lambda: self.start(list(range(len(SCENARIOS)))))
        self.run_selected.clicked.connect(lambda: self.start([self.table.currentRow()]))
        self.export.clicked.connect(self.save_results)
        self.table.itemSelectionChanged.connect(self.show_details)
        self.close_timer = QTimer(self)
        self.close_timer.setInterval(50)
        self.close_timer.timeout.connect(self.close)

    def change_face(self, index):
        self.choice.value = index

    def update_clock(self):
        self.clock_label.setText(self.data.clock.now().strftime('%d/%m/%Y %H:%M:%S WIB'))

    def advance_time(self, seconds):
        if self.session.jobs.tasks.busy or self.page.pending:
            self.session._message('Tunggu proses saat ini selesai, lalu majukan waktu.')
            return
        self.data.clock.advance(seconds)
        self.update_clock()
        self.session._auto_checkout()

    def advance_to_end(self):
        now = self.data.clock.now()
        self.advance_time(max(0, (now.replace(hour=17, minute=0, second=0)-now).total_seconds()))

    def start(self, indices):
        if self.tasks.busy or self.queue or self.closing:
            return
        self.queue = [index for index in indices if 0 <= index < len(SCENARIOS)]
        self.run_all.setEnabled(False)
        self.run_selected.setEnabled(False)
        self.export.setEnabled(False)
        self.next_scenario()

    def next_scenario(self):
        if self.closing:
            return
        if not self.queue:
            for button in (self.run_all, self.run_selected, self.export):
                button.setEnabled(True)
            return
        index = self.queue.pop(0)
        self.table.item(index, 1).setText('BERJALAN')
        self.tasks.start(lambda context: (index, run_scenario(index, self.config)))

    def received(self, outcome):
        index, result = outcome
        self.results[index] = result
        self.table.item(index, 1).setText(result['status'])
        self.table.item(index, 2).setText(result['detail'])
        self.table.selectRow(index)
        self.show_details()

    def show_details(self):
        result = self.results.get(self.table.currentRow())
        if not result:
            self.details.setPlainText('Skenario belum mempunyai hasil.')
            return
        names = {'IN': 'Masuk', 'OUT': 'Keluar', 'BREAK_OUT': 'Mulai istirahat', 'BREAK_IN': 'Selesai istirahat'}
        lines = [f"{result['name']} — {result['status']}", result['detail'],
                 f"Jumlah catatan: {len(result['events'])}"]
        for row in result['events']:
            stamp = datetime.fromisoformat(row['time']).astimezone(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S WIB')
            source = 'Otomatis' if row['automatic'] else 'Scan'
            status = 'Terlambat' if row['status'] == 'LATE' else 'Hadir'
            lines.append(f"{stamp} • {names[row['event']]} • {status} • {source}")
        self.details.setPlainText('\n'.join(lines))

    def save_results(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Simpan hasil demo', 'stargate-tahap10-demo.json', 'JSON (*.json)')
        if not path:
            return
        report = dict(mode='synthetic-demo', created=datetime.now(timezone.utc).isoformat(),
                      real_camera_tested=False, real_faces_tested=False,
                      results=[self.results.get(index, dict(name=title, status='BELUM DIUJI'))
                               for index, (title, _) in enumerate(SCENARIOS)])
        try:
            with open(path, 'w', encoding='utf-8') as output:
                json.dump(report, output, ensure_ascii=False, indent=2)
        except OSError:
            QMessageBox.warning(self, 'Hasil belum disimpan', 'Pilih folder yang dapat ditulis, lalu coba lagi.')

    def closeEvent(self, event):
        self.closing = True
        self.queue.clear()
        self.session.close()
        if self.tasks.busy or not self.session._close_ready:
            self.setEnabled(False)
            self.close_timer.start()
            event.ignore()
            return
        self.close_timer.stop()
        event.accept()

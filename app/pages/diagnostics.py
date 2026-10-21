from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QProgressBar, QPushButton,
                             QVBoxLayout, QWidget)

from app.widgets.cards import text_label


class DiagnosticsPage(QWidget):
    requested = pyqtSignal(bool)
    cancel_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        box = QFrame()
        box.setObjectName("featureCard")
        body = QVBoxLayout(box)
        body.setContentsMargins(28, 28, 28, 28)
        body.setSpacing(18)
        body.addWidget(text_label("PEMERIKSAAN APLIKASI", "eyebrow"))
        body.addWidget(text_label("Pastikan aplikasi tetap merespons.", "pageTitle"))
        body.addWidget(text_label(
            "Jalankan simulasi singkat, lalu coba berpindah halaman. "
            "Anda juga dapat membatalkan proses atau mencoba simulasi kesalahan. "
            "Pemeriksaan ini tidak membuka kamera dan tidak mengubah data.", "muted"))
        self.progress = QProgressBar()
        self.progress.setObjectName("taskProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        body.addWidget(self.progress)
        self.result = text_label("Siap untuk pemeriksaan.", "muted")
        self.result.setObjectName("taskResult")
        body.addWidget(self.result)
        row = QHBoxLayout()
        self.run_button = QPushButton("Jalankan pemeriksaan")
        self.run_button.setObjectName("runDiagnostic")
        self.run_button.setProperty("variant", "primary")
        self.fail_button = QPushButton("Simulasikan kesalahan")
        self.fail_button.setObjectName("failDiagnostic")
        self.fail_button.setProperty("variant", "secondary")
        self.cancel_button = QPushButton("Batalkan")
        self.cancel_button.setObjectName("cancelDiagnostic")
        self.cancel_button.setEnabled(False)
        self.run_button.clicked.connect(lambda: self.requested.emit(False))
        self.fail_button.clicked.connect(lambda: self.requested.emit(True))
        self.cancel_button.clicked.connect(self.cancel_requested)
        for button in (self.run_button, self.fail_button, self.cancel_button):
            row.addWidget(button)
        body.addLayout(row)
        self.heartbeat = text_label("Antarmuka aktif · 0", "muted")
        self.heartbeat.setObjectName("heartbeat")
        body.addWidget(self.heartbeat)
        layout.addWidget(box)
        layout.addWidget(text_label(
            "Hasil di halaman ini hanya memeriksa fondasi aplikasi. "
            "Pengujian pengenalan wajah dan absensi dilakukan setelah modulnya tersedia.", "muted"))
        layout.addStretch()

    @pyqtSlot(bool)
    def set_busy(self, busy):
        self.run_button.setEnabled(not busy)
        self.fail_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)
        if busy:
            self.progress.setValue(0)
            self.result.setText("Pemeriksaan berlangsung. Anda tetap dapat berpindah halaman.")

    @pyqtSlot(object)
    def on_success(self, result):
        self.result.setText(str(result))

    @pyqtSlot()
    def on_cancelled(self):
        self.result.setText("Pemeriksaan dibatalkan. Tidak ada data yang berubah.")

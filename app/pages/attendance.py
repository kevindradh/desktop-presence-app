"""Explicit, bounded camera attendance. Feedback/sound follow committed writes only."""
from dataclasses import dataclass, field
import time
from zoneinfo import ZoneInfo
import numpy as np
from PyQt6 import sip
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget)
from ai.attendance_process import AttendanceTarget
from app.pages.administration import fill_table, table
from app.services.cameras import STATE_TEXT, FINAL
from app.services.inference import InferenceController
from app.services.settings import configured
from app.ui.ai_lab import STATUS
from app.widgets.cards import text_label


@dataclass(repr=False)
class ScanNode:
    entry: object = field(repr=False)
    inference: object = field(repr=False)
    preview: object
    status: object
    latest: object = field(default=None, repr=False)
    latest_at: float = 0
    packet: object = field(default=None, repr=False)
    closing: bool = False


class AttendancePage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.pending = False
        self.reload_requested = False
        self.reloading = False
        self.nodes = {}
        self.rows = ()
        self.generation = 0
        self.queued = None
        self.manager = controller.cameras
        self.target_factory = AttendanceTarget
        self.body = QVBoxLayout(self)
        self.body.setSpacing(12)
        self.body.addWidget(text_label('Pilih kamera dan mode, lalu mulai absensi. Foto dan probe scan tidak disimpan. Sukses ditampilkan setelah riwayat tersimpan.'))
        self.device_table = table(['Perangkat', 'Jenis', 'Lokasi'])
        self.device_table.setMinimumHeight(100)
        self.device_table.setSelectionMode(self.device_table.SelectionMode.ExtendedSelection)
        self.device_table.itemSelectionChanged.connect(self.controls)
        self.body.addWidget(self.device_table)
        row = QHBoxLayout()
        self.mode = QComboBox()
        for title, value in (('Otomatis (masuk / keluar)', 'AUTO'), ('Masuk', 'IN'), ('Keluar', 'OUT'),
                             ('Mulai istirahat', 'BREAK_OUT'), ('Selesai istirahat', 'BREAK_IN')):
            self.mode.addItem(title, value)
        row.addWidget(self.mode)
        self.start_button, self.stop_button, self.reload_button = (QPushButton(title) for title in
            ('Mulai absensi', 'Hentikan absensi', 'Muat ulang'))
        self.start_button.setProperty('variant', 'primary')
        for button in (self.start_button, self.stop_button, self.reload_button):
            row.addWidget(button)
        self.body.addLayout(row)
        self.consent = QCheckBox('Peserta telah menyetujui pemrosesan wajah untuk pencatatan absensi')
        self.consent.toggled.connect(self.consent_changed)
        self.body.addWidget(self.consent)
        self.policy = text_label('Konfigurasi belum dimuat.')
        self.body.addWidget(self.policy)
        self.body.addWidget(text_label('AUTO: scan pertama masuk, scan berikutnya keluar setelah jeda; saat istirahat, scan berikutnya menyelesaikan istirahat. Setelah sukses, tinggalkan area kamera setidaknya satu detik sebelum scan lagi.'))
        self.message = text_label('')
        self.body.addWidget(self.message)
        self.grid = QGridLayout()
        self.body.addLayout(self.grid)
        self.history = table(['Nama', 'ID', 'Event', 'Waktu', 'Tanggal kerja', 'Status', 'Shift', 'Perangkat', 'Pulang awal', 'Sumber'])
        self.body.addWidget(self.history)
        self.body.addStretch()
        self.sound = QSoundEffect(self)
        source = controller.config.resource_root/'resources/sounds/success.wav'
        if source.is_file():
            self.sound.setSource(QUrl.fromLocalFile(str(source)))
        self.sound.setVolume(.35)
        self.sound.setLoopCount(1)
        self.manager.frame_ready.connect(self.frame)
        self.manager.changed.connect(self.camera_changed)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.reload_button.clicked.connect(self.reload)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.pump)
        self.timer.start()
        self.dispatch_timer = QTimer(self)
        self.dispatch_timer.setInterval(25)
        self.dispatch_timer.timeout.connect(self.dispatch)
        self.controls()

    @property
    def busy(self):
        return bool(self.nodes)

    def controls(self):
        running = bool(self.nodes)
        self.device_table.setEnabled(not self.pending and not running)
        self.mode.setEnabled(not self.pending and not running)
        self.start_button.setEnabled(not self.pending and not running and not self.manager.busy
            and self.consent.isChecked() and bool(self.device_table.selectedItems()))
        self.stop_button.setEnabled(running)
        # Frame submissions must not change the refresh button's appearance/focus.
        self.reload_button.setEnabled(not self.reloading and not self.reload_requested)

    def consent_changed(self, checked):
        if not checked:
            self.stop()
        self.controls()

    def run(self, operation, callback):
        if self.pending or not self.controller.login or self.controller._closing:
            return False
        self.pending = True
        self.queued = (self.controller.login.token, operation, callback)
        self.controls()
        self.dispatch_timer.start()
        self.dispatch()
        return True

    def dispatch(self):
        if self.queued is None:
            self.dispatch_timer.stop()
            return
        token, operation, callback = self.queued
        if not self.controller.login or token != self.controller.login.token or self.controller._closing:
            self.queued = None
            self.pending = False
            self.reload_requested = self.reloading = False
            self.dispatch_timer.stop()
            self.controls()
            return
        if self.controller.jobs.tasks.busy:
            return
        self.queued = None
        self.dispatch_timer.stop()
        def done(result):
            if sip.isdeleted(self):
                return
            self.pending = False
            if not self.controller.login or token != self.controller.login.token or self.controller._closing:
                return
            if result.error:
                self.reloading = False
                self.message.setText(result.error)
                self.stop()
                self.controller._handle_denial(result.error)
            else:
                callback(result.value)
            if self.reload_requested and not self.pending:
                self.reload()
            self.controls()
        self.controller.jobs.run(lambda: operation(token), done, blocks_ui=False)

    def reload(self):
        if not self.controller.login or self.controller._closing or self.reloading:
            return
        if self.pending:
            # Keep a single refresh request until the current scan has finished.
            self.reload_requested = True
            self.controls()
            return
        self.reload_requested = False
        self.reloading = True
        def loaded(result):
            self.reloading = False
            devices, values, history = result
            if not self.nodes:
                self.rows = devices
                fill_table(self.device_table, [(d.name, d.kind.value, d.location_name) for d in devices])
                self.policy.setText(self.policy_text(values))
            self.show_recent(history)
        self.run(self.controller.attendance_service.setup, loaded)

    @staticmethod
    def policy_text(values):
        return (f"Similarity {values['similarity_threshold']:.2f} • anti-spoof "+
            ('AKTIF' if values['anti_spoof_enabled'] else 'NONAKTIF — keaslian wajah tidak diperiksa')+
            f" • ambang {values['anti_spoof_threshold']:.2f} • timeout {values['recognition_timeout']:g} detik"
            f" • jeda {values['duplicate_window']} detik • checkout otomatis "+('aktif' if values['auto_checkout'] else 'nonaktif'))

    def show_recent(self, rows):
        zone = ZoneInfo(self.controller.config.timezone)
        fill_table(self.history, [(r.name, r.code, r.event, r.timestamp.astimezone(zone).strftime('%d/%m/%Y %H:%M:%S'),
            r.work_date.isoformat(), r.status, r.shift, r.device, 'Ya' if r.early else 'Tidak',
            'Otomatis' if r.automatic else 'Scan') for r in rows])

    def start(self):
        if self.nodes or self.manager.busy or not self.consent.isChecked():
            return
        ids = [self.rows[index.row()].id for index in self.device_table.selectionModel().selectedRows()]
        if not ids:
            return
        generation = self.generation
        mode = self.mode.currentData()
        def started(entries):
            if generation != self.generation or not self.isVisible() or not self.consent.isChecked():
                for entry in entries:
                    self.controller.attendance_service.cancel(entry.binding)
                return
            try:
                self.manager.start_many([entry.spec for entry in entries])
                for i, entry in enumerate(entries):
                    panel = QWidget(); body = QVBoxLayout(panel)
                    body.addWidget(text_label(entry.spec.name))
                    preview = QLabel('Menyiapkan kamera dan model…')
                    preview.setMinimumSize(300, 180)
                    preview.setMaximumHeight(300)
                    preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    status = text_label('Menyiapkan model…')
                    body.addWidget(preview); body.addWidget(status)
                    self.grid.addWidget(panel, i//2, i%2)
                    config = configured(self.controller.config, entry.binding['settings'])
                    worker = InferenceController(config, self,
                        target=self.target_factory(self.controller.attendance_service.key, entry.binding))
                    node = ScanNode(entry, worker, preview, status)
                    self.nodes[entry.spec.device_id] = node
                    worker.result.connect(lambda response, device=entry.spec.device_id: self.analyzed(device, response))
                    worker.changed.connect(lambda state, device=entry.spec.device_id: self.engine_changed(device, state))
                    worker.start()
                self.policy.setText(self.policy_text(entries[0].binding['settings']))
                self.message.setText('Absensi aktif. Arahkan wajah ke kamera.')
            except Exception:
                for entry in entries:
                    self.controller.attendance_service.cancel(entry.binding)
                self.stop()
                self.message.setText('Kamera atau model tidak dapat dimulai. Periksa perangkat dan coba kembali.')
            self.controls()
        self.run(lambda token: self.controller.attendance_service.begin(token, ids, mode), started)

    def frame(self, device, image):
        node = self.nodes.get(device)
        if node is None:
            return
        if image.isNull() or node.closing or not self.consent.isChecked():
            if node.latest is not None:
                node.latest.fill(0)
            node.latest = None
            node.preview.clear()
            return
        pointer = image.constBits(); pointer.setsize(image.sizeInBytes())
        rgb = np.frombuffer(pointer, dtype=np.uint8).reshape(image.height(), image.bytesPerLine())[:, :image.width()*3]
        rgb = rgb.reshape(image.height(), image.width(), 3)
        node.latest = np.ascontiguousarray(rgb[:, :, ::-1])
        node.latest_at = time.monotonic()
        node.preview.setPixmap(QPixmap.fromImage(image).scaled(node.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def engine_changed(self, device, state):
        node = self.nodes.get(device)
        if node is None:
            return
        if state in ('failed', 'timeout'):
            self.message.setText('Model gagal atau batas waktu terlampaui. Mulai absensi kembali.')
            self.stop()

    def camera_changed(self, device):
        node = self.nodes.get(device)
        if node and self.manager.nodes[device].state == 'failed':
            self.message.setText('Kamera terputus. Periksa perangkat dan nomor kamera, lalu mulai manual.')
            self.stop()
        self.controls()

    def analyzed(self, device, response):
        node = self.nodes.get(device)
        if node is None or node.closing or response['event'] != 'result':
            return
        node.status.setText(STATUS.get(response['status'], 'Memeriksa wajah…'))
        if response['status'] == 'spoof':
            node.status.setText('Spoof Detected — wajah ditolak oleh pemeriksaan keaslian.')
        node.packet = response.get('packet')

    def pump(self):
        for device, node in list(self.nodes.items()):
            if node.closing:
                camera = self.manager.nodes.get(device)
                if not node.inference.active and (camera is None or camera.state in FINAL):
                    node.inference.shutdown_now()
                    node.inference.deleteLater()
                    panel = node.preview.parentWidget()
                    self.grid.removeWidget(panel); panel.deleteLater()
                    self.nodes.pop(device)
                continue
            if self.pending or self.controller.jobs.tasks.busy:
                continue
            if node.packet is not None:
                packet, node.packet = node.packet, None
                generation = self.generation
                def accepted(result, current=node, original_generation=generation):
                    if original_generation != self.generation or not self.isVisible():
                        return
                    self.message.setText(result.message)
                    current.status.setText(result.message)
                    if result.saved:
                        self.sound.play()
                        if self.sound.status() == QSoundEffect.Status.Error:
                            self.message.setText(result.message+' Suara tidak tersedia; periksa keluaran audio.')
                        self.reload()
                    elif result.restart:
                        self.stop()
                self.run(lambda token, value=packet: self.controller.attendance_service.submit(token, value), accepted)
                break
            if node.inference.state == 'ready' and node.latest is not None and time.monotonic()-node.latest_at < 1:
                node.inference.submit(node.latest)
        self.controls()

    def stop(self):
        self.generation += 1
        self.reload_requested = False
        if self.queued is not None:
            self.queued = None
            self.pending = False
            self.reloading = False
            self.dispatch_timer.stop()
        for device, node in self.nodes.items():
            node.closing = True
            node.packet = None
            if node.latest is not None:
                node.latest.fill(0)
            node.latest = None
            node.preview.clear()
            self.controller.attendance_service.cancel(node.entry.binding)
            self.manager.stop(device)
            node.inference.stop()
        self.controls()

    def on_leave(self):
        self.stop()

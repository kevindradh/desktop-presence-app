"""Explicit, bounded camera attendance. Feedback/sound follow committed writes only."""
from dataclasses import dataclass, field
import time
from zoneinfo import ZoneInfo
import numpy as np
from PyQt6 import sip
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget)
from ai.attendance_process import AttendanceTarget
from app.pages.administration import fill_table, table
from app.services.cameras import FINAL
from app.services.inference import InferenceController
from app.services.settings import configured
from app.widgets.cards import text_label


class AttendancePreview(QLabel):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet('background: #142d25; border: 1px solid #d3ded4; border-radius: 6px;')
        self.notice = text_label('')
        self.notice.setParent(self)
        self.notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notice.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.notice.setStyleSheet('background: #e6eee1; color: #213e31; border: 1px solid #d3ded4; '
                                 'border-radius: 8px; padding: 10px 14px; font-size: 18px; font-weight: 650;')
        self.notice.hide()
        self.notice_timer = QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.setInterval(3000)
        self.notice_timer.timeout.connect(self.notice.hide)
        self.last_event_id = None

    def position_notice(self):
        width = max(1, self.width()-32)
        height = max(self.notice.sizeHint().height(), self.notice.heightForWidth(width))
        self.notice.setGeometry(16, 16, width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_notice()

    def show_success(self, event_id, message):
        if event_id is None or event_id == self.last_event_id:
            return
        self.last_event_id = event_id
        self.show_notice(message)

    def show_notice(self, message):
        self.notice.setText(message.replace(' — ', ': '))
        self.position_notice()
        self.notice.show()
        self.notice.raise_()
        self.notice_timer.start()

    def clear_notice(self):
        self.notice_timer.stop()
        self.notice.clear()
        self.notice.hide()


@dataclass(repr=False)
class ScanNode:
    entry: object = field(repr=False)
    inference: object = field(repr=False)
    preview: object
    latest: object = field(default=None, repr=False)
    latest_at: float = 0
    packet: object = field(default=None, repr=False)
    closing: bool = False
    notified_member: int | None = None


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
        row = QHBoxLayout()
        self.device = QComboBox()
        self.device.setAccessibleName('Kamera dan lokasi')
        self.device.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.device.setMinimumContentsLength(12)
        self.device.currentIndexChanged.connect(self.controls)
        row.addWidget(self.device, 2)
        self.mode = QComboBox()
        self.mode.setAccessibleName('Mode absensi')
        self.mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.mode.setMinimumContentsLength(10)
        for title, value in (('Otomatis', 'AUTO'), ('Masuk', 'IN'), ('Keluar', 'OUT'),
                             ('Mulai istirahat', 'BREAK_OUT'), ('Selesai istirahat', 'BREAK_IN')):
            self.mode.addItem(title, value)
        row.addWidget(self.mode, 1)
        self.start_button, self.stop_button, self.reload_button = (QPushButton(title) for title in
            ('Mulai', 'Hentikan', 'Muat ulang'))
        self.start_button.setProperty('variant', 'primary')
        for button in (self.reload_button, self.stop_button, self.start_button):
            row.addWidget(button)
        self.body.addLayout(row)
        self.message = text_label('')
        self.message.hide()
        self.body.addWidget(self.message)
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.empty_preview = self.camera_preview()
        self.grid.addWidget(self.empty_preview, 0, 0)
        self.body.addLayout(self.grid, 1)
        self.history = table(['Nama', 'ID', 'Event', 'Waktu', 'Tanggal kerja', 'Status', 'Shift', 'Perangkat', 'Pulang awal', 'Sumber'])
        self.history.setMinimumHeight(180)
        self.history.setMaximumHeight(220)
        self.body.addWidget(self.history)
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
        self.device.setEnabled(not self.pending and not running)
        self.mode.setEnabled(not self.pending and not running)
        self.start_button.setEnabled(not self.pending and not running and not self.manager.busy
            and bool(self.selected_devices()))
        self.stop_button.setEnabled(running)
        # Frame submissions must not change the refresh button's appearance/focus.
        self.reload_button.setEnabled(not self.reloading and not self.reload_requested)

    def selected_devices(self):
        selected = self.device.currentData()
        if selected == 'ALL':
            return [row.id for row in self.rows]
        return [row.id for row in self.rows if row.id == selected]

    def show_message(self, text):
        self.message.setText(text)
        self.message.setVisible(bool(text))

    @staticmethod
    def camera_preview():
        return AttendancePreview()

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
                self.show_message(result.error)
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
            devices, _, history = result
            if not self.nodes:
                self.rows = devices
                selected = self.device.currentData()
                self.device.blockSignals(True)
                self.device.clear()
                self.device.addItem('Pilih kamera' if devices else 'Belum ada kamera', None)
                for device in devices:
                    self.device.addItem(f'{device.name} · {device.location_name or "Tanpa lokasi"}', device.id)
                if len(devices) > 1:
                    self.device.addItem('Semua kamera', 'ALL')
                self.device.setCurrentIndex(max(0, self.device.findData(selected)))
                self.device.blockSignals(False)
            self.show_recent(history)
        self.run(self.controller.attendance_service.setup, loaded)

    def show_recent(self, rows):
        zone = ZoneInfo(self.controller.config.timezone)
        fill_table(self.history, [(r.name, r.code, r.event, r.timestamp.astimezone(zone).strftime('%d/%m/%Y %H:%M:%S'),
            r.work_date.isoformat(), r.status, r.shift, r.device, 'Ya' if r.early else 'Tidak',
            'Otomatis' if r.automatic else 'Scan') for r in rows])

    def start(self):
        if self.nodes or self.manager.busy:
            return
        ids = self.selected_devices()
        if not ids:
            return
        generation = self.generation
        mode = self.mode.currentData()
        def started(entries):
            if generation != self.generation or not self.isVisible():
                for entry in entries:
                    self.controller.attendance_service.cancel(entry.binding)
                return
            try:
                self.manager.start_many([entry.spec for entry in entries])
                self.empty_preview.hide()
                for i, entry in enumerate(entries):
                    panel = QWidget(); body = QVBoxLayout(panel)
                    body.setContentsMargins(0, 0, 0, 0)
                    body.addWidget(text_label(entry.spec.name))
                    preview = self.camera_preview()
                    preview.setText('Menyiapkan kamera…')
                    body.addWidget(preview, 1)
                    self.grid.addWidget(panel, i, 0)
                    config = configured(self.controller.config, entry.binding['settings'])
                    worker = InferenceController(config, self,
                        target=self.target_factory(self.controller.attendance_service.key, entry.binding))
                    node = ScanNode(entry, worker, preview)
                    self.nodes[entry.spec.device_id] = node
                    worker.result.connect(lambda response, device=entry.spec.device_id: self.analyzed(device, response))
                    worker.changed.connect(lambda state, device=entry.spec.device_id: self.engine_changed(device, state))
                    worker.start()
                self.show_message('')
            except Exception:
                for entry in entries:
                    self.controller.attendance_service.cancel(entry.binding)
                self.stop()
                self.show_message('Kamera atau model tidak dapat dimulai. Periksa perangkat dan coba kembali.')
            self.controls()
        self.run(lambda token: self.controller.attendance_service.begin(token, ids, mode), started)

    def frame(self, device, image):
        node = self.nodes.get(device)
        if node is None:
            return
        if image.isNull() or node.closing:
            if node.latest is not None:
                node.latest.fill(0)
            node.latest = None
            node.preview.clear()
            node.preview.clear_notice()
            return
        pointer = image.constBits(); pointer.setsize(image.sizeInBytes())
        rgb = np.frombuffer(pointer, dtype=np.uint8).reshape(image.height(), image.bytesPerLine())[:, :image.width()*3]
        rgb = rgb.reshape(image.height(), image.width(), 3)
        node.latest = np.ascontiguousarray(rgb[:, :, ::-1])
        node.latest_at = time.monotonic()
        node.preview.setPixmap(QPixmap.fromImage(image).transformed(QTransform().scale(-1, 1)).scaled(
            node.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def engine_changed(self, device, state):
        node = self.nodes.get(device)
        if node is None:
            return
        if state in ('failed', 'timeout'):
            self.show_message('Model gagal atau batas waktu terlampaui. Mulai absensi kembali.')
            self.stop()

    def camera_changed(self, device):
        node = self.nodes.get(device)
        if node and self.manager.nodes[device].state == 'failed':
            self.show_message('Kamera terputus. Periksa perangkat dan nomor kamera, lalu mulai manual.')
            self.stop()
        self.controls()

    def analyzed(self, device, response):
        node = self.nodes.get(device)
        if node is None or node.closing or response['event'] != 'result':
            return
        node.packet = response.get('packet')

    def notify_result(self, node, result):
        if result.reason == 'absence':
            node.notified_member = None
        elif result.member_id is not None:
            already_notified = any(n.notified_member == result.member_id for n in self.nodes.values())
            node.notified_member = result.member_id
            if result.reason == 'already_recorded' and not already_notified:
                node.preview.show_notice('Sudah absen.')
        if result.saved:
            node.preview.show_success(result.event_id, result.message)

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
                    if not self.nodes:
                        self.empty_preview.show()
                continue
            if self.pending or self.controller.jobs.tasks.busy:
                continue
            if node.packet is not None:
                packet, node.packet = node.packet, None
                generation = self.generation
                def accepted(result, current=node, original_generation=generation):
                    if original_generation != self.generation or not self.isVisible():
                        return
                    self.notify_result(current, result)
                    if result.saved:
                        self.sound.play()
                        if self.sound.status() == QSoundEffect.Status.Error:
                            self.show_message('Suara tidak tersedia; periksa keluaran audio.')
                        self.reload()
                    elif result.restart:
                        self.show_message(result.message)
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
            node.preview.clear_notice()
            self.controller.attendance_service.cancel(node.entry.binding)
            self.manager.stop(device)
            node.inference.stop()
        if not self.nodes:
            self.empty_preview.show()
        self.controls()

    def on_leave(self):
        self.stop()

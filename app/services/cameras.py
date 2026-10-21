"""Bounded latest-frame capture with nonblocking lifecycle and bounded retries."""
from dataclasses import dataclass, replace, field
import multiprocessing as mp
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QImage

from app.services.camera_capture import CaptureSpec, FRAME_BYTES, PREVIEW_HEIGHT, PREVIEW_WIDTH, capture_process
from app.services.database import DataValidationError

FINAL = {"stopped", "failed", "test_ok"}
STATE_TEXT = {"connecting":"Menghubungkan…", "streaming":"Pratinjau aktif", "stopping":"Menghentikan…",
    "retry_wait":"Koneksi terputus; mencoba kembali…", "stopped":"Dihentikan", "failed":"Kamera tidak tersedia atau koneksi gagal.",
    "test_ok":"Uji koneksi berhasil"}


@dataclass(repr=False)
class CaptureNode:
    spec: CaptureSpec
    test: bool = False
    state: str = "connecting"
    attempts: int = 0
    frames: int = 0
    last_sequence: int = 0
    last_frame_at: float = 0
    began: float = 0
    opened_at: float = 0
    next_at: float = 0
    stop_at: float = 0
    exit_action: str = "stopped"
    terminate_sent: bool = False
    kill_sent: bool = False
    displayed: bool = False
    actual_size: tuple = (0, 0)
    process: object = field(default=None, repr=False)
    pixels: object = field(default=None, repr=False)
    metadata: object = field(default=None, repr=False)
    lock: object = field(default=None, repr=False)
    connection: object = field(default=None, repr=False)
    event: object = field(default=None, repr=False)


class CameraManager(QObject):
    changed = pyqtSignal(int)
    frame_ready = pyqtSignal(int, QImage)

    def __init__(self, config, logger=None, parent=None, *, capture_target=capture_process, clock=time.monotonic):
        super().__init__(parent)
        self.config, self.logger, self.capture_target, self.clock = config, logger, capture_target, clock
        self.context = mp.get_context("spawn")
        self.nodes = {}
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    @property
    def busy(self):
        return any(node.state not in FINAL for node in self.nodes.values())

    def _state(self, node, state):
        node.state = state
        if state != "streaming":
            node.displayed = False
            self.frame_ready.emit(node.spec.device_id, QImage())
        if self.logger:
            self.logger.info("Camera id=%d state=%s attempts=%d", node.spec.device_id, state, node.attempts)
        self.changed.emit(node.spec.device_id)

    def start_many(self, specs, *, test=False):
        if not specs:
            raise DataValidationError("Pilih perangkat untuk pratinjau.")
        if any(not isinstance(spec, CaptureSpec) or not 1 <= spec.fps <= 60 for spec in specs):
            raise DataValidationError("Konfigurasi kamera tidak valid.")
        active = [node for node in self.nodes.values() if node.state not in FINAL]
        if len(active) + len(specs) > self.config.camera_max_streams:
            raise DataValidationError("Batas kamera aktif tercapai. Hentikan pratinjau lain terlebih dahulu.")
        identities = [node.spec.identity for node in active] + [spec.identity for spec in specs]
        ids = [node.spec.device_id for node in active] + [spec.device_id for spec in specs]
        if len(set(identities)) != len(identities) or len(set(ids)) != len(ids):
            raise DataValidationError("Kamera yang sama sedang digunakan atau dipilih dua kali.")
        started = []
        try:
            for spec in specs:
                node = CaptureNode(spec=spec, test=test)
                self.nodes[spec.device_id] = node
                started.append(spec.device_id)
                self._launch(node)
        except Exception:
            for device_id in started:
                self.stop(device_id)
            raise DataValidationError("Proses kamera tidak dapat dimulai. Coba lagi.") from None

    def _launch(self, node):
        node.pixels = self.context.RawArray("B", FRAME_BYTES)
        node.metadata = self.context.RawArray("d", 6)
        node.lock = self.context.Lock()
        node.event = self.context.Event()
        receive, send = self.context.Pipe(duplex=False)
        node.connection = receive
        node.process = self.context.Process(target=self.capture_target, name=f"StarGateCamera-{node.spec.device_id}",
            args=(node.spec, node.pixels, node.metadata, node.lock, send, node.event,
                  self.config.camera_open_timeout, self.config.camera_read_timeout), daemon=True)
        node.last_sequence = 0
        node.began = self.clock()
        node.opened_at = node.last_frame_at = 0
        node.terminate_sent = node.kill_sent = False
        try:
            node.process.start()
        finally:
            send.close()
        self._state(node, "connecting")

    def _shutdown(self, node, action):
        node.exit_action = action
        node.stop_at = self.clock()
        if node.event is not None:
            node.event.set()
        self._state(node, "stopping")

    def stop(self, device_id):
        node = self.nodes.get(device_id)
        if node is None or node.state in FINAL:
            return
        if node.state == "retry_wait":
            self._finish(node, "stopped")
        elif node.state == "stopping":
            node.exit_action = "stopped"
        else:
            self._shutdown(node, "stopped")

    def stop_all(self):
        for device_id in tuple(self.nodes):
            self.stop(device_id)

    def _failure(self, node):
        # A local camera index can refer to another physical camera after unplug.
        # Retry only addressable RTSP sources until stable local IDs are supported.
        retry = node.spec.kind == "RTSP" and node.attempts < self.config.camera_reconnect_attempts
        action = "retry_wait" if retry else "failed"
        self._shutdown(node, action)

    def _read_frame(self, node, now):
        if not node.lock.acquire(timeout=0):
            return
        try:
            sequence, width, height, captured, original_width, original_height = node.metadata[:]
            width, height = int(width), int(height)
            if sequence == node.last_sequence or sequence <= 0 or not (0 < width <= PREVIEW_WIDTH and 0 < height <= PREVIEW_HEIGHT):
                return
            node.last_sequence = sequence
            if now - captured > 1.0 or captured > now + 1:
                return
            node.last_frame_at = captured
            node.actual_size = (int(original_width), int(original_height))
            node.frames += 1
            if not node.test:
                data = memoryview(node.pixels).cast("B")[:width * height * 3].tobytes()
                image = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
                node.displayed = True
                self.frame_ready.emit(node.spec.device_id, image)
            if node.state != "streaming":
                self._state(node, "streaming")
            else:
                self.changed.emit(node.spec.device_id)
            if node.test:
                self._shutdown(node, "test_ok")
        finally:
            node.lock.release()

    def _release(self, node):
        if node.connection is not None:
            node.connection.close()
        if node.process is not None:
            if node.process.pid is not None:
                node.process.join(0)
            node.process.close()
        node.process = node.connection = node.pixels = node.metadata = node.lock = node.event = None

    def _finish(self, node, state):
        node.spec = replace(node.spec, rtsp_source="")
        self._state(node, state)

    def poll(self):
        now = self.clock()
        for node in tuple(self.nodes.values()):
            if node.state in FINAL:
                continue
            if node.state == "retry_wait":
                if now >= node.next_at:
                    try:
                        self._launch(node)
                    except Exception:
                        self._shutdown(node, "failed")
                continue
            if node.state == "stopping":
                process = node.process
                if process is None or process.pid is None or not process.is_alive():
                    self._release(node)
                    if node.exit_action == "retry_wait":
                        node.attempts += 1
                        node.next_at = now + .5 * node.attempts
                        self._state(node, "retry_wait")
                    else:
                        self._finish(node, node.exit_action)
                elif now - node.stop_at >= .5 and not node.terminate_sent:
                    process.terminate()
                    node.terminate_sent = True
                elif now - node.stop_at >= 1 and not node.kill_sent:
                    process.kill()
                    node.kill_sent = True
                continue
            try:
                while node.connection.poll():
                    kind, unused = node.connection.recv()
                    if kind == "opened":
                        node.opened_at = now
                    elif kind == "error":
                        self._failure(node)
                        break
                if node.state == "stopping":
                    continue
                self._read_frame(node, now)
                if node.state == "stopping":
                    continue
                if node.displayed and now - node.last_frame_at > 1:
                    node.displayed = False
                    self.frame_ready.emit(node.spec.device_id, QImage())
                if not node.process.is_alive():
                    self._failure(node)
                elif node.last_frame_at and now - node.last_frame_at >= self.config.camera_read_timeout:
                    self._failure(node)
                elif not node.last_frame_at:
                    deadline = self.config.camera_read_timeout if node.opened_at else self.config.camera_open_timeout
                    start = node.opened_at or node.began
                    if now - start >= deadline:
                        self._failure(node)
            except (EOFError, OSError, ValueError):
                self._failure(node)

    def shutdown_now(self):
        # Last-resort application exit only. Normal window closure polls asynchronously.
        self.timer.stop()
        for node in self.nodes.values():
            if node.event is not None:
                node.event.set()
            process = node.process
            if process is not None:
                if process.pid is not None and process.is_alive():
                    process.terminate()
                    process.join(.3)
                    if process.is_alive():
                        process.kill()
                        process.join(.5)
                try:
                    self._release(node)
                except (ValueError, OSError):
                    pass
            if node.state not in FINAL:
                self._finish(node, "stopped")

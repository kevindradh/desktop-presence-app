"""Cooperatively cancelled worker objects; no widget access from worker threads."""
from dataclasses import dataclass, field
from threading import Event
from typing import Callable

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot

from app.services.errors import ErrorReporter


class TaskCancelled(Exception):
    pass


@dataclass(frozen=True)
class TaskContext:
    cancelled: Event
    progress: Callable[[int], None]
    committed: Event = field(default_factory=Event)

    def checkpoint(self):
        if self.cancelled.is_set() and not self.committed.is_set():
            raise TaskCancelled

    def commit(self, action):
        """Once an irreversible publication finishes, report its real outcome."""
        self.checkpoint()
        result = action()
        self.committed.set()
        return result

    def pause(self, seconds):
        if self.cancelled.wait(seconds):
            raise TaskCancelled


class Worker(QObject):
    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    failed = pyqtSignal(object)
    cancelled = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, task, cancel_event):
        super().__init__()
        self.task = task
        self.cancel_event = cancel_event

    @pyqtSlot()
    def run(self):
        context = TaskContext(self.cancel_event, self.progress.emit)
        try:
            context.checkpoint()
            result = self.task(context)
            context.checkpoint()
            self.result.emit(result)
        except TaskCancelled:
            self.cancelled.emit()
        except Exception as error:
            self.failed.emit(error)
        finally:
            self.finished.emit()


class TaskController(QObject):
    progress = pyqtSignal(int)
    succeeded = pyqtSignal(object)
    cancelled = pyqtSignal()
    settled = pyqtSignal()
    busy_changed = pyqtSignal(bool)

    def __init__(self, reporter: ErrorReporter, parent=None):
        super().__init__(parent)
        self.reporter = reporter
        self._thread = None
        self._worker = None
        self._cancel_event = None
        # Connect once on the GUI thread. Creating a singleShot callback while
        # the worker is being destroyed can deadlock Qt's connection mutex
        # against the Python GIL in PyQt disconnectNotify.
        self._join_timer = QTimer(self)
        self._join_timer.setSingleShot(True)
        self._join_timer.setInterval(10)
        self._join_timer.timeout.connect(self._settled)

    @property
    def busy(self):
        return self._thread is not None

    def start(self, task):
        if self.busy:
            return False
        self._cancel_event = Event()
        thread = QThread(self)
        worker = Worker(task, self._cancel_event)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.result.connect(self.succeeded)
        worker.cancelled.connect(self.cancelled)
        worker.failed.connect(self._failed)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._settled)
        self._thread, self._worker = thread, worker
        self.busy_changed.emit(True)
        thread.start()
        return True

    @pyqtSlot(object)
    def _failed(self, error):
        self.reporter.report(error)

    @pyqtSlot()
    def cancel(self):
        if self.busy:
            self._cancel_event.set()
            self._thread.requestInterruption()

    @pyqtSlot()
    def _settled(self):
        thread = self._thread
        if thread is None:
            return
        # finished is emitted before all thread-local cleanup is complete.
        # Poll a nonblocking join so shutdown never waits on a busy GUI thread.
        if not thread.wait(0):
            self._join_timer.start()
            return
        self._thread = self._worker = self._cancel_event = None
        thread.deleteLater()
        self.busy_changed.emit(False)
        self.settled.emit()

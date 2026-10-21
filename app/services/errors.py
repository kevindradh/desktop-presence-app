"""One safe error route shared by UI callbacks and background workers."""
from dataclasses import dataclass
import logging
import uuid

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass(frozen=True)
class Incident:
    reference: str
    message: str


class ErrorReporter(QObject):
    occurred = pyqtSignal(object)

    def __init__(self, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.logger = logger

    def report(self, error: BaseException) -> Incident:
        reference = uuid.uuid4().hex[:10].upper()
        self.logger.error("Operation failed ref=%s type=%s", reference,
                          type(error).__name__, exc_info=(type(error), error, error.__traceback__))
        incident = Incident(reference, "Proses tidak dapat diselesaikan. Silakan coba lagi.")
        self.occurred.emit(incident)
        return incident

"""Transient window feedback that never takes keyboard focus."""
import time

from PyQt6.QtCore import QEvent, QTimer, Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from app.widgets.cards import text_label


class Toast(QFrame):
    def __init__(self, window):
        super().__init__(window)
        self.setObjectName('errorBanner')
        self.setAccessibleName('Notifikasi')
        self.message = text_label('')
        self.dismiss_button = QPushButton('Tutup')
        self.dismiss_button.clicked.connect(self.dismiss)
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 12, 16, 12)
        row.addWidget(self.message, 1)
        row.addWidget(self.dismiss_button, 0, Qt.AlignmentFlag.AlignTop)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.hide)
        self.last_text = ''
        self.last_shown = float('-inf')
        window.installEventFilter(self)
        self.hide()

    def show_message(self, text):
        if not text:
            self.dismiss()
            return
        now = time.monotonic()
        if text == self.last_text and now-self.last_shown < 10:
            return
        self.last_text, self.last_shown = text, now
        self.message.setText(text)
        self.position()
        self.show()
        self.raise_()
        self.timer.start()

    def position(self):
        width = min(460, max(1, self.parentWidget().width()-40))
        self.setFixedWidth(width)
        self.ensurePolished()
        self.layout().activate()
        height = self.layout().totalHeightForWidth(width)
        if height < 0:
            height = self.sizeHint().height()
        self.setGeometry(max(0, self.parentWidget().width()-width-20), 20, width, height)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.position()
            if self.isVisible():
                self.raise_()
        return super().eventFilter(watched, event)

    def dismiss(self):
        self.timer.stop()
        self.hide()
        self.last_text = ''

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


def text_label(text, style="", *, wrap=True):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    if style:
        label.setProperty("kind", style)
    return label


class FeatureCard(QFrame):
    def __init__(self, number, title, description, action, callback):
        super().__init__()
        self.setObjectName("featureCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)
        layout.addWidget(text_label(number, "eyebrow"))
        layout.addWidget(text_label(title, "cardTitle"))
        layout.addWidget(text_label(description, "muted"))
        layout.addStretch()
        button = QPushButton(action)
        button.setProperty("variant", "secondary")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        layout.addWidget(button)

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QLabel

from app.settings.paths import runtime_paths


def application_icon(resource_root=None):
    root = Path(resource_root) if resource_root is not None else runtime_paths().resources
    return QIcon(str(root / 'resources/branding/stargate.ico'))


def brand_mark(resource_root, size, *, on_dark=False):
    label = QLabel()
    label.setObjectName('brandMark')
    label.setAccessibleName('Logo StarGate')
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setProperty('onDark', on_dark)
    label.setFixedSize(size + 8 if on_dark else size, size + 8 if on_dark else size)
    pixmap = QPixmap(str(Path(resource_root) / 'resources/branding/stargate.png'))
    if pixmap.isNull():
        return label
    pixmap = pixmap.scaled(size * 2, size * 2, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
    pixmap.setDevicePixelRatio(2)
    label.setPixmap(pixmap)
    return label

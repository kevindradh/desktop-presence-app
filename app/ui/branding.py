from pathlib import Path
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QLabel

from app.settings.colors import PRIMARY
from app.settings.paths import runtime_paths


def application_icon(resource_root=None):
    root = Path(resource_root) if resource_root is not None else runtime_paths().resources
    filename = 'stargate.icns' if sys.platform == 'darwin' else 'stargate.ico'
    return QIcon(str(root / 'resources/branding' / filename))


def brand_image(resource_root, *, on_dark=False):
    filename = 'stargate-white.png' if on_dark else 'stargate.png'
    image = QImage(str(Path(resource_root) / 'resources/branding' / filename))
    if on_dark or image.isNull():
        return image
    image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(image)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), QColor(PRIMARY))
    painter.end()
    return image


def brand_mark(resource_root, size, *, on_dark=False):
    label = QLabel()
    label.setObjectName('brandMark')
    label.setAccessibleName('Logo StarGate')
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size + 8 if on_dark else size, size + 8 if on_dark else size)
    pixmap = QPixmap.fromImage(brand_image(resource_root, on_dark=on_dark))
    if pixmap.isNull():
        return label
    pixmap = pixmap.scaled(size * 2, size * 2, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
    pixmap.setDevicePixelRatio(2)
    label.setPixmap(pixmap)
    return label

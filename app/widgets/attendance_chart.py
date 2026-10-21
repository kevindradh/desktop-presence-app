"""Small Qt-native aggregate charts with an accessible text equivalent."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget


class AttendanceChart(QWidget):
    def __init__(self, *, trend=False):
        super().__init__()
        self.rows = ()
        self.trend = trend
        self.setMinimumHeight(220)

    def set_rows(self, rows):
        if self.rows == rows:
            return
        self.rows = rows
        self.setMinimumHeight(220 if self.trend else max(140, len(rows)*28+44))
        description = '\n'.join(f'{r.label}: hadir {r.present}, terlambat {r.late}' for r in rows)
        self.setAccessibleName(description or 'Belum ada check-in pada tanggal kerja ini')
        self.setToolTip(description)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#ffffff'))
        if not self.rows or not any(r.present for r in self.rows):
            painter.setPen(QColor('#60736b'))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Belum ada check-in')
            painter.end()
            return
        maximum = max(r.present for r in self.rows) or 1
        if self.trend:
            area = QRectF(35, 16, max(1, self.width()-55), self.height()-55)
            painter.setPen(QColor('#cbd9ce'))
            painter.drawLine(area.bottomLeft(), area.bottomRight())
            painter.drawText(QRectF(0, 0, 32, 30), Qt.AlignmentFlag.AlignCenter, str(maximum))
            for attribute, color in (('present', '#2d6240'), ('late', '#b36b19')):
                path = QPainterPath()
                for i, row in enumerate(self.rows):
                    point = QPointF(area.left()+i*area.width()/max(1, len(self.rows)-1),
                                    area.bottom()-getattr(row, attribute)*area.height()/maximum)
                    path.moveTo(point) if i == 0 else path.lineTo(point)
                painter.setPen(QPen(QColor(color), 2))
                painter.drawPath(path)
            painter.setPen(QColor('#60736b'))
            painter.drawText(QRectF(area.left(), area.bottom()+6, area.width(), 24),
                Qt.AlignmentFlag.AlignLeft, self.rows[0].label)
            painter.drawText(QRectF(area.left(), area.bottom()+6, area.width(), 24),
                Qt.AlignmentFlag.AlignRight, self.rows[-1].label)
        else:
            label_width = min(160, self.width()*.4)
            width = max(1, self.width()-label_width-72)
            for i, row in enumerate(self.rows):
                y = 8+i*28
                painter.setPen(QColor('#243a33'))
                label = painter.fontMetrics().elidedText(row.label, Qt.TextElideMode.ElideRight, int(label_width)-8)
                painter.drawText(QRectF(0, y, label_width-8, 24), Qt.AlignmentFlag.AlignVCenter, label)
                painter.fillRect(QRectF(label_width, y+3, width*row.present/maximum, 8), QColor('#2d6240'))
                painter.fillRect(QRectF(label_width, y+14, width*row.late/maximum, 6), QColor('#b36b19'))
                painter.drawText(QRectF(label_width+width+6, y, 65, 24), Qt.AlignmentFlag.AlignVCenter,
                                 f'{row.present} / {row.late}')
        painter.end()

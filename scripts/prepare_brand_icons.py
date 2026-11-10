"""Render the application backplate without modifying the supplied brand mark."""
from pathlib import Path
import sys

from PIL import Image
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ui.branding import brand_image


def main():
    folder = ROOT / 'resources/branding'
    mark = brand_image(ROOT)
    if mark.isNull():
        raise ValueError('Logo StarGate tidak dapat dibaca.')
    canvas = QImage(1024, 1024, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor('#ffffff'))
    plate = QRectF(64, 64, 896, 896)
    painter.drawRoundedRect(plate, 180, 180)
    painter.drawImage(plate, mark)
    painter.end()
    output = folder / 'stargate-app.png'
    if not canvas.save(str(output)):
        raise OSError('Ikon aplikasi tidak dapat disimpan.')
    with Image.open(output) as icon:
        icon.save(folder / 'stargate.ico', format='ICO',
                  sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
        mac_plate_size = 816
        mac_inset = (icon.width - mac_plate_size) // 2
        mac_plate = icon.crop(icon.getbbox()).resize((mac_plate_size, mac_plate_size), Image.Resampling.LANCZOS)
        mac_icon = Image.new('RGBA', icon.size)
        mac_icon.paste(mac_plate, (mac_inset, mac_inset))
        mac_icon.save(folder / 'stargate.icns', format='ICNS')
    print('Ikon aplikasi berlatar putih siap; PNG logo asli tetap dipertahankan.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Preview follows the user's motion while inference and saved photos retain source orientation."""
from PyQt6.QtGui import QColor,QImage

from app.settings.config import load_config
from app.ui.enrollment import CaptureLab
from app.ui.theme import apply_theme


def test_registration_preview_follows_motion_without_flipping_inference_or_photo(qt_app,tmp_path):
    apply_theme(qt_app)
    lab=CaptureLab(load_config(tmp_path,environ={}),target=None)
    lab.resize(1120,820)
    lab.show()
    try:
        qt_app.processEvents()
        assert lab.consent is None and lab.start_button.isEnabled()
        assert lab.start_button.text()=='Mulai'
        assert lab.stop_button.text().replace('&&','&')=='Hentikan & hapus'
        assert lab.reference_button.text()=='Capture'
        assert not lab.state_label.isVisible() and not lab.detail.isVisible()
        assert not lab.threshold_label.isVisible()
        assert lab.preview.height()>400
        frame=QImage(80,40,QImage.Format.Format_RGB888)
        frame.fill(QColor('blue'))
        for x in range(40):
            for y in range(40):frame.setPixelColor(x,y,QColor('red'))
        lab.preview_active=True
        lab.frame(1,frame)
        shown=lab.preview.pixmap().toImage()
        assert shown.pixelColor(5,shown.height()//2).blue()>200
        assert shown.pixelColor(shown.width()-6,shown.height()//2).red()>200
        assert lab.latest[20,5].tolist()==[0,0,255]
        assert lab.latest[20,75].tolist()==[255,0,0]
        response=dict(event='result',expected='LEFT',captured=1,status='ready',face_count=1,
                      elapsed_ms=1,has_reference=False,live_score=.99,similarity=None)
        lab.analyzed(response)
        assert 'ke kiri gambar' in lab.guide.text()
        lab.analyzed(dict(response,expected='RIGHT',captured=2))
        assert 'ke kanan gambar' in lab.guide.text()
        lab.completed_photo=frame.copy()
        lab.complete=True
        lab.frame(1,frame)
        shown=lab.preview.pixmap().toImage()
        assert shown.pixelColor(5,shown.height()//2).blue()>200
        assert shown.pixelColor(shown.width()-6,shown.height()//2).red()>200
        assert lab.completed_photo.pixelColor(5,20).red()>200
        lab.stop()
        assert lab.preview.text()=='' and lab.preview.pixmap().isNull()
        assert lab.latest is None
        lab.frame(1,frame)
        assert lab.preview.text()=='' and lab.preview.pixmap().isNull()
    finally:
        lab.close()
        qt_app.processEvents()

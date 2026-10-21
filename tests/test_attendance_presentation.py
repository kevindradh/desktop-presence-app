"""Attendance preview orientation and temporary committed-event feedback."""
from types import SimpleNamespace

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QImage

from app.pages.attendance import AttendancePage, AttendancePreview, ScanNode
from app.services.attendance import AttendanceFeedback
from app.settings.config import load_config
from app.ui.theme import apply_theme


def test_success_notice_expires_without_rearming_for_same_event(qt_app, wait_until):
    preview = AttendancePreview()
    preview.resize(700, 400)
    preview.show()
    try:
        preview.notice_timer.setInterval(30)
        preview.show_success(1, 'Peserta uji: Masuk berhasil tersimpan.')
        assert preview.notice.isVisible()
        assert preview.rect().contains(preview.notice.geometry())
        preview.resize(500, 360)
        qt_app.processEvents()
        assert preview.rect().contains(preview.notice.geometry())
        wait_until(lambda:not preview.notice.isVisible())
        preview.show_success(1, 'Peserta uji: Masuk berhasil tersimpan.')
        assert not preview.notice.isVisible() and not preview.notice_timer.isActive()
        preview.show_success(2, 'Peserta uji lain: Masuk berhasil tersimpan.')
        assert preview.notice.isVisible() and 'lain' in preview.notice.text()
        preview.clear_notice()
        assert not preview.notice.isVisible() and not preview.notice_timer.isActive()
    finally:
        preview.close()


def test_attendance_mirrors_display_only(qt_app, tmp_path):
    class Cameras(QObject):
        frame_ready = pyqtSignal(int, QImage)
        changed = pyqtSignal(int)
        busy = False
    apply_theme(qt_app)
    controller = SimpleNamespace(cameras=Cameras(),config=load_config(tmp_path,environ={}))
    page = AttendancePage(controller)
    preview = AttendancePreview()
    preview.resize(640,360)
    page.nodes[1] = ScanNode(None, None, preview)
    try:
        frame = QImage(80,40,QImage.Format.Format_RGB888)
        frame.fill(QColor('blue'))
        for x in range(40):
            for y in range(40):
                frame.setPixelColor(x,y,QColor('red'))
        page.frame(1,frame)
        shown = preview.pixmap().toImage()
        assert shown.pixelColor(5,shown.height()//2).blue()>200
        assert shown.pixelColor(shown.width()-6,shown.height()//2).red()>200
        assert page.nodes[1].latest[20,5].tolist()==[0,0,255]
        assert page.nodes[1].latest[20,75].tolist()==[255,0,0]
        assert frame.pixelColor(5,20).red()>200
    finally:
        page.timer.stop()
        page.nodes.clear()
        page.deleteLater()
        preview.close()
        qt_app.processEvents()


def test_already_notice_rearms_after_absence_without_cross_camera_repeats(qt_app):
    first=ScanNode(None,None,AttendancePreview())
    second=ScanNode(None,None,AttendancePreview())
    page=SimpleNamespace(nodes={1:first,2:second})
    duplicate=AttendanceFeedback(False,'',member_id=7,reason='already_recorded')
    absence=AttendanceFeedback(False,'',reason='absence')
    notify=lambda node,result:AttendancePage.notify_result(page,node,result)
    try:
        notify(first,duplicate)
        assert first.preview.notice_timer.isActive()
        first.preview.clear_notice()
        notify(first,duplicate)
        notify(second,duplicate)
        assert not first.preview.notice_timer.isActive()
        assert not second.preview.notice_timer.isActive()
        notify(first,absence)
        notify(first,duplicate)
        assert not first.preview.notice_timer.isActive()
        notify(first,absence)
        notify(second,absence)
        notify(first,duplicate)
        assert first.preview.notice_timer.isActive()
        first.preview.clear_notice()
        notify(first,AttendanceFeedback(False,'',member_id=8,reason='already_recorded'))
        assert first.preview.notice_timer.isActive()
        first.preview.clear_notice()
        notify(first,AttendanceFeedback(True,'Tersimpan',event_id=10,member_id=9))
        first.preview.clear_notice()
        notify(first,AttendanceFeedback(False,'',member_id=9,reason='already_recorded'))
        assert not first.preview.notice_timer.isActive()
    finally:
        for node in (first,second):
            node.preview.clear_notice()
            node.preview.close()

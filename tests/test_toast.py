from PyQt6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from app.ui.theme import apply_theme
from app.widgets.toast import Toast


def test_toast_expires_repositions_and_preserves_typing_focus(qt_app,wait_until,monkeypatch):
    apply_theme(qt_app)
    window=QWidget()
    layout=QVBoxLayout(window)
    field=QLineEdit()
    layout.addWidget(field)
    toast=Toast(window)
    clock=[100.]
    monkeypatch.setattr('app.widgets.toast.time.monotonic',lambda:clock[0])
    window.resize(1000,740)
    window.show()
    window.activateWindow()
    field.setFocus()
    qt_app.processEvents()
    try:
        toast.timer.setInterval(40)
        toast.show_message('Proses tidak dapat diselesaikan. Referensi: UJI123')
        assert toast.isVisible() and field.hasFocus()
        for width,height in ((1000,740),(1180,820),(1440,900)):
            window.resize(width,height)
            qt_app.processEvents()
            assert window.rect().contains(toast.geometry())
            assert toast.geometry().right()==window.width()-21
            assert toast.y()==20
        wait_until(lambda:not toast.isVisible())
        toast.show_message(toast.message.text())
        assert not toast.isVisible() and not toast.timer.isActive()
        clock[0]+=10
        toast.show_message(toast.message.text())
        assert toast.isVisible()
        toast.dismiss_button.click()
        assert not toast.isVisible() and not toast.timer.isActive()
        toast.show_message('Pesan berikutnya')
        assert toast.isVisible()
        toast.show_message('')
        assert not toast.isVisible()
    finally:
        window.close()

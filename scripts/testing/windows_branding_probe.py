"""Inspect the branding UI from the installed bundle without connecting to the database."""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace


def main():
    assert getattr(sys, 'frozen', False)
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    from PyQt6.QtWidgets import QApplication, QLabel
    from PyQt6.QtGui import QFont, QFontDatabase
    from app.settings.paths import runtime_paths
    from app.settings.config import load_config
    from app.services.errors import ErrorReporter
    from app.ui.branding import application_icon
    from app.ui.session_window import SessionWindow
    from app.ui.theme import apply_theme
    root = Path(os.environ['LOCALAPPDATA'])/'StarGate-Parallels-0141'
    assert (root/'.local/managed-postgres/state.json').is_file()
    output = Path('C:/StarGate-build/logo-evidence-0143')
    assert output.is_dir()
    config = load_config(root, bundle_root=runtime_paths(data_dir=root).resources)
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    apply_theme(app)
    font_file = Path(os.environ['SystemRoot'])/'Fonts/segoeui.ttf'
    font_id = QFontDatabase.addApplicationFont(str(font_file))
    families = QFontDatabase.applicationFontFamilies(font_id)
    assert families, 'Windows font could not be registered for the offscreen renderer'
    app.setFont(QFont(families[0],10))
    icon = application_icon(config.resource_root)
    assert not icon.isNull()
    for size in (16,32,48,128,256):
        image = icon.pixmap(size,size).toImage()
        assert not image.isNull()
        assert image.pixelColor(size//8,size//2).lightness() > 240
        assert image.pixelColor(0,0).alpha() == 0
    app.setWindowIcon(icon)
    logger = logging.Logger('frozen-branding-probe')
    logger.addHandler(logging.NullHandler())
    # This preview exercises the compiled UI only; startup/auth IO is disabled.
    SessionWindow._initialize = lambda self: None
    window = SessionWindow(config,logger,ErrorReporter(logger),
                           SimpleNamespace(clock=lambda:datetime.now(timezone.utc)),None)
    window.stack.setCurrentWidget(window.login_panel)
    window.show()
    app.processEvents()
    assert window.windowTitle() == 'StarGate' and not window.windowIcon().isNull()
    marks = window.findChildren(QLabel,'brandMark')
    assert len(marks) == 4 and all(not label.pixmap().isNull() for label in marks)
    assert window.grab().save(str(output/'frozen-login.png'))
    window.resize(1000,740)
    window.stack.setCurrentWidget(window.setup_panel)
    app.processEvents()
    for button in (window.setup_submit,window.setup_close):
        assert window.rect().contains(button.mapTo(window,button.rect().bottomRight()))
    assert window.grab().save(str(output/'frozen-setup.png'))
    window.timer.stop()
    window.checkout_timer.stop()
    window.cameras.shutdown_now()
    window.hide()
    result = {'frozen_ui':'PASS','mode':'offscreen Windows Qt from installed bundle',
              'offscreen_font':families[0],'white_application_icon':True,'icon_sizes':[16,32,48,128,256],
              'all_panel_logos_loaded':True,'setup_fits_1000x740':True,
              'database_connected':False,'camera_opened':False,'manual_login_uat':'not claimed'}
    (output/'frozen-ui.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result),flush=True)
    return 0


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())

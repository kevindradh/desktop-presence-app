"""Open a disposable Stage 10 attendance demo; no real camera or face required."""
from dataclasses import replace
import logging
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from app.services.errors import ErrorReporter
    from app.settings.config import load_config
    from app.ui.attendance_demo import AttendanceDemo
    from app.ui.theme import apply_theme
    from database.attendance_demo import seed_demo
    from database.demo import demo_database

    app = QApplication([])
    app.setApplicationName('StarGate — Demo Tahap 10')
    apply_theme(app)
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    try:
        with TemporaryDirectory(prefix='stage10-demo-', dir=local) as folder, demo_database() as store:
            root = Path(folder)
            sound = root / 'resources/sounds/success.wav'
            sound.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'resources/sounds/success.wav', sound)
            config = replace(load_config(ROOT), root=root, database=store.config, log_dir=root / 'logs')
            data = seed_demo(store, config)
            logger = logging.Logger('attendance-demo')
            logger.addHandler(logging.NullHandler())
            reporter = ErrorReporter(logger, app)
            window = AttendanceDemo(config, logger, reporter, data)
            previous = sys.excepthook
            sys.excepthook = lambda kind, error, tb: reporter.report(error.with_traceback(tb))
            try:
                window.show()
                return app.exec()
            finally:
                sys.excepthook = previous
    except Exception:
        QMessageBox.critical(None, 'Demo belum dapat dibuka',
                             'Periksa PostgreSQL lokal dan konfigurasi database test. Data kerja tidak diubah.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

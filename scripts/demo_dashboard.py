"""Run the isolated synthetic Stage 11 dashboard with one-click terminal events."""
import logging
from dataclasses import replace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from PyQt6.QtWidgets import QApplication,QMessageBox
    from app.settings.config import load_config
    from app.services.errors import ErrorReporter
    from app.ui.dashboard_demo import DashboardDemo
    from app.ui.theme import apply_theme
    from database.demo import demo_database
    from database.dashboard_demo import seed_dashboard_demo
    app=QApplication([])
    app.setApplicationName('StarGate — Demo Tahap 11')
    apply_theme(app)
    local=ROOT/'.local'
    local.mkdir(exist_ok=True)
    try:
        with TemporaryDirectory(prefix='stage11-demo-',dir=local) as folder,demo_database() as store:
            config=replace(load_config(ROOT),root=Path(folder),database=store.config,log_dir=Path(folder)/'logs')
            data=seed_dashboard_demo(store,config)
            logger=logging.Logger('dashboard-demo')
            logger.addHandler(logging.NullHandler())
            reporter=ErrorReporter(logger,app)
            window=DashboardDemo(config,logger,reporter,data)
            previous=sys.excepthook
            sys.excepthook=lambda kind,error,tb:reporter.report(error.with_traceback(tb))
            try:
                window.show()
                return app.exec()
            finally:
                sys.excepthook=previous
    except Exception:
        QMessageBox.critical(None,'Demo belum dapat dibuka','Periksa PostgreSQL lokal dan konfigurasi database test. Data kerja tidak diubah.')
        return 2


if __name__=='__main__':
    raise SystemExit(main())

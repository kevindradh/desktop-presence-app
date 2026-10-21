"""Run Stage 12 reports with prepared synthetic data and a Viewer account."""
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
    from app.ui.reports_demo import ReportsDemo
    from app.ui.theme import apply_theme
    from database.demo import demo_database
    from database.reports_demo import seed_reports_demo
    app=QApplication([]);app.setApplicationName('StarGate - Demo Laporan')
    apply_theme(app)
    local=ROOT/'.local';local.mkdir(exist_ok=True)
    try:
        with TemporaryDirectory(prefix='stage12-demo-',dir=local) as folder,demo_database() as store:
            config=replace(load_config(ROOT),root=Path(folder),database=store.config,log_dir=Path(folder)/'logs')
            data=seed_reports_demo(store,config)
            logger=logging.Logger('reports-demo');logger.addHandler(logging.NullHandler())
            reporter=ErrorReporter(logger,app)
            window=ReportsDemo(config,logger,reporter,data)
            previous=sys.excepthook
            sys.excepthook=lambda kind,error,tb:reporter.report(error.with_traceback(tb))
            try:
                window.show()
                return app.exec()
            finally:sys.excepthook=previous
    except Exception:
        QMessageBox.critical(None,'Demo belum dapat dibuka','Periksa PostgreSQL lokal dan konfigurasi database test. Data kerja tidak diubah.')
        return 2


if __name__=='__main__':raise SystemExit(main())

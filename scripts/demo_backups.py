"""Stage 13 synthetic audit and recovery sandbox; never targets development data."""
import logging
from dataclasses import replace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def main():
    from PyQt6.QtWidgets import QApplication,QMessageBox
    from app.models.entities import Role
    from app.services.errors import ErrorReporter
    from app.settings.config import load_config
    from app.ui.backups_demo import BackupsDemo,DEMO_PASSWORD,DEMO_USER
    from app.ui.theme import apply_theme
    from database.demo import demo_database,seed_administration_demo
    app=QApplication([]);app.setApplicationName('StarGate - Demo Pemulihan');apply_theme(app)
    local=ROOT/'.local';local.mkdir(exist_ok=True)
    try:
        with TemporaryDirectory(prefix='stage13-demo-',dir=local) as folder,demo_database() as store:
            config=replace(load_config(ROOT),root=Path(folder),database=store.config,log_dir=Path(folder)/'logs')
            auth,admin=seed_administration_demo(store.db,folder)
            initial='Demo-initial-2026!'
            auth.create_user(admin.token,DEMO_USER,'Penguji pemulihan',Role.SUPER_ADMIN,initial)
            login=auth.change_password(auth.login(DEMO_USER,initial).token,initial,DEMO_PASSWORD)
            auth.close_session(admin.token)
            logger=logging.Logger('backups-demo');logger.addHandler(logging.NullHandler());reporter=ErrorReporter(logger,app)
            window=BackupsDemo(config,logger,reporter,auth,login,store.migration)
            previous=sys.excepthook;sys.excepthook=lambda kind,error,tb:reporter.report(error.with_traceback(tb))
            try:window.show();return app.exec()
            finally:sys.excepthook=previous
    except Exception:
        QMessageBox.critical(None,'Demo belum dapat dibuka','Periksa PostgreSQL dan konfigurasi database test. Data kerja tidak diubah.');return 2


if __name__=='__main__':raise SystemExit(main())

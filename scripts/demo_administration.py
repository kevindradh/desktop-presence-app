"""Open a disposable Stage 5 UI with synthetic data, isolated from public/dev."""
import argparse
from dataclasses import replace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class NoCredentials:
    def get(self):
        return None
    def clear(self):
        pass
    def set(self, token):
        from app.services.credential_store import CredentialStoreError
        raise CredentialStoreError()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=["super-admin", "admin", "operator", "viewer"], default="super-admin")
    args = parser.parse_args()
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from app.models.entities import Role
    from app.services.diagnostic_logging import configure_logging
    from app.services.errors import ErrorReporter
    from app.settings.config import load_config
    from app.ui.session_window import SessionWindow
    from app.ui.theme import apply_theme
    from app.widgets.cards import text_label
    from database.demo import demo_database, seed_administration_demo

    app = QApplication([])
    app.setApplicationName("StarGate — Demo Administrasi")
    apply_theme(app)
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    try:
        with TemporaryDirectory(prefix="stage5-demo-", dir=local) as folder, demo_database() as store:
            auth, login = seed_administration_demo(store.db, folder, Role(args.role.replace("-", "_").upper()))
            config = replace(load_config(ROOT), root=Path(folder), database=store.config, log_dir=Path(folder) / "logs")
            logger = configure_logging(config.log_dir, config.log_level, config.secrets)
            reporter = ErrorReporter(logger, app)
            window = SessionWindow(config, logger, reporter, auth, NoCredentials())
            window._accepted(login)
            window.setWindowTitle("StarGate — MODE UJI SINTETIS")
            label = text_label("MODE UJI • Data sintetis sementara • Tutup dan buka demo kembali untuk mengulang")
            label.setStyleSheet("background:#fff0d9; color:#684719; padding:8px;")
            window.statusBar().addPermanentWidget(label, 1)
            previous = sys.excepthook
            sys.excepthook = lambda kind, error, tb: reporter.report(error.with_traceback(tb))
            try:
                window.show()
                return app.exec()
            finally:
                sys.excepthook = previous
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    except Exception:
        QMessageBox.critical(None, "Demo belum dapat dibuka", "Periksa PostgreSQL lokal dan konfigurasi database test. Data kerja tidak diubah.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

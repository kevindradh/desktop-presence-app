import argparse
from pathlib import Path
import sys

from app.settings.config import ConfigError, load_config


def main(argv=None):
    parser = argparse.ArgumentParser(description="StarGate desktop application")
    parser.add_argument("--data-dir", type=Path, help="Private writable application data directory")
    parser.add_argument("--package-check", action="store_true", help="Offline bundle/Qt/spawn smoke check")
    parser.add_argument("--verify-models", action="store_true", help="Also initialize pinned AI models in package check")
    parser.add_argument("--config", type=Path, help="Explicit .env path; missing file is an error")
    parser.add_argument("--check-config", action="store_true", help="Validate without opening GUI")
    args = parser.parse_args(argv)
    try:
        from app.settings.paths import runtime_paths
        paths = runtime_paths(data_dir=args.data_dir)
        config = load_config(paths.data, args.config, bundle_root=paths.resources)
        if args.package_check:
            from app.services.package_probe import check_package
            return check_package(config, verify_models=args.verify_models)
    except ConfigError as error:
        print(f"Konfigurasi tidak valid: {error}", file=sys.stderr)
        if not (args.check_config or args.package_check):
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication([])
            QMessageBox.critical(None, "StarGate", str(error))
        return 2
    if args.check_config:
        print("Konfigurasi valid. Nilai rahasia tidak ditampilkan.")
        return 0
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from app.services.diagnostic_logging import configure_logging
    from app.services.errors import ErrorReporter
    from app.ui.session_window import SessionWindow
    from app.services.auth import AuthService
    from app.services.credential_store import CredentialStore
    from app.services.database import Database, create_database_engine
    from app.ui.theme import apply_theme

    app = QApplication([])
    app.setApplicationName("StarGate")
    app.setOrganizationName("StarGate")
    try:
        logger = configure_logging(config.log_dir, config.log_level, config.secrets)
    except OSError:
        print("Log aplikasi tidak dapat dibuat. Periksa akses direktori log.", file=sys.stderr)
        QMessageBox.critical(None, "StarGate", "Log aplikasi tidak dapat dibuat. Periksa akses direktori log.")
        return 2
    reporter = ErrorReporter(logger, app)
    previous_hook = sys.excepthook
    sys.excepthook = lambda kind, error, tb: reporter.report(error.with_traceback(tb))
    try:
        apply_theme(app)
        database = Database(create_database_engine(config.database))
        window = SessionWindow(config, logger, reporter, AuthService(database), CredentialStore(config))
        window.show()
        try:
            return app.exec()
        finally:
            database.close()
    finally:
        sys.excepthook = previous_hook
        for handler in logger.handlers[:]:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)


if __name__ == "__main__":
    raise SystemExit(main())

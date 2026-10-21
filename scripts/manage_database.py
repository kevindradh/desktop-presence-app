"""Explicit schema/seed/admin commands; never runs during normal GUI startup."""
import argparse
import getpass
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["upgrade", "status", "check", "seed", "bootstrap-admin"])
    parser.add_argument("--database", choices=["dev", "test"], default="dev")
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args(argv)
    from app.settings.paths import runtime_paths
    data_root = runtime_paths(data_dir=args.data_dir).data
    from app.services.database import Database, create_database_engine
    from database.runtime import connection_config, schema_status, upgrade
    engine = None
    try:
        migration = args.action in {"upgrade", "status"}
        engine = create_database_engine(connection_config(args.database, migration=migration, root=data_root, env_file=args.config))
        if args.action == "upgrade":
            with engine.begin() as connection:
                upgrade(connection, application_role=connection_config(args.database, root=data_root, env_file=args.config).user)
            print("Migrasi selesai. Data yang sudah ada tidak dihapus.")
        elif args.action in {"status", "check"}:
            with engine.connect() as connection:
                result = schema_status(connection)
                if args.action == "check":
                    from sqlalchemy import select
                    from app.models.entities import AuditLog, Member, Setting
                    for model in (Member, Setting, AuditLog):
                        connection.execute(select(model.id).limit(1))
            print(json.dumps(result, indent=2))
            return 0 if result["at_head"] and result["schema_valid"] else 1
        else:
            db = Database(engine)
            if args.action == "seed":
                from database.seed.defaults import seed_defaults
                with db.transaction() as session:
                    result = seed_defaults(session)
                print(json.dumps(result))
            elif args.action == "bootstrap-admin":
                from app.services.bootstrap_admin import bootstrap_super_admin
                if not sys.stdin.isatty():
                    print("Jalankan bootstrap-admin di terminal interaktif agar password tidak ter-echo.",
                          file=sys.stderr)
                    return 2
                username = input("Username Super Admin: ").strip()
                fullname = input("Nama lengkap: ").strip()
                password = getpass.getpass("Password (12-72 byte UTF-8): ")
                confirmation = getpass.getpass("Ulangi password: ")
                if password != confirmation:
                    print("Password konfirmasi tidak cocok.", file=sys.stderr)
                    return 2
                with db.transaction() as session:
                    bootstrap_super_admin(session, username, fullname, password)
                print("Super Admin dibuat; password tidak ditampilkan atau ditulis ke log.")
        return 0
    except (Exception, KeyboardInterrupt, EOFError) as error:
        # No raw DB error/DSN/parameters on terminal; expected validation is safe.
        from app.services.database import DataValidationError, DataConflict, DatabaseUnavailable
        from app.settings.config import ConfigError
        if isinstance(error, (DataValidationError, DataConflict, DatabaseUnavailable, ConfigError)):
            print(str(error), file=sys.stderr)
        elif isinstance(error, (KeyboardInterrupt, EOFError)):
            print("Perintah dibatalkan.", file=sys.stderr)
        else:
            print(f"Database belum siap atau operasi gagal ({type(error).__name__}). "
                  "Periksa service, kredensial dan versi schema.", file=sys.stderr)
        return 2
    finally:
        if engine:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

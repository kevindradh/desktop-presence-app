"""Provision development roles/databases. No application tables are created."""
import argparse
import getpass
import os
from pathlib import Path
import secrets

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT)
    parser.add_argument('--admin-host', help='Unix socket directory for the local PostgreSQL owner')
    parser.add_argument('--port', type=int, default=55432)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    data_root = args.data_dir.expanduser().resolve()
    env_path = data_root / '.env'
    if env_path.exists():
        raise SystemExit(".env exists; refusing to overwrite credentials. Run smoke checks instead.")
    passwords = {role: secrets.token_urlsafe(32)
                 for role in ("stargate_app", "stargate_migrator")}
    socket = args.admin_host or str(ROOT / ".local/pgsocket")
    if not Path(socket).is_absolute():
        parser.error('--admin-host must be an absolute Unix socket directory')
    with psycopg.connect(host=socket, port=args.port, dbname="postgres",
                         user=getpass.getuser(), autocommit=True) as admin:
        if not admin.execute("SELECT 1 FROM pg_available_extensions WHERE name='vector'").fetchone():
            raise SystemExit('pgvector is not installed for this PostgreSQL server; no roles created')
        for role, password in passwords.items():
            if admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
                raise SystemExit("StarGate role already exists; no credentials changed")
        for name in ("stargate_dev", "stargate_test"):
            if admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
                raise SystemExit("StarGate database already exists; no existing data changed")
        for role, password in passwords.items():
            admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                          .format(sql.Identifier(role), sql.Literal(password)))
        for name in ("stargate_dev", "stargate_test"):
            admin.execute(sql.SQL("CREATE DATABASE {} OWNER stargate_migrator")
                          .format(sql.Identifier(name)))
            admin.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC")
                          .format(sql.Identifier(name)))
            admin.execute(sql.SQL("GRANT CONNECT, TEMPORARY ON DATABASE {} TO stargate_app")
                          .format(sql.Identifier(name)))
            with psycopg.connect(host=socket, port=args.port, dbname=name,
                                 user=getpass.getuser(), autocommit=True) as db:
                db.execute("CREATE EXTENSION IF NOT EXISTS vector")
                db.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
                db.execute("GRANT USAGE ON SCHEMA public TO stargate_app")
                db.execute("ALTER DEFAULT PRIVILEGES FOR ROLE stargate_migrator IN SCHEMA public "
                           "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO stargate_app")
                db.execute("ALTER DEFAULT PRIVILEGES FOR ROLE stargate_migrator IN SCHEMA public "
                           "GRANT USAGE, SELECT ON SEQUENCES TO stargate_app")
    # Secrets only written locally; do not print connection URLs/passwords.
    content = (f"STARGATE_DB_HOST=127.0.0.1\nSTARGATE_DB_PORT={args.port}\n"
               "STARGATE_DB_NAME=stargate_dev\nSTARGATE_DB_TEST_NAME=stargate_test\n"
               f"STARGATE_DB_USER=stargate_app\nSTARGATE_DB_PASSWORD={passwords['stargate_app']}\n"
               "STARGATE_DB_MIGRATION_USER=stargate_migrator\n"
               f"STARGATE_DB_MIGRATION_PASSWORD={passwords['stargate_migrator']}\n"
               "STARGATE_TIMEZONE=Asia/Jakarta\n")
    data_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(content)
    print("Provisioned stargate_dev + stargate_test; limited app role; credentials saved to .env (0600)")


if __name__ == "__main__":
    main()

"""Provision development roles/databases. No application tables are created."""
import getpass
import os
from pathlib import Path
import secrets

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"


def main():
    if ENV.exists():
        raise SystemExit(".env exists; refusing to overwrite credentials. Run smoke checks instead.")
    passwords = {role: secrets.token_urlsafe(32)
                 for role in ("stargate_app", "stargate_migrator")}
    socket = str(ROOT / ".local/pgsocket")
    with psycopg.connect(host=socket, port=55432, dbname="postgres",
                         user=getpass.getuser(), autocommit=True) as admin:
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
            with psycopg.connect(host=socket, port=55432, dbname=name,
                                 user=getpass.getuser(), autocommit=True) as db:
                db.execute("CREATE EXTENSION IF NOT EXISTS vector")
                db.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
                db.execute("GRANT USAGE ON SCHEMA public TO stargate_app")
                db.execute("ALTER DEFAULT PRIVILEGES FOR ROLE stargate_migrator IN SCHEMA public "
                           "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO stargate_app")
                db.execute("ALTER DEFAULT PRIVILEGES FOR ROLE stargate_migrator IN SCHEMA public "
                           "GRANT USAGE, SELECT ON SEQUENCES TO stargate_app")
    # Secrets only written locally; do not print connection URLs/passwords.
    content = ("STARGATE_DB_HOST=127.0.0.1\nSTARGATE_DB_PORT=55432\n"
               "STARGATE_DB_NAME=stargate_dev\nSTARGATE_DB_TEST_NAME=stargate_test\n"
               f"STARGATE_DB_USER=stargate_app\nSTARGATE_DB_PASSWORD={passwords['stargate_app']}\n"
               "STARGATE_DB_MIGRATION_USER=stargate_migrator\n"
               f"STARGATE_DB_MIGRATION_PASSWORD={passwords['stargate_migrator']}\n"
               "STARGATE_TIMEZONE=Asia/Jakarta\nSTARGATE_MODEL_DIR=resources/models\n")
    fd = os.open(ENV, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(content)
    print("Provisioned stargate_dev + stargate_test; limited app role; credentials saved to .env (0600)")


if __name__ == "__main__":
    main()

"""Manage only the project's development cluster, never a system DB service."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
DATA = LOCAL / "postgres"
SOCKET = LOCAL / "pgsocket"


def binary(name):
    override = os.environ.get("STARGATE_PG_BIN")
    if override:
        candidate = Path(override) / name
        if candidate.exists():
            return str(candidate)
        raise SystemExit(f"Missing {name} in configured STARGATE_PG_BIN")
    candidate = Path("/opt/homebrew/opt/postgresql@17/bin") / name
    if candidate.exists():
        return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(f"Missing {name}; set STARGATE_PG_BIN to PostgreSQL 17 bin folder")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["init", "start", "stop", "status"])
    args = parser.parse_args()
    LOCAL.mkdir(mode=0o700, exist_ok=True)
    SOCKET.mkdir(mode=0o700, exist_ok=True)
    if args.action == "init":
        if (DATA / "PG_VERSION").exists():
            print("Project cluster already initialized; unchanged")
            return
        subprocess.run([binary("initdb"), "-D", str(DATA), "--encoding=UTF8",
                        "--locale=C", "--auth-local=peer", "--auth-host=scram-sha-256"],
                       check=True)
        with (DATA / "postgresql.conf").open("a") as config:
            socket_value = str(SOCKET).replace("'", "''")
            config.write(f"\n# StarGate project-local development only\n"
                         f"listen_addresses = '127.0.0.1'\nport = 55432\n"
                         f"unix_socket_directories = '{socket_value}'\n"
                         "timezone = 'Asia/Jakarta'\npassword_encryption = 'scram-sha-256'\n")
    else:
        command = [binary("pg_ctl"), "-D", str(DATA)]
        if args.action == "start":
            status = subprocess.run(command + ["status"], capture_output=True)
            if status.returncode == 0:
                print("Project cluster already running")
                return
            command += ["-l", str(LOCAL / "postgres.log"), "-w", "start"]
        elif args.action == "stop":
            command += ["-m", "fast", "-w", "stop"]
        else:
            command += ["status"]
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()

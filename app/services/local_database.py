"""Opt-in bundled PostgreSQL for a new, private Windows installation."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import secrets
import socket
import subprocess
import sys

from app.services.private_files import restrict_path
from app.settings.config import ConfigError, load_config


class LocalSetupError(ConfigError):
    pass


def checked_path(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise LocalSetupError('Setup lokal tidak menerima folder atau berkas berupa tautan.')
    return path


def private_directory(path):
    path = checked_path(path)
    path.mkdir(parents=True, exist_ok=True)
    restrict_path(path, directory=True)
    return path


def write_new(path, text):
    path = checked_path(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
        restrict_path(path)
        stream.write(text)


@contextmanager
def setup_lock(folder):
    path = checked_path(folder/'setup.lock')
    with path.open('a+b') as stream:
        restrict_path(path)
        stream.seek(0)
        if not stream.read(1):
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise LocalSetupError('Setup lokal lain masih berjalan. Tunggu lalu coba lagi.') from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def runtime_folder(resources):
    return Path(resources)/'postgresql'


def verify_runtime(resources):
    folder = checked_path(runtime_folder(resources))
    try:
        manifest = json.loads(checked_path(folder/'runtime-manifest.json').read_text(encoding='utf-8'))
        files = manifest['files']
        if not isinstance(files, dict) or not all(isinstance(name, str) for name in files):
            raise ValueError
        required = {'bin/initdb.exe', 'bin/pg_ctl.exe', 'bin/postgres.exe', 'lib/vector.dll',
                    'share/extension/vector.control', 'share/extension/vector--0.8.7.sql',
                    'licenses/PostgreSQL.txt', 'licenses/pgvector.txt'}
        if (manifest['major'], manifest['architecture'], manifest['pgvector']) != (17, 'x64', '0.8.7') or not required <= files.keys():
            raise ValueError
        actual = set()
        for item in folder.rglob('*'):
            checked_path(item)
            if item.is_file() and item.name != 'runtime-manifest.json':
                actual.add(item.relative_to(folder).as_posix())
        if actual != set(files):
            raise ValueError
        for name, digest in files.items():
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
                raise ValueError
            file = checked_path(folder/relative)
            with file.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                    raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise LocalSetupError('Runtime database lokal belum lengkap atau berubah. Pasang ulang paket yang benar.') from None
    return folder


def process_environment(runtime, *, windows=None):
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith('PG')}
    windows = os.name == 'nt' if windows is None else windows
    if windows:
        system_root = next((value for key, value in environment.items() if key.upper() == 'SYSTEMROOT'), None)
        if not system_root:
            raise LocalSetupError('Direktori sistem Windows tidak tersedia pada proses ini.')
        system = PureWindowsPath(system_root)
        environment['PATH'] = ';'.join(map(str, (runtime/'bin', runtime.parent, system/'System32', system)))
    return environment


def run_tool(runtime, name, *arguments):
    try:
        return subprocess.run([str(runtime/'bin'/f'{name}.exe'), *map(str, arguments)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=90, creationflags=0x08000000 if os.name == 'nt' else 0, check=False, env=process_environment(runtime))
    except (OSError, subprocess.TimeoutExpired):
        raise LocalSetupError('Proses database lokal tidak dapat dijalankan. Periksa ruang disk dan paket aplikasi.') from None


def read_state(folder):
    try:
        state = json.loads(checked_path(folder/'state.json').read_text(encoding='utf-8'))
        if state['version'] != 1 or type(state['port']) is not int or not 55435 <= state['port'] <= 55444:
            raise ValueError
        return state
    except (OSError, ValueError, KeyError, TypeError):
        raise LocalSetupError('Penanda database lokal tidak valid. Data tidak diubah; periksa instalasi.') from None


def check_binding(config, state):
    db = config.database
    if (db.host, db.port, db.name, db.user) != ('127.0.0.1', state['port'], 'stargate_local', 'stargate_app'):
        raise LocalSetupError('Konfigurasi berbeda dari database kelolaan. Database tidak dimulai otomatis.')


def start_cluster(runtime, folder):
    state = read_state(folder)
    data = checked_path(folder/'data')
    version_file = checked_path(data/'PG_VERSION')
    if not version_file.is_file() or version_file.read_text().strip() != '17':
        raise LocalSetupError('Folder database lokal belum siap atau versinya berbeda.')
    if run_tool(runtime, 'pg_ctl', '-D', data, 'status').returncode == 0:
        return
    log = folder/'server.log'
    if not log.exists():
        write_new(log, '')
    if run_tool(runtime, 'pg_ctl', '-D', data, '-l', checked_path(log), '-w', '-t', '45',
                '-o', f"-h 127.0.0.1 -p {state['port']}", 'start').returncode:
        raise LocalSetupError('Database lokal tidak dapat dimulai. Periksa ruang disk atau port yang dipakai aplikasi lain.')


def ensure_local_database(config):
    folder = config.root/'.local/managed-postgres'
    if not (folder/'state.json').exists():
        return
    if sys.platform != 'win32':
        raise LocalSetupError('Database kelolaan ini memerlukan Windows x64.')
    with setup_lock(folder):
        state = read_state(folder)
        check_binding(config, state)
        start_cluster(verify_runtime(config.resource_root), folder)


def provision(state, credentials):
    import psycopg
    from psycopg import sql
    arguments = dict(host='127.0.0.1', port=state['port'], user='stargate_owner',
        password=credentials['owner'], connect_timeout=10, autocommit=True)
    with psycopg.connect(dbname='postgres', **arguments) as connection:
        for role, key in (('stargate_migrator', 'migrator'), ('stargate_app', 'app')):
            exists = connection.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone()
            if not exists:
                connection.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}').format(
                    sql.Identifier(role), sql.Literal(credentials[key])))
        if not connection.execute("SELECT 1 FROM pg_database WHERE datname='stargate_local'").fetchone():
            connection.execute('CREATE DATABASE stargate_local OWNER stargate_migrator')
        connection.execute('REVOKE ALL ON DATABASE stargate_local FROM PUBLIC')
        connection.execute('GRANT CONNECT, TEMPORARY ON DATABASE stargate_local TO stargate_app')
    with psycopg.connect(dbname='stargate_local', **arguments) as connection:
        connection.execute('CREATE EXTENSION IF NOT EXISTS vector')
        connection.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
        connection.execute('GRANT USAGE ON SCHEMA public TO stargate_app')


def migrate_and_seed(root):
    from app.services.database import create_database_engine
    from app.settings.config import DatabaseConfig
    from database.runtime import upgrade
    from database.seed.defaults import seed_defaults
    from sqlalchemy.orm import Session
    folder = root/'.local/managed-postgres'
    state = read_state(folder)
    credentials = json.loads(checked_path(folder/'credentials.json').read_text(encoding='utf-8'))
    engine = create_database_engine(DatabaseConfig(host='127.0.0.1', port=state['port'],
        name='stargate_local', user='stargate_migrator', password=credentials['migrator']))
    try:
        with engine.begin() as connection:
            upgrade(connection, application_role='stargate_app')
        with Session(engine) as session, session.begin():
            seed_defaults(session)
    finally:
        engine.dispose()


def setup_local(root, resources):
    if sys.platform != 'win32':
        raise LocalSetupError('Setup database otomatis tersedia untuk paket Windows x64.')
    root = checked_path(root)
    folder = root/'.local/managed-postgres'
    env_file = checked_path(root/'.env')
    if env_file.exists() and not (folder/'state.json').exists():
        return {'mode': 'existing_configuration', 'changed': False}
    runtime = verify_runtime(resources)
    private_directory(root)
    private_directory(root/'.local')
    private_directory(folder)
    with setup_lock(folder):
        marker = folder/'state.json'
        keyfile = folder/'credentials.json'
        if not keyfile.exists():
            write_new(keyfile, json.dumps({key: secrets.token_urlsafe(32) for key in ('owner', 'migrator', 'app')}))
        credentials = json.loads(checked_path(keyfile).read_text(encoding='utf-8'))
        if not marker.exists():
            port = None
            for candidate in range(55435, 55445):
                with socket.socket() as probe:
                    try:
                        probe.bind(('127.0.0.1', candidate))
                    except OSError:
                        continue
                    port = candidate
                    break
            if port is None:
                raise LocalSetupError('Port database lokal belum tersedia. Tutup aplikasi yang memakai port 55435–55444.')
            write_new(marker, json.dumps({'version': 1, 'port': port}))
        state = read_state(folder)
        if env_file.exists():
            check_binding(load_config(root, environ={}), state)
        data = checked_path(folder/'data')
        if not (data/'PG_VERSION').exists():
            if data.exists() and any(data.iterdir()):
                raise LocalSetupError('Setup sebelumnya belum selesai. Folder database dipertahankan; periksa instalasi.')
            password_file = folder/'init-password'
            if password_file.exists():
                checked_path(password_file).unlink()
            write_new(password_file, credentials['owner'])
            try:
                result = run_tool(runtime, 'initdb', '-D', data, '--username=stargate_owner',
                    f'--pwfile={password_file}', '--auth=scram-sha-256', '--encoding=UTF8', '--no-locale')
                if result.returncode:
                    raise LocalSetupError('Inisialisasi database lokal gagal. Data tidak dihapus; periksa ruang disk.')
                restrict_path(data, directory=True)
            finally:
                password_file.unlink(missing_ok=True)
        start_cluster(runtime, folder)
        provision(state, credentials)
        if not env_file.exists():
            write_new(env_file, f"STARGATE_DB_HOST=127.0.0.1\nSTARGATE_DB_PORT={state['port']}\n"
                "STARGATE_DB_NAME=stargate_local\nSTARGATE_DB_USER=stargate_app\n"
                f"STARGATE_DB_PASSWORD={credentials['app']}\nSTARGATE_DB_MIGRATION_USER=stargate_migrator\n"
                f"STARGATE_DB_MIGRATION_PASSWORD={credentials['migrator']}\nSTARGATE_TIMEZONE=Asia/Jakarta\n")
        migrate_and_seed(root)
    return {'mode': 'managed_local', 'changed': True, 'port': state['port']}


def stop_local(root, resources):
    folder = checked_path(Path(root)/'.local/managed-postgres')
    if not (folder/'state.json').exists():
        return
    with setup_lock(folder):
        state = read_state(folder)
        if (Path(root)/'.env').exists():
            check_binding(load_config(Path(root), environ={}), state)
        if run_tool(verify_runtime(resources), 'pg_ctl', '-D', folder/'data', '-w', '-t', '45', '-m', 'fast', 'stop').returncode:
            # An already stopped cluster is also a successful cleanup.
            if run_tool(runtime_folder(resources), 'pg_ctl', '-D', folder/'data', 'status').returncode == 0:
                raise LocalSetupError('Database lokal belum dapat dihentikan.')

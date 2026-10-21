"""Package an installed Windows PostgreSQL 17/pgvector runtime without user data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct


def amd64_executable(path):
    try:
        with Path(path).open('rb') as stream:
            if stream.read(2) != b'MZ':
                return False
            stream.seek(60)
            offset = struct.unpack('<I', stream.read(4))[0]
            stream.seek(offset)
            return stream.read(6) == b'PE\0\0\x64\x86'
    except (OSError, struct.error):
        return False


def prepare(source, output, postgres_license, vector_license):
    source, output = Path(source), Path(output)
    if output.resolve().is_relative_to(source.resolve()):
        raise ValueError('Output runtime harus di luar folder sumber PostgreSQL.')
    for name in ('initdb', 'pg_ctl', 'postgres'):
        if not amd64_executable(source/'bin'/f'{name}.exe'):
            raise ValueError('Runtime PostgreSQL harus Windows x64.')
    control = source/'share/extension/vector.control'
    if "default_version = '0.8.7'" not in control.read_text(encoding='utf-8'):
        raise ValueError('Runtime harus memuat pgvector 0.8.7.')
    if not (source/'share/postgresql.conf.sample').is_file():
        raise ValueError('Berkas runtime PostgreSQL belum lengkap.')
    if not amd64_executable(source/'lib/vector.dll'):
        raise ValueError('DLL pgvector harus dipasang untuk Windows x64.')
    if not Path(postgres_license).is_file() or not Path(vector_license).is_file():
        raise ValueError('Lisensi PostgreSQL dan pgvector harus disertakan.')
    output.mkdir(parents=True, exist_ok=False)
    for name in ('bin', 'lib', 'share', 'doc'):
        if not (source/name).is_dir():
            continue
        for file in (source/name).rglob('*'):
            if file.is_symlink():
                raise ValueError('Runtime tidak boleh memuat tautan.')
            if file.is_file():
                if file.name in {'.env', 'PG_VERSION', 'pg_hba.conf', 'postgresql.conf', 'credentials.json',
                                  'state.json', 'postmaster.pid', 'server.log', 'init-password'} or file.suffix == '.sgbackup':
                    raise ValueError('Data atau konfigurasi pengguna tidak boleh masuk runtime.')
                target = output/file.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target)
    licenses = output/'licenses'
    licenses.mkdir()
    shutil.copy2(postgres_license, licenses/'PostgreSQL.txt')
    shutil.copy2(vector_license, licenses/'pgvector.txt')
    for pattern in ('LICENSE*', 'COPYRIGHT*', 'NOTICE*'):
        for file in source.glob(pattern):
            if file.is_file() and not file.is_symlink():
                shutil.copy2(file, licenses/file.name)
    files = {}
    for file in output.rglob('*'):
        if file.is_file():
            with file.open('rb') as stream:
                files[file.relative_to(output).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
    (output/'runtime-manifest.json').write_text(json.dumps({'major': 17, 'architecture': 'x64',
        'pgvector': '0.8.7', 'files': files}, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--postgres-license', type=Path, required=True)
    parser.add_argument('--pgvector-license', type=Path, required=True)
    args = parser.parse_args()
    try:
        import subprocess
        version = subprocess.check_output([str(args.source/'bin/postgres.exe'), '--version'], text=True)
        if not version.startswith('postgres (PostgreSQL) 17.'):
            raise ValueError('Gunakan PostgreSQL seri 17.')
        prepare(args.source, args.output, args.postgres_license, args.pgvector_license)
        print('Runtime PostgreSQL x64 dan pgvector siap; berkas data tidak disertakan.')
        return 0
    except Exception:
        print('Runtime belum siap. Periksa versi, arsitektur, lisensi, dan folder output baru.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

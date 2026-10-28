"""Set up the supplied Windows source kit using verified offline dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import venv

ROOT = Path(__file__).resolve().parents[1]


def verify_support():
    manifest = json.loads((ROOT/'source-support-manifest.json').read_text(encoding='utf-8'))
    expected = manifest['files']
    for name, checksum in expected.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
            raise ValueError('Nama berkas pendukung tidak valid.')
        path = ROOT/relative
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('Berkas pendukung berupa tautan.')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest() != checksum:
                raise ValueError('Berkas pendukung berubah: '+name)
    actual = {p.relative_to(ROOT).as_posix() for folder in ('wheelhouse','postgresql','resources/models')
              for p in (ROOT/folder).rglob('*') if p.is_file()}
    actual.update(name for name in expected if not name.startswith(('wheelhouse/','postgresql/','resources/models/')))
    if actual != set(expected):
        raise ValueError('Berkas pendukung kurang atau bertambah. Ekstrak kembali paket asli.')
    return len(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--data-dir',type=Path)
    args = parser.parse_args()
    if sys.platform != 'win32' or sys.version_info[:2] != (3,11) or sysconfig.get_platform() != 'win-amd64':
        raise ValueError('Gunakan Python 3.11 x64 pada Windows 11.')
    print('Memeriksa berkas pendukung...',flush=True)
    count = verify_support()
    if args.verify_only:
        print('Berkas pendukung terverifikasi: '+str(count));return 0
    folder = ROOT/'.venv-win'
    python = folder/'Scripts/python.exe'
    if folder.is_symlink():raise ValueError('Folder Python tidak boleh berupa tautan.')
    if not python.exists():
        print('Membuat lingkungan Python...',flush=True)
        venv.EnvBuilder(with_pip=True).create(folder)
    environment = {k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','STARGATE_'))}
    environment.pop('QT_QPA_PLATFORM',None)
    def run(arguments):
        subprocess.run([str(python),*arguments],cwd=ROOT,env=environment,check=True)
    run(['-c',"import sys,sysconfig; assert sys.version_info[:2]==(3,11) and sysconfig.get_platform()=='win-amd64'"])
    print('Memasang library dari paket lokal...',flush=True)
    run(['-m','pip','install','--no-index','--find-links',str(ROOT/'wheelhouse'),
         '--require-hashes','--only-binary=:all:','-r',str(ROOT/'requirements-windows-x64.candidate.lock.txt')])
    run(['-m','pip','check'])
    data = args.data_dir or Path(os.environ['LOCALAPPDATA'])/'StarGate-Source'
    run(['scripts/setup_local_windows.py','setup-local','--data-dir',str(data)])
    run(['scripts/manage_database.py','check','--data-dir',str(data)])
    run(['main.py','--package-check','--verify-models','--data-dir',str(data)])
    print('SETUP SELESAI. Jalankan RUN-WINDOWS.cmd untuk membuka StarGate.',flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        print('Setup belum selesai: '+str(error),file=sys.stderr)
        raise SystemExit(1)

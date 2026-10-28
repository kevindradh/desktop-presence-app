"""Explicit target-native research build. Never recursively copies the checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import subprocess
import sys
import sysconfig
import shutil
import stat

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def validate_build(target,include_models):
    if target not in {'windows','macos'}:raise ValueError('Target tidak valid.')
    expected='Windows' if target=='windows' else 'Darwin'
    if platform.system()!=expected:raise ValueError('Build harus dijalankan pada OS target; cross-compile tidak didukung.')
    if target=='windows' and (sysconfig.get_platform()!='win-amd64' or sys.maxsize<=2**32):
        raise ValueError('Gunakan Python Windows x64, termasuk ketika Windows ARM menjalankan emulasi x64.')
    if include_models:
        from ai.models import verified_assets
        verified_assets(ROOT,ROOT/'resources/models')


def finalize_output(output, include_models, *, manifest_path=None):
    output=Path(output)
    if platform.system()=='Windows':
        from PyInstaller.utils.hooks import collect_delvewheel_libs_directory
        # ONNX wheels keep their repaired native dependencies beside the package.
        # Preserve that directory even when an identical DLL also exists in pandas.libs.
        datas,binaries=collect_delvewheel_libs_directory('onnx')
        for source,relative in datas+binaries:
            folder=output/'_internal'/relative
            folder.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,folder/Path(source).name)
    forbidden={'main.py','.env','.local','member_photos','backups','stargate.sgbackup'}
    if any(p.name in forbidden or p.suffix=='.sgbackup' for p in output.rglob('*')):
        raise ValueError('Paket mengandung data yang tidak boleh didistribusikan.')
    files={}
    for path in output.rglob('*'):
        if path.is_file() and path.name!='build-manifest.json':
            with path.open('rb') as stream:files[path.relative_to(output).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
    Path(manifest_path or output/'build-manifest.json').write_text(json.dumps({'purpose':'private non-commercial research',
      'platform':platform.system(),'architecture':platform.machine(),'python':platform.python_version(),
      'research_models':include_models,'windows_uat':'required separately','files':files},indent=2)+'\n')


def prepare_previous_output(output):
    output=Path(output)
    if platform.system()!='Windows' or not output.exists():return
    if output.is_symlink() or output.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError('Folder keluaran build tidak boleh berupa tautan.')
    for path in output.rglob('*'):
        if (path.is_symlink() or path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                or not path.resolve().is_relative_to(output.resolve())):
            raise ValueError('Keluaran build lama berisi tautan di luar folder.')
        if path.is_file() and path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
            path.chmod(stat.S_IREAD | stat.S_IWRITE)


def validate_macos_bundle(output):
    output = Path(output)
    with (output/'Contents/Info.plist').open('rb') as stream:
        info = plistlib.load(stream)
    if info.get('LSBackgroundOnly') or info.get('LSUIElement'):
        raise ValueError('Bundle macOS harus berupa aplikasi GUI dengan akses keyboard dan ikon Dock.')
    if info.get('CFBundleExecutable') != 'StarGate' or info.get('CFBundlePackageType') != 'APPL':
        raise ValueError('Entry point bundle macOS bukan aplikasi StarGate.')
    icon = info.get('CFBundleIconFile')
    if not icon or Path(icon).name != icon or not (output/'Contents/Resources'/icon).is_file():
        raise ValueError('Ikon bundle macOS tidak tersedia.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',choices=['windows','macos'],required=True)
    parser.add_argument('--include-research-models',action='store_true',help='Private non-commercial research only; not production clearance')
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--postgres-runtime',type=Path,help='Prepared Windows PostgreSQL 17 x64/pgvector runtime for automatic local setup')
    args=parser.parse_args(argv)
    try:
        validate_build(args.target,args.include_research_models)
        if args.postgres_runtime:
            if args.target!='windows':raise ValueError('Runtime database lokal hanya untuk paket Windows.')
            from app.services.local_database import verify_runtime
            if args.postgres_runtime.name!='postgresql':raise ValueError('Folder runtime harus bernama postgresql.')
            verify_runtime(args.postgres_runtime.parent)
        if args.check_only:print('Prasyarat build PASS; executable belum dibuat.');return 0
        import os
        env=dict(os.environ);env['STARGATE_BUILD_RESEARCH_MODELS']='1' if args.include_research_models else '0'
        prepare_previous_output(ROOT/'dist/StarGate')
        result=subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean',str(ROOT/'packaging/StarGate.spec')],cwd=ROOT,env=env)
        if result.returncode:return result.returncode
        output=ROOT/('dist/StarGate.app' if args.target=='macos' else 'dist/StarGate')
        if args.postgres_runtime:
            shutil.copytree(args.postgres_runtime,output/'_internal/postgresql')
        if args.target=='macos':
            validate_macos_bundle(output)
            # Keep the manifest outside the signed application bundle.
            finalize_output(output,args.include_research_models,manifest_path=ROOT/'dist/StarGate-build-manifest.json')
            subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(output)],check=True)
            shutil.rmtree(ROOT/'dist/StarGate')
        else:
            finalize_output(output,args.include_research_models)
        print('Paket dibuat; lakukan package-check dan UAT pada OS target sebelum distribusi.')
        return 0
    except Exception as error:
        if isinstance(error,ValueError):print(str(error),file=sys.stderr)
        else:print('Build gagal ('+type(error).__name__+'). Periksa dependensi dan ruang penyimpanan.',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())

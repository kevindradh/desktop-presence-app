"""Assemble the research source kit from curated code and verified Windows assets."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

BUILD=Path('C:/StarGate-build')
SHARE=Path('C:/Mac/Home/Downloads/dekstop_face_recognition').resolve()


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    assert sys.platform=='win32'
    sys.path.insert(0,str(SHARE))
    from scripts.prepare_windows_kit import selected_files
    from app.services.local_database import verify_runtime
    from ai.models import verified_assets
    runtime=verify_runtime(BUILD/'prerequisites/auto-20261028')
    assets=verified_assets(SHARE,SHARE/'resources/models')
    manifest=json.loads((SHARE/'models/manifest.json').read_text())
    files={p.relative_to(SHARE).as_posix():p for p in selected_files(SHARE)}
    files['SOURCE-README.md']=SHARE/'docs/windows-source-setup.md'
    support={}
    for path in runtime.rglob('*'):
        if path.is_file():support['postgresql/'+path.relative_to(runtime).as_posix()]=path
    for item in manifest['assets']:
        support[item['path']]=SHARE/item['path']
    lock=(SHARE/'requirements-windows-x64.candidate.lock.txt').read_text()
    allowed=set(__import__('re').findall(r'--hash=sha256:([a-f0-9]{64})',lock))
    wheels=list((BUILD/'wheelhouse').glob('*.whl'))
    assert wheels and {digest(path) for path in wheels}==allowed,'Wheelhouse and lock differ'
    for path in wheels:support['wheelhouse/'+path.name]=path
    for path in support.values():
        assert path.is_file() and not path.is_symlink()
    hashes={name:digest(path) for name,path in support.items()}
    output=SHARE/'dist/StarGate-Source-Windows-x64-0.14.3.zip'
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for name,path in sorted((files|support).items()):archive.write(path,name)
        archive.writestr('source-support-manifest.json',json.dumps({'purpose':'non-commercial research source setup',
            'python':'CPython 3.11 x64','files':hashes},indent=2)+'\n')
    checksum=digest(output)
    output.with_suffix('.zip.sha256').write_text(checksum+'  '+output.name+'\n',encoding='utf-8',newline='\n')
    report={'archive':str(output.relative_to(SHARE)),'sha256':checksum,'bytes':output.stat().st_size,
        'source_files':len(files),'support_files':len(support),'wheels':len(wheels),
        'contains_user_data':False,'python_included':False,'application_entry':'main.py',
        'source_only':'No StarGate executable; PostgreSQL tools are native binaries'}
    target=SHARE/'docs/testing/evidence/windows-source-0.14.3'
    assert target.is_dir()
    (target/'artifact.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()

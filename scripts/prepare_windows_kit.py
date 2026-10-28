"""Curated source transfer kit; never includes .env, galleries, dumps, logs or virtualenvs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def selected_files(root,include_models=False):
    root=Path(root).resolve()
    selected={root/p for p in ('main.py','alembic.ini','requirements.in','pytest.ini','README.md','PLAN.md','.env.example')}
    # Preserve the Windows candidate pins/hashes without treating a macOS lock as portable.
    for name in ('requirements-windows-x64.candidate.txt','requirements-windows-x64.candidate.lock.txt'):
        if (root/name).is_file():selected.add(root/name)
    for folder in ('app','ai','database','scripts','tests','packaging'):
        selected.update(p for p in (root/folder).rglob('*') if p.is_file() and (p.suffix in {'.py','.spec','.iss','.ps1','.md','.sql'} or p.name=='.env.example') and '__pycache__' not in p.parts)
    selected.update(root/p for p in ('models/manifest.json','resources/branding/stargate.png',
        'resources/branding/stargate.ico','resources/branding/stargate.icns','resources/samples/profile-removed.svg',
        'resources/samples/profile-test.png','resources/sounds/success.wav',
        'third_party/minifasnet/__init__.py','third_party/minifasnet/MiniFASNet.py',
        'third_party/minifasnet/LICENSE','third_party/minifasnet/README.md',
        'docs/testing/stage-14.md','docs/testing/stage-14-manual.md','docs/windows-install.md',
        'docs/windows-auto-setup.md','docs/windows11-amd-setup.md'))
    if include_models:
        from ai.models import verified_assets
        verified_assets(root,root/'resources/models')
        selected.update(root/'resources/models'/name for name in ('Widerface-RetinaFace.caffemodel','deploy.prototxt',
            '2.7_80x80_MiniFASNetV2.pth','w600k_r50.onnx','2d106det.onnx'))
    for path in selected:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):raise ValueError('Sumber kit tidak lengkap atau berupa tautan.')
        relative=path.relative_to(root)
        if any(part in {'.local','.venv','.git','data','backups','logs'} for part in relative.parts) or path.suffix=='.sgbackup' or path.name=='.env':
            raise ValueError('Data privat tidak boleh masuk kit.')
    return sorted(selected)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--include-research-models',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'dist/StarGate-Windows-build-kit.zip');args=parser.parse_args(argv)
    try:
        files=selected_files(ROOT,args.include_research_models)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive creation protects existing user exports.
        with args.output.open('xb') as output,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
            hashes={}
            for path in files:
                relative=path.relative_to(ROOT).as_posix();archive.write(path,relative)
                with path.open('rb') as stream:hashes[relative]=hashlib.file_digest(stream,'sha256').hexdigest()
            archive.writestr('kit-manifest.json',json.dumps({'kind':'SOURCE BUILD KIT, NOT WINDOWS EXECUTABLE',
                'research_models':args.include_research_models,'files':hashes},indent=2)+'\n')
        print('Kit sumber siap. Build dan UAT Windows masih diperlukan.');return 0
    except Exception as error:
        print('Kit belum dibuat ('+type(error).__name__+'). File lama tidak ditimpa.',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())

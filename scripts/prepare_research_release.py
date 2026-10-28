"""Assemble a verified internal research candidate from explicitly selected files."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

DOCUMENTS=('docs/operations.md','docs/architecture.md','docs/database.md','docs/decisions.md',
    'docs/biometric-retention.md','docs/windows-auto-setup.md','docs/testing/stage-15.md',
    'docs/testing/stage-15-acceptance-map.md','docs/release-candidate.md','docs/testing/stage-16.md')


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def build_release(installer,artifact,output,*,root=ROOT):
    from scripts.prepare_windows_kit import selected_files
    root=Path(root).resolve();installer=Path(installer);output=Path(output)
    metadata=json.loads(Path(artifact).read_text(encoding='utf-8'))
    version=metadata['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+-research',version):raise ValueError('Expected a research version')
    if installer.is_symlink() or digest(installer)!=metadata['sha256'] or installer.stat().st_size!=metadata['bytes']:
        raise ValueError('Installer checksum mismatch')
    archive_path=Path(str(output)+'.zip')
    if output.exists() or archive_path.exists() or archive_path.with_suffix('.zip.sha256').exists():
        raise FileExistsError('Release output already exists')
    sources=selected_files(root,include_models=False)
    for source in sources:
        relative=source.relative_to(root)
        if source.is_symlink() or not source.resolve().is_relative_to(root) or source.name=='.env' or source.suffix=='.sgbackup':
            raise ValueError('Private or linked source rejected')
        if any(part in {'.local','.git','.venv','data','logs','backups'} for part in relative.parts):
            raise ValueError('Private source folder rejected')
    extras=sorted(set([root/name for name in DOCUMENTS]+list((root/'docs').rglob('*.md'))+
        [root/'packaging/THIRD_PARTY_NOTICES.md']))
    evidence=root/'docs/testing/evidence'
    extras+=sorted(path for pattern in ('stage-15-*.xml','stage-15-*.json','stage-16-*.xml',
        'stage-15-final-windows/*.json','stage-15-final-windows/*.txt',
        'parallels-interactive-20261028/search-scale.json') for path in evidence.glob(pattern))
    if any(not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root) for path in extras):
        raise ValueError('Release documents incomplete or linked')
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(installer,output/'StarGate-Research-Windows-x64.exe')
    source_manifest={}
    with zipfile.ZipFile(output/'source-code.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for source in sources:
            name=source.relative_to(root).as_posix();archive.write(source,name);source_manifest[name]=digest(source)
        archive.writestr('kit-manifest.json',json.dumps({'kind':'SOURCE BUILD KIT, NOT WINDOWS EXECUTABLE',
            'research_models':False,'files':source_manifest},indent=2)+'\n')
    for source in extras:
        relative=source.relative_to(root);target=output/relative
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    shutil.copyfile(artifact,output/'artifact.json')
    (output/'README.md').write_text(
        '# StarGate '+version+'\n\n'
        'Kandidat untuk lomba, penelitian dan uji internal. Penerimaan V1 belum ditutup.\n\n'
        '1. Tutup StarGate dan cocokkan SHA256 installer dengan `artifact.json`.\n'
        '2. Jalankan `StarGate-Research-Windows-x64.exe` pada akun Windows pemakai.\n'
        '3. Ikuti [panduan operasi](docs/operations.md) dan '
        '[panduan setup](docs/windows-auto-setup.md).\n'
        '4. Catat hasil sesuai [gerbang yang tersisa](docs/testing/remaining-acceptance.md).\n\n'
        '`source-code.zip` berisi source build kit tanpa bobot pretrained, database atau data pengguna. '
        'Hash seluruh isi tersedia pada `release-manifest.json`.\n\n'
        'Baca [catatan kandidat](docs/release-candidate.md) dan '
        '[notice pihak ketiga](packaging/THIRD_PARTY_NOTICES.md) sebelum penyerahan.\n',encoding='utf-8')
    manifest={'version':version,'status':'internal research candidate; acceptance gates remain in PLAN.md',
        'pretrained_weights_in_source':False,'installer_sha256':digest(output/'StarGate-Research-Windows-x64.exe'),
        'files':{path.relative_to(output).as_posix():digest(path) for path in sorted(output.rglob('*')) if path.is_file()}}
    (output/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with zipfile.ZipFile(archive_path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for path in sorted(output.rglob('*')):
            if path.is_file():archive.write(path,path.relative_to(output).as_posix())
    archive_path.with_suffix('.zip.sha256').write_text(digest(archive_path)+'  '+archive_path.name+'\n',encoding='utf-8')
    return {'archive':str(archive_path),'sha256':digest(archive_path),'version':version,'files':len(manifest['files'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer',type=Path,required=True)
    parser.add_argument('--artifact',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build_release(args.installer,args.artifact,args.output)))


if __name__=='__main__':main()

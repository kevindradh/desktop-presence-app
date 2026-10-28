"""Fresh source-kit setup with an isolated database; no existing app data touched."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

SHARE=Path('C:/Mac/Home/Downloads/dekstop_face_recognition')
SOURCE=Path('C:/StarGate-source-0143')
EVIDENCE=Path('C:/StarGate-build/source-evidence-0143')
DATA=Path(os.environ['LOCALAPPDATA'])/'StarGate-Source-UAT0143'
BASE=Path('C:/StarGate-build/prerequisites/Python-3.11.17/PCbuild/amd64/python.exe')


def main():
    assert sys.platform=='win32'
    EVIDENCE.mkdir(exist_ok=True)
    action=sys.argv[1]
    environment={k:v for k,v in os.environ.items() if not k.upper().startswith(('STARGATE_','PYTHON'))}
    environment['SG_SOURCE_PYTHON']=str(BASE)
    environment['SG_SOURCE_NO_PAUSE']='1'
    if action in {'extract','refresh-extract'}:
        assert not DATA.exists(),'Test data folder must be new'
        if action=='extract':assert not SOURCE.exists(),'Test source folder must be new'
        else:assert SOURCE.is_dir() and not (SOURCE/'.venv-win').exists()
        archive=SHARE/'dist/StarGate-Source-Windows-x64-0.14.3.zip'
        metadata=json.loads((SHARE/'docs/testing/evidence/windows-source-0.14.3/artifact.json').read_text())
        with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==metadata['sha256']
        SOURCE.mkdir(exist_ok=action=='refresh-extract')
        with zipfile.ZipFile(archive) as bundle:
            for name in bundle.namelist():
                path=Path(name)
                assert not path.is_absolute() and '..' not in path.parts and ':' not in name and '\\' not in name
                assert path.name!='.env'
                bundle.extract(name,SOURCE)
        print('Fresh source kit extracted; checksum matches',flush=True)
    elif action in {'setup','repeat'}:
        with (EVIDENCE/(action+'.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run(['cmd.exe','/d','/c',str(SOURCE/'SETUP-WINDOWS.cmd'),
                                   '--data-dir',str(DATA)],cwd=SOURCE,env=environment,
                                  stdout=log,stderr=subprocess.STDOUT,timeout=900)
        print('Source setup exit: '+str(result.returncode),flush=True)
        return result.returncode
    elif action=='inspect':
        code="""import json
from pathlib import Path
from database.runtime import connection_config,schema_status
from app.services.database import create_database_engine
from sqlalchemy import text
root=Path(__import__('sys').argv[1])
engine=create_database_engine(connection_config('dev',root=root))
with engine.connect() as c:
 report={'schema':schema_status(c),'counts':{name:c.scalar(text('SELECT count(*) FROM '+name)) for name in ('users','members','attendance','face_embeddings')}}
engine.dispose()
print(json.dumps(report))
"""
        result=subprocess.run([str(SOURCE/'.venv-win/Scripts/python.exe'),'-c',code,str(DATA)],
                              cwd=SOURCE,env=environment,capture_output=True,text=True,encoding='utf-8',check=True)
        report=json.loads(result.stdout)
        assert report['schema']['at_head'] and report['schema']['schema_valid']
        assert all(value==0 for value in report['counts'].values())
        report.update(source_entry='main.py',fresh_venv=True,offline_wheels=True,
                      real_faces_used=False,environment='Windows11 ARM64 Parallels with x64 CPython3.11.17',
                      physical_amd_tested=False)
        (EVIDENCE/'source-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report),flush=True)
    elif action=='stop':
        return subprocess.call([str(SOURCE/'.venv-win/Scripts/python.exe'),'scripts/setup_local_windows.py',
                                'stop-local-db','--data-dir',str(DATA)],cwd=SOURCE,env=environment)
    elif action=='export':
        output=SHARE/'docs/testing/evidence/windows-source-0.14.3'
        for path in EVIDENCE.iterdir():
            if path.suffix=='.json':(output/path.name).write_text(path.read_text(),encoding='utf-8',newline='\n')
            elif path.suffix=='.log':
                (output/(path.name+'.tail.txt')).write_text('\n'.join(path.read_text(encoding='utf-8',errors='replace').splitlines()[-40:])+'\n',encoding='utf-8',newline='\n')
        print('Source setup evidence exported',flush=True)
    else:raise ValueError(action)
    return 0


if __name__=='__main__':raise SystemExit(main())

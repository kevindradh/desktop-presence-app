"""VM build helper; no access to customer configuration or database contents."""
import hashlib
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import zipfile

BUILD = Path('C:/StarGate-build')
SHARE = Path('C:/Mac/Home/Downloads/dekstop_face_recognition')
PYTHON = BUILD/'.venv-win/Scripts/python.exe'


def main():
    action = sys.argv[1] if len(sys.argv)>1 else 'inventory'
    if action == 'inventory':
        import shutil
        import ctypes
        print(json.dumps({'python': str(PYTHON), 'share_available': SHARE.is_dir(),
            'free_bytes': shutil.disk_usage(BUILD).free, 'elevated': bool(ctypes.windll.shell32.IsUserAnAdmin())}))
        postgres = BUILD/'prerequisites/postgresql17/pgsql'
        subprocess.run([str(postgres/'bin/postgres.exe'),'--version'],check=True)
        for path in postgres.rglob('*'):
            if path.is_file() and any(word in path.name.lower() for word in ('license','copyright','notice')):
                print(path)
        for base in (Path(os.environ['LOCALAPPDATA'])/'Programs', BUILD/'prerequisites'):
            for compiler in base.rglob('ISCC.exe'):
                print('ISCC:',compiler)
        print('prerequisites:',[p.name for p in (BUILD/'prerequisites').iterdir() if p.is_dir()])
        print('PG folders:',[p.name for p in postgres.iterdir()])
        print('PLAN attributes:',(BUILD/'PLAN.md').stat().st_file_attributes)
        subprocess.run(['icacls',str(BUILD/'PLAN.md')],check=True)
        return 0
    if action == 'sync':
        if len(sys.argv)<3:raise ValueError('Pass the reviewed source kit path explicitly')
        archive = Path(sys.argv[2])
        with zipfile.ZipFile(archive) as source:
            manifest = json.loads(source.read('kit-manifest.json'))
            for name, digest in manifest['files'].items():
                relative = Path(name)
                if relative.is_absolute() or '..' in relative.parts or ':' in name or '\\' in name or relative.name=='.env':
                    raise ValueError('Unsafe source kit entry')
                content = source.read(name)
                if hashlib.sha256(content).hexdigest()!=digest:
                    raise ValueError('Source kit checksum mismatch')
                target = BUILD/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists() and target.stat().st_file_attributes & 1:
                    target.chmod(stat.S_IREAD | stat.S_IWRITE)
                target.write_bytes(content)
        return subprocess.call([str(PYTHON),'-m','pip','check'],cwd=BUILD)
    if action == 'prepare':
        return subprocess.call([str(PYTHON),str(BUILD/'scripts/prepare_postgres_runtime.py'),
            '--source',str(BUILD/'prerequisites/postgresql17/pgsql'),
            '--output',str(BUILD/'prerequisites/auto-20261028/postgresql'),
            '--postgres-license',str(SHARE/'.local/build-inputs/postgresql17-COPYRIGHT'),
            '--pgvector-license',str(BUILD/'prerequisites/pgvector-source/pgvector-0.8.7/LICENSE')],cwd=BUILD)
    if action == 'build':
        evidence=BUILD/'automatic-evidence-20261028';evidence.mkdir(exist_ok=True)
        with (evidence/'build.log').open('w',encoding='utf-8') as log:
            result=subprocess.run([str(PYTHON),'scripts/build_package.py','--target','windows',
                '--include-research-models','--postgres-runtime',
                str(BUILD/'prerequisites/auto-20261028/postgresql')],cwd=BUILD,stdout=log,stderr=subprocess.STDOUT)
        print('PyInstaller exit:',result.returncode,flush=True)
        return result.returncode
    if action == 'status':
        import shutil
        evidence=BUILD/'automatic-evidence-20261028'
        for name in ('build.log','installer.log'):
            file=evidence/name
            if file.exists():
                print(name,flush=True)
                print('\n'.join(file.read_text(encoding='utf-8',errors='replace').splitlines()[-7:]),flush=True)
        print(json.dumps({'free_bytes':shutil.disk_usage(BUILD).free}),flush=True)
        return 0
    if action == 'compile':
        compiler=Path(os.environ['LOCALAPPDATA'])/'Programs/Inno Setup 6/ISCC.exe'
        evidence=BUILD/'automatic-evidence-20261028';evidence.mkdir(exist_ok=True)
        with (evidence/'installer.log').open('w',encoding='utf-8') as log:
            result=subprocess.run([str(compiler),str(BUILD/'packaging/windows/StarGate.iss')],
                cwd=BUILD,stdout=log,stderr=subprocess.STDOUT)
        print('Inno Setup exit:',result.returncode,flush=True)
        return result.returncode
    if action == 'uat-companion':
        evidence=BUILD/'automatic-evidence-20261028';evidence.mkdir(exist_ok=True)
        script=BUILD/'scripts/testing/windows_auto_frozen_uat.py'
        spec=evidence/'StarGateAutoUAT.spec'
        spec.write_text('''from pathlib import Path
from PyInstaller.utils.misc import load_py_data_struct
from PyInstaller.building.build_main import Analysis
root=Path(r"C:\\StarGate-build")
state=load_py_data_struct(root/'build/StarGate/Analysis-00.toc')
index=[item[0] for item in Analysis._GUTS].index('scripts')
scripts=[entry for entry in state[index] if entry[0] not in {'main','admin_entry'}]
scripts.append(('windows_auto_frozen_uat',str(root/'scripts/testing/windows_auto_frozen_uat.py'),'PYSOURCE'))
pure_index=[item[0] for item in Analysis._GUTS].index('pure')
pyz=PYZ(state[pure_index])
exe=EXE(pyz,scripts,[],
    exclude_binaries=True,name='StarGateAutoUAT',console=True,debug=False,upx=False)
''',encoding='utf-8')
        with (evidence/'uat-companion.log').open('w',encoding='utf-8') as log:
            result=subprocess.run([str(PYTHON),'-m','PyInstaller','--noconfirm',str(spec)],
                cwd=BUILD,stdout=log,stderr=subprocess.STDOUT)
        print('UAT companion exit:',result.returncode,flush=True)
        return result.returncode
    if action == 'deploy-uat':
        import shutil
        installed=Path('C:/Users/SGAuto28/AppData/Local/Programs/StarGate')
        assert (installed/'StarGate.exe').is_file()
        shutil.copy2(BUILD/'build/StarGateAutoUAT/StarGateAutoUAT.exe',installed/'StarGateAutoUAT.exe')
        print('Build-only UAT companion deployed to the owned test profile')
        return 0
    if action == 'profile-status':
        folder=Path('C:/Users/SGAuto28/AppData/Local/StarGate-UAT28')
        print('evidence_available:',folder.exists())
        if folder.exists():
            print('files:',[p.name for p in folder.iterdir()])
            for name in ('failure.log','install-inno.log','repair-inno.log','reinstall-inno.log'):
                file=folder/name
                if file.exists():print(name+'\n'+'\n'.join(file.read_text(encoding='utf-8',errors='replace').splitlines()[-8:]))
        return 0
    if action == 'export':
        import shutil
        evidence=BUILD/'automatic-evidence-20261028'
        profile=Path('C:/Users/SGAuto28/AppData/Local/StarGate-UAT28')
        output=SHARE/'docs/testing/evidence/automatic-windows-20261028'
        output.mkdir(parents=True,exist_ok=True)
        for name in ('source-core.xml','source-uat.json',*[f'frozen-probe-{i}.log' for i in range(6)]):
            source=evidence/name
            if source.is_file():shutil.copyfile(source,output/name)
        for name in ('install.json','probe.json','repair.json','uninstall.json','reinstall.json',
                     'inspect.json','stop.json','fresh-probe.json','frozen-ui.json',
                     'frozen-dashboard.png','frozen-toast.png','frozen-inspect.log',
                     'frozen-resume.log'):
            source=profile/name
            if source.is_file():shutil.copyfile(source,output/name)
        for name in ('installer.log','build.log','uat-companion.log'):
            source=evidence/name
            if source.is_file():
                (output/(name+'.tail.txt')).write_text('\n'.join(source.read_text(encoding='utf-8',errors='replace').splitlines()[-35:]),encoding='utf-8')
        for name in ('install-inno.log','repair-inno.log','uninstall-inno.log','reinstall-inno.log',
                     'first-install-inno.log','first-repair-inno.log'):
            source=profile/name
            if source.is_file():
                (output/(name+'.tail.txt')).write_text('\n'.join(source.read_text(encoding='utf-8',errors='replace').splitlines()[-65:]),encoding='utf-8')
        installer=BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
        target=SHARE/'dist/windows/StarGate-Research-Windows-x64-0.14.1.exe'
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(installer,target)
        def digest(path):
            with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest(installer)==digest(target)
        result={'version':'0.14.1-research','artifact':str(target.relative_to(SHARE)),
            'bytes':installer.stat().st_size,'sha256':digest(installer),
            'environment':'Windows 11 ARM64 Parallels running x64 package',
            'physical_amd_tested':False,'synthetic_data_only':True}
        manifest=BUILD/'dist/StarGate/build-manifest.json'
        shutil.copyfile(manifest,output/'build-manifest.json')
        result['bundle_file_count']=len(json.loads(manifest.read_text(encoding='utf-8'))['files'])
        result['bundle_manifest_sha256']=digest(manifest)
        result['installer_definition_sha256']=digest(SHARE/'packaging/windows/StarGate.iss')
        result['installer_definition_matches_build']=(SHARE/'packaging/windows/StarGate.iss').read_bytes()==(BUILD/'packaging/windows/StarGate.iss').read_bytes()
        assert result['installer_definition_matches_build']
        source_files={}
        for name in ('app/services/local_database.py','app/ui/session_window.py',
                     'app/pages/dashboard.py','app/pages/attendance.py','app/widgets/toast.py',
                     'scripts/setup_local_windows.py','packaging/StarGate.spec'):
            assert (SHARE/name).read_bytes()==(BUILD/name).read_bytes(),name
            source_files[name]=digest(SHARE/name)
        result['verified_source_sha256']=source_files
        import base64
        signature_code="Get-AuthenticodeSignature 'C:\\StarGate-build\\dist\\installer\\StarGate-Research-Windows-x64.exe' | Select-Object Status,StatusMessage | ConvertTo-Json"
        signature=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',
            base64.b64encode(signature_code.encode('utf-16-le')).decode('ascii')],
            capture_output=True,text=True,check=True)
        signature_result=json.loads(signature.stdout)
        result['authenticode']={'status_code':signature_result['Status'],
            'status':'NotSigned' if signature_result['Status']==2 else signature_result['StatusMessage']}
        (output/'artifact.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
        return 0
    if action == 'frozen-probe':
        evidence=BUILD/'automatic-evidence-20261028';evidence.mkdir(exist_ok=True)
        admin=BUILD/'dist/StarGate/StarGateAdmin.exe'
        root=evidence/'frozen-data'
        environment={key:value for key,value in os.environ.items() if not key.upper().startswith(('STARGATE_','PYTHON'))}
        system=Path(os.environ['SystemRoot'])
        environment.update(PATH=str(system/'System32')+';'+str(system),QT_QPA_PLATFORM='offscreen')
        commands=[['setup-check'],['package-check','--verify-models'],['setup-local'],['check'],['setup-local'],['stop-local-db']]
        for index,arguments in enumerate(commands):
            with (evidence/f'frozen-probe-{index}.log').open('w',encoding='utf-8') as log:
                result=subprocess.run([str(admin),*arguments,'--data-dir',str(root)],cwd=evidence,
                    env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=240)
            print(arguments[0],result.returncode,flush=True)
            if result.returncode:return result.returncode
        return 0
    if action == 'test':
        evidence=BUILD/'automatic-evidence-20261028';evidence.mkdir(exist_ok=True)
        return subprocess.call([str(PYTHON),'-m','pytest','tests/test_local_database.py',
            'tests/test_private_files.py','tests/test_packaging.py','-q','--tb=short','--maxfail=1',
            '--junitxml='+str(evidence/'source-core.xml')],cwd=BUILD)
    if action == 'refresh-tests':
        names=[p.relative_to(SHARE) for p in (SHARE/'scripts/testing').glob('windows_auto_*.py')]
        names.append(Path('packaging/windows/StarGate.iss'))
        for name in names:
            target=BUILD/name;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():target.chmod(stat.S_IREAD|stat.S_IWRITE)
            target.write_bytes((SHARE/name).read_bytes())
        print('Refreshed testing helpers and installer definition')
        return 0
    if action == 'source-uat':
        sys.path.insert(0,str(BUILD))
        import secrets
        from app.services.local_database import setup_local,stop_local,ensure_local_database
        from app.settings.config import load_config
        from app.services.auth import AuthService
        from app.services.database import Database,create_database_engine
        from database.runtime import schema_status
        from sqlalchemy import text
        evidence=BUILD/'automatic-evidence-20261028';evidence.mkdir(exist_ok=True)
        root=evidence/'source-data'
        resources=BUILD/'prerequisites/auto-20261028'
        database=None
        try:
            setup=setup_local(root,resources)
            config=load_config(root,environ={},bundle_root=resources)
            original=(root/'.env').read_bytes()
            database=Database(create_database_engine(config.database))
            auth=AuthService(database)
            if auth.bootstrap_required():auth.bootstrap('auto-uat','Penguji Sintetis',secrets.token_urlsafe(24)+'aA1!')
            with database.transaction() as session:
                schema=schema_status(session.connection())
                assert schema['at_head'] and schema['schema_valid']
                assert not session.execute(text('SELECT rolsuper FROM pg_roles WHERE rolname=current_user')).scalar_one()
                assert session.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one()=='0.8.7'
            setup_local(root,resources)
            assert (root/'.env').read_bytes()==original and not auth.bootstrap_required()
            database.close();database=None
            stop_local(root,resources)
            ensure_local_database(config)
            database=Database(create_database_engine(config.database))
            assert not AuthService(database).bootstrap_required()
            result={'mode':'source Windows x64','setup':setup,'schema':schema,'app_role_minimal':True,
                'setup_repeat_preserves_account_and_config':True,'stop_start_preserves_account':True}
            (evidence/'source-uat.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(json.dumps(result))
        finally:
            if database is not None:database.close()
            if (root/'.local/managed-postgres/state.json').exists():stop_local(root,resources)
        return 0
    raise ValueError('Unknown phase')


if __name__=='__main__':raise SystemExit(main())

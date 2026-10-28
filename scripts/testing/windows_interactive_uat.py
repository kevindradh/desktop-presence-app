"""Prepare an isolated interactive test using the released Windows installer."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BUILD=Path('C:/StarGate-build')
SHARE=Path('C:/Mac/Home/Downloads/dekstop_face_recognition')


def main():
    import ctypes
    if sys.platform!='win32' or ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError('Use the logged-in standard Windows account')
    local=Path(os.environ['LOCALAPPDATA'])
    installed=local/'Programs/StarGate'
    root=local/'StarGate-Parallels-0141'
    evidence=BUILD/'final-evidence-0142'
    evidence.mkdir(exist_ok=True)
    original=local/'StarGate/.env'
    def fingerprint():
        return hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None
    action=sys.argv[1]
    environment={k:v for k,v in os.environ.items() if not k.upper().startswith(('STARGATE_','PYTHON')) and k!='QT_QPA_PLATFORM'}
    system=Path(os.environ['SystemRoot'])
    environment['PATH']=str(system/'System32')+';'+str(system)
    if action=='resume-build':
        import shutil
        import stat
        target=BUILD/'scripts/build_package.py'
        if target.exists():target.chmod(stat.S_IREAD | stat.S_IWRITE)
        shutil.copyfile(SHARE/'scripts/build_package.py',target)
        sys.path.insert(0,str(BUILD))
        from scripts.build_package import prepare_previous_output,finalize_output
        previous=BUILD/'automatic-evidence-20261028/build.log'
        (evidence/'initial-build-failure.txt').write_text('\n'.join(previous.read_text(encoding='utf-8',errors='replace').splitlines()[-25:])+'\n',encoding='utf-8')
        prepare_previous_output(BUILD/'dist/StarGate')
        build_environment=dict(os.environ,STARGATE_BUILD_RESEARCH_MODELS='1')
        with previous.open('w',encoding='utf-8') as log:
            result=subprocess.run([str(BUILD/'.venv-win/Scripts/python.exe'),'-m','PyInstaller',
                '--noconfirm',str(BUILD/'packaging/StarGate.spec')],cwd=BUILD,env=build_environment,
                stdout=log,stderr=subprocess.STDOUT)
        assert result.returncode==0,result.returncode
        shutil.copytree(BUILD/'prerequisites/auto-20261028/postgresql',BUILD/'dist/StarGate/_internal/postgresql')
        finalize_output(BUILD/'dist/StarGate',True)
        print('Build without --clean completed; output finalized',flush=True)
    elif action=='inventory':
        import base64
        code="Get-CimInstance Win32_PnPEntity | Where-Object {$_.PNPClass -in @('Camera','Image')} | Select-Object Name,Status | ConvertTo-Json"
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',
            base64.b64encode(code.encode('utf-16-le')).decode('ascii')],capture_output=True,text=True,check=True)
        data=json.loads(result.stdout)
        (evidence/'camera-inventory.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps(data),flush=True)
    elif action=='verify-build-output':
        import shutil
        import stat
        target=BUILD/'scripts/build_package.py'
        target.chmod(stat.S_IREAD | stat.S_IWRITE)
        shutil.copyfile(SHARE/'scripts/build_package.py',target)
        sys.path.insert(0,str(BUILD))
        from scripts.build_package import prepare_previous_output
        fixture=evidence/'readonly-fixture'
        fixture.mkdir(exist_ok=True)
        readonly=fixture/'notice.txt'
        if readonly.exists():readonly.chmod(stat.S_IREAD | stat.S_IWRITE)
        readonly.write_text('owned synthetic license fixture',encoding='utf-8')
        readonly.chmod(stat.S_IREAD)
        assert readonly.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY
        prepare_previous_output(fixture)
        assert not readonly.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY
        readonly.write_text('writable after preparation',encoding='utf-8')
        prepare_previous_output(BUILD/'dist/StarGate')
        result={'native_windows_readonly_recovery':True,'scope':'owned build output only',
            'user_data_modified':False,'build_script_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        (evidence/'build-recovery.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    elif action=='data-check':
        sys.path.insert(0,str(BUILD))
        from sqlalchemy import text
        from app.services.database import create_database_engine
        from database.runtime import connection_config
        config=connection_config('dev',root=root)
        assert config.name=='stargate_local' and config.host in {'localhost','127.0.0.1','::1'}
        engine=create_database_engine(config)
        try:
            with engine.connect() as connection:
                counts={name:connection.scalar(text('SELECT count(*) FROM '+name))
                    for name in ('members','users','attendance','face_embeddings')}
                revision=connection.scalar(text('SELECT version_num FROM alembic_version'))
            assert counts['members']>=80 and counts['users']>=4 and counts['attendance']>=2467,counts
            assert revision=='0006_search_storage',revision
            result={'actual_database_counts':counts,'revision':revision,'original_seed_baseline_present':True,'comparison':'at least 80 members, 4 seeded roles, 2467 seeded attendance events; not a full before/after user-data diff',
                'biometric_content_exported':False}
            (evidence/'data-preservation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(json.dumps(result),flush=True)
        finally:engine.dispose()
    elif action=='package-probe':
        result=subprocess.run([str(installed/'StarGateAdmin.exe'),'package-check','--verify-models',
            '--data-dir',str(root)],env=environment,capture_output=True,text=True,encoding='utf-8',timeout=240)
        assert result.returncode==0,result.returncode
        safe=json.loads(result.stdout)
        assert safe['package_check']=='PASS'
        (evidence/'package-check.json').write_text(json.dumps(safe,indent=2),encoding='utf-8')
        print(json.dumps(safe),flush=True)
    elif action=='artifact':
        import shutil
        import base64
        output=SHARE/'docs/testing/evidence/stage-15-final-windows'
        assert output.is_dir()
        candidate=BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
        definition=BUILD/'packaging/windows/StarGate.iss'
        assert '#define AppVersion "0.14.2-research"' in definition.read_text()
        def digest(path):
            with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        target=SHARE/'dist/windows/StarGate-Research-Windows-x64-0.14.2.exe'
        assert not target.exists(),'Never replace an existing versioned artifact'
        shutil.copyfile(candidate,target)
        assert digest(candidate)==digest(target)
        manifest=BUILD/'dist/StarGate/build-manifest.json'
        shutil.copyfile(manifest,output/'build-manifest.json')
        files={}
        for name in ('app/repositories/core.py','database/migrations/versions/0006_exact_search_storage.py',
                     'packaging/windows/StarGate.iss','packaging/StarGate.spec','packaging/THIRD_PARTY_NOTICES.md','scripts/build_package.py'):
            assert (SHARE/name).read_bytes()==(BUILD/name).read_bytes(),name
            files[name]=digest(SHARE/name)
        code="Get-AuthenticodeSignature 'C:\\StarGate-build\\dist\\installer\\StarGate-Research-Windows-x64.exe' | Select-Object Status | ConvertTo-Json"
        signature=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',
            base64.b64encode(code.encode('utf-16-le')).decode('ascii')],capture_output=True,text=True,check=True)
        status=json.loads(signature.stdout)['Status']
        result={'version':'0.14.2-research','artifact':target.relative_to(SHARE).as_posix(),
            'bytes':candidate.stat().st_size,'sha256':digest(candidate),
            'environment':'Windows 11 ARM64 Parallels running x64 package','physical_amd_tested':False,
            'synthetic_data_only':True,'production_source_commit':'5de31fb',
            'verified_source_sha256':files,'bundle_manifest_sha256':digest(manifest),
            'bundle_file_count':len(json.loads(manifest.read_text())['files']),
            'authenticode':{'status_code':status,'status':'NotSigned' if status==2 else str(status)}}
        (output/'artifact.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        for name in ('build.log','installer.log'):
            log=BUILD/'automatic-evidence-20261028'/name
            (output/(name+'.tail.txt')).write_text('\n'.join(log.read_text(encoding='utf-8',errors='replace').splitlines()[-35:])+'\n',encoding='utf-8')
        print(json.dumps(result),flush=True)
    elif action=='install':
        before=fingerprint()
        installer=BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
        expected=json.loads((SHARE/'docs/testing/evidence/stage-15-final-windows/artifact.json').read_text())
        with installer.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==expected['sha256']
        result=subprocess.run([str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',
            '/LOG='+str(evidence/'install.log')],env=environment,timeout=900)
        assert result.returncode==0, result.returncode
        assert fingerprint()==before,'Existing configuration changed'
        (evidence/'install.json').write_text(json.dumps({'installer_sha256':expected['sha256'],
            'standard_user':True,'existing_configuration_preserved':True},indent=2),encoding='utf-8')
        print('Latest installer installed; original configuration preserved',flush=True)
    elif action=='prepare':
        for arguments,name in ((['setup-local'],'setup'),(['check'],'schema'),(['seed-school'],'school')):
            result=subprocess.run([str(installed/'StarGateAdmin.exe'),*arguments,'--data-dir',str(root)],
                env=environment,capture_output=True,text=True,encoding='utf-8',timeout=240)
            if result.returncode:raise RuntimeError(name+' failed: '+str(result.returncode))
            safe=json.JSONDecoder().raw_decode(result.stdout.lstrip())[0]
            (evidence/(name+'.json')).write_text(json.dumps(safe,indent=2),encoding='utf-8')
            print(name+': PASS',flush=True)
        buffer=ctypes.create_unicode_buffer(32768)
        assert ctypes.windll.shell32.SHGetFolderPathW(None,0x10,None,0,buffer)==0
        shortcut=Path(buffer.value)/'StarGate Uji Parallels.cmd'
        shortcut.write_text('@echo off\nstart "" "%LOCALAPPDATA%\\Programs\\StarGate\\StarGate.exe" --data-dir "%LOCALAPPDATA%\\StarGate-Parallels-0141"\n',encoding='utf-8')
        print('Isolated test launcher prepared',flush=True)
    elif action in {'build-cameras','build-search'}:
        import shutil
        source='windows_interactive_cameras' if action=='build-cameras' else 'benchmark_search'
        executable='StarGateCameraUAT' if action=='build-cameras' else 'StarGateSearchUAT'
        helper=BUILD/('scripts/testing/'+source+'.py')
        shutil.copyfile(SHARE/('scripts/testing/'+source+'.py'),helper)
        spec=evidence/(executable+'.spec')
        spec.write_text('''from pathlib import Path
from PyInstaller.utils.misc import load_py_data_struct
from PyInstaller.building.api import EXE
root=Path(r"C:\\StarGate-build")
state=load_py_data_struct(root/'build/StarGate/EXE-00.toc')
index=[item[0] for item in EXE._GUTS].index('toc')
toc=[entry for entry in state[index] if entry[0] not in {'main','admin_entry'}]
toc.append((__PAYLOAD__,str(root/('scripts/testing/'+__PAYLOAD__+'.py')),'PYSOURCE'))
exe=EXE(toc,exclude_binaries=True,name=__EXECUTABLE__,console=True,debug=False,upx=False)
'''.replace('__PAYLOAD__',repr(source)).replace('__EXECUTABLE__',repr(executable)),encoding='utf-8')
        with (evidence/(source+'-build.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run([str(BUILD/'.venv-win/Scripts/python.exe'),'-m','PyInstaller',
                '--noconfirm',str(spec)],cwd=BUILD,stdout=log,stderr=subprocess.STDOUT)
        assert result.returncode==0
        shutil.copyfile(BUILD/('build/'+executable+'/'+executable+'.exe'),installed/(executable+'.exe'))
        print('Installed-runtime helper ready: '+source,flush=True)
    elif action=='search':
        return subprocess.call([str(installed/'StarGateSearchUAT.exe'),'--data-dir',str(root),
            '--output',str(evidence/'search-scale.json')],cwd=root,env=environment)
    elif action=='cameras':
        return subprocess.call([str(installed/'StarGateCameraUAT.exe'),'--indices','0','--output',str(evidence/'cameras.json')],cwd=root,env=environment)
    elif action=='export':
        output=SHARE/'docs/testing/evidence/stage-15-final-windows'
        assert output.is_dir(),'Create the evidence folder on macOS before transfer'
        for name in ('install.json','setup.json','schema.json','school.json','camera-inventory.json','cameras.json','search-scale.json','package-check.json','build-recovery.json','initial-build-failure.txt','data-preservation.json'):
            source=evidence/name
            if source.is_file():
                (output/name).write_text(source.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
        log=evidence/'install.log'
        (output/'install-tail.txt').write_text('\n'.join(log.read_text(encoding='utf-8').splitlines()[-38:])+'\n',encoding='utf-8',newline='\n')
        print('Non-biometric test evidence exported',flush=True)
    elif action=='cleanup-helpers':
        for name in ('StarGateCameraUAT.exe','StarGateSearchUAT.exe'):
            (installed/name).unlink(missing_ok=True)
        print('Build-only helpers removed; installed app, test data and launcher retained',flush=True)
    elif action=='launch':
        assert (root/'.local/managed-postgres/state.json').is_file()
        process=subprocess.Popen([str(installed/'StarGate.exe'),'--data-dir',str(root)],
            cwd=root,env=environment,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print(json.dumps({'launched':True,'pid':process.pid,'data_directory':str(root)}),flush=True)
    elif action=='stop':
        return subprocess.call([str(installed/'StarGateAdmin.exe'),'stop-local-db','--data-dir',str(root)],env=environment)
    else:raise ValueError('Use inventory, install, prepare, build-cameras, cameras, build-search, search, export, cleanup-helpers, launch, or stop')
    return 0


if __name__=='__main__':raise SystemExit(main())

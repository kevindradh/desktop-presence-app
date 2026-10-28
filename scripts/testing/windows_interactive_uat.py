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
    evidence=BUILD/'interactive-evidence-20261028'
    evidence.mkdir(exist_ok=True)
    original=local/'StarGate/.env'
    def fingerprint():
        return hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None
    action=sys.argv[1]
    environment={k:v for k,v in os.environ.items() if not k.upper().startswith(('STARGATE_','PYTHON')) and k!='QT_QPA_PLATFORM'}
    system=Path(os.environ['SystemRoot'])
    environment['PATH']=str(system/'System32')+';'+str(system)
    if action=='inventory':
        import base64
        code="Get-CimInstance Win32_PnPEntity | Where-Object {$_.PNPClass -in @('Camera','Image')} | Select-Object Name,Status | ConvertTo-Json"
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',
            base64.b64encode(code.encode('utf-16-le')).decode('ascii')],capture_output=True,text=True,check=True)
        data=json.loads(result.stdout)
        (evidence/'camera-inventory.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps(data),flush=True)
    elif action=='install':
        before=fingerprint()
        installer=BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
        expected=json.loads((SHARE/'docs/testing/evidence/automatic-windows-20261028/artifact.json').read_text())
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
        return subprocess.call([str(installed/'StarGateCameraUAT.exe')],cwd=root,env=environment)
    elif action=='export':
        output=SHARE/'docs/testing/evidence/parallels-interactive-20261028'
        assert output.is_dir(),'Create the evidence folder on macOS before transfer'
        for name in ('install.json','setup.json','schema.json','school.json','camera-inventory.json','cameras.json','search-scale.json'):
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

"""Run only under the isolated SGAuto28 standard Windows test profile."""
import ctypes
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

BUILD=Path('C:/StarGate-build')


def main():
    if getpass.getuser().lower()!='sgauto28' or ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError('Only the isolated standard UAT profile is permitted')
    local=Path(os.environ['LOCALAPPDATA'])
    if 'sgauto28' not in str(local).lower():raise RuntimeError('Unexpected profile environment')
    evidence=local/'StarGate-UAT28';evidence.mkdir(exist_ok=True)
    root=local/'StarGate'
    installed=local/'Programs/StarGate'
    phase=sys.argv[1]
    installer=BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
    environment={key:value for key,value in os.environ.items() if not key.upper().startswith(('STARGATE_','PYTHON'))}
    system=Path(os.environ['SystemRoot'])
    environment.update(PATH=str(system/'System32')+';'+str(system),QT_QPA_PLATFORM='offscreen')
    def run(executable,arguments,name,timeout=900):
        with (evidence/(name+'.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run([str(executable),*arguments],cwd=evidence,env=environment,
                stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if result.returncode:raise RuntimeError(name+' failed with exit '+str(result.returncode))
    if phase in {'install','repair','reinstall'}:
        fresh=not (root/'.env').exists()
        before=(root/'.env').read_bytes() if not fresh else None
        run(installer,['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',
            '/LOG='+str(evidence/(phase+'-inno.log'))],phase)
        assert (root/'.env').is_file() and (root/'.local/managed-postgres/state.json').is_file()
        if before is not None:assert (root/'.env').read_bytes()==before
        run(installed/'StarGateAdmin.exe',['check'],phase+'-database-check')
        result={'phase':phase,'standard_user':True,'fresh_configuration':fresh,
            'automatic_database_created':True,'existing_config_preserved':before is None or (root/'.env').read_bytes()==before}
    elif phase=='diagnose':
        run(installed/'StarGateAdmin.exe',['setup-local'],'diagnose-setup')
        run(installed/'StarGateAdmin.exe',['check'],'diagnose-check')
        result={'phase':phase,'setup_and_check':True}
    elif phase=='fresh-probe':
        fresh_root=evidence/'fresh-admin-data'
        assert not fresh_root.exists()
        run(installed/'StarGateAdmin.exe',['setup-local','--data-dir',str(fresh_root)],'fresh-setup')
        run(installed/'StarGateAdmin.exe',['check','--data-dir',str(fresh_root)],'fresh-check')
        run(installed/'StarGateAdmin.exe',['stop-local-db','--data-dir',str(fresh_root)],'fresh-stop')
        result={'phase':phase,'fresh_setup_and_check':True}
    elif phase=='probe':
        for name,args in (('runtime',['setup-check']),('models',['package-check','--verify-models']),('repeat',['setup-local'])):
            run(installed/'StarGateAdmin.exe',args,'probe-'+name)
        assert (installed/'StarGateAutoUAT.exe').is_file()
        run(installed/'StarGateAutoUAT.exe',['initialize'],'frozen-gui')
        run(installed/'StarGateAutoUAT.exe',['resume'],'frozen-resume')
        result={'phase':phase,'system_path_only':True,'runtime_model_database_checks':True}
    elif phase=='uninstall':
        before=(root/'.env').read_bytes()
        run(installed/'unins000.exe',['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',
            '/LOG='+str(evidence/'uninstall-inno.log')],'uninstall')
        assert (root/'.env').read_bytes()==before and (root/'.local/managed-postgres/data/PG_VERSION').is_file()
        assert not (root/'.local/managed-postgres/data/postmaster.pid').exists()
        result={'phase':phase,'data_and_config_preserved':True,'owned_database_stopped':True}
    elif phase=='inspect':
        run(installed/'StarGateAutoUAT.exe',['inspect'],'frozen-inspect')
        result={'phase':phase,'installed_data_inspected':True}
    elif phase=='archive-first':
        assert not (installed/'StarGate.exe').exists()
        archived=evidence/'first-attempt-data'
        assert root.is_dir() and not archived.exists()
        assert (root/'.local/managed-postgres/state.json').is_file()
        root.rename(archived)
        result={'phase':phase,'first_attempt_data_preserved':True,'default_data_root_absent':not root.exists()}
    elif phase=='stop':
        run(installed/'StarGateAdmin.exe',['stop-local-db'],'final-stop')
        result={'phase':phase,'owned_database_stopped':True}
    else:raise ValueError('Unknown phase')
    (evidence/(phase+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        local=Path(os.environ.get('LOCALAPPDATA','C:/StarGate-build/automatic-evidence-20261028'))
        destination=local/'StarGate-UAT28';destination.mkdir(parents=True,exist_ok=True)
        (destination/'failure.log').write_text(traceback.format_exc(),encoding='utf-8')
        raise

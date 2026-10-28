"""Bounded Windows UAT account; native logon keeps passwords out of argv."""
import base64
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

BUILD=Path('C:/StarGate-build')
NAME='SGAuto28'
DESCRIPTION='StarGate automatic setup UAT 20261028'
TASK='StarGateAutoSetup20261028'


def run_as_user(password,phase):
    api=c.WinDLL('advapi32',use_last_error=True)
    kernel=c.WinDLL('kernel32',use_last_error=True)
    userenv=c.WinDLL('userenv',use_last_error=True)
    class Luid(c.Structure):_fields_=[('low',w.DWORD),('high',w.LONG)]
    class Privilege(c.Structure):_fields_=[('count',w.DWORD),('luid',Luid),('attributes',w.DWORD)]
    class Profile(c.Structure):
        _fields_=[('size',w.DWORD),('flags',w.DWORD),('username',w.LPWSTR),('path',w.LPWSTR),
            ('default_path',w.LPWSTR),('server',w.LPWSTR),('policy',w.LPWSTR),('handle',w.HANDLE)]
    class Startup(c.Structure):
        _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),
            ('x',w.DWORD),('y',w.DWORD),('cx',w.DWORD),('cy',w.DWORD),('xc',w.DWORD),('yc',w.DWORD),
            ('fill',w.DWORD),('flags',w.DWORD),('show',w.WORD),('reserved_size',w.WORD),
            ('reserved_bytes',c.POINTER(w.BYTE)),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
    class Process(c.Structure):
        _fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
    kernel.GetCurrentProcess.restype=w.HANDLE
    kernel.CloseHandle.argtypes=[w.HANDLE]
    kernel.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
    kernel.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
    api.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,c.POINTER(w.HANDLE)]
    api.LookupPrivilegeValueW.argtypes=[w.LPCWSTR,w.LPCWSTR,c.POINTER(Luid)]
    api.AdjustTokenPrivileges.argtypes=[w.HANDLE,w.BOOL,c.POINTER(Privilege),w.DWORD,c.c_void_p,c.c_void_p]
    api.LogonUserW.argtypes=[w.LPCWSTR,w.LPCWSTR,w.LPCWSTR,w.DWORD,w.DWORD,c.POINTER(w.HANDLE)]
    api.CreateProcessAsUserW.argtypes=[w.HANDLE,w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,
        w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(Startup),c.POINTER(Process)]
    userenv.LoadUserProfileW.argtypes=[w.HANDLE,c.POINTER(Profile)]
    userenv.UnloadUserProfile.argtypes=[w.HANDLE,w.HANDLE]
    userenv.CreateEnvironmentBlock.argtypes=[c.POINTER(c.c_void_p),w.HANDLE,w.BOOL]
    userenv.DestroyEnvironmentBlock.argtypes=[c.c_void_p]
    def checked(result):
        if not result:raise c.WinError(c.get_last_error())
    current=w.HANDLE()
    checked(api.OpenProcessToken(kernel.GetCurrentProcess(),0x28,c.byref(current)))
    try:
        for name in ('SeBackupPrivilege','SeRestorePrivilege'):
            privilege=Privilege();privilege.count=1;privilege.attributes=2
            checked(api.LookupPrivilegeValueW(None,name,c.byref(privilege.luid)))
            checked(api.AdjustTokenPrivileges(current,False,c.byref(privilege),0,None,None))
            if c.get_last_error():raise c.WinError(c.get_last_error())
    finally:kernel.CloseHandle(current)
    token=w.HANDLE();environment=c.c_void_p();profile=Profile();process=Process()
    profile.size=c.sizeof(Profile);profile.flags=1;profile.username=NAME
    checked(api.LogonUserW(NAME,'.',password,2,0,c.byref(token)))
    try:
        checked(userenv.LoadUserProfileW(token,c.byref(profile)))
        checked(userenv.CreateEnvironmentBlock(c.byref(environment),token,False))
        startup=Startup();startup.cb=c.sizeof(Startup);startup.desktop=''
        executable=BUILD/'.venv-win/Scripts/python.exe'
        command=c.create_unicode_buffer(subprocess.list2cmdline([str(executable),
            str(BUILD/'scripts/testing/windows_auto_profile.py'),phase]))
        checked(api.CreateProcessAsUserW(token,str(executable),command,None,None,False,
            0x08000400,environment,str(BUILD),c.byref(startup),c.byref(process)))
        if kernel.WaitForSingleObject(process.process,1800000)!=0:raise RuntimeError('Owned UAT process timeout')
        status=w.DWORD();checked(kernel.GetExitCodeProcess(process.process,c.byref(status)))
        print(json.dumps({'phase':phase,'native_user_launch':True,'exit':status.value}),flush=True)
        if status.value:raise RuntimeError('UAT child failed with exit '+str(status.value))
    finally:
        if process.thread:kernel.CloseHandle(process.thread)
        if process.process:kernel.CloseHandle(process.process)
        if environment:userenv.DestroyEnvironmentBlock(environment)
        if profile.handle:userenv.UnloadUserProfile(token,profile.handle)
        kernel.CloseHandle(token)


def powershell(code,environment):
    encoded=base64.b64encode(code.encode('utf-16-le')).decode('ascii')
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],env=environment)
    if result.returncode:raise RuntimeError('UAT runner failed with exit '+str(result.returncode))


def main():
    if os.name!='nt' or not c.windll.shell32.IsUserAnAdmin():raise RuntimeError('UAT administrator context required')
    sys.path.insert(0,str(BUILD))
    from app.services.local_database import private_directory,write_new,checked_path
    folder=private_directory(BUILD/'.local/automatic-account-20261028')
    file=folder/'account.json'
    api=c.WinDLL('netapi32',use_last_error=True)
    class Info(c.Structure):
        _fields_=[('name',w.LPWSTR),('password',w.LPWSTR),('password_age',w.DWORD),
            ('privilege',w.DWORD),('home',w.LPWSTR),('comment',w.LPWSTR),('flags',w.DWORD),('script',w.LPWSTR)]
    api.NetUserAdd.argtypes=[w.LPCWSTR,w.DWORD,c.c_void_p,c.POINTER(w.DWORD)]
    api.NetUserGetInfo.argtypes=[w.LPCWSTR,w.LPCWSTR,w.DWORD,c.POINTER(c.c_void_p)]
    api.NetUserSetInfo.argtypes=[w.LPCWSTR,w.LPCWSTR,w.DWORD,c.c_void_p,c.POINTER(w.DWORD)]
    api.NetApiBufferFree.argtypes=[c.c_void_p]
    if not file.exists():
        existing=c.c_void_p()
        result=api.NetUserGetInfo(None,NAME,1,c.byref(existing))
        if result==0:
            api.NetApiBufferFree(existing)
            raise RuntimeError('Refusing an account without this UAT ownership marker')
        if result!=2221:raise RuntimeError('Unable to inspect UAT account')
        write_new(file,json.dumps({'name':NAME,'password':secrets.token_urlsafe(24)+'aA1!'}))
    credentials=json.loads(checked_path(file).read_text())
    if credentials['name']!=NAME:raise RuntimeError('Unexpected UAT marker')
    parameter=w.DWORD()
    info=Info(NAME,credentials['password'],0,1,None,DESCRIPTION,0x200,None)
    result=api.NetUserAdd(None,1,c.byref(info),c.byref(parameter))
    if result not in (0,2224):raise RuntimeError('Unable to create bounded UAT account')
    existing=c.c_void_p()
    if api.NetUserGetInfo(None,NAME,1,c.byref(existing))!=0:raise RuntimeError('Unable to validate UAT account')
    try:
        if c.cast(existing,c.POINTER(Info)).contents.comment!=DESCRIPTION:raise RuntimeError('Unexpected UAT account owner')
    finally:api.NetApiBufferFree(existing)
    action=sys.argv[1] if len(sys.argv)>1 else 'ensure'
    if action=='ensure':
        print(json.dumps({'account':NAME,'standard_user':True,'password_printed':False}))
        return 0
    if action=='lifecycle':
        import shutil
        for phase in ('inspect','uninstall','reinstall','inspect','stop'):
            run_as_user(credentials['password'],phase)
            if phase=='reinstall':
                installed=Path('C:/Users/SGAuto28/AppData/Local/Programs/StarGate')
                assert (installed/'StarGate.exe').is_file()
                shutil.copyfile(BUILD/'build/StarGateAutoUAT/StarGateAutoUAT.exe',installed/'StarGateAutoUAT.exe')
        print(json.dumps({'lifecycle':'PASS','account':NAME}),flush=True)
        return 0
    environment=dict(os.environ,SG_AUTOUAT_TASK=TASK)
    if action=='cleanup':
        powershell('''$ErrorActionPreference='Stop'
$s=New-Object -ComObject Schedule.Service; $s.Connect();
$folder=$s.GetFolder('\\')
foreach($task in $folder.GetTasks(1)) {
 if($task.Name -eq $env:SG_AUTOUAT_TASK) {
  if($task.Definition.RegistrationInfo.Description -ne 'StarGate automatic setup UAT 20261028'){throw 'Unexpected task owner'}
  $folder.DeleteTask($env:SG_AUTOUAT_TASK,0)
 }
}
foreach($task in $folder.GetTasks(1)){if($task.Name -eq $env:SG_AUTOUAT_TASK){throw 'UAT task was not removed'}}
''',environment)
        flags=w.DWORD(0x202)
        if api.NetUserSetInfo(None,NAME,1008,c.byref(flags),c.byref(parameter))!=0:raise RuntimeError('Unable to disable UAT account')
        print(json.dumps({'account_disabled':True,'on_demand_task_removed':True}))
        return 0
    if action!='run' or len(sys.argv)!=3:raise ValueError('Use ensure, run PHASE, or cleanup')
    phase=sys.argv[2]
    if phase not in {'install','diagnose','fresh-probe','probe','repair','uninstall','reinstall','inspect','stop','archive-first'}:raise ValueError('Unknown UAT phase')
    run_as_user(credentials['password'],phase)
    return 0



if __name__=='__main__':raise SystemExit(main())

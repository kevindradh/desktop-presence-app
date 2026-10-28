"""Build evidence and install checks for the Windows branding update."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

BUILD = Path('C:/StarGate-build')
SHARE = Path('C:/Mac/Home/Downloads/dekstop_face_recognition')
VERSION = '0.14.3'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def embedded_icon(path, output):
    from PIL import Image
    import numpy as np
    from PyInstaller.compat import win32api
    handle = win32api.LoadLibraryEx(str(path), 0, 2)
    try:
        group = win32api.EnumResourceNames(handle, 14)[0]
        data = win32api.LoadResource(handle, 14, group)
        reserved, kind, count = struct.unpack_from('<HHH', data)
        assert reserved == 0 and kind == 1 and 0 < count < 256
        entries, images = [], []
        offset = 6 + count * 16
        for index in range(count):
            fields = struct.unpack_from('<BBBBHHIH', data, 6 + index * 14)
            content = win32api.LoadResource(handle, 3, fields[-1])
            assert len(content) == fields[-2]
            entries.append(struct.pack('<BBBBHHII', *fields[:-1], offset))
            images.append(content)
            offset += len(content)
        ico = struct.pack('<HHH', 0, 1, count) + b''.join(entries + images)
    finally:
        win32api.FreeLibrary(handle)
    with Image.open(io.BytesIO(ico)) as icon, Image.open(SHARE/'resources/branding/stargate.ico') as source:
        common = icon.ico.sizes() & source.ico.sizes()
        assert common
        size = max(common)
        pixels = icon.ico.getimage(size).convert('RGBA')
        expected = source.ico.getimage(size).convert('RGBA')
        assert pixels.tobytes() == expected.tobytes(), 'Embedded icon differs from approved asset'
        rgba = np.asarray(pixels)
        opaque = rgba[:,:,3] > 245
        white = int(np.count_nonzero(np.all(rgba[:,:,:3] > 245,axis=2) & opaque))
        green = int(np.count_nonzero((rgba[:,:,1] > rgba[:,:,0]) & (rgba[:,:,1] > rgba[:,:,2]) & opaque))
        assert white > size[0] * size[1] * .2 and green > 0
        pixels.save(output)
        return {'resource_group':str(group), 'sizes':sorted(common), 'checked_size':size,
                'white_pixels':white, 'green_pixels':green, 'pixels_match_approved_icon':True}


def main():
    import ctypes
    if sys.platform != 'win32' or ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError('Use the logged-in standard Windows account')
    action = sys.argv[1]
    local = Path(os.environ['LOCALAPPDATA'])
    installed = local/'Programs/StarGate'
    root = local/'StarGate-Parallels-0141'
    assert (root/'.local/managed-postgres/state.json').is_file()
    evidence = BUILD/'logo-evidence-0143'
    evidence.mkdir(exist_ok=True)
    exported = SHARE/'docs/testing/evidence/windows-logo-0.14.3'
    assert exported.is_dir(), 'Create evidence directory on macOS first'
    system = Path(os.environ['SystemRoot'])
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith(('STARGATE_','PYTHON')) and k != 'QT_QPA_PLATFORM'}
    env['PATH'] = str(system/'System32') + ';' + str(system)

    def save(name, value):
        (evidence/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')

    def admin(*arguments):
        result = subprocess.run([str(installed/'StarGateAdmin.exe'), *arguments, '--data-dir', str(root)],
                                env=env, capture_output=True, text=True, encoding='utf-8', timeout=240)
        assert result.returncode == 0, (arguments[0], result.returncode)
        return json.JSONDecoder().raw_decode(result.stdout.lstrip())[0]

    def snapshot():
        sys.path.insert(0, str(BUILD))
        from sqlalchemy import text
        from app.services.database import create_database_engine
        from database.runtime import connection_config
        config = connection_config('dev', root=root)
        assert config.host in {'localhost','127.0.0.1','::1'} and config.name == 'stargate_local'
        engine = create_database_engine(config)
        try:
            with engine.connect() as connection:
                counts = {name:connection.scalar(text('SELECT count(*) FROM '+name))
                          for name in ('members','users','attendance','face_embeddings')}
                revision = connection.scalar(text('SELECT version_num FROM alembic_version'))
        finally:
            engine.dispose()
        configs = {name:digest(path) if path.exists() else None for name,path in
                   (('default',local/'StarGate/.env'),('test_space',root/'.env'))}
        return {'counts':counts,'revision':revision,'config_sha256':configs}

    def cleanup_probe():
        import stat
        import time
        helper = installed/'StarGateBrandCheck.exe'
        was_readonly = bool(helper.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY) if helper.exists() else False
        for attempt in range(20):
            try:
                if helper.exists():
                    helper.chmod(stat.S_IREAD | stat.S_IWRITE)
                    helper.unlink()
                result = {'qa_helper_removed':True,'initial_readonly':was_readonly,'attempts':attempt+1}
                save('cleanup.json',result)
                return result
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(.25)

    if action == 'cleanup':
        print(json.dumps(cleanup_probe()),flush=True)
    elif action == 'before':
        save('before-setup.json', admin('setup-local'))
        save('data-before.json', snapshot())
        print('Pre-update database counts and configuration fingerprints recorded', flush=True)
    elif action == 'stop':
        save('stop.json', admin('stop-local-db'))
        print('Owned test database stopped', flush=True)
    elif action == 'build-icon':
        result = embedded_icon(BUILD/'build/StarGate/StarGate.exe', evidence/'build-icon.png')
        save('build-icon.json',result)
        print(json.dumps(result),flush=True)
    elif action == 'artifact':
        for name in ('packaging/windows/StarGate.iss','packaging/StarGate.spec','scripts/build_package.py',
                     'app/bootstrap.py','app/ui/branding.py','app/ui/main_window.py',
                     'app/ui/session_window.py','app/ui/theme.py','app/services/package_probe.py',
                     'resources/branding/stargate.png','resources/branding/stargate-app.png',
                     'resources/branding/stargate.ico','resources/branding/stargate.icns'):
            assert (BUILD/name).read_bytes() == (SHARE/name).read_bytes(), name
        assert '#define AppVersion "'+VERSION+'-research"' in (BUILD/'packaging/windows/StarGate.iss').read_text()
        installer = BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
        code = "$p='C:\\StarGate-build\\dist\\installer\\StarGate-Research-Windows-x64.exe'; $v=(Get-Item $p).VersionInfo; [PSCustomObject]@{FileVersion=$v.FileVersion; ProductVersion=$v.ProductVersion; Signature=(Get-AuthenticodeSignature $p).Status} | ConvertTo-Json"
        result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',
                                 base64.b64encode(code.encode('utf-16-le')).decode('ascii')],
                                capture_output=True,text=True,check=True)
        native = json.loads(result.stdout)
        assert native['FileVersion'].startswith(VERSION+'.'), native
        icons = {'application':embedded_icon(BUILD/'dist/StarGate/StarGate.exe', evidence/'application-icon.png'),
                 'installer':embedded_icon(installer, evidence/'installer-icon.png')}
        target = SHARE/('dist/windows/StarGate-Research-Windows-x64-'+VERSION+'.exe')
        with installer.open('rb') as source, target.open('xb') as destination:
            shutil.copyfileobj(source,destination)
        assert digest(target) == digest(installer)
        manifest = BUILD/'dist/StarGate/build-manifest.json'
        shutil.copyfile(manifest, exported/'build-manifest.json')
        metadata = {'version':VERSION+'-research', 'artifact':target.relative_to(SHARE).as_posix(),
                    'bytes':installer.stat().st_size,'sha256':digest(installer),
                    'application_source_commit':'bac91ef',
                    'environment':'Windows 11 ARM64 Parallels running x64 package',
                    'physical_amd_tested':False, 'native_file_version':native['FileVersion'],
                    'native_product_version':native['ProductVersion'],
                    'authenticode':'NotSigned' if native['Signature']==2 else str(native['Signature']),
                    'bundle_manifest_sha256':digest(manifest),
                    'bundle_file_count':len(json.loads(manifest.read_text())['files']),
                    'approved_icon_sha256':digest(SHARE/'resources/branding/stargate.ico'),
                    'embedded_icons':icons}
        save('artifact.json',metadata)
        (exported/'artifact.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps(metadata),flush=True)
    elif action == 'install':
        before = json.loads((evidence/'data-before.json').read_text())
        current = {name:digest(path) if path.exists() else None for name,path in
                   (('default',local/'StarGate/.env'),('test_space',root/'.env'))}
        assert before['config_sha256'] == current
        listing = subprocess.run(['tasklist','/FI','IMAGENAME eq StarGate.exe','/FO','CSV','/NH'],
                                 capture_output=True,text=True,check=True)
        assert '"stargate.exe"' not in listing.stdout.lower(), 'Close StarGate before updating'
        installer = BUILD/'dist/installer/StarGate-Research-Windows-x64.exe'
        metadata = json.loads((evidence/'artifact.json').read_text())
        assert digest(installer) == metadata['sha256']
        result = subprocess.run([str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',
                                 '/LOG='+str(evidence/'install.log')],env=env,timeout=900)
        assert result.returncode == 0, result.returncode
        save('install.json',{'installer_sha256':metadata['sha256'],'standard_user':True,'exit_code':result.returncode})
        print('Installer update completed on the standard account',flush=True)
    elif action == 'verify':
        save('setup.json',admin('setup-local'))
        save('schema.json',admin('check'))
        after = snapshot()
        before = json.loads((evidence/'data-before.json').read_text())
        assert before == after, 'Database counts/revision or configuration changed'
        save('data-after.json',dict(after,counts_and_config_unchanged=True,
                                    scope='Counts of four tables, schema revision and config fingerprints; no full row diff'))
        save('package-check.json',admin('package-check','--verify-models'))
        manifest = json.loads((BUILD/'dist/StarGate/build-manifest.json').read_text())
        for name in ('StarGate.exe','StarGateAdmin.exe','_internal/resources/branding/stargate.ico',
                     '_internal/resources/branding/stargate.png','_internal/resources/branding/stargate-app.png'):
            assert digest(installed/name) == manifest['files'][name],name
        result = embedded_icon(installed/'StarGate.exe', evidence/'installed-icon.png')
        save('installed-icon.json',dict(result,installed_bytes_match_build=True))
        print('Installed icon, models, schema, counts and configuration: PASS',flush=True)
    elif action == 'ui-probe':
        payload = BUILD/'scripts/testing/windows_branding_probe.py'
        shutil.copyfile(SHARE/'scripts/testing/windows_branding_probe.py',payload)
        spec = evidence/'StarGateBrandCheck.spec'
        spec.write_text("""from pathlib import Path
from PyInstaller.utils.misc import load_py_data_struct
from PyInstaller.building.api import EXE
root=Path(r'C:\\StarGate-build')
state=load_py_data_struct(root/'build/StarGate/EXE-00.toc')
index=[item[0] for item in EXE._GUTS].index('toc')
toc=[entry for entry in state[index] if entry[0] not in {'main','admin_entry'}]
toc.append(('windows_branding_probe',str(root/'scripts/testing/windows_branding_probe.py'),'PYSOURCE'))
exe=EXE(toc,exclude_binaries=True,name='StarGateBrandCheck',console=True,debug=False,upx=False)
""",encoding='utf-8')
        helper = installed/'StarGateBrandCheck.exe'
        try:
            with (evidence/'ui-probe-build.log').open('w',encoding='utf-8') as log:
                result = subprocess.run([str(BUILD/'.venv-win/Scripts/python.exe'),'-m','PyInstaller',
                                         '--noconfirm',str(spec)],cwd=BUILD,stdout=log,stderr=subprocess.STDOUT)
            assert result.returncode == 0
            shutil.copyfile(BUILD/'build/StarGateBrandCheck/StarGateBrandCheck.exe',helper)
            result = subprocess.run([str(helper)],cwd=root,env=env,capture_output=True,text=True,
                                    encoding='utf-8',timeout=90)
            assert result.returncode == 0,result.returncode
            print(result.stdout,flush=True)
        finally:
            cleanup_probe()
    elif action == 'launch':
        process = subprocess.Popen([str(installed/'StarGate.exe'),'--data-dir',str(root)],cwd=root,env=env,
                                   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        import time
        time.sleep(5)
        assert process.poll() is None,'Application exited during startup'
        save('launch.json',{'launched':True,'pid':process.pid,'running_after_seconds':5,
                            'data_directory':str(root),'manual_login_uat':'not claimed'})
        print('Updated application opened using the existing isolated test space',flush=True)
    elif action == 'export':
        for path in evidence.iterdir():
            if path.suffix in {'.json','.png'}:
                shutil.copyfile(path,exported/path.name)
        for name in ('build.log','installer.log'):
            path = BUILD/'automatic-evidence-20261028'/name
            (exported/(name+'.tail.txt')).write_text('\n'.join(path.read_text(encoding='utf-8',errors='replace').splitlines()[-35:])+'\n',encoding='utf-8',newline='\n')
        path = evidence/'install.log'
        (exported/'install-tail.txt').write_text('\n'.join(path.read_text(encoding='utf-8',errors='replace').splitlines()[-38:])+'\n',encoding='utf-8',newline='\n')
        print('Non-biometric build and installation evidence exported',flush=True)
    else:
        raise ValueError('Use before, stop, build-icon, artifact, install, verify, ui-probe, cleanup, launch or export')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

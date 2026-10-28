# Run via scripts/build_package.py, on the target operating system.
from pathlib import Path
import os
import importlib.metadata as metadata
import re
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root=Path(SPECPATH).parent
common=[(str(root/'models/manifest.json'),'models'),
        (str(root/'resources/branding/stargate.png'),'resources/branding'),
        (str(root/'resources/branding/stargate-app.png'),'resources/branding'),
        (str(root/'resources/branding/stargate.ico'),'resources/branding'),
        (str(root/'resources/branding/stargate.icns'),'resources/branding'),
        (str(root/'resources/sounds/success.wav'),'resources/sounds'),
        (str(root/'resources/samples/profile-removed.svg'),'resources/samples'),
        (str(root/'third_party/minifasnet/MiniFASNet.py'),'third_party/minifasnet'),
        (str(root/'third_party/minifasnet/LICENSE'),'third_party/minifasnet'),
        (str(root/'packaging/THIRD_PARTY_NOTICES.md'),'.'),
        (str(root/'alembic.ini'),'.')]
for file in (root/'database/migrations').rglob('*.py'):
    if '__pycache__' not in file.parts:common.append((str(file),str(file.parent.relative_to(root))))
for package in ('reportlab','tzdata'):
    common+=collect_data_files(package)
for package in ('insightface','keyring','cryptography','SQLAlchemy','alembic','PyQt6'):
    common+=copy_metadata(package)
# Retain the licenses shipped by installed wheels, including Qt's license directory.
for distribution in metadata.distributions():
    name=re.sub(r'[^A-Za-z0-9_.-]','_',distribution.metadata['Name'])
    for relative in distribution.files or ():
        if not any(word in str(relative).lower() for word in ('license','copying','copyright','notice')):continue
        file=Path(distribution.locate_file(relative))
        if file.is_file():
            # Keep each original relative path; do not flatten names from different licenses.
            safe=[part for part in Path(relative).parts if part not in ('.','..')]
            common.append((str(file),str(Path('licenses')/name/Path(*safe).parent)))
for name in ('LICENSE','LICENSE.txt'):
    file=Path(sys.base_prefix)/name
    if file.is_file():common.append((str(file),'licenses/Python'))
if os.environ.get('STARGATE_BUILD_RESEARCH_MODELS')=='1':
    for name in ('Widerface-RetinaFace.caffemodel','deploy.prototxt','2.7_80x80_MiniFASNetV2.pth','w600k_r50.onnx','2d106det.onnx'):
        common.append((str(root/'resources/models'/name),'resources/models'))
hidden=(collect_submodules('insightface.model_zoo')+collect_submodules('keyring.backends')+collect_submodules('tzdata')+
        ['PyQt6.QtSvg','ai.attendance_process','ai.enrollment_process','ai.process','app.services.camera_capture',
         'third_party.minifasnet.MiniFASNet','psycopg_binary','sqlalchemy.dialects.postgresql.psycopg'])
# Excluding other Qt bindings avoids accidental PySide6 loading through optional dependencies.
excluded=['PySide6','PySide2','PyQt5','tkinter','pytest','IPython','jupyter','matplotlib.tests']
a=Analysis([str(root/'main.py'),str(root/'packaging/admin_entry.py')],pathex=[str(root)],binaries=[],datas=common,hiddenimports=hidden,
           hookspath=[],runtime_hooks=[],excludes=excluded,noarchive=False)
pyz=PYZ(a.pure)
assert {'main','admin_entry'} <= {entry[0] for entry in a.scripts}
# Keep all runtime hooks, but execute only the entry point belonging to this EXE.
gui_scripts=[entry for entry in a.scripts if entry[0]!='admin_entry']
admin_scripts=[entry for entry in a.scripts if entry[0]!='main']
gui=EXE(pyz,gui_scripts,[],exclude_binaries=True,name='StarGate',console=False,debug=False,upx=False,
        icon=str(root/'resources/branding/stargate.ico'))
admin=EXE(pyz,admin_scripts,[],exclude_binaries=True,name='StarGateAdmin',console=True,debug=False,upx=False)
collection=COLLECT(gui,admin,a.binaries,a.datas,strip=False,upx=False,name='StarGate')
if sys.platform == 'darwin':
    app=BUNDLE(collection, name='StarGate.app',
        icon=str(root/'resources/branding/stargate.icns'),
        bundle_identifier='org.stargate.attendance', version='0.14.3',
        info_plist={
            'CFBundleDisplayName': 'StarGate',
            # COLLECT also contains the console admin helper; the app itself is foreground GUI.
            'LSBackgroundOnly': False,
            'LSUIElement': False,
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': True,
            'NSCameraUsageDescription': 'StarGate menggunakan kamera untuk registrasi wajah dan absensi.',
        })

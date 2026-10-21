"""Packaging preparation contracts; no assertion that an unbuilt Windows installer works."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

import pytest
from app.settings.paths import runtime_paths
from app.settings.config import load_config,ConfigError
from scripts.build_package import validate_build
from scripts.prepare_windows_kit import selected_files,main as prepare

ROOT=Path(__file__).resolve().parents[1]


def test_frozen_windows_writes_user_data_and_reads_bundle(tmp_path):
    bundle=tmp_path/'readonly-bundle';user=tmp_path/'local-app-data';bundle.mkdir()
    layout=runtime_paths(platform='win32',frozen=True,bundle=bundle,environ={'LOCALAPPDATA':str(user)})
    assert layout.resources==bundle and layout.data==user/'StarGate'
    config=load_config(layout.data,environ={},bundle_root=layout.resources)
    assert config.root==user/'StarGate' and config.resource_root==bundle
    assert config.model_dir==bundle/'resources/models'
    assert config.log_dir==user/'StarGate/logs'
    assert config.config_file==user/'StarGate/.env'
    assert not list(bundle.iterdir()) and not user.exists()


def test_source_defaults_and_explicit_private_instance(tmp_path):
    assert runtime_paths(frozen=False).resources==ROOT
    assert runtime_paths(frozen=False).data==ROOT
    layout=runtime_paths(data_dir=tmp_path/'data',frozen=True,bundle=tmp_path/'bundle')
    assert layout.data==tmp_path/'data'
    cfg=load_config(layout.data,environ={'STARGATE_MODEL_DIR':'external-models'},bundle_root=layout.resources)
    assert cfg.model_dir==layout.data/'external-models'
    assert cfg.resource_root!=cfg.root


def test_windows_without_private_home_rejected():
    with pytest.raises(ConfigError):runtime_paths(platform='win32',frozen=True,environ={})


def test_explicit_config_preserved_for_owner_helper(tmp_path,monkeypatch):
    from database.runtime import connection_config
    path=tmp_path/'instance.env';path.write_text('STARGATE_DB_NAME=private_instance\nSTARGATE_DB_USER=app_instance\nSTARGATE_DB_PASSWORD=synthetic-app\nSTARGATE_DB_MIGRATION_USER=owner_instance\nSTARGATE_DB_MIGRATION_PASSWORD=synthetic-owner\n')
    for key in list(__import__('os').environ):
        if key.startswith('STARGATE_'):monkeypatch.delenv(key)
    cfg=load_config(tmp_path,path,environ={})
    actual=connection_config(root=cfg.root,env_file=cfg.config_file,migration=True)
    assert actual.name=='private_instance' and actual.user=='owner_instance'
    assert 'synthetic-owner' not in repr(actual)


def test_cross_compile_and_mixed_architecture_rejected(monkeypatch):
    import scripts.build_package as module
    monkeypatch.setattr(module.platform,'system',lambda:'Darwin')
    with pytest.raises(ValueError,match='OS target'):validate_build('windows',False)
    monkeypatch.setattr(module.platform,'system',lambda:'Windows')
    monkeypatch.setattr(module.sysconfig,'get_platform',lambda:'win-arm64')
    with pytest.raises(ValueError,match='Python Windows x64'):validate_build('windows',False)
    monkeypatch.setattr(module.sysconfig,'get_platform',lambda:'win-amd64')
    validate_build('windows',False)


def test_windows_finalizer_preserves_delvewheel_directory_and_hashes(tmp_path,monkeypatch):
    import scripts.build_package as build
    import PyInstaller.utils.hooks as hooks
    dll=tmp_path/'source'/'dependency.dll';dll.parent.mkdir();dll.write_bytes(b'synthetic-native')
    output=tmp_path/'bundle';output.mkdir();(output/'StarGate.exe').write_bytes(b'synthetic-exe')
    monkeypatch.setattr(build.platform,'system',lambda:'Windows')
    monkeypatch.setattr(hooks,'collect_delvewheel_libs_directory',lambda name:([],[(str(dll),'onnx.libs')]))
    build.finalize_output(output,True)
    destination=output/'_internal/onnx.libs/dependency.dll'
    assert destination.read_bytes()==dll.read_bytes()
    manifest=json.loads((output/'build-manifest.json').read_text())
    assert manifest['files']['_internal/onnx.libs/dependency.dll']==hashlib.sha256(dll.read_bytes()).hexdigest()
    assert 'build-manifest.json' not in manifest['files']
    build.finalize_output(output,True)
    assert json.loads((output/'build-manifest.json').read_text())==manifest
    (output/'.env').write_text('synthetic-private')
    with pytest.raises(ValueError,match='data'):build.finalize_output(output,True)


def test_transfer_kit_actual_files_hashes_and_secret_exclusion(tmp_path):
    files=selected_files(ROOT)
    assert ROOT/'models/manifest.json' in files
    assert ROOT/'pytest.ini' in files
    for name in ('requirements-windows-x64.candidate.txt','requirements-windows-x64.candidate.lock.txt'):
        if (ROOT/name).is_file():assert ROOT/name in files
    assert ROOT/'.env.example' in files and ROOT/'.env' not in files
    assert not any('.local' in p.relative_to(ROOT).parts or '.venv' in p.relative_to(ROOT).parts for p in files)
    assert not any(p.name=='w600k_r50.onnx' for p in files)
    destination=tmp_path/'kit.zip'
    assert prepare(['--output',str(destination)])==0
    with zipfile.ZipFile(destination) as archive:
        manifest=json.loads(archive.read('kit-manifest.json'))
        assert set(archive.namelist())==set(manifest['files'])|{'kit-manifest.json'}
        for name,expected in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==expected
    before=destination.read_bytes()
    assert prepare(['--output',str(destination)])==2 and destination.read_bytes()==before


def test_model_kit_requires_verified_pinned_assets():
    files=selected_files(ROOT,include_models=True)
    assert ROOT/'resources/models/w600k_r50.onnx' in files
    assert ROOT/'resources/models/2d106det.onnx' in files


def test_cli_data_dir_and_error_without_graphics(tmp_path):
    result=subprocess.run([sys.executable,str(ROOT/'main.py'),'--check-config','--data-dir',str(tmp_path)],capture_output=True,text=True,timeout=15)
    assert result.returncode==0 and 'valid' in result.stdout
    (tmp_path/'.env').write_text('STARGATE_DB_PORT=synthetic-secret\n')
    result=subprocess.run([sys.executable,str(ROOT/'main.py'),'--package-check','--data-dir',str(tmp_path)],capture_output=True,text=True,timeout=15)
    assert result.returncode==2 and 'synthetic-secret' not in result.stdout+result.stderr


def test_admin_companion_help_runs_from_source_without_private_config():
    result=subprocess.run([sys.executable,str(ROOT/'packaging/admin_entry.py'),'--help'],capture_output=True,text=True,timeout=15)
    assert result.returncode==0 and 'bootstrap-admin' in result.stdout and '--data-dir' in result.stdout


def test_model_diagnostics_does_not_serialize_exception_messages(monkeypatch):
    import ai.models
    from app.services.package_probe import model_diagnostics
    records=[]
    class Pipe:
        closed=False
        def send(self,value):records.append(value)
        def close(self):self.closed=True
    def fail(*args):raise ValueError('synthetic-private-value')
    monkeypatch.setattr(ai.models,'verified_assets',fail)
    pipe=Pipe();model_diagnostics(ROOT,ROOT/'resources/models',pipe)
    assert pipe.closed and records[0]['step']=='assets' and not records[0]['ok']
    assert records[0]['error_type']=='ValueError' and records[0]['frames']
    assert 'synthetic-private-value' not in json.dumps(records)


@pytest.mark.models
def test_source_package_probe_models_spawn_and_clean_data_directory(tmp_path):
    # This validates source smoke tooling, not a Windows executable or a blocked-network VM.
    import os
    env=dict(os.environ);env['QT_QPA_PLATFORM']='offscreen'
    result=subprocess.run([sys.executable,str(ROOT/'main.py'),'--package-check','--verify-models',
        '--data-dir',str(tmp_path)],capture_output=True,text=True,timeout=90,env=env)
    assert result.returncode==0,result.stdout
    report=json.loads(result.stdout)
    assert report['package_check']=='PASS' and all(report['checks'].values())
    assert report['checks']['spawn'] and report['checks']['pinned_ai_models']
    assert (tmp_path/'logs').is_dir() and not (tmp_path/'.env').exists()

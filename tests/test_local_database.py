import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import local_database as local
from app.settings.config import load_config
from scripts.prepare_postgres_runtime import prepare


def executable():
    value=bytearray(160)
    value[:2]=b'MZ'
    value[60:64]=(128).to_bytes(4,'little')
    value[128:134]=b'PE\0\0\x64\x86'
    return value


@pytest.fixture
def runtime(tmp_path):
    source=tmp_path/'installed'
    for name in ('initdb','pg_ctl','postgres'):
        file=source/'bin'/f'{name}.exe';file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(executable())
    for name,content in (('lib/vector.dll','synthetic'),('share/postgresql.conf.sample','template'),
                         ('share/extension/vector.control',"default_version = '0.8.7'"),
                         ('share/extension/vector--0.8.7.sql','synthetic SQL')):
        file=source/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(content)
    (source/'lib/vector.dll').write_bytes(executable())
    pg_license=tmp_path/'pg-license';pg_license.write_text('Synthetic license fixture')
    vector_license=tmp_path/'vector-license';vector_license.write_text('Synthetic license fixture')
    output=tmp_path/'bundle/postgresql'
    prepare(source,output,pg_license,vector_license)
    return output.parent


@pytest.fixture
def simulated(monkeypatch):
    calls=[];provisions=[];migrations=[];running=[False]
    monkeypatch.setattr(local,'sys',SimpleNamespace(platform='win32'))
    def run(runtime,name,*args):
        calls.append((name,args))
        if name=='initdb':
            data=Path(args[1]);data.mkdir(parents=True)
            (data/'PG_VERSION').write_text('17')
        elif args[-1]=='start':running[0]=True
        elif args[-1]=='stop':running[0]=False
        elif args[-1]=='status':return SimpleNamespace(returncode=0 if running[0] else 3)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(local,'run_tool',run)
    monkeypatch.setattr(local,'provision',lambda state,passwords:provisions.append((state,passwords)))
    monkeypatch.setattr(local,'migrate_and_seed',lambda root:migrations.append(root))
    return SimpleNamespace(calls=calls,provisions=provisions,migrations=migrations,running=running)


def test_new_setup_is_private_idempotent_and_restarts_own_cluster(runtime,tmp_path,simulated):
    root=tmp_path/'customer'
    result=local.setup_local(root,runtime)
    assert result['mode']=='managed_local'
    env=(root/'.env').read_bytes()
    config=load_config(root,environ={},bundle_root=runtime)
    assert config.database.host=='127.0.0.1' and 55435<=config.database.port<=55444
    passwords=simulated.provisions[0][1]
    assert len(set(passwords.values()))==3 and all(len(p)>=32 for p in passwords.values())
    assert not (root/'.local/managed-postgres/init-password').exists()
    serialized=str(simulated.calls)
    assert all(password not in serialized for password in passwords.values())
    assert '--auth=scram-sha-256' in serialized and '-h 127.0.0.1 -p' in serialized
    assert (root/'.env').stat().st_mode & 0o777==0o600
    local.setup_local(root,runtime)
    assert (root/'.env').read_bytes()==env
    assert sum(name=='initdb' for name,args in simulated.calls)==1
    assert len(simulated.migrations)==2
    local.stop_local(root,runtime)
    assert not simulated.running[0] and (root/'.env').read_bytes()==env
    local.ensure_local_database(config)
    assert simulated.running[0]


def test_existing_configuration_is_not_changed_or_started(tmp_path,simulated):
    root=tmp_path/'customer';root.mkdir()
    old='STARGATE_DB_NAME=existing_customer_database\n'
    (root/'.env').write_text(old)
    assert local.setup_local(root,tmp_path/'no-runtime')=={'mode':'existing_configuration','changed':False}
    assert (root/'.env').read_text()==old and not simulated.calls
    local.ensure_local_database(load_config(root,environ={}))
    assert not simulated.calls and not (root/'.local').exists()


def test_setup_resumes_after_migration_failure_without_reset(runtime,tmp_path,simulated,monkeypatch):
    root=tmp_path/'customer'
    def fail(root):raise RuntimeError('synthetic failed migration')
    monkeypatch.setattr(local,'migrate_and_seed',fail)
    with pytest.raises(RuntimeError):local.setup_local(root,runtime)
    env=(root/'.env').read_bytes()
    sentinel=root/'.local/managed-postgres/data/customer-sentinel';sentinel.write_text('keep')
    monkeypatch.setattr(local,'migrate_and_seed',lambda root:None)
    local.setup_local(root,runtime)
    assert sentinel.read_text()=='keep' and (root/'.env').read_bytes()==env
    assert sum(name=='initdb' for name,args in simulated.calls)==1


def test_mismatched_config_and_occupied_start_do_not_provision(runtime,tmp_path,simulated,monkeypatch):
    root=tmp_path/'customer';local.setup_local(root,runtime)
    count=len(simulated.provisions)
    env=root/'.env';env.write_text(env.read_text().replace('stargate_local','customer_other'))
    with pytest.raises(local.LocalSetupError,match='berbeda'):local.setup_local(root,runtime)
    with pytest.raises(local.LocalSetupError,match='berbeda'):
        local.ensure_local_database(load_config(root,environ={},bundle_root=runtime))
    assert len(simulated.provisions)==count


@pytest.mark.parametrize('attack',['hash','traversal','version','missing','symlink','extra'])
def test_runtime_tampering_rejected_before_creating_customer_data(runtime,tmp_path,simulated,attack):
    folder=runtime/'postgresql';file=folder/'runtime-manifest.json'
    manifest=json.loads(file.read_text())
    if attack=='hash':(folder/'bin/pg_ctl.exe').write_bytes(b'changed')
    elif attack=='traversal':manifest['files']['../outside']='123'
    elif attack=='version':manifest['major']=18
    elif attack=='missing':manifest['files'].pop('lib/vector.dll')
    elif attack=='symlink':
        original=folder/'bin/pg_ctl.exe';original.unlink();original.symlink_to(tmp_path/'outside')
    else:(folder/'bin/unexpected.dll').write_bytes(b'unverified')
    file.write_text(json.dumps(manifest))
    root=tmp_path/'customer'
    with pytest.raises(local.LocalSetupError):local.setup_local(root,runtime)
    assert not root.exists() and not simulated.calls


def test_failed_native_open_has_no_raw_output(runtime,monkeypatch):
    import subprocess
    def fail(*args,**kwargs):raise subprocess.TimeoutExpired('synthetic-secret',1,output='synthetic-secret')
    monkeypatch.setattr(local.subprocess,'run',fail)
    with pytest.raises(local.LocalSetupError) as error:
        local.run_tool(runtime/'postgresql','pg_ctl','status')
    assert 'synthetic-secret' not in str(error.value)


def test_non_windows_setup_is_rejected_before_creating_files(tmp_path,monkeypatch):
    monkeypatch.setattr(local,'sys',SimpleNamespace(platform='darwin'))
    with pytest.raises(local.LocalSetupError,match='Windows'):
        local.setup_local(tmp_path/'customer',tmp_path/'bundle')
    assert not (tmp_path/'customer').exists()


def test_failed_start_never_provisions_another_server(runtime,tmp_path,simulated,monkeypatch):
    original=local.run_tool
    def failing(runtime,name,*args):
        if args[-1]=='start':return SimpleNamespace(returncode=1)
        return original(runtime,name,*args)
    monkeypatch.setattr(local,'run_tool',failing)
    root=tmp_path/'customer'
    with pytest.raises(local.LocalSetupError,match='dimulai'):local.setup_local(root,runtime)
    assert not simulated.provisions and not (root/'.env').exists()
    assert not (root/'.local/managed-postgres/init-password').exists()


def test_partial_setup_can_stop_without_env(runtime,tmp_path,simulated):
    root=tmp_path/'customer';local.setup_local(root,runtime)
    (root/'.env').unlink()
    local.stop_local(root,runtime)
    assert not simulated.running[0]


def test_concurrent_setup_rejected_without_mutating_data(tmp_path):
    folder=local.private_directory(tmp_path/'private')
    with local.setup_lock(folder):
        with pytest.raises(local.LocalSetupError,match='lain masih berjalan'):
            with local.setup_lock(folder):pass


def test_postgres_source_output_inside_source_rejected(tmp_path):
    with pytest.raises(ValueError,match='di luar'):
        prepare(tmp_path/'postgres',tmp_path/'postgres/share/output',tmp_path/'license',tmp_path/'license')


def test_native_environment_accepts_uppercase_windows_keys_and_ignores_pg_overrides(tmp_path,monkeypatch):
    monkeypatch.setenv('SYSTEMROOT',r'C:\Windows')
    monkeypatch.setenv('PGHOST','untrusted.example')
    monkeypatch.setenv('PGPASSWORD','synthetic-private')
    monkeypatch.setenv('PATH','untrusted-native-folder')
    environment=local.process_environment(tmp_path/'postgresql',windows=True)
    assert not any(key.upper().startswith('PG') for key in environment)
    assert 'untrusted-native-folder' not in environment['PATH']
    assert r'C:\Windows\System32' in environment['PATH']


@pytest.mark.database
def test_provision_migrations_and_restart_on_isolated_native_postgres(runtime,tmp_path,monkeypatch):
    """Real PostgreSQL on macOS validates SQL/lifecycle, not Windows executables."""
    import subprocess
    from app.services.database import Database,create_database_engine
    from app.services.auth import AuthService
    from database.runtime import schema_status
    prefix=Path('/opt/homebrew/opt/postgresql@17/bin')
    if not (prefix/'initdb').is_file():pytest.skip('PostgreSQL 17 native test tools unavailable')
    monkeypatch.setattr(local,'sys',SimpleNamespace(platform='win32'))
    def native(runtime,name,*args):
        return subprocess.run([str(prefix/name),*map(str,args)],stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90,check=False)
    monkeypatch.setattr(local,'run_tool',native)
    root=tmp_path/'isolated-customer'
    database=None
    try:
        local.setup_local(root,runtime)
        config=load_config(root,environ={},bundle_root=runtime)
        database=Database(create_database_engine(config.database))
        with database.transaction() as session:
            assert schema_status(session.connection())['at_head']
            from sqlalchemy import text
            assert not session.execute(text('SELECT rolsuper FROM pg_roles WHERE rolname=current_user')).scalar_one()
            assert session.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one()=='0.8.7'
        service=AuthService(database)
        assert service.bootstrap_required()
        service.bootstrap('synthetic-root','Synthetic administrator','SyntheticTest2026!')
        original=(root/'.env').read_bytes()
        local.setup_local(root,runtime)
        assert not service.bootstrap_required() and (root/'.env').read_bytes()==original
        database.close();database=None
        local.stop_local(root,runtime)
        local.ensure_local_database(config)
        database=Database(create_database_engine(config.database))
        assert not AuthService(database).bootstrap_required()
    finally:
        if database is not None:database.close()
        if (root/'.local/managed-postgres/data/PG_VERSION').exists():
            native(None,'pg_ctl','-D',root/'.local/managed-postgres/data','-w','-t','15','-m','fast','stop')

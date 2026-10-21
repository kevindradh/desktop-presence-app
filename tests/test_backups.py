from tests.permissions import assert_private_path
"""Encrypted real PostgreSQL recovery: owned test schema only, never development."""
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from threading import Event
import json
import os

import pytest
from sqlalchemy import select, text
from app.models.entities import Base, FaceAngle, FaceEmbedding, Member, Role, User, AuditLog
from app.repositories.core import MemberRepository, EmbeddingRepository, SettingsRepository
from app.services.auth import AuthError
from app.services.backups import BackupService, REMOVED_PHOTO, TABLES
from app.services.backup_codec import unseal, seal, MAGIC
from app.services.database import DataValidationError
from app.services.member_photos import PhotoStore
from app.services.tasks import TaskContext, TaskCancelled
from tests.test_database import store, graph, record
from tests.test_auth import auth, add_role, NEW

pytestmark=pytest.mark.database
PASSWORD='Synthetic-backup-2026!'


@pytest.fixture
def backup(auth,store,tmp_path,qt_app):
    service,login,now=auth
    from PyQt6.QtGui import QImage,QColor
    image=QImage(12,12,QImage.Format.Format_RGB32);image.fill(QColor('#17602f'))
    source=tmp_path/'synthetic.png';assert image.save(str(source))
    photo=PhotoStore(tmp_path).import_photo(source)
    with store.db.transaction() as session:
        group,member,shift,device=graph(session)
        member.photo_path=photo
        for angle in FaceAngle:
            EmbeddingRepository(session).add(FaceEmbedding(member_id=member.id,embedding=[.01]*512,angle=angle,model_version='synthetic-v1'))
        record(session,member,shift,device)
    @contextmanager
    def owner():yield store.migration
    result=BackupService(service,tmp_path,owner=owner)
    return result,login,now,tmp_path


def archive(data,name='copy.sgbackup'):
    service,login,now,root=data;path=root/name
    service.backup(login.token,path,PASSWORD)
    return path


def rows(store):
    from app.services.backup_codec import canonical
    with store.db.transaction() as session:
        return {t.name:json.loads(canonical([dict(r) for r in session.execute(select(t).order_by(t.c.id)).mappings()])) for t in TABLES}


def test_backup_encryption_assets_and_secret_exclusion(backup,store):
    service,login,now,root=backup;path=archive(backup)
    raw=path.read_bytes();assert raw.startswith(MAGIC) and b'Pengelola Uji' not in raw
    assert_private_path(path)
    payload=unseal(path,PASSWORD)
    assert payload['tables']['auth_sessions']==[]
    assert len(payload['tables']['face_embeddings'])==5 and len(payload['photos'])==1
    assert all(r['secret_ref'] is None for r in payload['tables']['devices'])
    assert 'password' not in payload and 'database' not in payload
    info=service.inspect(login.token,path,PASSWORD)
    assert info['embeddings']==5 and info['photos']==1
    assert (root/'synthetic.png').exists()


def test_restore_roundtrip_all_tables_and_approved_biometric_policy(backup,store):
    service,login,now,root=backup;path=archive(backup);payload=unseal(path,PASSWORD)
    with store.db.transaction() as session:
        session.scalar(select(Member)).full_name='Changed after backup'
        SettingsRepository(session).set('duplicate_window',120)
    result=service.restore(login.token,path,PASSWORD,'PULIHKAN')
    recovered=rows(store)
    for table,values in payload['tables'].items():
        if table=='audit_logs':
            assert recovered[table][:-1]==values and recovered[table][-1]['action']=='backup.restored'
        elif table=='members':
            assert recovered[table]==[dict(r,photo_path=REMOVED_PHOTO,revision=r['revision']+1) for r in values]
        elif table=='face_embeddings':assert recovered[table]==[]
        else:assert recovered[table]==values
    assert result['reenrollment_required'] and not result['cleanup_pending']
    safety=unseal(result['safety_backup'],PASSWORD)
    assert safety['tables']['members'][0]['full_name']=='Changed after backup'
    assert len(safety['tables']['face_embeddings'])==5
    assert not list((root/'.local/member_photos').glob('*.png'))
    assert (root/'synthetic.png').exists()
    with pytest.raises(AuthError):service.auth.inspect(login.token)
    fresh=service.auth.login('root',NEW)
    with store.db.transaction() as session:
        created=MemberRepository(session).create('AFTER-RESTORE','New member',recovered['member_groups'][0]['id'],REMOVED_PHOTO)
        assert created.id>max(m['id'] for m in recovered['members'])
    assert service.auth.authorize(fresh.token,'backup')


@pytest.mark.parametrize('damage',['password','corrupt','format','schema','revision','expired','traversal','checksum','missing_table','invalid_setting','sql'])
def test_invalid_backups_never_change_database(backup,store,damage):
    service,login,now,root=backup;path=archive(backup);payload=unseal(path,PASSWORD)
    password=PASSWORD
    if damage=='password':password='Different-password-2026!'
    elif damage=='corrupt':path.write_bytes(path.read_bytes()[:-2]+b'xx')
    elif damage=='format':payload['format']=999
    elif damage=='schema':payload['schema']='unknown'
    elif damage=='revision':payload['revision']='future'
    elif damage=='expired':now[0]+=timedelta(days=7);login=service.auth.login('root',NEW)
    elif damage=='traversal':payload['photos']['../../escape.png']=next(iter(payload['photos'].values()))
    elif damage=='checksum':next(iter(payload['photos'].values()))['sha256']='bad'
    elif damage=='missing_table':del payload['tables']['attendance']
    elif damage=='invalid_setting':payload['tables']['settings'][0]['setting_key']='unknown'
    elif damage=='sql':payload['sql']='DROP SCHEMA public CASCADE'
    if damage not in ('password','corrupt','expired'):path.write_bytes(seal(payload,PASSWORD))
    before=rows(store)
    with pytest.raises(DataValidationError):service.restore(login.token,path,password,'PULIHKAN')
    after=rows(store)
    assert {k:v for k,v in after.items() if k!='audit_logs'}=={k:v for k,v in before.items() if k!='audit_logs'}
    assert after['audit_logs'][:len(before['audit_logs'])]==before['audit_logs']
    assert not (root.parent/'escape.png').exists()


@pytest.mark.parametrize('role',[Role.ADMIN,Role.OPERATOR,Role.VIEWER])
def test_backup_restore_direct_role_denial(backup,role):
    service,login,now,root=backup;_,other=add_role(service.auth,login,role)
    for operation in (lambda:service.backup(other.token,root/'forbidden',PASSWORD),
                      lambda:service.inspect(other.token,root/'absent',PASSWORD),
                      lambda:service.restore(other.token,root/'absent',PASSWORD,'PULIHKAN')):
        with pytest.raises(AuthError):operation()
    assert not (root/'forbidden').exists()


def test_confirmation_file_change_and_revocation(backup,store):
    service,login,now,root=backup;path=archive(backup);info=service.inspect(login.token,path,PASSWORD)
    before=rows(store)
    with pytest.raises(DataValidationError):service.restore(login.token,path,PASSWORD,'yes')
    payload=unseal(path,PASSWORD);payload['tables']['members'][0]['full_name']='Changed archive'
    path.write_bytes(seal(payload,PASSWORD))
    with pytest.raises(DataValidationError):service.restore(login.token,path,PASSWORD,'PULIHKAN',expected_digest=info['sha256'])
    after=rows(store)
    assert {k:v for k,v in after.items() if k!='audit_logs'}=={k:v for k,v in before.items() if k!='audit_logs'}
    assert after['audit_logs'][:len(before['audit_logs'])]==before['audit_logs']
    service.auth.logout(login.token)
    with pytest.raises(AuthError):service.restore(login.token,path,PASSWORD,'PULIHKAN')


@pytest.mark.parametrize('failure',['cancel','constraint','io','owner'])
def test_interrupted_restore_rollback_and_recovery_copy(backup,store,monkeypatch,failure):
    service,login,now,root=backup;path=archive(backup)
    before=rows(store);context=TaskContext(Event(),lambda _:None)
    if failure=='cancel':
        def progress(value):
            if value>=50:context.cancelled.set()
        context=TaskContext(Event(),progress)
    elif failure=='constraint':
        payload=unseal(path,PASSWORD);payload['tables']['attendance'][0]['member_id']=999999
        path.write_bytes(seal(payload,PASSWORD))
    elif failure=='io':
        import app.services.backups as module
        monkeypatch.setattr(module,'publish',lambda *args:(_ for _ in ()).throw(OSError()))
    else:
        @contextmanager
        def owner():yield store.engine
        service.owner=owner
    with pytest.raises((TaskCancelled,DataValidationError)):
        service.restore(login.token,path,PASSWORD,'PULIHKAN',context)
    after=rows(store)
    assert {k:v for k,v in after.items() if k!='audit_logs'}=={k:v for k,v in before.items() if k!='audit_logs'}
    assert after['audit_logs'][:len(before['audit_logs'])]==before['audit_logs']
    assert service.auth.inspect(login.token)
    with store.db.transaction() as session:
        seq=session.execute(text("SELECT nextval(pg_get_serial_sequence('members','id'))")).scalar_one()
        assert seq>max(row['id'] for row in before['members'])
    if failure in ('cancel','constraint'):
        copies=list((root/'.local/backups').glob('*.sgbackup'))
        assert len(copies)==1
        payload=unseal(copies[0],PASSWORD)
        assert payload['tables']['members']==before['members']


def test_cancel_and_no_overwrite_never_publish_partial(backup,store):
    service,login,now,root=backup;path=archive(backup);original=path.read_bytes()
    with pytest.raises(DataValidationError):service.backup(login.token,path,PASSWORD)
    assert path.read_bytes()==original
    context=TaskContext(Event(),lambda _:None);context.cancelled.set()
    with pytest.raises(TaskCancelled):service.backup(login.token,root/'cancelled',PASSWORD,context)
    assert not (root/'cancelled').exists() and not list(root.glob('.stargate-backup-*'))


def crash_during_restore(schema,root,path,token,clock):
    # Spawned process; credentials are loaded locally, never command line arguments.
    from contextlib import contextmanager
    from app.services.auth import AuthService
    from app.services.database import Database,create_database_engine
    from database.runtime import connection_config
    runtime=create_database_engine(connection_config('test'),schema=schema)
    owner_engine=create_database_engine(connection_config('test',migration=True),schema=schema)
    @contextmanager
    def owner():yield owner_engine
    service=BackupService(AuthService(Database(runtime),clock=lambda:clock),root,owner=owner)
    def crash(value):
        if value>=50:os._exit(23)
    service.restore(token,path,PASSWORD,'PULIHKAN',TaskContext(Event(),crash))


def test_process_crash_rolls_back_database_and_keeps_safety_copy(backup,store):
    import multiprocessing
    service,login,now,root=backup;path=archive(backup);before=rows(store)
    process=multiprocessing.get_context('spawn').Process(target=crash_during_restore,
        args=(store.schema,root,path,login.token,now[0]))
    process.start();process.join(20)
    if process.is_alive():process.terminate();process.join(5)
    assert process.exitcode==23
    assert rows(store)==before
    copies=list((root/'.local/backups').glob('*.sgbackup'));assert len(copies)==1
    assert unseal(copies[0],PASSWORD)['tables']['members']==before['members']


def test_maintenance_lock_blocks_concurrent_writer_and_revokes_old_session(backup,store):
    from concurrent.futures import ThreadPoolExecutor
    service,login,now,root=backup;path=archive(backup)
    reached=Event();release=Event()
    def progress(value):
        if value==35:reached.set();assert release.wait(6)
    def write():
        return service.auth._protected(login.token,'members',lambda session,actor:
            session.execute(Member.__table__.update().values(full_name='SHOULD NOT COMMIT')))
    with ThreadPoolExecutor(max_workers=2) as pool:
        restore=pool.submit(service.restore,login.token,path,PASSWORD,'PULIHKAN',TaskContext(Event(),progress))
        assert reached.wait(10)
        writer=pool.submit(write)
        assert not writer.done()
        release.set();assert restore.result(timeout=15)['reenrollment_required']
        with pytest.raises(AuthError):writer.result(timeout=10)
    with store.db.transaction() as session:assert session.scalar(select(Member.full_name))!='SHOULD NOT COMMIT'


def test_safety_retention_removes_only_expired_owned_files(tmp_path):
    import time
    folder=tmp_path/'copies';folder.mkdir()
    old=folder/('a'*32+'.sgbackup');old.write_bytes(b'encrypted')
    fresh=folder/('b'*32+'.sgbackup');fresh.write_bytes(b'encrypted')
    unrelated=folder/'my-export.sgbackup';unrelated.write_bytes(b'keep')
    os.utime(old,(time.time()-8*86400,)*2);os.utime(unrelated,(time.time()-8*86400,)*2)
    BackupService.expire_safety_copies(folder)
    assert not old.exists() and fresh.exists() and unrelated.exists()

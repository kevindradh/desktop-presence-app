from tests.permissions import assert_private_path
import json
from pathlib import Path
import numpy as np
import pytest
from sqlalchemy import select,func
from ai.enrollment import CapturePacket
from app.models.entities import Member,FaceEmbedding,AuditLog,Role,Attendance
from app.services.enrollment import EnrollmentService
from app.services.administration import AdministrationService
from app.services.database import DataValidationError
from app.services.auth import AuthError
from ai.embedding.search import identify
from tests.test_auth import auth,add_role
from tests.test_database import store,graph,record
from tests.test_enrollment_capture import packet,analysis

pytestmark=pytest.mark.database


@pytest.fixture
def enrollment(auth,tmp_path):
    service,login,_=auth
    value=EnrollmentService(service,tmp_path,storage_enabled=True)
    with service.database.transaction() as session:
        group,_,_,_=graph(session)
        group_id=group.id
    return value,login,group_id


def fields(group):return dict(code='ENROLL-1',name='Anggota capture sintetis',group_id=group)


def test_enrollment_atomic_five_samples_photo_restart_search_and_replay(enrollment,store):
    service,login,group=enrollment
    binding=service.begin(login.token)
    payload=packet(service,binding)
    row=service.save(login.token,payload,**fields(group))
    photo=service.photos.root/row.photo
    assert photo.is_file(); assert_private_path(photo)
    with store.db.transaction() as session:
        rows=list(session.scalars(select(FaceEmbedding).where(FaceEmbedding.member_id==row.id)))
        assert len(rows)==5 and len({r.angle for r in rows})==5
        assert identify(session,analysis().embedding,model_version='synthetic-v1').member_id==row.id
        assert session.scalar(select(AuditLog).where(AuditLog.action=='member.enrolled')).details['record_count']==5
    with pytest.raises(DataValidationError):service.save(login.token,payload,**fields(group))
    restarted=EnrollmentService(service.auth,service.photos.root,storage_enabled=True)
    with pytest.raises(DataValidationError):restarted.save(login.token,payload,**fields(group))


def test_reregister_replaces_after_complete_and_preserves_history(enrollment,store):
    service,login,group=enrollment
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    old_photo=service.photos.root/row.photo
    with store.db.transaction() as session:
        m=session.get(Member,row.id)
        from app.models.entities import Shift,Device
        shift=session.scalar(select(Shift));device=session.scalar(select(Device))
        record(session,m,shift,device)
        old_ids=set(session.scalars(select(FaceEmbedding.id).where(FaceEmbedding.member_id==row.id)))
    binding=service.begin(login.token,member_id=row.id,revision=row.revision)
    result=service.save(login.token,packet(service,binding,offset=1),**fields(group),member_id=row.id,revision=row.revision)
    assert result.revision==row.revision+1 and not old_photo.exists()
    with store.db.transaction() as session:
        ids=set(session.scalars(select(FaceEmbedding.id).where(FaceEmbedding.member_id==row.id)))
        assert len(ids)==5 and ids.isdisjoint(old_ids)
        assert session.scalar(select(func.count()).select_from(Attendance).where(Attendance.member_id==row.id))==1
    admin=AdministrationService(service.auth,service.photos.root)
    admin.deactivate_member(login.token,result.id,result.revision)
    assert not (service.photos.root/result.photo).exists()
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.member_id==row.id))==0
        assert session.scalar(select(func.count()).select_from(Attendance).where(Attendance.member_id==row.id))==1


def test_failure_rollback_no_photo_or_half_member(enrollment,store,monkeypatch):
    service,login,group=enrollment
    payload=packet(service,service.begin(login.token))
    from app.repositories.core import EmbeddingRepository
    original=EmbeddingRepository.create
    calls=[0]
    def fail(self,*args,**kwargs):
        calls[0]+=1
        if calls[0]==3:raise DataValidationError('Simulasi gagal sampel ketiga')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(EmbeddingRepository,'create',fail)
    with pytest.raises(DataValidationError):service.save(login.token,payload,**fields(group))
    assert not list(service.photos.folder.glob('*.png'))
    with store.db.transaction() as session:
        assert session.scalar(select(Member).where(Member.member_code=='ENROLL-1')) is None
        assert session.scalar(select(func.count()).select_from(FaceEmbedding))==0


def test_invalid_packet_duplicate_expired_and_missing_fields(enrollment,store):
    service,login,group=enrollment
    payload=packet(service,service.begin(login.token))
    with pytest.raises(DataValidationError):service.save(login.token,CapturePacket(payload.body+b' ',payload.signature),**fields(group))
    with pytest.raises(DataValidationError):service.save(login.token,payload,code='',name='Test',group_id=group)
    service.save(login.token,payload,**fields(group))
    with pytest.raises(DataValidationError,match='digunakan'):
        service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    expired=packet(service,service.begin(login.token))
    service.clock=lambda:1e20
    with pytest.raises(DataValidationError):service.save(login.token,expired,code='NEW',name='Test',group_id=group)


@pytest.mark.parametrize('role',list(Role))
def test_enrollment_permissions_and_token_binding(enrollment,role):
    service,root,group=enrollment
    _,login=add_role(service.auth,root,role)
    if role==Role.VIEWER:
        with pytest.raises(AuthError):service.begin(login.token)
        return
    payload=packet(service,service.begin(login.token))
    with pytest.raises(DataValidationError):service.save(root.token,payload,**fields(group))
    assert service.save(login.token,payload,**fields(group))


def test_reregister_failure_keeps_old_set_photo_and_revision(enrollment,store,monkeypatch):
    service,login,group=enrollment
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    with store.db.transaction() as session:
        original=set(session.scalars(select(FaceEmbedding.id).where(FaceEmbedding.member_id==row.id)))
    path=service.photos.root/row.photo
    capture=packet(service,service.begin(login.token,member_id=row.id,revision=row.revision))
    from app.repositories.core import EmbeddingRepository
    def fail(*args,**kwargs):raise DataValidationError('simulasi gagal penggantian')
    monkeypatch.setattr(EmbeddingRepository,'create',fail)
    with pytest.raises(DataValidationError):service.save(login.token,capture,**fields(group),member_id=row.id,revision=row.revision)
    assert path.is_file() and len(list(service.photos.folder.glob('*.png')))==1
    with store.db.transaction() as session:
        assert set(session.scalars(select(FaceEmbedding.id).where(FaceEmbedding.member_id==row.id)))==original
        assert session.get(Member,row.id).revision==row.revision


def test_retention_failed_file_delete_is_reported_and_retried(enrollment,store,monkeypatch):
    service,login,group=enrollment
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    path=service.photos.root/row.photo
    administration=AdministrationService(service.auth,service.photos.root)
    original=administration.photos.discard_after_commit
    monkeypatch.setattr(administration.photos,'discard_after_commit',lambda unused:False)
    result=administration.deactivate_member(login.token,row.id,row.revision)
    assert result.cleanup_pending and path.exists()
    with store.db.transaction() as session:
        assert not list(session.scalars(select(FaceEmbedding).where(FaceEmbedding.member_id==row.id)))
    assert administration.members(login.token).cleanup_pending
    monkeypatch.setattr(administration.photos,'discard_after_commit',original)
    assert not administration.members(login.token).cleanup_pending and not path.exists()


def test_packet_incomplete_cancelled_revoked_and_stale_cannot_write(enrollment,store):
    import hmac,hashlib
    service,login,group=enrollment
    binding=service.begin(login.token)
    original=packet(service,binding)
    data=json.loads(original.body)
    data['samples']=data['samples'][:4]
    body=json.dumps(data).encode()
    incomplete=CapturePacket(body,hmac.new(service.key,body,hashlib.sha256).hexdigest())
    with pytest.raises(DataValidationError):service.save(login.token,incomplete,**fields(group))
    service.cancel(binding)
    with pytest.raises(DataValidationError):service.save(login.token,original,**fields(group))
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    binding=service.begin(login.token,member_id=row.id,revision=row.revision)
    stale=packet(service,binding)
    admin=AdministrationService(service.auth,service.photos.root)
    admin.update_member(login.token,row.id,row.revision,row.code,'Nama diperbarui',group)
    with pytest.raises(DataValidationError):service.save(login.token,stale,**fields(group),member_id=row.id,revision=row.revision)
    binding=service.begin(login.token)
    payload=packet(service,binding)
    service.auth.logout(login.token)
    with pytest.raises(AuthError):service.save(login.token,payload,code='DENIED',name='Test',group_id=group)


def test_saved_embeddings_are_searchable_from_a_fresh_process(enrollment,store):
    import subprocess,sys
    service,login,group=enrollment
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    code='''
import sys,numpy as np
from app.services.database import Database,create_database_engine
from database.runtime import connection_config
from ai.embedding.search import identify
engine=create_database_engine(connection_config('test'),schema=sys.argv[1])
try:
 with Database(engine).transaction() as session:
  match=identify(session,np.arange(512)+1,model_version='synthetic-v1')
  assert match.member_id==int(sys.argv[2])
finally:
 engine.dispose()
'''
    result=subprocess.run([sys.executable,'-c',code,store.schema,str(row.id)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,'Fresh-process synthetic recognition failed; private output withheld'
    assert not result.stdout


def test_verification_uses_stored_gallery_without_writing_probe(enrollment,store):
    import hmac,hashlib,time
    service,login,group=enrollment
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    def probe(binding,vector):
        body=json.dumps(dict(kind='probe',binding=binding,created=time.monotonic(),model_version='synthetic-v1',vector=vector.tolist())).encode()
        return CapturePacket(body,hmac.new(service.key,body,hashlib.sha256).hexdigest())
    binding=service.begin(login.token,member_id=row.id,revision=row.revision,purpose='verification')
    payload=probe(binding,analysis().embedding)
    result=service.verify(login.token,payload)
    assert result.matched and result.similarity>.999
    with pytest.raises(DataValidationError):service.verify(login.token,payload)
    binding=service.begin(login.token,member_id=row.id,revision=row.revision,purpose='verification')
    assert not service.verify(login.token,probe(binding,-analysis().embedding)).matched
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.member_id==row.id))==5
        assert session.scalar(select(func.count()).select_from(Attendance))==0


def test_inactive_member_cannot_restore_biometric_photo_via_metadata_edit(enrollment):
    service,login,group=enrollment
    row=service.save(login.token,packet(service,service.begin(login.token)),**fields(group))
    admin=AdministrationService(service.auth,service.photos.root)
    inactive=admin.deactivate_member(login.token,row.id,row.revision)
    with pytest.raises(DataValidationError,match='nonaktif'):
        admin.update_member(login.token,row.id,inactive.revision,row.code,row.name,group,photo_source='any-photo.png')
    result=admin.update_member(login.token,row.id,inactive.revision,row.code,'Nama metadata',group)
    assert not result.active and result.photo.endswith('profile-removed.svg')

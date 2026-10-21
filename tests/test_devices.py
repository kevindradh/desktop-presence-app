from dataclasses import replace
import json

import pytest
from sqlalchemy import func,select

from app.models.entities import AuditLog,Device,DeviceType,Location,Role
from app.services.database import DataValidationError
from app.services.devices import DevicesService
from app.services.device_secrets import DeviceSecretError,DeviceSecretStore
from app.services.auth import AuthError
from app.settings.config import load_config
from tests.test_credentials import MemoryKeyring
from tests.test_auth import auth,add_role
from tests.test_database import store,graph,record

pytestmark=pytest.mark.database
URL="rtsp://test-user:private-password@127.0.0.1:8554/private-stream?token=private-query"


@pytest.fixture
def devices(auth,store,tmp_path):
    service,login,clock=auth
    config=replace(load_config(tmp_path,environ={}),database=store.config)
    backend=MemoryKeyring()
    secrets=DeviceSecretStore(config,backend=backend)
    service=DevicesService(service,config,secrets=secrets)
    return service,login,backend


def location(service,login):
    return service.list(login.token).locations[0].id


def test_device_local_crud_stale_duplicate_and_audit(devices,store):
    service,login,backend=devices
    row=service.save(login.token,"USB","USB","1280x720",30,location(service,login),camera_index=1)
    assert row.camera_index==1 and not backend.entries
    with pytest.raises(DataValidationError,match="digunakan"):
        service.save(login.token,"usb","INTERNAL","1280x720",30,row.location_id)
    updated=service.save(login.token,"USB Edit","USB","640x480",15,row.location_id,
                         camera_index=0,device_id=row.id,revision=row.revision)
    assert updated.revision==row.revision+1
    with pytest.raises(DataValidationError,match="berubah"):
        service.delete(login.token,row.id,row.revision)
    service.delete(login.token,updated.id,updated.revision)
    assert not service.list(login.token).devices
    with store.db.transaction() as session:
        assert {"device.created","device.updated","device.deleted"}<=set(session.scalars(select(AuditLog.action)))


def test_rtsp_secret_private_persist_update_delete_and_sources(devices,store):
    service,login,backend=devices
    row=service.save(login.token,"IP Camera","RTSP","1280x720",30,location(service,login),rtsp_source=URL)
    assert row.rtsp_display=="rtsp://127.0.0.1:8554/" and row.has_source
    assert "private" not in repr(row)
    with store.db.transaction() as session:
        stored=session.get(Device,row.id)
        assert stored.rtsp_url==row.rtsp_display and stored.secret_ref
        assert "private" not in json.dumps([a.details for a in session.scalars(select(AuditLog))])
    source=service.sources(login.token,[row.id])[0]
    assert source.rtsp_source==URL and "private" not in repr(source)
    same=service.save(login.token,row.name,"RTSP",row.resolution,row.fps,row.location_id,
                      device_id=row.id,revision=row.revision)
    assert same.revision==row.revision and len(backend.entries)==1
    changed=service.save(login.token,row.name,"RTSP",row.resolution,row.fps,row.location_id,
        device_id=row.id,revision=row.revision,rtsp_source=URL+"2")
    assert len(backend.entries)==1 and service.sources(login.token,[row.id])[0].rtsp_source==URL+"2"
    service.delete(login.token,row.id,changed.revision)
    assert not backend.entries


def test_rtsp_replaced_by_webcam_removes_native_secret(devices):
    service,login,backend=devices
    row=service.save(login.token,"Camera","RTSP","640x480",15,location(service,login),rtsp_source=URL)
    row=service.save(login.token,"Camera","USB","640x480",15,row.location_id,
        device_id=row.id,revision=row.revision,camera_index=0)
    assert not backend.entries and not row.has_source and not row.rtsp_display


def test_rtsp_vault_failure_has_safe_error_and_no_partial_rows(devices,store,monkeypatch):
    service,login,backend=devices
    def fail(*args):
        raise RuntimeError(URL)
    monkeypatch.setattr(backend,"set_password",fail)
    with pytest.raises(DeviceSecretError) as error:
        service.save(login.token,"IP","RTSP","640x480",15,location(service,login),rtsp_source=URL)
    assert "private" not in str(error.value) and not backend.entries
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Device))==0
        assert not list(session.scalars(select(AuditLog).where(AuditLog.action=="device.created")))


def test_rtsp_commit_failure_discards_new_vault_entry(devices,store,monkeypatch):
    service,login,backend=devices
    from app.repositories.core import AuditRepository
    original=AuditRepository.append
    def fail(self,action,*args,**kwargs):
        if action=="device.created":
            raise DataValidationError("synthetic failure")
        return original(self,action,*args,**kwargs)
    monkeypatch.setattr(AuditRepository,"append",fail)
    with pytest.raises(DataValidationError):
        service.save(login.token,"IP","RTSP","640x480",15,location(service,login),rtsp_source=URL)
    assert not backend.entries and not service.list(login.token).devices


def test_device_with_history_cannot_delete(devices,store):
    service,login,backend=devices
    with store.db.transaction() as session:
        group,member,shift,device=graph(session)
        record(session,member,shift,device)
        device_id=device.id
    with pytest.raises(DataValidationError,match="riwayat"):
        service.delete(login.token,device_id,1)


@pytest.mark.parametrize("role",list(Role))
def test_device_permissions_and_revocation(devices,role):
    service,login,backend=devices
    row=service.save(login.token,"Camera","USB","640x480",15,location(service,login))
    _,account=add_role(service.auth,login,role)
    actions=(lambda:service.list(account.token),lambda:service.sources(account.token,[row.id]),
        lambda:service.save(account.token,"New","USB","640x480",15,row.location_id),
        lambda:service.delete(account.token,row.id,row.revision))
    if role in {Role.OPERATOR,Role.VIEWER}:
        for action in actions:
            with pytest.raises(AuthError):
                action()
    else:
        assert service.list(account.token).devices
        assert service.sources(account.token,[row.id])[0].camera_index==0
    service.auth.logout(account.token)
    with pytest.raises(AuthError):
        service.sources(account.token,[row.id])


def test_invalid_device_fields_and_sources(devices):
    service,login,backend=devices
    location_id=location(service,login)
    for changes in ({"name":""},{"kind":"FILE"},{"resolution":"9999x9999"},{"fps":True},
        {"fps":0},{"fps":61},{"location_id":99999},{"camera_index":-1},
        {"kind":"RTSP"},{"kind":"RTSP","rtsp_source":"file:///private"}):
        arguments=dict(name="Camera",kind="USB",resolution="640x480",fps=15,location_id=location_id)
        arguments.update(changes)
        with pytest.raises(DataValidationError):
            service.save(login.token,**arguments)
    for ids in ([],[1,1],[1,2,3]):
        with pytest.raises(DataValidationError):
            service.sources(login.token,ids)

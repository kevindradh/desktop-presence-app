"""Real PostgreSQL attendance transactions; synthetic vectors and controlled time."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np
import pytest
from sqlalchemy import func, select

from ai.attendance_process import signed_packet
from ai.enrollment import CapturePacket
from app.models.entities import (Attendance, AttendanceType, AttendanceStatus, AuditLog, CalendarDay,
    Device, DeviceType, FaceAngle, FaceEmbedding, Member, MemberLeave, Role)
from app.repositories.core import (DeviceRepository, EmbeddingRepository, SettingsRepository, ShiftRepository)
from app.services.attendance import AttendanceService, next_event, shift_window
from app.services.auth import AuthError
from app.services.database import DataValidationError, DatabaseUnavailable
from app.services.devices import DevicesService
from app.services.settings import SettingsService
from app.settings.config import load_config
from tests.test_auth import auth, add_role
from tests.test_database import store, graph
from tests.test_enrollment_capture import analysis as generated_analysis

pytestmark = pytest.mark.database
DAY = date(2026, 10, 18)
UTC = timezone.utc


def analysis():
    return replace(generated_analysis(),model_version="synthetic-v1")


@pytest.fixture
def attendance(auth, store, tmp_path):
    authority, login, _ = auth
    now = [datetime(2026, 10, 18, 1, tzinfo=UTC)]  # 08:00 Jakarta
    monotonic = [1000.]
    config = load_config(tmp_path, environ={})
    devices = DevicesService(authority, config)
    with store.db.transaction() as session:
        group, member, _, device = graph(session)
        shift = ShiftRepository(session).create('Pagi absensi', time(8), time(17), 10)
        ShiftRepository(session).assign(member.id, shift.id, DAY, None)
        EmbeddingRepository(session).create(member.id, analysis().embedding, FaceAngle.FRONT, 'synthetic-v1')
        other = DeviceRepository(session).create('Kamera kedua', DeviceType.USB, device.location_id)
        other.camera_index = 1
        ids = member.id, shift.id, device.id, other.id, group.id
    service = AttendanceService(authority, config, devices, clock=lambda:now[0], monotonic=lambda:monotonic[0])
    return SimpleNamespace(service=service, auth=authority, token=login.token, login=login,
        now=now, mono=monotonic, member=ids[0], shift=ids[1], device=ids[2], second=ids[3], group=ids[4], sequence={})


def begin(data, mode='AUTO', device=None, token=None):
    return data.service.begin(token or data.token, [device or data.device], mode)[0].binding


def payload(data, binding, *, value=None, absent=False, sequence=None):
    nonce = binding['nonce']
    seq = sequence if sequence is not None else data.sequence.get(nonce, 0)+1
    data.sequence[nonce] = seq
    return signed_packet(data.service.key, binding, seq, data.mono[0], analysis=None if absent else (value or analysis()))


def scan(data, binding=None, **kwargs):
    return data.service.submit(data.token, payload(data, binding or begin(data), **kwargs))


def rows(store):
    with store.db.transaction() as session:
        return list(session.scalars(select(Attendance).order_by(Attendance.id)))


@pytest.mark.parametrize('minute,status', [(0,'PRESENT'), (5,'PRESENT'), (10,'PRESENT'), (11,'LATE')])
def test_in_grace_boundaries_and_audit_after_commit(attendance, store, minute, status):
    data = attendance
    data.now[0] += timedelta(minutes=minute)
    result = scan(data)
    assert result.saved and result.event == 'IN'
    entry = rows(store)[0]
    assert entry.status.value == status and entry.work_date == DAY and not entry.is_automatic
    with store.db.transaction() as session:
        audit = session.scalar(select(AuditLog).where(AuditLog.action=='attendance.recorded'))
        assert audit.actor_id == data.login.principal.id and audit.entity_id == entry.id
        assert set(audit.details) == {'event_type','changed_fields'}
        assert session.scalar(select(func.count()).select_from(FaceEmbedding)) == 1


@pytest.mark.parametrize('delta,allowed', [(59.999,False),(60,True),(60.001,True)])
def test_cooldown_cross_camera_exact_boundary(attendance, store, delta, allowed):
    data=attendance
    assert scan(data).saved
    data.now[0] += timedelta(seconds=delta)
    result=scan(data,begin(data,device=data.second))
    assert result.saved is allowed
    assert len(rows(store)) == (2 if allowed else 1)
    if allowed:
        assert result.event=='OUT' and rows(store)[1].is_early_leave


def test_explicit_modes_break_transitions_late_preserved_and_closed_session(attendance, store):
    data=attendance;data.now[0]+=timedelta(minutes=11)
    assert not scan(data,begin(data,'OUT')).saved
    assert scan(data,begin(data,'IN')).saved
    for mode, expected in [('IN',None),('BREAK_IN',None),('BREAK_OUT','BREAK_OUT'),
                           ('OUT',None),('BREAK_OUT',None),('AUTO','BREAK_IN'),('OUT','OUT'),('AUTO',None)]:
        data.now[0]+=timedelta(seconds=61)
        result=scan(data,begin(data,mode))
        assert result.saved is (expected is not None)
        if expected: assert result.event==expected
    entries=rows(store)
    assert [entry.attendance_type.value for entry in entries]==['IN','BREAK_OUT','BREAK_IN','OUT']
    assert all(entry.status==AttendanceStatus.LATE for entry in entries)


def test_latch_requires_signed_absence_even_after_cooldown(attendance, store):
    data=attendance;binding=begin(data)
    assert scan(data,binding).saved
    data.now[0]+=timedelta(seconds=61)
    assert not scan(data,binding).saved
    assert len(rows(store))==1
    assert not scan(data,binding,absent=True).saved
    assert scan(data,binding).event=='OUT'


@pytest.mark.parametrize('cause',['early','unassigned','leave','holiday','inactive','unknown','spoof'])
def test_rejections_never_create_attendance(attendance, store, cause):
    data=attendance;value=analysis()
    if cause=='early':data.now[0]-=timedelta(microseconds=1)
    with store.db.transaction() as session:
        if cause=='unassigned':
            from app.models.entities import ShiftAssignment
            for item in session.scalars(select(ShiftAssignment)):session.delete(item)
        elif cause=='leave':session.add(MemberLeave(member_id=data.member,starts_on=DAY,ends_on=DAY))
        elif cause=='holiday':
            device=session.get(Device,data.device)
            session.add(CalendarDay(location_id=device.location_id,calendar_date=DAY,is_workday=False,label='Libur sintetis'))
        elif cause=='inactive':session.get(Member,data.member).is_active=False
    if cause=='unknown':value=replace(value,embedding=-value.embedding)
    if cause=='spoof':value=replace(value,live_score=.84)
    if cause=='spoof':
        with pytest.raises(DataValidationError):scan(data,value=value)
    else:assert not scan(data,value=value).saved
    assert not rows(store)


def test_policy_changes_reject_inflight_even_when_values_return_to_old(attendance, store):
    data=attendance
    settings=SettingsService(data.auth)
    before=settings.load(data.token)
    binding=begin(data)
    updated=settings.save(data.token,dict(before,anti_spoof_enabled=False),before)
    settings.save(data.token,before,updated)
    result=scan(data,binding)
    assert result.restart and not result.saved and not rows(store)
    assert scan(data).saved


def test_disabling_liveness_applies_only_to_new_flow(attendance):
    data=attendance;settings=SettingsService(data.auth)
    before=settings.load(data.token)
    settings.save(data.token,dict(before,anti_spoof_enabled=False),before)
    assert scan(data,value=replace(analysis(),live_score=None,live_class=None)).saved


@pytest.mark.parametrize('attack',['tamper','expired','replay','wrong_token','cancel','bad_mode','device_changed'])
def test_packet_session_and_device_guards(attendance, store, attack):
    data=attendance;binding=begin(data);packet=payload(data,binding)
    if attack=='bad_mode':
        with pytest.raises(DataValidationError):begin(data,'ILLEGAL')
        return
    if attack=='device_changed':
        with store.db.transaction() as session:session.get(Device,data.device).revision+=1
        assert data.service.submit(data.token,packet).restart
        assert not rows(store)
        return
    if attack=='tamper':packet=CapturePacket(packet.body+b' ',packet.signature)
    if attack=='expired':data.mono[0]+=3.001
    if attack=='replay':
        assert data.service.submit(data.token,packet).saved
    if attack=='wrong_token':
        _, other=add_role(data.auth,data.login,Role.OPERATOR)
        with pytest.raises(DataValidationError):data.service.submit(other.token,packet)
        return
    if attack=='cancel':data.service.cancel(binding)
    with pytest.raises(DataValidationError):data.service.submit(data.token,packet)
    assert len(rows(store))==(1 if attack=='replay' else 0)


@pytest.mark.parametrize('role',list(Role))
def test_attendance_access_and_revoked_session(attendance, role):
    data=attendance
    _,login=add_role(data.auth,data.login,role)
    if role==Role.VIEWER:
        for operation in (lambda:data.service.setup(login.token),lambda:begin(data,token=login.token),lambda:data.service.auto_checkout(login.token)):
            with pytest.raises(AuthError):operation()
    else:
        assert data.service.setup(login.token)[0]
        binding=begin(data,token=login.token)
        data.auth.logout(login.token)
        with pytest.raises(AuthError):data.service.submit(login.token,payload(data,binding))


def test_two_independent_terminals_cannot_duplicate_in_or_out(attendance, store):
    data=attendance
    from app.services.auth import AuthService
    independent_auth=AuthService(data.auth.database,clock=data.auth.clock)
    other=AttendanceService(independent_auth,data.service.config,data.service.devices,
        clock=data.service.clock,monotonic=data.service.monotonic)
    left=begin(data);right=other.begin(data.token,[data.second])[0].binding
    def attempt(pair):
        service,binding=pair
        packet=signed_packet(service.key,binding,1,data.mono[0],analysis=analysis())
        return service.submit(data.token,packet).saved
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt,[(data.service,left),(other,right)]))==[False,True]
    assert len(rows(store))==1
    data.now[0]+=timedelta(seconds=60)
    left=begin(data,'OUT');right=other.begin(data.token,[data.second],'OUT')[0].binding
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt,[(data.service,left),(other,right)]))==[False,True]
    assert [entry.attendance_type for entry in rows(store)]==[AttendanceType.IN,AttendanceType.OUT]


def test_audit_failure_rolls_back_event_and_no_success(attendance, store, monkeypatch):
    data=attendance
    from app.repositories.core import AuditRepository
    original=AuditRepository.append
    def fail(self,action,*args,**kwargs):
        if action=='attendance.recorded':raise DataValidationError('Simulasi gagal audit')
        return original(self,action,*args,**kwargs)
    monkeypatch.setattr(AuditRepository,'append',fail)
    with pytest.raises(DataValidationError):scan(data)
    assert not rows(store)


def test_overnight_work_date_and_out_at_shift_end(attendance, store):
    data=attendance
    with store.db.transaction() as session:
        from app.models.entities import Shift
        shift=session.get(Shift,data.shift);shift.start_time=time(20);shift.end_time=time(4)
    data.now[0]=datetime(2026,10,18,13,tzinfo=UTC)
    assert scan(data).saved
    data.now[0]=datetime(2026,10,18,21,tzinfo=UTC)
    assert scan(data).event=='OUT'
    assert all(entry.work_date==DAY for entry in rows(store))
    assert not rows(store)[1].is_early_leave


def test_auto_checkout_catchup_idempotent_respects_manual_and_inactive(attendance, store):
    data=attendance
    assert scan(data).saved
    data.now[0]=datetime(2026,10,18,10,tzinfo=UTC)
    assert data.service.auto_checkout(data.token)==0
    settings=SettingsService(data.auth);before=settings.load(data.token)
    settings.save(data.token,dict(before,auto_checkout=True),before)
    with store.db.transaction() as session:session.get(Member,data.member).is_active=False
    assert data.service.auto_checkout(data.token)==1
    assert data.service.auto_checkout(data.token)==0
    out=rows(store)[1]
    assert out.is_automatic and out.attendance_time==data.now[0] and not out.is_early_leave
    assert out.status==rows(store)[0].status


def test_auto_checkout_does_not_replace_manual_out(attendance, store):
    data=attendance
    assert scan(data).saved
    data.now[0]+=timedelta(seconds=60)
    assert scan(data).event=='OUT'
    settings=SettingsService(data.auth);before=settings.load(data.token)
    settings.save(data.token,dict(before,auto_checkout=True),before)
    data.now[0]=datetime(2026,10,18,10,tzinfo=UTC)
    assert data.service.auto_checkout(data.token)==0 and len(rows(store))==2


def test_next_day_session_and_open_break_can_be_closed_after_end(attendance, store):
    data=attendance
    assert scan(data).event=='IN'
    data.now[0]+=timedelta(seconds=60)
    assert scan(data,begin(data,'BREAK_OUT')).event=='BREAK_OUT'
    data.now[0]=datetime(2026,10,18,10,tzinfo=UTC)
    assert scan(data,begin(data,'BREAK_IN')).event=='BREAK_IN'
    data.now[0]+=timedelta(seconds=60)
    assert scan(data,begin(data,'OUT')).event=='OUT'
    data.now[0]=datetime(2026,10,19,1,tzinfo=UTC)
    assert scan(data).event=='IN'
    assert rows(store)[-1].work_date==DAY+timedelta(days=1)


def test_overnight_auto_checkout_before_and_at_end_and_two_schedulers(attendance, store):
    data=attendance
    from app.models.entities import Shift
    with store.db.transaction() as session:
        shift=session.get(Shift,data.shift);shift.start_time=time(20);shift.end_time=time(4)
    settings=SettingsService(data.auth);before=settings.load(data.token)
    settings.save(data.token,dict(before,auto_checkout=True),before)
    data.now[0]=datetime(2026,10,18,13,tzinfo=UTC)
    assert scan(data).saved
    data.now[0]=datetime(2026,10,18,21,tzinfo=UTC)-timedelta(microseconds=1)
    assert data.service.auto_checkout(data.token)==0
    data.now[0]+=timedelta(microseconds=1)
    other=AttendanceService(data.auth,data.service.config,data.service.devices,clock=data.service.clock)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(lambda s:s.auto_checkout(data.token),[data.service,other]))
    assert sorted(results)==[0,1]
    entry=rows(store)[1]
    assert entry.work_date==DAY and entry.is_automatic and entry.attendance_time==data.now[0]


@pytest.mark.models
def test_real_attendance_model_worker_rejects_blank_and_clears_input(attendance, store, qt_app, wait_until):
    import time as runtime_time
    from ai.attendance_process import AttendanceTarget
    from app.services.inference import InferenceController
    from app.services.settings import configured
    data=attendance
    data.service.monotonic=runtime_time.monotonic
    binding=begin(data)
    root=Path(__file__).resolve().parents[1]
    config=configured(load_config(root,environ={}),binding['settings'])
    worker=InferenceController(config,target=AttendanceTarget(data.service.key,binding))
    responses=[];worker.result.connect(responses.append)
    try:
        worker.start();wait_until(lambda:worker.state in ('ready','failed','timeout'),timeout=32000)
        assert worker.state=='ready'
        worker.submit(np.zeros((240,320,3),np.uint8))
        wait_until(lambda:len(responses)>=2,timeout=6000)
        assert responses[-1]['status']=='no_face' and 'packet' not in responses[-1]
        QTestWait=runtime_time.monotonic()+1.05
        wait_until(lambda:runtime_time.monotonic()>=QTestWait,timeout=2000)
        worker.submit(np.zeros((240,320,3),np.uint8))
        wait_until(lambda:'packet' in responses[-1],timeout=6000)
        assert not data.service.submit(data.token,responses[-1]['packet']).saved
        assert not rows(store)
    finally:
        worker.stop();wait_until(lambda:not worker.active,timeout=6000)
        assert worker.pixels is None and worker.shape is None
        worker.shutdown_now();worker.deleteLater()


@pytest.mark.parametrize('phase',['query','write'])
def test_scan_that_expires_inside_database_work_is_rolled_back(attendance, store, monkeypatch, phase):
    data=attendance
    if phase=='query':
        import app.services.attendance as module
        original=module.identify
        def delayed(*args,**kwargs):
            result=original(*args,**kwargs)
            data.mono[0]+=3.001
            return result
        monkeypatch.setattr(module,'identify',delayed)
    else:
        original=data.service._record
        def delayed(*args,**kwargs):
            result=original(*args,**kwargs)
            data.mono[0]+=3.001
            return result
        monkeypatch.setattr(data.service,'_record',delayed)
    with pytest.raises(DataValidationError,match='terlambat'):scan(data)
    assert not rows(store)
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action=='attendance.recorded'))==0


def test_continuous_view_on_second_camera_does_not_turn_in_into_out(attendance, store):
    data=attendance
    first=begin(data);second=begin(data,device=data.second)
    assert scan(data,first).saved
    assert not scan(data,second).saved
    data.now[0]+=timedelta(seconds=61)
    assert not scan(data,second).saved and len(rows(store))==1
    scan(data,second,absent=True)
    assert scan(data,second).event=='OUT'


def test_late_camera_in_same_capture_group_cannot_auto_checkout(attendance, store):
    data=attendance
    captures=data.service.begin(data.login.token,[data.device,data.second])
    first,second=(entry.binding for entry in captures)
    assert scan(data,first).event=='IN'
    data.now[0]+=timedelta(seconds=61)
    # Camera 2's first result arrives after cooldown; camera 1 still sees the member.
    assert not scan(data,second).saved and len(rows(store))==1
    scan(data,second,absent=True)
    assert not scan(data,second).saved
    scan(data,first,absent=True)
    scan(data,second,absent=True)
    assert scan(data,second).event=='OUT'

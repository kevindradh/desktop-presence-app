"""Actual PostgreSQL reports, snapshots and permission boundaries."""
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
from threading import Event

import pytest
from sqlalchemy import select

from app.models.entities import AttendanceStatus,AttendanceType,Member,Role,Shift
from app.repositories.core import AttendanceRepository,GroupRepository,MemberRepository,ShiftRepository
from app.services.auth import AuthError
from app.services.reports import ReportFilter,ReportsService,period_range
from app.services.database import DataValidationError
from app.services.tasks import TaskContext,TaskCancelled
from app.settings.config import load_config
from tests.test_database import store
from tests.test_auth import auth,add_role
from tests.test_attendance import attendance,scan,begin,DAY

pytestmark=pytest.mark.database


def reports(data,tmp_path):
    return ReportsService(data.auth,load_config(tmp_path,environ={}),clock=lambda:data.now[0],monotonic=lambda:data.mono[0])


def test_report_one_row_preserves_breaks_and_all_events(attendance,tmp_path):
    data=attendance
    assert scan(data).saved
    for mode in ('BREAK_OUT','BREAK_IN','OUT'):
        data.now[0]+=timedelta(seconds=61)
        assert scan(data,begin(data,mode)).saved
    service=reports(data,tmp_path)
    snapshot=service.build(data.token,ReportFilter(DAY,DAY))
    assert len(snapshot.rows)==1 and len(snapshot.events)==4
    row=snapshot.rows[0]
    assert row.status=='PRESENT' and row.check_in and row.check_out and row.early
    assert len(row.break_out)==len(row.break_in)==1
    assert service.snapshot(data.token,snapshot.id)==snapshot


def test_report_demo_statuses_filters_and_readonly_snapshot(store,tmp_path):
    from database.dashboard_demo import seed_dashboard_demo
    config=load_config(tmp_path,environ={})
    data=seed_dashboard_demo(store,config)
    service=ReportsService(data.auth,config,clock=data.clock.now)
    day=data.clock.now().date();filters=ReportFilter(day,day)
    snapshot=service.build(data.token,filters)
    assert sorted(row.status for row in snapshot.rows)==['ABSENT','LATE','LEAVE','PENDING','PRESENT']
    attended=service.build(data.token,replace(filters,status='ATTENDED'))
    assert {row.status for row in attended.rows}=={'PRESENT','LATE'}
    late=service.build(data.token,replace(filters,status='LATE',member='terlambat'))
    assert len(late.rows)==1
    missing=service.build(data.token,replace(filters,member='NO-SUCH-MEMBER'))
    assert not missing.rows and not missing.events
    groups,shifts=service.options(data.token)
    for group,_ in groups:
        chosen=service.build(data.token,replace(filters,group=group))
        assert all(row.group==dict(groups)[group] for row in chosen.rows)
    for shift,_ in shifts:
        chosen=service.build(data.token,replace(filters,shift=shift))
        assert all(row.shift==dict(shifts)[shift] for row in chosen.rows)


def test_snapshot_unchanged_after_commit_and_bound_to_session(attendance,tmp_path):
    data=attendance;service=reports(data,tmp_path)
    first=service.build(data.token,ReportFilter(DAY,DAY))
    assert first.rows[0].status=='PENDING'
    assert scan(data).saved
    assert service.snapshot(data.token,first.id).rows[0].status=='PENDING'
    second=service.build(data.token,ReportFilter(DAY,DAY))
    assert second.rows[0].status=='PRESENT'
    _,other=add_role(data.auth,data.login,Role.VIEWER)
    with pytest.raises(DataValidationError):service.snapshot(other.token,second.id)
    data.mono[0]+=901
    with pytest.raises(DataValidationError):service.snapshot(data.token,second.id)


def test_report_night_shift_inactive_history_and_historical_group(attendance,store,tmp_path):
    data=attendance
    from datetime import time
    with store.db.transaction() as session:
        shift=session.get(Shift,data.shift);shift.start_time=time(20);shift.end_time=time(4)
    data.now[0]=datetime(2026,10,18,13,tzinfo=timezone.utc)
    assert scan(data).saved
    data.now[0]+=timedelta(hours=6)
    assert scan(data,begin(data,'OUT')).saved
    with store.db.transaction() as session:
        group=GroupRepository(session).create('Grup baru')
        member=session.get(Member,data.member);member.group_id=group.id;member.is_active=False
    service=reports(data,tmp_path)
    result=service.build(data.token,ReportFilter(DAY,DAY))
    assert len(result.rows)==1 and result.rows[0].group!='Grup baru'
    assert result.rows[0].check_out.astimezone(service.zone).date()==DAY+timedelta(days=1)
    assert not service.build(data.token,ReportFilter(DAY+timedelta(days=1),DAY+timedelta(days=1))).rows


@pytest.mark.parametrize('role',list(Role))
def test_reports_all_documented_roles_and_revoked_access(attendance,tmp_path,role):
    data=attendance;service=reports(data,tmp_path)
    _,login=add_role(data.auth,data.login,role)
    result=service.build(login.token,ReportFilter(DAY,DAY))
    assert len(result.rows)==1
    data.auth.logout(login.token)
    with pytest.raises(AuthError):service.snapshot(login.token,result.id)


def test_report_bounds_cancel_and_period_ranges(attendance,tmp_path):
    data=attendance;service=reports(data,tmp_path)
    for bad in (ReportFilter(DAY,DAY-timedelta(days=1)),ReportFilter(DAY,DAY+timedelta(days=366)),
                ReportFilter(DAY,DAY,status='WRONG'),ReportFilter(DAY,DAY,group=True)):
        with pytest.raises(DataValidationError):service.build(data.token,bad)
    context=TaskContext(Event(),lambda value:None);context.cancelled.set()
    with pytest.raises(TaskCancelled):service.build(data.token,ReportFilter(DAY,DAY),context)
    assert period_range('WEEKLY',date(2026,10,18))==(date(2026,10,12),date(2026,10,18))
    assert period_range('MONTHLY',date(2024,2,20))==(date(2024,2,1),date(2024,2,29))
    assert period_range('MONTHLY',date(2026,12,3))==(date(2026,12,1),date(2026,12,31))

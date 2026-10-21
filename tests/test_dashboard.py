"""Dashboard counts committed people/schedules in isolated real PostgreSQL."""
from datetime import date, datetime, time, timedelta, timezone
import pytest
from sqlalchemy import select

from app.models.entities import (Attendance, AttendanceStatus, AttendanceType, CalendarDay, Device, Location,
    Member, MemberLeave, Role, Shift)
from app.repositories.core import AttendanceRepository, MemberRepository, ShiftRepository
from app.services.auth import AuthError
from app.services.dashboard import DashboardService
from app.services.database import DataValidationError
from app.settings.config import load_config
from tests.test_auth import auth, add_role
from tests.test_database import store
from tests.test_attendance import attendance, begin, scan, DAY

pytestmark = pytest.mark.database


def dashboard(data, tmp_path):
    return DashboardService(data.auth, load_config(tmp_path, environ={}), clock=lambda:data.now[0])


def test_empty_dashboard_and_input_validation(auth, tmp_path):
    authority, login, _ = auth
    service = DashboardService(authority, load_config(tmp_path, environ={}))
    result = service.load(login.token)
    assert (result.registered, result.present, result.late, result.absent, result.on_leave, result.pending) == (0,)*6
    assert not result.activity and not result.groups and len(result.daily)==30 and len(result.monthly)==12
    for invalid in ('2026-10-18', datetime.now(), date(1,1,1)):
        with pytest.raises(DataValidationError): service.load(login.token, invalid)


def test_dashboard_counts_people_not_events_and_preserves_late_subset(attendance, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    first=service.load(data.token,DAY)
    assert (first.registered,first.present,first.pending,first.absent)==(1,0,1,0)
    data.now[0]+=timedelta(minutes=11)
    assert scan(data).saved
    for mode in ('BREAK_OUT','BREAK_IN','OUT'):
        data.now[0]+=timedelta(seconds=61)
        assert scan(data,begin(data,mode)).saved
    result=service.load(data.token,DAY)
    assert (result.present,result.late,result.pending,result.absent)==(1,1,0,0)
    assert len(result.activity)==4
    assert result.shifts[0].present==result.groups[0].present==1
    assert result.daily[-1].present==result.monthly[-1].present==1
    assert result.monthly[-1].late==1


def test_absent_only_at_end_shift_and_holiday_leave_unassigned_inactive(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    data.now[0]=datetime(2026,10,18,9,59,59,tzinfo=timezone.utc)
    assert service.load(data.token,DAY).pending==1
    data.now[0]+=timedelta(seconds=1)
    assert service.load(data.token,DAY).absent==1
    with store.db.transaction() as session:
        session.add(MemberLeave(member_id=data.member,starts_on=DAY,ends_on=DAY))
    result=service.load(data.token,DAY)
    assert result.on_leave==1 and result.absent==0
    with store.db.transaction() as session:
        location=session.scalar(select(Location))
        session.add(CalendarDay(location_id=location.id,calendar_date=DAY,is_workday=False,label='Hari libur'))
    result=service.load(data.token,DAY)
    assert result.on_leave==result.absent==result.pending==0
    with store.db.transaction() as session:
        member=session.get(Member,data.member);member.is_active=False
        MemberRepository(session).create('NO-SCHEDULE','Tanpa jadwal',data.group,'synthetic/no-photo.png')
    result=service.load(data.token,DAY)
    assert result.registered==1 and result.absent==0


def test_existing_in_wins_over_later_leave_or_inactive_member(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    assert scan(data).saved
    with store.db.transaction() as session:
        session.add(MemberLeave(member_id=data.member,starts_on=DAY,ends_on=DAY))
        session.get(Member,data.member).is_active=False
    result=service.load(data.token,DAY)
    assert result.present==1 and result.on_leave==result.absent==result.pending==result.registered==0
    assert len(result.activity)==1


def test_night_shift_uses_start_work_date_and_end_next_day(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    with store.db.transaction() as session:
        shift=session.get(Shift,data.shift);shift.start_time=time(20);shift.end_time=time(4)
    data.now[0]=datetime(2026,10,18,13,tzinfo=timezone.utc)
    assert scan(data).saved
    data.now[0]=datetime(2026,10,18,18,tzinfo=timezone.utc) # 01:00 next day Jakarta
    assert scan(data,begin(data,'OUT')).saved
    result=service.load(data.token,DAY)
    assert result.present==1 and len(result.activity)==2
    next_day=service.load(data.token,DAY+timedelta(days=1))
    assert next_day.present==0 and next_day.pending==1 and next_day.absent==0
    assert next_day.daily[-2].present==1 and next_day.daily[-1].present==0


def test_unscanned_night_shift_is_not_absent_until_next_day_end(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    with store.db.transaction() as session:
        shift=session.get(Shift,data.shift);shift.start_time=time(20);shift.end_time=time(4)
    data.now[0]=datetime(2026,10,18,20,59,59,tzinfo=timezone.utc)
    assert service.load(data.token,DAY).pending==1
    data.now[0]+=timedelta(seconds=1)
    assert service.load(data.token,DAY).absent==1


def test_conflicting_assignments_not_reported_as_absent(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    with store.db.transaction() as session:
        other=ShiftRepository(session).create('Konflik',time(7),time(16))
        ShiftRepository(session).assign(data.member,other.id,DAY-timedelta(days=1),None)
    result=service.load(data.token,DAY)
    assert result.conflicts==1 and result.pending==result.absent==0


@pytest.mark.parametrize('role',list(Role))
def test_dashboard_authorization_rechecked(attendance, tmp_path, role):
    data=attendance;service=dashboard(data,tmp_path)
    _,login=add_role(data.auth,data.login,role)
    if role in (Role.SUPER_ADMIN,Role.ADMIN,Role.OPERATOR):
        assert service.load(login.token,DAY).registered==1
    else:
        with pytest.raises(AuthError):service.load(login.token,DAY)
    data.auth.logout(login.token)
    with pytest.raises(AuthError):service.load(login.token,DAY)


def test_month_trends_count_person_days_and_group_uses_historical_group(attendance, store, tmp_path):
    from app.repositories.core import GroupRepository
    data=attendance;service=dashboard(data,tmp_path)
    assert scan(data).saved
    with store.db.transaction() as session:
        newer=GroupRepository(session).create('Grup terbaru')
        session.get(Member,data.member).group_id=newer.id
        AttendanceRepository(session).record(member_id=data.member,device_id=data.device,shift_id=data.shift,
            event_type=AttendanceType.IN,timestamp=data.now[0]-timedelta(days=1),work_date=DAY-timedelta(days=1),status=AttendanceStatus.PRESENT)
    result=service.load(data.token,DAY)
    assert result.present==1 and result.monthly[-1].present==2
    assert result.daily[-2].present==result.daily[-1].present==1
    assert result.groups[0].label!='Grup terbaru'


def test_future_rows_and_rolled_back_events_are_not_in_dashboard(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    with pytest.raises(RuntimeError):
        with store.db.transaction() as session:
            AttendanceRepository(session).record(member_id=data.member,device_id=data.device,shift_id=data.shift,
                event_type=AttendanceType.IN,timestamp=data.now[0],work_date=DAY,status=AttendanceStatus.PRESENT)
            raise RuntimeError('Rollback fixture')
    assert service.load(data.token,DAY).present==0
    with store.db.transaction() as session:
        AttendanceRepository(session).record(member_id=data.member,device_id=data.device,shift_id=data.shift,
            event_type=AttendanceType.IN,timestamp=data.now[0]+timedelta(hours=1),work_date=DAY,status=AttendanceStatus.PRESENT)
    result=service.load(data.token,DAY)
    assert result.present==0 and not result.activity


def test_feed_bounded_and_ordered_with_automatic_out(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    assert scan(data).saved
    with store.db.transaction() as session:
        for i in range(24):
            AttendanceRepository(session).record(member_id=data.member,device_id=data.device,shift_id=data.shift,
                event_type=AttendanceType.BREAK_OUT if i%2==0 else AttendanceType.BREAK_IN,
                timestamp=data.now[0]+timedelta(seconds=i+1),work_date=DAY,status=AttendanceStatus.PRESENT)
    data.now[0]+=timedelta(seconds=30)
    result=service.load(data.token,DAY)
    assert result.present==1 and len(result.activity)==20
    assert list(result.activity)==sorted(result.activity,key=lambda row:(row.timestamp,row.id),reverse=True)


def test_multiple_sessions_on_one_day_still_count_one_person(attendance, store, tmp_path):
    data=attendance;service=dashboard(data,tmp_path)
    assert scan(data).saved
    with store.db.transaction() as session:
        other=ShiftRepository(session).create('Riwayat shift lain',time(5),time(6))
        AttendanceRepository(session).record(member_id=data.member,device_id=data.device,shift_id=other.id,
            event_type=AttendanceType.IN,timestamp=data.now[0]-timedelta(hours=2),work_date=DAY,status=AttendanceStatus.PRESENT)
    result=service.load(data.token,DAY)
    assert result.present==result.daily[-1].present==result.monthly[-1].present==1
    assert sum(row.present for row in result.shifts)==2 and len(result.activity)==2

"""School simulation uses owned test schemas, never the development database."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import event, func, select

from app.models.entities import (Attendance, AttendanceStatus, AttendanceType, AuditLog, Base,
    CalendarDay, Device, FaceEmbedding, Member, MemberGroup, ShiftAssignment, User)
from app.services.auth import AuthService
from app.services.dashboard import DashboardService
from app.services.database import DataValidationError
from app.services.reports import ReportFilter, ReportsService
from app.settings.config import DatabaseConfig, load_config
from database.seed.school import seed_school
from scripts.manage_database import main
from tests.test_database import store, graph


DAY = date(2026, 10, 21)
ZONE = ZoneInfo('Asia/Jakarta')
NOW = datetime(2026, 10, 21, 18, tzinfo=ZONE)


def counts(session):
    return {name:session.scalar(select(func.count()).select_from(table))
            for name,table in Base.metadata.tables.items()}


@pytest.mark.database
def test_school_seed_counts_timestamps_flags_no_faces_accounts_and_repeat(store):
    with store.db.transaction() as session:
        result = seed_school(session, anchor=DAY, now=NOW)
        before = counts(session)
        assert (result['members'], result['active_members'], result['groups'], result['shifts'], result['devices']) == (80,74,8,4,3)
        assert before['users'] == before['face_embeddings'] == 0
        assert before['members'] == 80 and before['member_leaves'] == 12
        assert before['shift_assignments'] == 74
        assert all(d.camera_index is None and d.rtsp_url is None for d in session.scalars(select(Device)))
        assert all(m.member_code.startswith('SIM-SMP-') for m in session.scalars(select(Member)))
        rows = list(session.scalars(select(Attendance)))
        assert all(r.attendance_time <= NOW for r in rows)
        assert sum(r.is_early_leave for r in rows) > 0
        assert sum(r.is_automatic for r in rows) > 0
        assert {r.attendance_type for r in rows} == set(AttendanceType)
        tolerance = session.scalar(select(Member).where(Member.member_code=='SIM-SMP-7A-03'))
        row = next(r for r in rows if r.member_id==tolerance.id and r.work_date==DAY and r.attendance_type==AttendanceType.IN)
        assert row.status == AttendanceStatus.PRESENT
        assert row.attendance_time.astimezone(ZONE).strftime('%H:%M') == '07:10'
        holiday = date.fromisoformat(result['holiday'])
        assert all(r.work_date != holiday for r in rows)
        session.get(Member,tolerance.id).full_name = 'Siswa Simulasi Diubah Penguji'
    with store.db.transaction() as session:
        repeated = seed_school(session, anchor=DAY, now=NOW+timedelta(hours=1))
        assert repeated['already_seeded']
        assert counts(session) == before
        assert session.get(Member,tolerance.id).full_name == 'Siswa Simulasi Diubah Penguji'
        with pytest.raises(DataValidationError, match='parameter berbeda'):
            seed_school(session, anchor=DAY, history_days=14, now=NOW)


@pytest.mark.database
def test_school_seed_real_dashboard_reports_and_overnight_semantics(store,tmp_path):
    with store.db.transaction() as session:
        result = seed_school(session, anchor=DAY, now=NOW)
    config = load_config(tmp_path, environ={})
    auth = AuthService(store.db, clock=lambda:NOW)
    auth.bootstrap('school-review','Penguji Simulasi','Synthetic-school-2026!')
    login = auth.login('school-review','Synthetic-school-2026!')
    dashboard = DashboardService(auth,config,clock=lambda:NOW)
    data = dashboard.load(login.token,DAY)
    assert (data.registered,data.present,data.late,data.absent,data.on_leave,data.pending)==(74,43,7,6,12,1)
    reports = ReportsService(auth,config,clock=lambda:NOW)
    report = reports.build(login.token,ReportFilter(DAY,DAY))
    assert len(report.rows)==62
    assert {r.status for r in report.rows}=={'PRESENT','LATE','ABSENT','LEAVE','PENDING'}
    assert any(r.early for r in report.rows) and any(r.automatic for r in report.rows)
    assert any(r.break_out and r.break_in for r in report.rows)
    holiday = dashboard.load(login.token,date.fromisoformat(result['holiday']))
    assert (holiday.present,holiday.absent,holiday.pending,holiday.on_leave)==(0,0,0,0)
    with store.db.transaction() as session:
        night = session.scalar(select(Member).where(Member.member_code=='SIM-SMP-PIKET'))
        events = list(session.scalars(select(Attendance).where(Attendance.member_id==night.id)))
        assert events
        for row in events:
            local = row.attendance_time.astimezone(ZONE)
            assert local.date()==row.work_date+timedelta(days=row.attendance_type==AttendanceType.OUT)
            assert local.hour==(20 if row.attendance_type==AttendanceType.IN else 6)
        inactive = session.scalar(select(Member).where(Member.member_code=='SIM-SMP-7A-10'))
        assert not inactive.is_active
        assert session.scalar(select(func.count()).select_from(Attendance).where(Attendance.member_id==inactive.id))>0


@pytest.mark.database
def test_school_seed_preserves_existing_business_data_and_rolls_back_failure(store):
    with store.db.transaction() as session:
        graph(session)
        before = counts(session)
    with pytest.raises(DataValidationError,match='kosong'):
        with store.db.transaction() as session:
            seed_school(session,anchor=DAY,now=NOW)
    with store.db.transaction() as session:
        assert counts(session)==before


@pytest.mark.database
def test_school_seed_is_atomic_and_retryable(store):
    def fail(session,*args):
        if any(isinstance(row,AuditLog) and row.action=='simulation.school_seeded' for row in session.new):
            raise RuntimeError('Synthetic failure')
    with store.db.transaction() as session:
        before = counts(session)
    with pytest.raises(RuntimeError):
        with store.db.transaction() as session:
            event.listen(session,'before_flush',fail)
            seed_school(session,anchor=DAY,now=NOW)
    with store.db.transaction() as session:
        assert counts(session)==before
    with store.db.transaction() as session:
        assert seed_school(session,anchor=DAY,now=NOW)['members']==80


@pytest.mark.database
def test_school_seed_concurrent_calls_do_not_duplicate(store):
    def run():
        with store.db.transaction() as session:
            return seed_school(session,anchor=DAY,now=NOW)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:run(),range(2)))
    assert sorted(r['already_seeded'] for r in results)==[False,True]
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==80


@pytest.mark.database
def test_school_seed_weekend_anchor_and_morning_cutoff(store):
    morning = datetime(2026,10,25,6,tzinfo=ZONE)
    with store.db.transaction() as session:
        result = seed_school(session,history_days=14,now=morning)
        assert result['date']=='2026-10-25'
        day = morning.date()
        assert session.scalar(select(CalendarDay.is_workday).where(CalendarDay.calendar_date==day)) is True
        assert session.scalar(select(func.count()).select_from(Attendance).where(Attendance.work_date==day))==0
        assert all(t<=morning for t in session.scalars(select(Attendance.attendance_time)))


@pytest.mark.database
def test_school_cli_requires_current_migrations(store,monkeypatch,tmp_path,capsys):
    import app.services.database as db
    import database.runtime as runtime
    monkeypatch.setattr(runtime,'connection_config',lambda *a,**kw:store.config)
    monkeypatch.setattr(db,'create_database_engine',lambda *a,**kw:store.engine)
    monkeypatch.setattr(runtime,'schema_status',lambda connection:{'at_head':False,'schema_valid':False})
    assert main(['seed-school','--data-dir',str(tmp_path)])==2
    assert 'upgrade terlebih dahulu' in capsys.readouterr().err
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==0


@pytest.mark.parametrize('kwargs',[{'anchor':'2026-10-21'}, {'anchor':date(2026,10,22)},
    {'history_days':13},{'history_days':91},{'history_days':True},{'now':datetime(2026,10,21)}])
def test_school_seed_invalid_options_rejected_before_database(kwargs):
    with pytest.raises(DataValidationError):
        seed_school(None,**dict({'anchor':DAY,'now':NOW},**kwargs))


@pytest.mark.parametrize('host,name',[('example.invalid','stargate_dev'),('127.0.0.1','postgres')])
def test_school_cli_rejects_nonlocal_or_system_database_before_connect(monkeypatch,host,name,capsys):
    import database.runtime as runtime
    import app.services.database as db
    monkeypatch.setattr(runtime,'connection_config',lambda *a,**kw:DatabaseConfig(host=host,name=name))
    monkeypatch.setattr(db,'create_database_engine',lambda *a,**kw:pytest.fail('Must not open database'))
    assert main(['seed-school'])==2
    assert 'database aplikasi lokal' in capsys.readouterr().err


@pytest.mark.database
def test_school_cli_runs_after_upgrade_and_keeps_existing_login(store,monkeypatch,tmp_path,capsys):
    import app.services.database as db
    import database.runtime as runtime
    monkeypatch.setattr(runtime,'connection_config',lambda *a,**kw:store.config)
    monkeypatch.setattr(db,'create_database_engine',lambda *a,**kw:store.engine)
    auth = AuthService(store.db)
    auth.bootstrap('school-review','Penguji Simulasi','Synthetic-school-2026!')
    assert main(['seed-school','--date',DAY.isoformat(),'--data-dir',str(tmp_path)])==0
    assert '"members": 80' in capsys.readouterr().out
    assert auth.login('school-review','Synthetic-school-2026!').principal.username=='school-review'
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(User))==1
        assert session.scalar(select(func.count()).select_from(FaceEmbedding))==0

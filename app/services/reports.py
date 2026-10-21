"""Authorized, immutable report snapshots. No biometric/credential data."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import secrets
from threading import Lock
import time
from zoneinfo import ZoneInfo

from sqlalchemy import Date, and_, cast, exists, func, or_, select, union

from app.models.entities import (Attendance, AttendanceType, CalendarDay, Device, Location,
    Member, MemberGroup, MemberLeave, Shift, ShiftAssignment)
from app.services.attendance import shift_window
from app.services.auth import digest
from app.services.database import DataValidationError

STATUS = {'PRESENT':'Hadir tepat waktu','LATE':'Terlambat','ABSENT':'Absent',
          'LEAVE':'Izin','PENDING':'Belum masuk','CONFLICT':'Perlu diperiksa'}
MAX_ROWS, MAX_EVENTS = 50000, 200000


@dataclass(frozen=True)
class ReportFilter:
    start: date
    end: date
    group: int | None = None
    member: str = ''
    shift: int | None = None
    status: str = 'ALL'

    def validate(self):
        if type(self.start) is not date or type(self.end) is not date or not 2 <= self.start.year <= 9998 or not 2 <= self.end.year <= 9998:
            raise DataValidationError('Tanggal laporan tidak valid.')
        if not 0 <= (self.end-self.start).days <= 365:
            raise DataValidationError('Rentang laporan harus berurutan dan paling lama 366 hari.')
        if any(value is not None and (type(value) is not int or value <= 0) for value in (self.group,self.shift)):
            raise DataValidationError('Filter grup atau shift tidak valid.')
        if not isinstance(self.member,str) or len(self.member)>200 or self.status not in (*STATUS,'ALL','ATTENDED'):
            raise DataValidationError('Filter anggota atau status tidak valid.')


def period_range(kind, anchor):
    if type(anchor) is not date or not 2 <= anchor.year <= 9998:
        raise DataValidationError('Tanggal acuan tidak valid.')
    if kind=='DAILY':return anchor,anchor
    if kind=='WEEKLY':
        start=anchor-timedelta(days=anchor.weekday())
        return start,start+timedelta(days=6)
    if kind=='MONTHLY':
        start=anchor.replace(day=1)
        end=(start.replace(year=start.year+1,month=1) if start.month==12 else start.replace(month=start.month+1))-timedelta(days=1)
        return start,end
    raise DataValidationError('Jenis periode tidak valid.')


@dataclass(frozen=True)
class ReportRow:
    work_date: date
    member_id: int
    code: str
    name: str
    group: str
    shift: str
    status: str
    check_in: datetime | None
    check_out: datetime | None
    break_out: tuple[datetime,...]
    break_in: tuple[datetime,...]
    early: bool
    automatic: bool
    devices: str


@dataclass(frozen=True)
class ReportEvent:
    work_date: date
    code: str
    name: str
    event: str
    timestamp: datetime
    device: str
    automatic: bool


@dataclass(frozen=True)
class ReportSnapshot:
    id: str
    filters: ReportFilter
    created: datetime
    zone: str
    group_label: str
    shift_label: str
    rows: tuple[ReportRow,...]
    events: tuple[ReportEvent,...]


@dataclass(repr=False)
class CachedReport:
    token_hash: str = field(repr=False)
    born: float
    snapshot: ReportSnapshot


class ReportsService:
    def __init__(self, auth, config, *, clock=None, monotonic=time.monotonic):
        self.auth=auth
        self.zone=ZoneInfo(config.timezone)
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        self.monotonic=monotonic
        self.cache={}
        self.lock=Lock()

    def clear(self):
        with self.lock:self.cache.clear()

    def options(self,token):
        def operation(session,actor):
            result=[]
            for entity,label in ((MemberGroup,MemberGroup.group_name),(Shift,Shift.shift_name)):
                rows=tuple(session.execute(select(entity.id,label).order_by(label).limit(5001)).all())
                if len(rows)>5000:raise DataValidationError('Terlalu banyak pilihan grup/shift untuk dimuat.')
                result.append(rows)
            return tuple(result)
        return self.auth._protected(token,'reports',operation)

    def build(self,token,filters,context=None):
        filters.validate()
        def operation(session,actor):
            if context:context.checkpoint()
            snapshot=self._build(session,filters,context)
            with self.lock:
                self.cache={key:value for key,value in self.cache.items() if self.monotonic()-value.born<900}
                while len(self.cache)>=2:self.cache.pop(next(iter(self.cache)))
                self.cache[snapshot.id]=CachedReport(digest(token),self.monotonic(),snapshot)
            return snapshot
        return self.auth._protected(token,'reports',operation)

    def _cached(self,token,key):
        with self.lock:
            value=self.cache.get(key)
            if value is None or value.token_hash!=digest(token) or not 0<=self.monotonic()-value.born<900:
                raise DataValidationError('Hasil laporan sudah kedaluwarsa. Tampilkan laporan kembali.')
            return value.snapshot

    def snapshot(self,token,key):
        return self.auth._protected(token,'reports',lambda s,a:self._cached(token,key))

    def publish(self,token,key,action):
        def operation(session,actor):
            from app.repositories.core import AuditRepository
            snapshot=self._cached(token,key)
            AuditRepository(session).append('report.exported','system',actor_id=actor.id,
                details={'record_count':len(snapshot.rows)})
            return action()
        return self.auth._protected(token,'reports',operation)

    def _build(self,session,f,context):
        now=self.clock()
        if not isinstance(now,datetime) or now.utcoffset() is None:
            raise DataValidationError('Waktu laporan tidak valid.')
        days=select(cast(func.generate_series(cast(f.start,Date),cast(f.end,Date),timedelta(days=1)),Date).label('day')).cte('report_days')
        holiday=exists(select(CalendarDay.id).join(Location).where(Location.location_code=='LOCAL',
            CalendarDay.calendar_date==days.c.day,CalendarDay.is_workday.is_(False)))
        schedules=(select(Member.id.label('member'),ShiftAssignment.shift_id.label('shift'),days.c.day.label('day'))
            .select_from(days).join(ShiftAssignment,and_(ShiftAssignment.starts_on<=days.c.day,
                or_(ShiftAssignment.ends_on.is_(None),ShiftAssignment.ends_on>=days.c.day)))
            .join(Member,Member.id==ShiftAssignment.member_id).where(Member.is_active.is_(True),~holiday))
        event_filter=(Attendance.work_date>=f.start,Attendance.work_date<=f.end,Attendance.attendance_time<=now)
        actual=select(Attendance.member_id,Attendance.shift_id,Attendance.work_date).where(*event_filter)
        keys=union(schedules,actual).subquery()
        incoming=(select(Attendance.member_id.label('member'),Attendance.shift_id.label('shift'),Attendance.work_date.label('day'),
            func.min(Attendance.group_id).label('group')).where(*event_filter,Attendance.attendance_type==AttendanceType.IN)
            .group_by(Attendance.member_id,Attendance.shift_id,Attendance.work_date).subquery())
        same=lambda table:and_(table.c.member==keys.c.member,table.c.shift==keys.c.shift,table.c.day==keys.c.day)
        leave=exists(select(MemberLeave.id).where(MemberLeave.member_id==keys.c.member,
            MemberLeave.starts_on<=keys.c.day,MemberLeave.ends_on>=keys.c.day))
        assignments=(select(func.count()).select_from(ShiftAssignment).where(ShiftAssignment.member_id==keys.c.member,
            ShiftAssignment.starts_on<=keys.c.day,or_(ShiftAssignment.ends_on.is_(None),ShiftAssignment.ends_on>=keys.c.day)).scalar_subquery())
        base=(select(keys.c.member,keys.c.shift,keys.c.day,Member.member_code,Member.full_name,
            MemberGroup.group_name,Shift,leave.label('leave'),assignments.label('assignments'))
            .join(Member,Member.id==keys.c.member).join(Shift,Shift.id==keys.c.shift)
            .outerjoin(incoming,same(incoming)).join(MemberGroup,MemberGroup.id==func.coalesce(incoming.c.group,Member.group_id)))
        if f.group:base=base.where(MemberGroup.id==f.group)
        if f.shift:base=base.where(Shift.id==f.shift)
        if f.member.strip():base=base.where(or_(Member.member_code.icontains(f.member.strip(),autoescape=True),Member.full_name.icontains(f.member.strip(),autoescape=True)))
        records=session.execute(base.order_by(keys.c.day,Member.member_code,Shift.id).limit(MAX_ROWS+1)).all()
        if len(records)>MAX_ROWS:raise DataValidationError('Hasil melebihi 50.000 baris. Persempit rentang/filter, lalu tampilkan kembali.')
        if context:context.checkpoint();context.progress(20)
        selected=base.with_only_columns(keys.c.member,keys.c.shift,keys.c.day).subquery()
        details=session.execute(select(Attendance,Device.device_name).join(Device)
            .join(selected,and_(Attendance.member_id==selected.c.member,Attendance.shift_id==selected.c.shift,Attendance.work_date==selected.c.day))
            .where(*event_filter).order_by(Attendance.attendance_time,Attendance.id).limit(MAX_EVENTS+1)).all()
        if len(details)>MAX_EVENTS:raise DataValidationError('Detail melebihi 200.000 event. Persempit rentang/filter.')
        by_key={}
        for event,device in details:
            by_key.setdefault((event.member_id,event.shift_id,event.work_date),[]).append((event,device))
        rows=[];events=[]
        for index,(member,shift_id,day,code,name,group,shift,on_leave,count) in enumerate(records):
            if context and index%250==0:context.checkpoint()
            items=by_key.get((member,shift_id,day),[])
            ins=[event for event,device in items if event.attendance_type==AttendanceType.IN]
            outs=[event for event,device in items if event.attendance_type==AttendanceType.OUT]
            if ins:status=ins[0].status.value
            elif items or count>1:status='CONFLICT'
            elif on_leave:status='LEAVE'
            else:status='ABSENT' if now>=shift_window(shift,day,self.zone)[1] else 'PENDING'
            if f.status not in ('ALL',status) and not (f.status=='ATTENDED' and status in ('PRESENT','LATE')):continue
            row=ReportRow(day,member,code,name,group,shift.shift_name,status,
                ins[0].attendance_time if ins else None,outs[-1].attendance_time if outs else None,
                tuple(event.attendance_time for event,device in items if event.attendance_type==AttendanceType.BREAK_OUT),
                tuple(event.attendance_time for event,device in items if event.attendance_type==AttendanceType.BREAK_IN),
                bool(outs and outs[-1].is_early_leave),bool(outs and outs[-1].is_automatic),
                ', '.join(dict.fromkeys(device for event,device in items)))
            rows.append(row)
            events.extend(ReportEvent(day,code,name,event.attendance_type.value,event.attendance_time,device,event.is_automatic) for event,device in items)
        group_label=session.get(MemberGroup,f.group).group_name if f.group and session.get(MemberGroup,f.group) else ('Grup tidak ditemukan' if f.group else 'Semua grup')
        shift_label=session.get(Shift,f.shift).shift_name if f.shift and session.get(Shift,f.shift) else ('Shift tidak ditemukan' if f.shift else 'Semua shift')
        if context:context.progress(40)
        return ReportSnapshot(secrets.token_urlsafe(24),f,now,str(self.zone),group_label,shift_label,tuple(rows),tuple(events))

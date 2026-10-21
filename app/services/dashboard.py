"""Authorized, bounded aggregates of people/check-ins, never frame/break counts."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import case, exists, func, literal, or_, select, tuple_

from app.models.entities import (Attendance, AttendanceStatus, AttendanceType, CalendarDay,
    Device, Location, Member, MemberGroup, MemberLeave, Shift, ShiftAssignment)
from app.services.database import DataValidationError


@dataclass(frozen=True)
class ChartRow:
    label: str
    present: int
    late: int


@dataclass(frozen=True)
class Activity:
    id: int
    name: str
    code: str
    event: str
    timestamp: datetime
    shift: str
    device: str
    automatic: bool


@dataclass(frozen=True)
class DashboardData:
    work_date: date
    updated: datetime
    registered: int
    present: int
    late: int
    absent: int
    on_leave: int
    pending: int
    conflicts: int
    shifts: tuple[ChartRow, ...]
    groups: tuple[ChartRow, ...]
    daily: tuple[ChartRow, ...]
    monthly: tuple[ChartRow, ...]
    activity: tuple[Activity, ...]


def month_start(value, offset):
    index = value.year*12+value.month-1+offset
    year, month = divmod(index, 12)
    return date(year, month+1, 1)


class DashboardService:
    def __init__(self, auth, config, *, clock=None):
        self.auth = auth
        self.zone = ZoneInfo(config.timezone)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def load(self, token, work_date=None):
        now = self.clock()
        if not isinstance(now, datetime) or now.utcoffset() is None:
            raise DataValidationError('Waktu dashboard harus menyertakan zona waktu.')
        day = now.astimezone(self.zone).date() if work_date is None else work_date
        if type(day) is not date or not 2 <= day.year <= 9998:
            raise DataValidationError('Tanggal kerja dashboard tidak valid.')
        return self.auth._protected(token, 'dashboard', lambda session, actor: self._load(session, day, now))

    def _load(self, session, day, now):
        # The auth advisory lock serializes all supported app/terminal writes
        # throughout this snapshot. No photos, vectors, or credential columns.
        incoming = (Attendance.attendance_type == AttendanceType.IN, Attendance.attendance_time <= now)
        today = (*incoming, Attendance.work_date == day)
        present, late = session.execute(select(func.count(func.distinct(Attendance.member_id)),
            func.count(func.distinct(case((Attendance.status == AttendanceStatus.LATE, Attendance.member_id)))))
            .where(*today)).one()
        registered = session.scalar(select(func.count()).select_from(Member).where(Member.is_active.is_(True)))

        # Assignments have no location FK. The single-site schedule uses the
        # configured organization zone and LOCAL calendar; scan dates stay as stored.
        holiday = exists(select(CalendarDay.id).join(Location).where(Location.location_code == 'LOCAL',
            CalendarDay.calendar_date == day, CalendarDay.is_workday.is_(False)))
        leave = exists(select(MemberLeave.id).where(MemberLeave.member_id == Member.id,
            MemberLeave.starts_on <= day, MemberLeave.ends_on >= day))
        end = func.timezone(str(self.zone), literal(day)+Shift.end_time+
            case((Shift.end_time < Shift.start_time, timedelta(days=1)), else_=timedelta(0)))
        scheduled = (select(Member.id.label('member'), func.count(ShiftAssignment.id).label('assignments'),
            func.min(end).label('end'), leave.label('leave'))
            .join(ShiftAssignment, ShiftAssignment.member_id == Member.id)
            .join(Shift, Shift.id == ShiftAssignment.shift_id)
            .where(Member.is_active.is_(True), ShiftAssignment.starts_on <= day,
                   or_(ShiftAssignment.ends_on.is_(None), ShiftAssignment.ends_on >= day), ~holiday)
            .group_by(Member.id).subquery())
        checked_in = select(Attendance.member_id).where(*today)
        status = case((scheduled.c.assignments > 1, 'conflict'),
                      (scheduled.c.leave, 'leave'), (scheduled.c.end <= now, 'absent'), else_='pending')
        counts = dict(session.execute(select(status, func.count()).where(~scheduled.c.member.in_(checked_in))
                                      .group_by(status)).all())

        def chart(entity, key, label):
            query = (select(label, func.count(func.distinct(Attendance.member_id)),
                func.count(func.distinct(case((Attendance.status == AttendanceStatus.LATE, Attendance.member_id)))))
                .select_from(Attendance).join(entity, entity.id == key).where(*today).group_by(entity.id, label)
                .order_by(func.count(func.distinct(Attendance.member_id)).desc(), label).limit(12))
            return tuple(ChartRow(str(name), count, late_count) for name, count, late_count in session.execute(query))

        start = day-timedelta(days=29)
        daily_counts = {work: (count, late_count) for work, count, late_count in session.execute(
            select(Attendance.work_date, func.count(func.distinct(Attendance.member_id)),
                func.count(func.distinct(case((Attendance.status == AttendanceStatus.LATE, Attendance.member_id)))))
            .where(*incoming, Attendance.work_date >= start, Attendance.work_date <= day).group_by(Attendance.work_date))}
        daily = tuple(ChartRow((start+timedelta(days=i)).isoformat(), *daily_counts.get(start+timedelta(days=i), (0, 0))) for i in range(30))
        first, last = month_start(day, -11), month_start(day, 1)
        month = func.date_trunc('month', Attendance.work_date)
        monthly_counts = {stamp.date(): (count, late_count) for stamp, count, late_count in session.execute(
            select(month, func.count(func.distinct(tuple_(Attendance.member_id, Attendance.work_date))),
                func.count(func.distinct(case((Attendance.status == AttendanceStatus.LATE,
                                               tuple_(Attendance.member_id, Attendance.work_date))))))
            .where(*incoming, Attendance.work_date >= first, Attendance.work_date < last,
                   Attendance.work_date <= day).group_by(month))}
        monthly = tuple(ChartRow(month_start(day, i).strftime('%Y-%m'), *monthly_counts.get(month_start(day, i), (0, 0))) for i in range(-11, 1))
        feed = tuple(Activity(row.id, name, code, row.attendance_type.value, row.attendance_time,
                              shift, device, row.is_automatic)
            for row, name, code, shift, device in session.execute(select(Attendance, Member.full_name,
                Member.member_code, Shift.shift_name, Device.device_name).join(Member).join(Shift).join(Device)
                .where(Attendance.work_date == day, Attendance.attendance_time <= now)
                .order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(20)))
        return DashboardData(day, now, registered, present, late, counts.get('absent', 0), counts.get('leave', 0),
            counts.get('pending', 0), counts.get('conflict', 0),
            chart(Shift, Attendance.shift_id, Shift.shift_name),
            chart(MemberGroup, Attendance.group_id, MemberGroup.group_name), daily, monthly, feed)

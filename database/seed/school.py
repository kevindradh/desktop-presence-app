"""Explicit synthetic school fixtures, without accounts or biometric data."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, text

from app.models.entities import (Attendance, AttendanceStatus, AttendanceType, AuditLog, CalendarDay,
    Device, DeviceType, Location, Member, MemberGroup, MemberLeave, Shift, ShiftAssignment)
from app.services.database import DataValidationError
from database.seed.defaults import seed_defaults


VERSION = 'smp-v1'
MARKER = 'simulation.school_seeded'
SCENARIOS = (
    'Tepat waktu', 'Terlambat', 'Batas toleransi', 'Pulang awal',
    'Istirahat lengkap', 'Checkout otomatis', 'Izin', 'Sakit',
    'Belum check-in', 'Nonaktif', 'Tanpa jadwal', 'Penugasan berakhir',
)


def seed_school(session, *, anchor=None, history_days=30, timezone_name='Asia/Jakarta', now=None):
    zone = ZoneInfo(timezone_name)
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise DataValidationError('Waktu seeder harus menyertakan zona waktu.')
    anchor = now.astimezone(zone).date() if anchor is None else anchor
    if type(anchor) is not date or not date(2000, 1, 1) <= anchor <= now.astimezone(zone).date():
        raise DataValidationError('Tanggal simulasi harus sejak tahun 2000 dan tidak boleh di masa depan.')
    if type(history_days) is not int or not 14 <= history_days <= 90:
        raise DataValidationError('Riwayat simulasi harus 14 sampai 90 hari.')
    parameters = {'version': VERSION, 'date': anchor.isoformat(), 'days': history_days, 'zone': str(zone)}
    session.execute(text('SELECT pg_advisory_xact_lock(734281003)'))
    marker = session.scalar(select(AuditLog).where(AuditLog.action == MARKER).order_by(AuditLog.id).limit(1))
    if marker is not None:
        previous = marker.details if isinstance(marker.details, dict) else {}
        if previous.get('parameters') != parameters or not isinstance(previous.get('summary'), dict):
            raise DataValidationError('Data simulasi sudah ada dengan parameter berbeda atau penanda berubah. '
                                      'Gunakan parameter semula; fresh diperlukan untuk membuat simulasi baru.')
        return dict(previous['summary'], already_seeded=True)
    for model in (Member, MemberGroup, Shift, Device, ShiftAssignment, Attendance, MemberLeave, CalendarDay):
        if session.scalar(select(select(model.id).exists())):
            raise DataValidationError('Seeder SMP memerlukan data anggota, grup, shift, perangkat, jadwal, '
                                      'kalender, dan kehadiran yang kosong. Akun login boleh tetap ada.')

    seed_defaults(session)
    location = session.scalar(select(Location).where(Location.location_code == 'LOCAL'))
    start = anchor-timedelta(days=history_days-1)
    ended = anchor-timedelta(days=7)
    days = tuple(start+timedelta(days=i) for i in range(history_days))
    holiday = anchor-timedelta(days=10)
    while holiday.weekday() >= 5:
        holiday -= timedelta(days=1)
    holidays = {day for day in days if day.weekday() >= 5} | {holiday}
    # The anchor is always available for review, even when seeded on a weekend.
    holidays.discard(anchor)
    calendar = [CalendarDay(location_id=location.id, calendar_date=day, is_workday=False,
                label='SIM SMP: libur akhir pekan' if day.weekday() >= 5 else 'SIM SMP: libur kegiatan simulasi')
                for day in sorted(holidays)]
    if anchor.weekday() >= 5:
        calendar.append(CalendarDay(location_id=location.id, calendar_date=anchor, is_workday=True,
                                    label='SIM SMP: hari uji khusus'))
    session.add_all(calendar)
    groups = [MemberGroup(group_name=f'SIM SMP {name}', description='Data sintetis untuk pengujian sekolah.')
              for name in ('7A', '7B', '8A', '8B', '9A', '9B', 'Guru', 'Staf')]
    shifts = [Shift(shift_name='SIM SMP '+name, start_time=begin, end_time=end, grace_minutes=grace)
              for name, begin, end, grace in (
                  ('Siswa', time(7), time(14), 10),
                  ('Guru', time(6, 45), time(14, 30), 5),
                  ('Tata usaha', time(7, 30), time(15, 30), 5),
                  ('Piket malam', time(20), time(6), 0))]
    devices = [Device(device_name='SIM SMP '+name, device_type=kind, location_id=location.id,
                      camera_index=None, resolution='1280x720', fps=30)
               for name, kind in (('Gerbang siswa', DeviceType.USB), ('Ruang guru', DeviceType.INTERNAL),
                                  ('Pos piket', DeviceType.USB))]
    session.add_all(groups+shifts+devices)
    session.flush()
    participants = []
    for group in groups[:6]:
        classroom = group.group_name.removeprefix('SIM SMP ')
        for index, scenario in enumerate(SCENARIOS, 1):
            member = Member(member_code=f'SIM-SMP-{classroom}-{index:02}',
                full_name=f'Siswa Simulasi {classroom} {index:02} ({scenario})', group_id=group.id,
                position='Siswa simulasi', photo_path='synthetic/smp/no-photo.png')
            participants.append((member, shifts[0], devices[0], scenario))
    for index in range(1, 7):
        member = Member(member_code=f'SIM-SMP-GURU-{index:02}', full_name=f'Guru Simulasi {index:02}',
            group_id=groups[6].id, position='Guru simulasi', photo_path='synthetic/smp/no-photo.png')
        participants.append((member, shifts[1], devices[1], 'Terlambat' if index == 2 else 'Tepat waktu'))
    for code, name, shift, scenario in (
            ('TU', 'Staf Tata Usaha Simulasi', shifts[2], 'Istirahat lengkap'),
            ('PIKET', 'Petugas Piket Simulasi', shifts[3], 'Tepat waktu')):
        member = Member(member_code='SIM-SMP-'+code, full_name=name, group_id=groups[7].id,
            position='Staf simulasi', photo_path='synthetic/smp/no-photo.png')
        participants.append((member, shift, devices[2], scenario))
    session.add_all([member for member, *_ in participants])
    session.flush()
    events, assignments, leaves = [], [], []
    for member, shift, device, scenario in participants:
        if scenario != 'Tanpa jadwal':
            assignments.append(ShiftAssignment(member_id=member.id, shift_id=shift.id, starts_on=start,
                ends_on=ended if scenario in ('Nonaktif', 'Penugasan berakhir') else None))
        if scenario in ('Izin', 'Sakit'):
            leaves.append(MemberLeave(member_id=member.id, starts_on=start, ends_on=anchor,
                                      leave_type='SICK' if scenario == 'Sakit' else 'LEAVE'))
        for day in days:
            if day in holidays or scenario in ('Izin', 'Sakit', 'Belum check-in', 'Tanpa jadwal'):
                continue
            if scenario in ('Nonaktif', 'Penugasan berakhir') and day > ended:
                continue
            begin = datetime.combine(day, shift.start_time, zone)
            end = datetime.combine(day, shift.end_time, zone)
            if end <= begin:
                end += timedelta(days=1)
            minute = shift.grace_minutes+15 if scenario == 'Terlambat' else (
                shift.grace_minutes if scenario == 'Batas toleransi' else 0)
            incoming = begin+timedelta(minutes=minute)
            status = AttendanceStatus.LATE if scenario == 'Terlambat' else AttendanceStatus.PRESENT
            timeline = [(AttendanceType.IN, incoming, False, False)]
            if scenario == 'Istirahat lengkap':
                timeline.extend(((AttendanceType.BREAK_OUT, begin+timedelta(hours=3), False, False),
                                 (AttendanceType.BREAK_IN, begin+timedelta(hours=3, minutes=15), False, False)))
            timeline.append((AttendanceType.OUT, end-timedelta(minutes=90) if scenario == 'Pulang awal' else end,
                             scenario == 'Pulang awal', scenario == 'Checkout otomatis'))
            for kind, stamp, early, automatic in timeline:
                if stamp <= now:
                    events.append(Attendance(member_id=member.id, device_id=device.id, shift_id=shift.id,
                        attendance_type=kind, attendance_time=stamp, status=status, work_date=day,
                        group_id=member.group_id, is_early_leave=early, is_automatic=automatic))
        if scenario == 'Nonaktif':
            member.is_active = False
    session.add_all(assignments+leaves+events)
    session.flush()
    summary = dict(parameters, start=start.isoformat(), cutoff=now.isoformat(),
        groups=len(groups), members=len(participants), active_members=sum(m.is_active for m, *_ in participants), students=72, teachers=6, staff=2,
        shifts=len(shifts), devices=len(devices), assignments=len(assignments), leaves=len(leaves),
        calendar_days=len(calendar), attendance_events=len(events),
        holiday=holiday.isoformat(), ended_assignment=ended.isoformat(), already_seeded=False)
    # Seed provenance stays in the audit, not in an editable classroom description.
    session.add(AuditLog(action=MARKER, entity_type='system', details={
        'parameters': parameters, 'summary': summary,
        'record_count':len(participants)+len(events)+len(assignments)+len(leaves)+len(calendar)+len(groups)+len(shifts)+len(devices)}))
    session.flush()
    return summary

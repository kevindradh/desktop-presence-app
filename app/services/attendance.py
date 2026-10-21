"""Authenticated face attendance, serialized validation/commit and bounded catch-up."""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math
import secrets
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.orm import aliased

from ai.embedding.search import identify
from ai.enrollment import CapturePacket
from app.models.entities import (Attendance, AttendanceStatus, AttendanceType, CalendarDay,
    Device, Location, Member, MemberGroup, MemberLeave, Shift, ShiftAssignment)
from app.repositories.core import AuditRepository, normalized_vector
from app.services.database import DataValidationError
from app.services.settings import read_policy

MODES = ('AUTO', 'IN', 'OUT', 'BREAK_OUT', 'BREAK_IN')
EVENTS = {'IN': 'Masuk', 'OUT': 'Keluar', 'BREAK_OUT': 'Mulai istirahat', 'BREAK_IN': 'Selesai istirahat'}
UTC = timezone.utc


class AlreadyRecorded(DataValidationError):
    pass


@dataclass(frozen=True, repr=False)
class AttendanceCapture:
    spec: object = field(repr=False)
    binding: dict = field(repr=False)


@dataclass(frozen=True)
class AttendanceFeedback:
    saved: bool
    message: str
    event_id: int | None = None
    member_id: int | None = None
    event: str = ''
    similarity: float | None = None
    restart: bool = False
    reason: str = ''


@dataclass(frozen=True)
class AttendanceRow:
    id: int
    name: str
    code: str
    event: str
    timestamp: datetime
    status: str
    work_date: object
    shift: str
    device: str
    early: bool
    automatic: bool


def shift_window(shift, work_date, zone):
    """Absolute instants; overnight work date is always the shift start date."""
    start = datetime.combine(work_date, shift.start_time, zone)
    end = datetime.combine(work_date, shift.end_time, zone)
    if shift.end_time < shift.start_time:
        end += timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def next_event(previous, mode):
    if mode not in MODES:
        raise DataValidationError('Mode absensi tidak valid.')
    if mode == 'AUTO':
        mode = {None: 'IN', 'IN': 'OUT', 'BREAK_IN': 'OUT', 'BREAK_OUT': 'BREAK_IN'}.get(previous)
    allowed = {None: {'IN'}, 'IN': {'OUT', 'BREAK_OUT'},
               'BREAK_OUT': {'BREAK_IN'}, 'BREAK_IN': {'BREAK_OUT', 'OUT'}, 'OUT': set()}
    if mode not in allowed.get(previous, set()):
        if previous == 'OUT' or (mode == 'IN' and previous is not None):
            raise AlreadyRecorded('Urutan absensi tidak sah atau sesi shift sudah selesai.')
        raise DataValidationError('Urutan absensi tidak sah atau sesi shift sudah selesai.')
    return AttendanceType(mode)


class AttendanceService:
    def __init__(self, auth, config, devices, *, clock=None, monotonic=time.monotonic):
        self.auth, self.config, self.devices = auth, config, devices
        self.clock = clock or auth.clock
        self.monotonic = monotonic
        self.key = secrets.token_bytes(32)
        self.flows = {}

    def _run(self, token, operation):
        return self.auth._protected(token, 'attendance', operation)

    def _now(self):
        value = self.clock()
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise DataValidationError('Waktu absensi harus menyertakan zona waktu.')
        return value.astimezone(UTC)

    @staticmethod
    def _zone(location):
        try:
            return ZoneInfo(location.timezone)
        except (ZoneInfoNotFoundError, ValueError, AttributeError):
            raise DataValidationError('Zona waktu lokasi tidak valid.') from None

    def setup(self, token):
        def operation(session, actor):
            values, _ = read_policy(session)
            devices = tuple(self.devices._data(session, row) for row in session.scalars(
                select(Device).join(Location).where(Location.is_active.is_(True)).order_by(Device.device_name)))
            return devices, values, self._recent(session)
        return self._run(token, operation)

    def begin(self, token, device_ids, mode='AUTO'):
        def operation(session, actor):
            if mode not in MODES:
                raise DataValidationError('Mode absensi tidak valid.')
            values, revision = read_policy(session)
            specs = self.devices._sources(session, device_ids)
            now = self.monotonic()
            self.flows = {key: value for key, value in self.flows.items()
                          if 0 <= now-value['binding']['created'] <= 86400}
            if len(self.flows)+len(specs) > 20:
                raise DataValidationError('Tutup pemeriksaan lama sebelum membuka kamera lagi.')
            result = []
            capture_group = secrets.token_hex(24)
            for spec in specs:
                device = session.get(Device, spec.device_id)
                location = session.get(Location, device.location_id)
                if not location.is_active:
                    raise DataValidationError('Lokasi perangkat sudah nonaktif.')
                self._zone(location)
                binding = dict(nonce=secrets.token_hex(24), token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    capture_group=capture_group,
                    purpose='attendance', created=now, device_id=device.id, device_revision=device.revision,
                    location_id=location.id, timezone=location.timezone, mode=mode,
                    settings=values, policy_revision=revision)
                result.append(AttendanceCapture(spec, deepcopy(binding)))
            for entry in result:
                self.flows[entry.binding['nonce']] = dict(binding=deepcopy(entry.binding), sequence=0, latched=None)
            return tuple(result)
        return self._run(token, operation)

    def cancel(self, binding):
        self.flows.pop(binding['nonce'], None)

    def cancel_all(self):
        self.flows.clear()

    def _read(self, token, packet):
        try:
            if not isinstance(packet, CapturePacket) or not isinstance(packet.body, bytes) or len(packet.body) > 100_000:
                raise ValueError
            signature = hmac.new(self.key, packet.body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, packet.signature):
                raise ValueError
            data = json.loads(packet.body)
            binding = data['binding']
            flow = self.flows.get(binding['nonce'])
            now = self.monotonic()
            if flow is None or binding != flow['binding'] or binding['purpose'] != 'attendance':
                raise ValueError
            if binding['token_hash'] != hashlib.sha256(token.encode()).hexdigest() or not 0 <= now-binding['created'] <= 86400:
                raise ValueError
            if type(data['created']) not in (int, float) or not math.isfinite(data['created']):
                raise ValueError
            if not binding['created'] <= data['created'] <= now or now-data['created'] > binding['settings']['recognition_timeout']:
                raise ValueError
            sequence = data['sequence']
            if type(sequence) is not int or sequence <= flow['sequence'] or data['kind'] not in ('face', 'absence'):
                raise ValueError
            if data['kind'] == 'face':
                data['vector'] = normalized_vector(data['vector'])
                if not isinstance(data['model_version'], str) or not 1 <= len(data['model_version']) <= 120:
                    raise ValueError
                if binding['settings']['anti_spoof_enabled']:
                    score = data['live_score']
                    if type(score) not in (int, float) or not math.isfinite(score) or not binding['settings']['anti_spoof_threshold'] <= score <= 1:
                        raise ValueError
                    if type(data['live_class']) is not int or data['live_class'] != 1:
                        raise ValueError
            flow['sequence'] = sequence  # Never replay an uncertain transaction; take a fresh frame instead.
            return data, binding, flow
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise DataValidationError('Hasil scan tidak valid, terlambat atau sudah digunakan. Mulai pemeriksaan baru.') from None

    def submit(self, token, packet):
        def operation(session, actor):
            data, binding, flow = self._read(token, packet)
            values, revision = read_policy(session, lock=True)
            device = session.get(Device, binding['device_id'])
            location = session.get(Location, binding['location_id'])
            if revision != binding['policy_revision'] or values != binding['settings']:
                return AttendanceFeedback(False, 'Pengaturan berubah. Hentikan lalu mulai absensi kembali.', restart=True)
            if device is None or device.revision != binding['device_revision'] or device.location_id != binding['location_id'] or not location or not location.is_active or location.timezone != binding['timezone']:
                return AttendanceFeedback(False, 'Perangkat atau lokasi berubah. Muat ulang dan mulai kembali.', restart=True)
            if data['kind'] == 'absence':
                flow['latched'] = None
                return AttendanceFeedback(False, 'Siap untuk scan berikutnya.', reason='absence')
            match = identify(session, data['vector'], model_version=data['model_version'], threshold=values['similarity_threshold'])
            if match.member_id is None:
                return AttendanceFeedback(False, 'Face Not Recognized — wajah tidak dikenali.', similarity=match.similarity)
            member = session.scalar(select(Member).where(Member.id == match.member_id).with_for_update())
            if member is None or not member.is_active:
                return AttendanceFeedback(False, 'Anggota tidak aktif.')
            present_in_group = any(other['latched'] == member.id and
                other['binding']['capture_group'] == binding['capture_group']
                for other in list(self.flows.values()))
            if present_in_group:
                flow['latched'] = member.id
                return AttendanceFeedback(False, 'Scan sudah tersimpan. Tinggalkan area kamera sebentar sebelum scan lagi.', member_id=member.id, reason='already_recorded')
            now = self._now()
            if values['auto_checkout']:
                self._close_due(session, actor, now, member_id=member.id)
            latest = session.scalar(select(Attendance).where(Attendance.member_id == member.id)
                .order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(1))
            if latest and now < latest.attendance_time + timedelta(seconds=values['duplicate_window']):
                flow['latched'] = member.id
                return AttendanceFeedback(False, 'Absensi berulang ditolak; tunggu sampai jeda selesai.', member_id=member.id, reason='already_recorded')
            try:
                shift, work_date, start, end, previous, status = self._session(session, member, location, now)
                event = next_event(previous, binding['mode'])
                if event in (AttendanceType.IN, AttendanceType.BREAK_OUT) and now >= end:
                    raise DataValidationError('Shift sudah berakhir. Tutup sesi masuk yang masih terbuka.')
                if event == AttendanceType.IN:
                    status = AttendanceStatus.PRESENT if now <= start+timedelta(minutes=shift.grace_minutes) else AttendanceStatus.LATE
            except DataValidationError as error:
                return AttendanceFeedback(False, str(error), member_id=member.id,
                    reason='already_recorded' if isinstance(error, AlreadyRecorded) else '')
            self._fresh(data, binding)
            row = self._record(session, actor, member, device.id, shift.id, work_date, event,
                now, status, early=(event == AttendanceType.OUT and now < end))
            self._fresh(data, binding)
            flow['latched'] = member.id
            return AttendanceFeedback(True, f'{member.full_name} — {EVENTS[event.value]} berhasil tersimpan.',
                row.id, member.id, event.value, match.similarity)
        return self._run(token, operation)  # Success is returned only after Database.transaction commits.

    def _fresh(self, data, binding):
        if self.monotonic()-data['created'] > binding['settings']['recognition_timeout']:
            raise DataValidationError('Hasil scan terlambat; transaksi dibatalkan. Mulai pemeriksaan baru.')

    @staticmethod
    def _open_query(member_id=None):
        finished = aliased(Attendance)
        return select(Attendance).where(Attendance.attendance_type == AttendanceType.IN,
            Attendance.member_id == member_id if member_id is not None else True,
            ~exists(select(finished.id).where(finished.member_id == Attendance.member_id,
                finished.shift_id == Attendance.shift_id, finished.work_date == Attendance.work_date,
                finished.attendance_type == AttendanceType.OUT)))

    def _session(self, session, member, location, now):
        opened = session.scalar(self._open_query(member.id).order_by(Attendance.attendance_time).limit(1))
        if opened:
            shift = session.get(Shift, opened.shift_id)
            source = session.get(Device, opened.device_id)
            zone = self._zone(session.get(Location, source.location_id))
            start, end = shift_window(shift, opened.work_date, zone)
            last = session.scalar(select(Attendance).where(Attendance.member_id == member.id,
                Attendance.shift_id == shift.id, Attendance.work_date == opened.work_date)
                .order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(1))
            return shift, opened.work_date, start, end, last.attendance_type.value, opened.status
        zone = self._zone(location)
        today = now.astimezone(zone).date()
        for work_date in (today-timedelta(days=1), today):
            assignments = list(session.scalars(select(ShiftAssignment).where(ShiftAssignment.member_id == member.id,
                ShiftAssignment.starts_on <= work_date, or_(ShiftAssignment.ends_on.is_(None), ShiftAssignment.ends_on >= work_date))))
            if len(assignments) > 1:
                raise DataValidationError('Penugasan shift bertumpang tindih. Hubungi Admin.')
            if not assignments:
                continue
            shift = session.get(Shift, assignments[0].shift_id)
            start, end = shift_window(shift, work_date, zone)
            if start <= now < end:
                previous = session.scalar(select(Attendance).where(Attendance.member_id == member.id,
                    Attendance.shift_id == shift.id, Attendance.work_date == work_date)
                    .order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(1))
                if previous:
                    raise AlreadyRecorded('Sesi shift ini sudah selesai; check-in kedua ditolak.')
                calendar = session.scalar(select(CalendarDay).where(CalendarDay.location_id == location.id,
                    CalendarDay.calendar_date == work_date))
                on_leave = session.scalar(select(MemberLeave.id).where(MemberLeave.member_id == member.id,
                    MemberLeave.starts_on <= work_date, MemberLeave.ends_on >= work_date).limit(1))
                if (calendar and not calendar.is_workday) or on_leave is not None:
                    raise DataValidationError('Tidak dapat check-in pada hari libur atau periode izin anggota.')
                return shift, work_date, start, end, None, AttendanceStatus.PRESENT
        raise DataValidationError('Belum masuk jam shift atau tidak ada penugasan shift yang berlaku.')

    @staticmethod
    def _record(session, actor, member, device_id, shift_id, work_date, event, timestamp, status, *, early=False, automatic=False, group_id=None):
        row = Attendance(member_id=member.id, device_id=device_id, shift_id=shift_id, work_date=work_date,
            attendance_type=event, attendance_time=timestamp, status=status,
            group_id=member.group_id if group_id is None else group_id, is_early_leave=early, is_automatic=automatic)
        session.add(row)
        session.flush()
        AuditRepository(session).append('attendance.recorded', 'attendance', row.id, actor_id=actor.id,
            details={'event_type': event, 'changed_fields': ['is_automatic'] if automatic else []})
        return row

    def _close_due(self, session, actor, now, *, member_id=None):
        # SQL limits the due set before fetching; includes old sessions and inactive members.
        local_end = Attendance.work_date + Shift.end_time + case(
            (Shift.end_time < Shift.start_time, timedelta(days=1)), else_=timedelta(0))
        statement = self._open_query(member_id).join(Shift).join(Device).join(Location, Location.id == Device.location_id)
        statement = statement.where(func.timezone(Location.timezone, local_end) <= now)
        opened = list(session.scalars(statement.order_by(Attendance.attendance_time, Attendance.id).limit(100)))
        closed = 0
        for entry in opened:
            if closed >= 100:
                break
            shift = session.get(Shift, entry.shift_id)
            device = session.get(Device, entry.device_id)
            zone = self._zone(session.get(Location, device.location_id))
            _, end = shift_window(shift, entry.work_date, zone)
            if now < end:
                continue
            member = session.scalar(select(Member).where(Member.id == entry.member_id).with_for_update())
            self._record(session, actor, member, entry.device_id, entry.shift_id, entry.work_date,
                AttendanceType.OUT, end, entry.status, automatic=True, group_id=entry.group_id)
            closed += 1
        return closed

    def auto_checkout(self, token):
        def operation(session, actor):
            values, _ = read_policy(session, lock=True)
            return self._close_due(session, actor, self._now()) if values['auto_checkout'] else 0
        return self._run(token, operation)

    @staticmethod
    def _recent(session):
        return tuple(AttendanceRow(row.id, name, code, row.attendance_type.value, row.attendance_time,
            row.status.value, row.work_date, shift, device, row.is_early_leave, row.is_automatic)
            for row, name, code, shift, device in session.execute(select(Attendance, Member.full_name,
                Member.member_code, Shift.shift_name, Device.device_name).join(Member).join(Shift).join(Device)
                .order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(30)))

"""Administrative actions recheck authorization in the same transaction as writes."""
from dataclasses import dataclass, replace
from datetime import date, time
import re

from sqlalchemy import func, or_, select

from app.models.entities import (Attendance, Member, MemberGroup, Shift, ShiftAssignment, FaceEmbedding)
from app.repositories.core import AuditRepository, GroupRepository, MemberRepository, ShiftRepository, required
from app.services.database import DataValidationError
from app.services.member_photos import PhotoStore


@dataclass(frozen=True)
class GroupData:
    id: int
    name: str
    description: str
    revision: int
    member_count: int


@dataclass(frozen=True)
class ShiftData:
    id: int
    name: str
    start: time
    end: time
    grace: int
    revision: int

    @property
    def overnight(self):
        return self.end < self.start


@dataclass(frozen=True)
class MemberData:
    id: int
    code: str
    name: str
    group_id: int
    group_name: str
    photo: str
    email: str
    phone: str
    position: str
    active: bool
    revision: int
    cleanup_pending: bool = False


@dataclass(frozen=True)
class MemberPage:
    rows: tuple[MemberData, ...]
    total: int
    offset: int
    limit: int
    groups: tuple[GroupData, ...]
    cleanup_pending: bool = False


@dataclass(frozen=True)
class AssignmentData:
    id: int
    shift_id: int
    shift_name: str
    starts: date
    ends: date | None


@dataclass(frozen=True)
class HistoryData:
    timestamp: object
    event: str
    status: str
    work_date: date
    group_name: str
    shift_name: str
    early: bool
    automatic: bool = False


@dataclass(frozen=True)
class MemberDetail:
    member: MemberData
    assignments: tuple[AssignmentData, ...]
    history: tuple[HistoryData, ...]
    history_total: int
    shifts: tuple[ShiftData, ...]
    can_assign: bool
    has_embeddings: bool = False


def clean(value, maximum, *, mandatory=False):
    if value is None and not mandatory:
        return ""
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        raise DataValidationError("Isian mengandung karakter yang tidak valid.")
    result = value.strip()
    if len(result) > maximum or (mandatory and not result):
        raise DataValidationError("Field wajib kosong atau melebihi panjang yang diizinkan.")
    return result


def validate_member(code, name, group_id, email="", phone="", position=""):
    result = {"member_code": clean(code, 64, mandatory=True),
              "full_name": clean(name, 200, mandatory=True), "group_id": identifier(group_id),
              "email": clean(email, 254), "phone": clean(phone, 40), "position": clean(position, 160)}
    if result["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", result["email"]):
        raise DataValidationError("Alamat email tidak valid.")
    return result


def identifier(value):
    if type(value) is not int or value < 1:
        raise DataValidationError("Pilih data yang valid.")
    return value


def validate_shift(name, start, end, grace):
    name = clean(name, 120, mandatory=True)
    if (not isinstance(start, time) or not isinstance(end, time) or start.tzinfo or end.tzinfo
        or start == end or start.second or start.microsecond or end.second or end.microsecond):
        raise DataValidationError("Jam shift harus berbeda dan menggunakan ketelitian menit.")
    duration = ((end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)) % 1440
    if type(grace) is not int or not 0 <= grace < duration:
        raise DataValidationError("Toleransi harus nol atau lebih dan kurang dari durasi shift.")
    return name, start, end, grace


def group_data(session, row):
    count = session.scalar(select(func.count()).select_from(Member).where(Member.group_id == row.id))
    return GroupData(row.id, row.group_name, row.description or "", row.revision, count)


def shift_data(row):
    return ShiftData(row.id, row.shift_name, row.start_time, row.end_time, row.grace_minutes, row.revision)


def member_data(session, row):
    return MemberData(row.id, row.member_code, row.full_name, row.group_id,
        session.get(MemberGroup, row.group_id).group_name, row.photo_path,
        row.email or "", row.phone or "", row.position or "", row.is_active, row.revision)


class AdministrationService:
    def __init__(self, auth, root):
        self.auth = auth
        self.photos = PhotoStore(root)

    def _run(self, token, permission, operation):
        # Auth's transaction lock serializes writes with account/session changes as well.
        return self.auth._protected(token, permission, operation)

    @staticmethod
    def _row(session, model, record_id, revision=None):
        row = session.scalar(select(model).where(model.id == identifier(record_id)).with_for_update())
        if row is None:
            raise DataValidationError("Data tidak ditemukan. Muat ulang daftar.")
        if revision is not None and (type(revision) is not int or row.revision != revision):
            raise DataValidationError("Data telah diubah pengguna lain. Muat ulang sebelum menyimpan.")
        return row

    @staticmethod
    def _audit(session, actor, action, kind, row, fields=None):
        AuditRepository(session).append(action, kind, row.id, actor_id=actor.id,
            details={"changed_fields": fields} if fields else None)

    @staticmethod
    def _groups(session):
        return tuple(group_data(session, row) for row in session.scalars(
            select(MemberGroup).order_by(func.lower(MemberGroup.group_name), MemberGroup.id)))

    def groups(self, token):
        return self._run(token, "groups", lambda s, u: self._groups(s))

    def save_group(self, token, name, description="", *, group_id=None, revision=None):
        def operation(session, actor):
            title = clean(name, 160, mandatory=True)
            detail = clean(description, 2000)
            if group_id is None:
                row = GroupRepository(session).create(title, detail or None, actor_id=actor.id)
            else:
                row = self._row(session, MemberGroup, group_id, identifier(revision))
                if (row.group_name, row.description or "") != (title, detail):
                    row.group_name, row.description = title, detail or None
                    row.revision += 1
                    self._audit(session, actor, "group.updated", "group", row, ["group_name", "description"])
            return group_data(session, row)
        return self._run(token, "groups", operation)

    def delete_group(self, token, group_id, revision):
        def operation(session, actor):
            row = self._row(session, MemberGroup, group_id, identifier(revision))
            if session.scalar(select(Member.id).where(Member.group_id == row.id).limit(1)) is not None or \
               session.scalar(select(Attendance.id).where(Attendance.group_id == row.id).limit(1)) is not None:
                raise DataValidationError("Grup masih digunakan anggota atau riwayat kehadiran dan tidak dapat dihapus.")
            self._audit(session, actor, "group.deleted", "group", row)
            session.delete(row)
        return self._run(token, "groups", operation)

    @staticmethod
    def _shifts(session):
        return tuple(shift_data(row) for row in session.scalars(select(Shift).order_by(Shift.shift_name, Shift.id)))

    def shifts(self, token):
        return self._run(token, "shifts", lambda s, u: self._shifts(s))

    def save_shift(self, token, name, start, end, grace, *, shift_id=None, revision=None):
        def operation(session, actor):
            title, begin, finish, minutes = validate_shift(name, start, end, grace)
            duplicate = session.scalar(select(Shift.id).where(func.lower(Shift.shift_name) == title.lower(),
                                      Shift.id != shift_id if shift_id is not None else True).limit(1))
            if duplicate is not None:
                raise DataValidationError("Nama shift sudah digunakan.")
            if shift_id is None:
                row = ShiftRepository(session).create(title, begin, finish, minutes, actor_id=actor.id)
            else:
                row = self._row(session, Shift, shift_id, identifier(revision))
                schedule_changed = (row.start_time, row.end_time, row.grace_minutes) != (begin, finish, minutes)
                if schedule_changed and self._shift_referenced(session, row.id):
                    raise DataValidationError("Jadwal shift sudah direferensikan. Buat shift baru agar riwayat tetap akurat.")
                if (row.shift_name, row.start_time, row.end_time, row.grace_minutes) != (title, begin, finish, minutes):
                    row.shift_name, row.start_time, row.end_time, row.grace_minutes = title, begin, finish, minutes
                    row.revision += 1
                    self._audit(session, actor, "shift.updated", "shift", row,
                                ["shift_name", "start_time", "end_time", "grace_minutes"])
            return shift_data(row)
        return self._run(token, "shifts", operation)

    @staticmethod
    def _shift_referenced(session, shift_id):
        return (session.scalar(select(ShiftAssignment.id).where(ShiftAssignment.shift_id == shift_id).limit(1)) is not None
            or session.scalar(select(Attendance.id).where(Attendance.shift_id == shift_id).limit(1)) is not None)

    def delete_shift(self, token, shift_id, revision):
        def operation(session, actor):
            row = self._row(session, Shift, shift_id, identifier(revision))
            if self._shift_referenced(session, row.id):
                raise DataValidationError("Shift masih digunakan penugasan atau riwayat dan tidak dapat dihapus.")
            self._audit(session, actor, "shift.deleted", "shift", row)
            session.delete(row)
        return self._run(token, "shifts", operation)

    def members(self, token, *, search="", group_id=None, active=True, offset=0, limit=10):
        def operation(session, actor):
            if type(offset) is not int or offset < 0 or type(limit) is not int or limit not in {10, 25, 50}:
                raise DataValidationError("Pagination tidak valid.")
            if active is not None and type(active) is not bool:
                raise DataValidationError("Filter status tidak valid.")
            if group_id is not None:
                identifier(group_id)
            page_offset = offset
            items, total = MemberRepository(session).list(search=clean(search, 200), group_id=group_id,
                                                         active=active, offset=page_offset, limit=limit)
            if total and page_offset >= total:
                page_offset = ((total - 1) // limit) * limit
                items, total = MemberRepository(session).list(search=clean(search, 200), group_id=group_id,
                                                             active=active, offset=page_offset, limit=limit)
            if not total:
                page_offset = 0
            return MemberPage(tuple(member_data(session, row) for row in items), total, page_offset, limit,
                self._groups(session),self.photos.cleanup_orphans(session)>0)
        return self._run(token, "members", operation)

    def member(self, token, member_id):
        def operation(session, actor):
            row = self._row(session, Member, member_id)
            assignments = tuple(AssignmentData(a.id, a.shift_id, name, a.starts_on, a.ends_on)
                for a, name in session.execute(select(ShiftAssignment, Shift.shift_name).join(
                    Shift, Shift.id == ShiftAssignment.shift_id).where(ShiftAssignment.member_id == row.id)
                    .order_by(ShiftAssignment.starts_on.desc(), ShiftAssignment.id.desc())))
            count = session.scalar(select(func.count()).select_from(Attendance).where(Attendance.member_id == row.id))
            history = tuple(HistoryData(a.attendance_time, a.attendance_type.value, a.status.value,
                    a.work_date, group, shift, a.is_early_leave, a.is_automatic)
                for a, group, shift in session.execute(select(Attendance, MemberGroup.group_name, Shift.shift_name)
                    .join(MemberGroup, MemberGroup.id == Attendance.group_id).join(Shift, Shift.id == Attendance.shift_id)
                    .where(Attendance.member_id == row.id).order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(50)))
            can_assign = actor.role.value in {"SUPER_ADMIN", "ADMIN"}
            return MemberDetail(member_data(session, row), assignments, history, count,
                                self._shifts(session) if can_assign else (), can_assign,
                                session.scalar(select(FaceEmbedding.id).where(FaceEmbedding.member_id==row.id,
                                    FaceEmbedding.is_active.is_(True)).limit(1)) is not None)
        return self._run(token, "members", operation)

    def update_member(self, token, member_id, revision, code, name, group_id, *, email="", phone="", position="", photo_source=None):
        imported = []
        def operation(session, actor):
            row = self._row(session, Member, member_id, identifier(revision))
            if not row.is_active and photo_source:
                raise DataValidationError('Anggota nonaktif tidak dapat diberi foto baru. Kebijakan retensi menghapus biometrik saat dinonaktifkan.')
            fields = validate_member(code, name, group_id, email, phone, position)
            self._row(session, MemberGroup, fields["group_id"])
            changes = []
            for key, value in fields.items():
                if key in {"email", "phone", "position"}:
                    value = value or None
                if getattr(row, key) != value:
                    setattr(row, key, value)
                    changes.append(key)
            if photo_source:
                replacement = self.photos.import_photo(photo_source)
                imported.append(replacement)
                row.photo_path = replacement
                changes.append("photo_path")
            if not row.photo_path:
                raise DataValidationError("Foto anggota wajib tersedia.")
            if changes:
                row.revision += 1
                self._audit(session, actor, "member.updated", "member", row, changes)
            return member_data(session, row)
        try:
            return self._run(token, "members", operation)
        except Exception:
            for path in imported:
                self.photos.discard_uncommitted(path)
            raise

    def deactivate_member(self, token, member_id, revision):
        obsolete=[]
        def operation(session, actor):
            row = self._row(session, Member, member_id, identifier(revision))
            if row.is_active:
                obsolete.append(row.photo_path)
                row.photo_path='resources/samples/profile-removed.svg'
                for embedding in session.scalars(select(FaceEmbedding).where(FaceEmbedding.member_id==row.id)):
                    session.delete(embedding)
                AuditRepository(session).append('member.biometrics_deleted','member',row.id,actor_id=actor.id,
                    details={'changed_fields':['photo_path','embedding']})
                MemberRepository(session).deactivate(row.id, actor_id=actor.id)
                row.revision += 1
            return member_data(session, row)
        result=self._run(token, "members", operation)
        try:
            pending=self.cleanup_biometric_photos(token)>0
        except Exception:
            pending=bool(obsolete)
        return replace(result,cleanup_pending=pending)

    def cleanup_biometric_photos(self, token):
        return self._run(token,'members',lambda session,actor:self.photos.cleanup_orphans(session))

    def assign_shift(self, token, member_id, revision, shift_id, starts, ends=None):
        def operation(session, actor):
            member = self._row(session, Member, member_id, identifier(revision))
            self._row(session, Shift, shift_id)
            if not member.is_active:
                raise DataValidationError("Anggota nonaktif tidak dapat menerima penugasan baru.")
            if type(starts) is not date or (ends is not None and type(ends) is not date) or (ends is not None and ends < starts):
                raise DataValidationError("Rentang tanggal penugasan tidak valid.")
            overlap = select(ShiftAssignment.id).where(ShiftAssignment.member_id == member.id,
                or_(ShiftAssignment.ends_on.is_(None), ShiftAssignment.ends_on >= starts))
            if ends is not None:
                overlap = overlap.where(ShiftAssignment.starts_on <= ends)
            if session.scalar(overlap.limit(1)) is not None:
                raise DataValidationError("Tanggal penugasan bertumpang tindih. Akhiri penugasan lama terlebih dahulu.")
            row = ShiftRepository(session).assign(member.id, shift_id, starts, ends)
            member.revision += 1
            self._audit(session, actor, "schedule.created", "schedule", row, ["member_id", "shift_id", "starts_on", "ends_on"])
            return row.id
        return self._run(token, "shifts", operation)

    def end_assignment(self, token, member_id, revision, assignment_id, ends):
        def operation(session, actor):
            member = self._row(session, Member, member_id, identifier(revision))
            row = self._row(session, ShiftAssignment, assignment_id)
            if row.member_id != member.id or type(ends) is not date or ends < row.starts_on:
                raise DataValidationError("Tanggal akhir penugasan tidak valid.")
            latest = session.scalar(select(func.max(Attendance.work_date)).where(
                Attendance.member_id == member.id, Attendance.shift_id == row.shift_id,
                Attendance.work_date >= row.starts_on,
                Attendance.work_date <= row.ends_on if row.ends_on else True))
            if latest and ends < latest:
                raise DataValidationError("Tanggal akhir tidak boleh mengeluarkan riwayat kehadiran yang sudah tercatat.")
            if row.ends_on is not None and ends > row.ends_on:
                raise DataValidationError("Tanggal akhir hanya dapat dipersingkat; buat penugasan baru untuk perpanjangan.")
            if ends != row.ends_on:
                row.ends_on = ends
                member.revision += 1
                self._audit(session, actor, "schedule.ended", "schedule", row, ["ends_on"])
        return self._run(token, "shifts", operation)

    def register_member(self, token, **fields):
        def operation(session, actor):
            raise DataValidationError("Registrasi memerlukan hasil capture lima sudut yang sah. Gunakan alur capture anggota.")
        return self._run(token, "members", operation)

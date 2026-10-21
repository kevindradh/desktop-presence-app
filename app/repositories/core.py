"""ORM-only persistence. Callers own transactions; UI authorization comes in Stage 4."""
from dataclasses import dataclass
from datetime import datetime
import math
import re

from sqlalchemy import func, or_, select

from app.models.entities import (Attendance, AttendanceType, AuditLog, Device,
                                FaceAngle, FaceEmbedding, Member, MemberGroup,
                                Role, Setting, Shift, ShiftAssignment, User)
from app.services.database import DataValidationError
from app.settings.defaults import validate_setting


def required(value, maximum=200):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise DataValidationError("Field wajib kosong atau melebihi panjang yang diizinkan.")
    return value.strip()


class Repository:
    def __init__(self, session):
        self.session = session

    def add(self, entity):
        self.session.add(entity)
        self.session.flush()
        return entity


class AuditRepository(Repository):
    def append(self, action, entity_type, entity_id=None, *, actor_id=None, details=None):
        if not isinstance(action, str) or not re.fullmatch(r"[a-z][a-z0-9_.]{0,79}", action):
            raise DataValidationError("Kode audit tidak valid.")
        if entity_type not in {"member", "group", "shift", "device", "attendance", "user",
                               "setting", "system", "location", "schedule", "leave", "calendar"}:
            raise DataValidationError("Jenis entitas audit tidak valid.")
        details = dict(details or {})
        if set(details) - {"changed_fields", "record_count", "setting_key", "old_value",
                           "new_value", "event_type"}:
            raise DataValidationError("Detail audit mengandung field yang tidak diizinkan.")
        if "changed_fields" in details:
            fields = details["changed_fields"]
            if not isinstance(fields, list) or len(fields) > 20 or any(
                not isinstance(f, str) or not re.fullmatch(r"[a-z_]{1,64}", f) for f in fields):
                raise DataValidationError("Nama field audit tidak valid.")
        if "record_count" in details and (type(details["record_count"]) is not int
                                          or not 0 <= details["record_count"] <= 1_000_000):
            raise DataValidationError("Jumlah record audit tidak valid.")
        if {"old_value", "new_value"} & set(details) and "setting_key" not in details:
            raise DataValidationError("Nilai audit memerlukan key pengaturan.")
        if "setting_key" in details:
            from app.settings.defaults import DEFAULT_SETTINGS
            key = details["setting_key"]
            if key not in DEFAULT_SETTINGS:
                raise DataValidationError("Key audit pengaturan tidak dikenal.")
            for field in ("old_value", "new_value"):
                if field in details and details[field] is not None:
                    validate_setting(key, details[field])
        if "event_type" in details:
            try:
                details["event_type"] = AttendanceType(details["event_type"]).value
            except (ValueError, TypeError):
                raise DataValidationError("Jenis event audit tidak valid.") from None
        return self.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type,
                                 entity_id=entity_id, details=details))

    def recent(self, *, action=None, limit=100):
        if not 1 <= limit <= 200:
            raise DataValidationError("Batas hasil audit harus 1 sampai 200.")
        query = select(AuditLog)
        if action:
            query = query.where(AuditLog.action == action)
        return list(self.session.scalars(query.order_by(AuditLog.id.desc()).limit(limit)))


class GroupRepository(Repository):
    def create(self, name, description=None, *, actor_id=None):
        group = self.add(MemberGroup(group_name=required(name, 160), description=description))
        AuditRepository(self.session).append("group.created", "group", group.id, actor_id=actor_id)
        return group

    def all(self):
        return list(self.session.scalars(select(MemberGroup).order_by(MemberGroup.group_name)))


class MemberRepository(Repository):
    def create(self, member_code, full_name, group_id, photo_path, *, actor_id=None, **optional):
        if set(optional) - {"email", "phone", "position"}:
            raise DataValidationError("Field anggota tidak dikenal.")
        member = self.add(Member(member_code=required(member_code, 64),
                                 full_name=required(full_name), group_id=group_id,
                                 photo_path=required(photo_path, 4096), **optional))
        AuditRepository(self.session).append("member.created", "member", member.id, actor_id=actor_id)
        return member

    def get(self, member_id):
        member = self.session.get(Member, member_id)
        if member is None:
            raise DataValidationError("Anggota tidak ditemukan.")
        return member

    def list(self, *, search="", group_id=None, active=True, offset=0, limit=50):
        if offset < 0 or not 1 <= limit <= 200:
            raise DataValidationError("Pagination tidak valid.")
        filters = []
        if search:
            filters.append(or_(Member.full_name.icontains(search, autoescape=True),
                               Member.member_code.icontains(search, autoescape=True)))
        if group_id is not None:
            filters.append(Member.group_id == group_id)
        if active is not None:
            filters.append(Member.is_active.is_(active))
        count = self.session.scalar(select(func.count()).select_from(Member).where(*filters))
        items = list(self.session.scalars(select(Member).where(*filters).order_by(Member.id)
                                         .offset(offset).limit(limit)))
        return items, count

    def deactivate(self, member_id, *, actor_id=None):
        member = self.get(member_id)
        if member.is_active:
            member.is_active = False
            self.session.flush()
            AuditRepository(self.session).append("member.deactivated", "member", member.id,
                actor_id=actor_id, details={"changed_fields": ["is_active"]})
        return member


def normalized_vector(vector):
    try:
        if len(vector) != 512:
            raise ValueError
        values = [float(v) for v in vector]
        if not all(math.isfinite(v) for v in values):
            raise ValueError
        norm = math.hypot(*values)
        if not math.isfinite(norm) or norm == 0:
            raise ValueError
        return [v / norm for v in values]
    except (TypeError, ValueError, OverflowError):
        raise DataValidationError("Embedding harus 512 angka finite dan bukan vektor nol.") from None


@dataclass(frozen=True)
class FaceMatch:
    member_id: int
    similarity: float


class EmbeddingRepository(Repository):
    def create(self, member_id, vector, angle, model_version):
        member = MemberRepository(self.session).get(member_id)
        if not member.is_active:
            raise DataValidationError("Anggota tidak aktif.")
        try:
            angle = FaceAngle(angle)
        except (ValueError, TypeError):
            raise DataValidationError("Sudut wajah tidak valid.") from None
        return self.add(FaceEmbedding(member_id=member_id, embedding=normalized_vector(vector),
                        angle=angle, model_version=required(model_version, 120)))

    def nearest(self, vector, *, model_version, limit=5):
        if not 1 <= limit <= 100:
            raise DataValidationError("Batas hasil pencarian wajah tidak valid.")
        distance = FaceEmbedding.embedding.cosine_distance(normalized_vector(vector))
        # Group by member so five enrolled angles do not crowd out other identities.
        best = func.min(distance)
        query = (select(Member.id, best.label("distance"))
                 .join(FaceEmbedding, FaceEmbedding.member_id == Member.id)
                 .where(Member.is_active.is_(True), FaceEmbedding.is_active.is_(True),
                        FaceEmbedding.model_version == model_version)
                 .group_by(Member.id).order_by(best, Member.id).limit(limit))
        return [FaceMatch(row.id, max(-1.0, min(1.0, 1.0 - row.distance)))
                for row in self.session.execute(query)]


class ShiftRepository(Repository):
    def create(self, name, start, end, grace_minutes=0, *, actor_id=None):
        shift = self.add(Shift(shift_name=required(name, 120), start_time=start,
                               end_time=end, grace_minutes=grace_minutes))
        AuditRepository(self.session).append("shift.created", "shift", shift.id, actor_id=actor_id)
        return shift

    def assign(self, member_id, shift_id, starts_on, ends_on=None):
        return self.add(ShiftAssignment(member_id=member_id, shift_id=shift_id,
                                        starts_on=starts_on, ends_on=ends_on))


class DeviceRepository(Repository):
    def create(self, name, device_type, location_id, *, resolution="1280x720", fps=30):
        # Credential-bearing RTSP storage is deliberately deferred to Stage 6.
        device = self.add(Device(device_name=required(name, 160), device_type=device_type,
                                 location_id=location_id, resolution=resolution, fps=fps))
        AuditRepository(self.session).append("device.created", "device", device.id)
        return device


class UserRepository(Repository):
    def by_username(self, username):
        return self.session.scalar(select(User).where(
            func.lower(User.username) == func.lower(username.strip())))

    def create_with_hash(self, username, fullname, password_hash, role, *, actor_id=None):
        if not isinstance(password_hash, str) or not re.fullmatch(r"\$2[aby]\$\d{2}\$.{53}", password_hash):
            raise DataValidationError("Hash password tidak valid.")
        user = self.add(User(username=required(username, 80), fullname=required(fullname),
                             password_hash=password_hash, role=role))
        AuditRepository(self.session).append("user.created", "user", user.id, actor_id=actor_id,
                                             details={"changed_fields": ["username", "fullname", "role"]})
        return user


class SettingsRepository(Repository):
    def get(self, key):
        return self.session.scalar(select(Setting.setting_value).where(Setting.setting_key == key))

    def set(self, key, value, *, actor_id=None):
        validate_setting(key, value)
        row = self.session.scalar(select(Setting).where(Setting.setting_key == key).with_for_update())
        before = row.setting_value if row else None
        if row is None:
            row = self.add(Setting(setting_key=key, setting_value=value))
        elif before == value:
            return row
        else:
            row.setting_value = value
            self.session.flush()
        AuditRepository(self.session).append("setting.changed", "setting", row.id, actor_id=actor_id,
            details={"setting_key": key, "old_value": before, "new_value": value})
        return row


class AttendanceRepository(Repository):
    def record(self, *, member_id, device_id, shift_id, event_type, timestamp,
               work_date, status, is_early_leave=False, is_automatic=False):
        if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
            raise DataValidationError("Waktu absensi harus menyertakan zona waktu.")
        member = MemberRepository(self.session).get(member_id)
        if not member.is_active:
            raise DataValidationError("Anggota tidak aktif.")
        entry = self.add(Attendance(member_id=member_id, device_id=device_id, shift_id=shift_id,
                    attendance_type=event_type, attendance_time=timestamp, work_date=work_date,
                    status=status, group_id=member.group_id, is_early_leave=is_early_leave,
                    is_automatic=is_automatic))
        AuditRepository(self.session).append("attendance.recorded", "attendance", entry.id,
                                             details={"event_type": event_type})
        return entry

    def history(self, member_id, limit=100):
        if not 1 <= limit <= 500:
            raise DataValidationError("Batas riwayat tidak valid.")
        return list(self.session.scalars(select(Attendance).where(Attendance.member_id == member_id)
                    .order_by(Attendance.attendance_time.desc(), Attendance.id.desc()).limit(limit)))

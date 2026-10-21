"""Persistence schema. Authentication policy belongs to services/auth.py."""
from datetime import date, datetime, time
import enum

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Date, DateTime, Enum,
                        ForeignKey, Identity, Index, Integer, MetaData, String, Text,
                        Time, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


class Role(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class AttendanceType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    BREAK_OUT = "BREAK_OUT"
    BREAK_IN = "BREAK_IN"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    LATE = "LATE"


class DeviceType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    USB = "USB"
    RTSP = "RTSP"


class FaceAngle(str, enum.Enum):
    FRONT = "FRONT"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP = "UP"
    DOWN = "DOWN"


def enum_column(kind, name):
    return Enum(kind, name=name, native_enum=False, create_constraint=True,
                validate_strings=True, values_callable=lambda e: [item.value for item in e])


class Identified:
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)


class Created:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Updated(Created):
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                server_default=func.now(), onupdate=func.now())


class Location(Identified, Updated, Base):
    __tablename__ = "locations"
    location_code: Mapped[str] = mapped_column(String(40), unique=True)
    location_name: Mapped[str] = mapped_column(String(160))
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Jakarta")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (CheckConstraint("length(trim(location_code)) > 0", name="code_not_empty"),)


class MemberGroup(Identified, Created, Base):
    __tablename__ = "member_groups"
    group_name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    members: Mapped[list["Member"]] = relationship(back_populates="group", passive_deletes="all")
    __table_args__ = (Index("uq_member_groups_name_ci", func.lower(group_name), unique=True),
                      CheckConstraint("length(trim(group_name)) > 0", name="name_not_empty"))


class Member(Identified, Updated, Base):
    __tablename__ = "members"
    member_code: Mapped[str] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(200))
    group_id: Mapped[int] = mapped_column(ForeignKey("member_groups.id", ondelete="RESTRICT"), index=True)
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(40))
    position: Mapped[str | None] = mapped_column(String(160))
    photo_path: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    group: Mapped[MemberGroup] = relationship(back_populates="members")
    embeddings: Mapped[list["FaceEmbedding"]] = relationship(back_populates="member", passive_deletes="all")
    __table_args__ = (
        Index("uq_members_code_ci", func.lower(member_code), unique=True),
        CheckConstraint("length(trim(member_code)) > 0", name="code_not_empty"),
        CheckConstraint("length(trim(full_name)) > 0", name="name_not_empty"),
        CheckConstraint("length(trim(photo_path)) > 0", name="photo_not_empty"),
    )


class FaceEmbedding(Identified, Created, Base):
    __tablename__ = "face_embeddings"
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="RESTRICT"), index=True)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(512))
    angle: Mapped[FaceAngle] = mapped_column(enum_column(FaceAngle, "face_angle"))
    model_version: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    member: Mapped[Member] = relationship(back_populates="embeddings")
    __table_args__ = (CheckConstraint("length(trim(model_version)) > 0", name="model_not_empty"),)


class Shift(Identified, Created, Base):
    __tablename__ = "shifts"
    shift_name: Mapped[str] = mapped_column(String(120), unique=True)
    start_time: Mapped[time] = mapped_column(Time(timezone=False))
    end_time: Mapped[time] = mapped_column(Time(timezone=False))
    grace_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    __table_args__ = (CheckConstraint("grace_minutes >= 0 AND grace_minutes < 1440", name="grace_range"),
                      CheckConstraint("start_time <> end_time", name="nonzero_duration"),
                      CheckConstraint("length(trim(shift_name)) > 0", name="name_not_empty"))


class ShiftAssignment(Identified, Created, Base):
    __tablename__ = "shift_assignments"
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="RESTRICT"), index=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id", ondelete="RESTRICT"), index=True)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (UniqueConstraint("member_id", "starts_on"),
                      CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="date_range"))


class MemberLeave(Identified, Created, Base):
    __tablename__ = "member_leaves"
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="RESTRICT"), index=True)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    leave_type: Mapped[str] = mapped_column(String(40), default="LEAVE")
    __table_args__ = (CheckConstraint("ends_on >= starts_on", name="date_range"),)


class CalendarDay(Identified, Created, Base):
    __tablename__ = "calendar_days"
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"))
    calendar_date: Mapped[date] = mapped_column(Date)
    is_workday: Mapped[bool] = mapped_column(Boolean)
    label: Mapped[str] = mapped_column(String(160))
    __table_args__ = (UniqueConstraint("location_id", "calendar_date"),)


class Device(Identified, Created, Base):
    __tablename__ = "devices"
    device_name: Mapped[str] = mapped_column(String(160), unique=True)
    device_type: Mapped[DeviceType] = mapped_column(enum_column(DeviceType, "device_type"))
    rtsp_url: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(String(32), default="1280x720")
    fps: Mapped[int] = mapped_column(Integer, default=30, server_default="30")
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"), index=True)
    camera_index: Mapped[int | None] = mapped_column(Integer().evaluates_none(), default=0, server_default="0")
    secret_ref: Mapped[str | None] = mapped_column(String(64), unique=True)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    __table_args__ = (CheckConstraint("fps > 0 AND fps <= 240", name="fps_range"),
                      CheckConstraint("length(trim(device_name)) > 0", name="name_not_empty"))


class User(Identified, Created, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(128))
    fullname: Mapped[str] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(enum_column(Role, "user_role"))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # Retained for existing backup/schema compatibility; password changes are voluntary.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("uq_users_username_ci", func.lower(username), unique=True),
                      CheckConstraint("length(trim(username)) > 0", name="username_not_empty"),
                      CheckConstraint("length(trim(fullname)) > 0", name="name_not_empty"),
                      CheckConstraint("length(password_hash) = 60 AND substring(password_hash from 1 for 4) "
                                      "IN ('$2a$', '$2b$', '$2y$')", name="bcrypt_hash_format"))


class AuthSession(Identified, Created, Base):
    __tablename__ = "auth_sessions"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    is_remember: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class Setting(Identified, Updated, Base):
    __tablename__ = "settings"
    setting_key: Mapped[str] = mapped_column(String(80), unique=True)
    setting_value: Mapped[object] = mapped_column(JSONB(none_as_null=True), nullable=False)


class Attendance(Identified, Created, Base):
    __tablename__ = "attendance"
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="RESTRICT"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="RESTRICT"))
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id", ondelete="RESTRICT"), index=True)
    attendance_type: Mapped[AttendanceType] = mapped_column(enum_column(AttendanceType, "attendance_type"))
    attendance_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[AttendanceStatus] = mapped_column(enum_column(AttendanceStatus, "attendance_status"))
    work_date: Mapped[date] = mapped_column(Date, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("member_groups.id", ondelete="RESTRICT"))
    is_early_leave: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


Index("uq_attendance_single_in_out", Attendance.member_id, Attendance.shift_id,
      Attendance.work_date, Attendance.attendance_type, unique=True,
      postgresql_where=Attendance.attendance_type.in_([AttendanceType.IN, AttendanceType.OUT]))


class AuditLog(Identified, Created, Base):
    __tablename__ = "audit_logs"
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (CheckConstraint("length(trim(action)) > 0", name="action_not_empty"),)

"""Authorized, atomic settings edits and immutable configuration snapshots."""
from dataclasses import replace
import hashlib
import json

from sqlalchemy import select, update

from app.models.entities import Attendance, Device, Location, Setting
from app.repositories.core import AttendanceRepository, SettingsRepository
from app.services.database import DataValidationError
from app.settings.defaults import OPERATIONAL_TIMEZONE, validate_setting


EDITABLE = (
    'similarity_threshold', 'max_face_size', 'recognition_timeout',
    'anti_spoof_enabled', 'anti_spoof_threshold', 'duplicate_window',
    'check_in_start', 'auto_checkout',
)


def read_values(session, *, lock=False):
    return read_policy(session, lock=lock)[0]


def read_policy(session, *, lock=False):
    statement = select(Setting).where(Setting.setting_key.in_(EDITABLE)).order_by(Setting.setting_key)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    rows = list(session.scalars(statement))
    values = {row.setting_key: row.setting_value for row in rows}
    if set(values) != set(EDITABLE):
        raise DataValidationError('Pengaturan belum lengkap. Jalankan pemeriksaan dan seed database.')
    for key, value in values.items():
        validate_setting(key, value)
    revision = hashlib.sha256(json.dumps([(row.setting_key, row.setting_value,
        row.updated_at.isoformat()) for row in rows], sort_keys=True).encode()).hexdigest()
    return values, revision


def configured(config, values):
    """Database overrides operational defaults, never connection credentials."""
    for key in EDITABLE:
        validate_setting(key, values[key])
    return replace(config, similarity_threshold=values['similarity_threshold'],
        max_face_size=values['max_face_size'], recognition_timeout=values['recognition_timeout'],
        liveness_enabled=values['anti_spoof_enabled'], liveness_threshold=values['anti_spoof_threshold'],
        duplicate_window=values['duplicate_window'], check_in_start=values['check_in_start'],
        auto_checkout=values['auto_checkout'])


class SettingsService:
    def __init__(self, auth, default_timezone='Asia/Jakarta'):
        self.auth = auth
        self.default_timezone = default_timezone

    def _timezone(self, session):
        saved = SettingsRepository(session).get(OPERATIONAL_TIMEZONE)
        return validate_setting('timezone', self.default_timezone if saved is None else saved)

    def timezone(self):
        with self.auth.database.transaction() as session:
            return self._timezone(session)

    def load(self, token):
        return self.auth._protected(token, 'settings', lambda session, actor:
            dict(read_values(session), timezone=self._timezone(session)))

    def save(self, token, values, expected):
        def operation(session, actor):
            if not isinstance(values, dict) or set(values) != {*EDITABLE, 'timezone'}:
                raise DataValidationError('Daftar pengaturan tidak valid.')
            for key, value in values.items():
                validate_setting(key, value)
            current = dict(read_values(session, lock=True), timezone=self._timezone(session))
            if current != expected:
                raise DataValidationError('Pengaturan telah diubah oleh sesi lain. Muat ulang sebelum menyimpan.')
            repository = SettingsRepository(session)
            zone = values['timezone']
            location = session.scalar(select(Location).where(Location.location_code == 'LOCAL').with_for_update())
            location_changed = location is not None and location.timezone != zone
            if location_changed or zone != current['timezone']:
                if location is None:
                    raise DataValidationError('Lokasi utama belum tersedia. Jalankan seed database.')
                if location_changed:
                    opened = AttendanceRepository.open_checkins().join(Device).where(Device.location_id == location.id)
                    session.execute(update(Attendance).where(
                        Attendance.id.in_(opened.with_only_columns(Attendance.id)),
                        Attendance.timezone_name.is_(None)).values(timezone_name=location.timezone))
                    location.timezone = zone
                repository.set(OPERATIONAL_TIMEZONE, zone, actor_id=actor.id)
            for key in EDITABLE:
                repository.set(key, values[key], actor_id=actor.id)
            return dict(values)
        return self.auth._protected(token, 'settings', operation)

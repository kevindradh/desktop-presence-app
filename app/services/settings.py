"""Authorized, atomic settings edits and immutable configuration snapshots."""
from dataclasses import replace
import hashlib
import json

from sqlalchemy import select

from app.models.entities import Setting
from app.repositories.core import SettingsRepository
from app.services.database import DataValidationError
from app.settings.defaults import validate_setting


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
    def __init__(self, auth):
        self.auth = auth

    def load(self, token):
        return self.auth._protected(token, 'settings', lambda session, actor: read_values(session))

    def save(self, token, values, expected):
        def operation(session, actor):
            if not isinstance(values, dict) or set(values) != set(EDITABLE):
                raise DataValidationError('Daftar pengaturan tidak valid.')
            for key, value in values.items():
                validate_setting(key, value)
            current = read_values(session, lock=True)
            if current != expected:
                raise DataValidationError('Pengaturan telah diubah oleh sesi lain. Muat ulang sebelum menyimpan.')
            repository = SettingsRepository(session)
            for key in EDITABLE:
                repository.set(key, values[key], actor_id=actor.id)
            return dict(values)
        return self.auth._protected(token, 'settings', operation)

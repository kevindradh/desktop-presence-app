"""Settings acceptance against isolated PostgreSQL and the actual recognition boundary."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import hmac
import json
import math
import numpy as np
import pytest
from sqlalchemy import func, select, delete

from ai.contracts import EngineOptions
from ai.enrollment import CapturePacket
from app.models.entities import AuditLog, Role, Setting
from app.services.auth import AuthError, AuthService
from app.services.database import DataValidationError
from app.services.settings import SettingsService, configured
from app.settings.config import load_config
from tests.test_auth import auth, add_role
from tests.test_database import store
from tests.test_enrollment import enrollment, fields
from tests.test_enrollment_capture import packet, analysis

pytestmark = pytest.mark.database


def test_persist_audit_noop_and_new_service_restart(auth, store, tmp_path):
    service, login, _ = auth
    settings = SettingsService(service)
    original = settings.load(login.token)
    values = dict(original, similarity_threshold=.65, anti_spoof_enabled=False,
                  duplicate_window=90, auto_checkout=True)
    assert settings.save(login.token, values, original) == values
    restarted = SettingsService(AuthService(store.db, clock=service.clock))
    assert restarted.load(login.token) == values
    config = configured(load_config(tmp_path, environ={}), values)
    assert EngineOptions.from_config(config).similarity_threshold == .65
    assert not config.liveness_enabled and config.duplicate_window == 90 and config.auto_checkout
    settings.save(login.token, values, values)
    with store.db.transaction() as session:
        rows = list(session.scalars(select(AuditLog).where(AuditLog.action == 'setting.changed')))
        assert len(rows) == 4
        item = next(row for row in rows if row.details['setting_key'] == 'similarity_threshold')
        assert item.details == dict(setting_key='similarity_threshold', old_value=.60, new_value=.65)
        assert item.actor_id == login.principal.id


@pytest.mark.parametrize('role', list(Role))
def test_settings_permissions_rechecked_on_read_write(auth, role):
    service, root, _ = auth
    settings = SettingsService(service)
    values = settings.load(root.token)
    _, login = add_role(service, root, role)
    if role in (Role.SUPER_ADMIN, Role.ADMIN):
        assert settings.load(login.token) == values
        settings.save(login.token, dict(values, similarity_threshold=.65), values)
    else:
        with pytest.raises(AuthError): settings.load(login.token)
        with pytest.raises(AuthError): settings.save(login.token, dict(values, similarity_threshold=.65), values)
    service.logout(login.token)
    with pytest.raises(AuthError): settings.save(login.token, values, values)


@pytest.mark.parametrize('key,value', [
    ('similarity_threshold', float('nan')), ('similarity_threshold', True),
    ('anti_spoof_threshold', 1.01), ('recognition_timeout', 0),
    ('duplicate_window', 1.5), ('duplicate_window', 0),
    ('anti_spoof_enabled', 'false'), ('auto_checkout', 1),
    ('max_face_size', '640'), ('check_in_start', '08:00'),
])
def test_invalid_values_preserve_all_settings_and_audit(auth, store, key, value):
    service, login, _ = auth
    settings = SettingsService(service)
    before = settings.load(login.token)
    values = dict(before, similarity_threshold=.65)
    values[key] = value
    with pytest.raises(DataValidationError): settings.save(login.token, values, before)
    assert settings.load(login.token) == before
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == 'setting.changed')) == 0


def test_conflicting_concurrent_edits_and_missing_rows_fail_closed(auth, store):
    service, login, _ = auth
    settings = SettingsService(service)
    before = settings.load(login.token)
    def save(threshold):
        try:
            settings.save(login.token, dict(before, similarity_threshold=threshold), before)
            return 'saved'
        except DataValidationError:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(save, [.65, .70])) == ['conflict', 'saved']
    with store.db.transaction() as session:
        session.execute(delete(Setting).where(Setting.setting_key == 'auto_checkout'))
    with pytest.raises(DataValidationError, match='belum lengkap'): settings.load(login.token)


def test_failed_later_write_rolls_back_settings_and_audit(auth, store, monkeypatch):
    from app.repositories.core import SettingsRepository
    service, login, _ = auth
    settings = SettingsService(service)
    before = settings.load(login.token)
    original = SettingsRepository.set
    def fail(self, key, value, **kwargs):
        if key == 'auto_checkout': raise DataValidationError('Kegagalan uji sintetis')
        return original(self, key, value, **kwargs)
    monkeypatch.setattr(SettingsRepository, 'set', fail)
    with pytest.raises(DataValidationError):
        settings.save(login.token, dict(before, similarity_threshold=.65, auto_checkout=True), before)
    assert settings.load(login.token) == before
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == 'setting.changed')) == 0


def test_threshold_065_actually_changes_gallery_decision_and_existing_snapshot(enrollment):
    service, login, group = enrollment
    member = service.save(login.token, packet(service, service.begin(login.token)), **fields(group))
    settings = SettingsService(service.auth)
    initial = settings.load(login.token)
    before = service.begin(login.token, member_id=member.id, revision=member.revision, purpose='verification')
    values = settings.save(login.token, dict(initial, similarity_threshold=.65), initial)
    after = service.begin(login.token, member_id=member.id, revision=member.revision, purpose='verification')
    # Cosine .625: accepted under .60, rejected under .65, using the real pgvector query.
    vector = np.array(analysis().embedding, dtype=np.float64)
    orthogonal = np.zeros(512); orthogonal[0] = 1
    orthogonal -= np.dot(orthogonal, vector) * vector
    orthogonal /= np.linalg.norm(orthogonal)
    probe = .625 * vector + math.sqrt(1 - .625**2) * orthogonal
    def payload(binding):
        body = json.dumps(dict(kind='probe', binding=binding, created=service.clock(),
            model_version='synthetic-v1', vector=probe.tolist())).encode()
        return CapturePacket(body, hmac.new(service.key, body, hashlib.sha256).hexdigest())
    assert service.verify(login.token, payload(before)).matched
    result = service.verify(login.token, payload(after))
    assert not result.matched and result.similarity == pytest.approx(.625, abs=1e-5)
    # Returned dictionaries cannot alter the private snapshot.
    binding = service.begin(login.token)
    binding['settings']['similarity_threshold'] = .1
    assert service.flows[binding['nonce']]['settings']['similarity_threshold'] == .65


def test_persisted_liveness_settings_control_actual_engine_gate(auth, tmp_path):
    from tests.test_ai_engine import engine, frame
    settings = SettingsService(auth[0]); token = auth[1].token
    values = settings.load(token)
    for enabled, score, label, expected in (
        (False, .01, 0, 'ready'), (True, .89, 1, 'spoof'),
        (True, .90, 1, 'ready'), (True, .99, 0, 'spoof'),
    ):
        updated = dict(values, anti_spoof_enabled=enabled, anti_spoof_threshold=.90)
        values = settings.save(token, updated, values)
        options = EngineOptions.from_config(configured(load_config(tmp_path, environ={}), values))
        actual = engine(score=score, label=label, options=options)
        result = actual.analyze(frame(), purpose='recognition')
        assert result.status == expected
        assert (result.embedding is not None) == (expected == 'ready')
        assert actual.recognizer.calls == (1 if expected == 'ready' else 0)

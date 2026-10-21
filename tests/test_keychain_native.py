"""Opt-in native Keychain test across separate Python processes, synthetic scope."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import func, select

from app.models.entities import AuthSession
from tests.test_auth import auth
from tests.test_database import store

pytestmark = pytest.mark.database


@pytest.mark.skipif(os.environ.get("STARGATE_TEST_NATIVE_KEYCHAIN") != "1",
                    reason="Native OS credential test is explicitly opt-in")
def test_native_keychain_remember_across_process_restart(auth, store, tmp_path):
    service, login, _ = auth
    # Every subprocess reads configuration locally, never via credential arguments.
    # Namespace by unique schema so no existing remembered account is overwritten.
    code = r'''
from dataclasses import replace
from pathlib import Path
import sys
from app.services.auth import AuthService
from app.services.credential_store import CredentialStore
from app.services.database import Database, create_database_engine
from app.settings.config import load_config
from database.runtime import connection_config
schema, folder, phase = sys.argv[1:]
config = load_config(Path(folder), environ={})
connection = connection_config("test")
config = replace(config, database=replace(connection, name=schema))
credentials = CredentialStore(config)
engine = create_database_engine(connection, schema=schema)
service = AuthService(Database(engine))
try:
    if phase == 'save':
        login = service.login('root', 'Changed-test-2026!')
        grant = service.remember(login.token)
        credentials.set(grant.token)
        service.close_session(login.token)
    elif phase == 'resume':
        token = credentials.get()
        assert token
        login = service.resume(token)
        assert service.authorize(login.token, 'users')
        service.logout(login.token)
    else:
        credentials.clear()
        assert credentials.get() is None
finally:
    engine.dispose()
'''
    root = Path(__file__).resolve().parents[1]
    try:
        for phase in ("save", "resume"):
            result = subprocess.run([sys.executable, "-c", code, store.schema, str(tmp_path), phase],
                cwd=root, capture_output=True, text=True, timeout=45)
            # Do not forward OS exception messages or secret-bearing locals.
            assert result.returncode == 0, f"Native credential phase {phase} failed (details withheld)"
            assert not result.stdout
    finally:
        cleanup = subprocess.run([sys.executable, "-c", code, store.schema, str(tmp_path), "clear"],
            cwd=root, capture_output=True, text=True, timeout=45)
        assert cleanup.returncode == 0, "Native credential cleanup failed"
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(AuthSession).where(
            AuthSession.is_remember.is_(True), AuthSession.revoked.is_(False))) == 0


@pytest.mark.skipif(os.environ.get("STARGATE_TEST_NATIVE_KEYCHAIN") != "1",
                    reason="Native OS credential test is explicitly opt-in")
def test_native_camera_source_restart_and_cleanup(tmp_path):
    from dataclasses import replace
    import uuid
    from app.settings.config import load_config
    from app.services.device_secrets import DeviceSecretStore, DeviceSecretError
    config=load_config(tmp_path,environ={})
    config=replace(config,database=replace(config.database,name="camera-test-"+uuid.uuid4().hex))
    first=DeviceSecretStore(config)
    source="rtsp://synthetic:private@127.0.0.1:9/private?token=hidden"
    reference=first.write(source)
    try:
        second=DeviceSecretStore(config)
        assert second.read(reference)==source
    finally:
        assert first.discard(reference)
    with pytest.raises(DeviceSecretError):
        DeviceSecretStore(config).read(reference)

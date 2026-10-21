from tests.permissions import assert_private_path
from types import SimpleNamespace

import pytest

from app.services.credential_store import CredentialStore, CredentialStoreError
from app.settings.config import load_config


class MemoryKeyring:
    def __init__(self):
        self.entries = {}
    def set_password(self, service, username, password):
        self.entries[service, username] = password
    def get_password(self, service, username):
        return self.entries.get((service, username))
    def delete_password(self, service, username):
        self.entries.pop((service, username), None)


def test_secure_token_roundtrip_marker_contains_no_secret_and_scoped(tmp_path):
    config = load_config(tmp_path, environ={})
    backend = MemoryKeyring()
    store = CredentialStore(config, backend=backend)
    assert store.get() is None
    token = "synthetic-token-never-on-disk"
    store.set(token)
    assert store.get() == token
    assert store.marker.read_bytes() == b""
    assert_private_path(store.marker)
    restarted = CredentialStore(config, backend=backend)
    assert restarted.get() == token
    other = CredentialStore(load_config(tmp_path, environ={"STARGATE_DB_NAME": "other"}), backend=backend)
    assert other.get() is None and other.service != store.service
    store.clear()
    assert not store.marker.exists() and not backend.entries
    store.clear()


def test_unsupported_or_locked_backend_has_no_plaintext_fallback(tmp_path, monkeypatch):
    import keyring
    backend = MemoryKeyring()
    monkeypatch.setattr(keyring, "get_keyring", lambda: backend)
    store = CredentialStore(load_config(tmp_path, environ={}))
    with pytest.raises(CredentialStoreError):
        store.set("secret")
    assert not store.marker.exists()
    class Locked(MemoryKeyring):
        def get_password(self, *args):
            raise RuntimeError("secret backend detail")
        def set_password(self, *args):
            raise RuntimeError("secret backend detail")
    store = CredentialStore(load_config(tmp_path, environ={}), backend=Locked())
    store.marker.parent.mkdir(parents=True, exist_ok=True)
    store.marker.touch()
    with pytest.raises(CredentialStoreError) as error:
        store.get()
    assert "secret" not in str(error.value)
    with pytest.raises(CredentialStoreError):
        store.set("secret")
    store.clear()
    assert not store.marker.exists()

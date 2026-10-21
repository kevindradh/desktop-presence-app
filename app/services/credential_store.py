"""Only native OS credential backends; never fall back to a local token file."""
import hashlib
from pathlib import Path
from app.services.private_files import restrict_path


class CredentialStoreError(ValueError):
    def __init__(self):
        super().__init__("Ingat saya tidak tersedia. Periksa izin penyimpanan aman sistem operasi.")


class CredentialStore:
    def __init__(self, config, *, backend=None):
        db = config.database
        scope = hashlib.sha256(f"{db.host}:{db.port}/{db.name}/{db.user}".encode()).hexdigest()[:24]
        self.service = "StarGate.session." + scope
        self.marker = Path(config.root) / ".local" / ("remember-" + scope)
        self.backend = backend

    def _backend(self):
        if self.backend is not None:
            return self.backend
        import keyring
        backend = keyring.get_keyring()
        if type(backend).__module__ not in {"keyring.backends.macOS", "keyring.backends.Windows"}:
            raise CredentialStoreError()
        return backend

    def get(self):
        if not self.marker.exists():
            return None
        try:
            return self._backend().get_password(self.service, "session")
        except Exception:
            raise CredentialStoreError() from None

    def set(self, token):
        try:
            self._backend().set_password(self.service, "session", token)
            self.marker.parent.mkdir(parents=True, exist_ok=True)
            self.marker.touch(mode=0o600)
            restrict_path(self.marker)
        except Exception:
            # The marker contains no token. If its creation fails, roll back the OS entry.
            try:
                self._backend().delete_password(self.service, "session")
            except Exception:
                pass
            raise CredentialStoreError() from None

    def clear(self):
        if not self.marker.exists():
            return
        try:
            self._backend().delete_password(self.service, "session")
        except Exception:
            # Server-side revocation makes any stale credential unusable.
            pass
        self.marker.unlink(missing_ok=True)

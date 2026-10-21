"""Full RTSP endpoints live in the native OS vault, never in database rows."""
import hashlib
import uuid

from app.services.credential_store import CredentialStore
from app.services.database import DataValidationError


class DeviceSecretError(DataValidationError):
    def __init__(self):
        super().__init__("Sumber RTSP tidak dapat diakses melalui penyimpanan aman. Periksa izin Keychain/Credential Manager.")


class DeviceSecretStore:
    def __init__(self, config, *, backend=None):
        db = config.database
        scope = hashlib.sha256(f"{db.host}:{db.port}/{db.name}/{db.user}".encode()).hexdigest()[:24]
        self.service = "StarGate.camera." + scope
        self.credentials = CredentialStore(config, backend=backend)

    def write(self, source):
        reference = uuid.uuid4().hex
        try:
            self.credentials._backend().set_password(self.service, reference, source)
        except Exception:
            self.discard(reference)
            raise DeviceSecretError() from None
        return reference

    def read(self, reference):
        try:
            source = self.credentials._backend().get_password(self.service, reference)
            if not source:
                raise DeviceSecretError()
            return source
        except Exception:
            raise DeviceSecretError() from None

    def discard(self, reference):
        if not reference:
            return True
        try:
            self.credentials._backend().delete_password(self.service, reference)
            return True
        except Exception:
            return False

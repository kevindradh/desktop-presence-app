"""Authenticated, bounded backup format. Never executes SQL from an archive."""
import base64
from datetime import date, datetime, time
import hashlib
import json
import os
from pathlib import Path
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from app.services.database import DataValidationError
from app.services.private_files import restrict_path

MAGIC = b'STARGATE-BACKUP-1\x00'
MAX_BYTES = 128 * 1024 * 1024
ERROR = 'Cadangan rusak, tidak kompatibel, atau kata sandi tidak sesuai.'


def password_bytes(password):
    if not isinstance(password, str) or not 12 <= len(password.encode('utf8')) <= 256:
        raise DataValidationError('Kata sandi cadangan harus 12 sampai 256 byte UTF-8.')
    return password.encode('utf8')


def key(password, salt):
    return Scrypt(salt=salt, length=32, n=2**17, r=8, p=1).derive(password_bytes(password))


def encode_value(value):
    if isinstance(value, (datetime, date, time)): return value.isoformat()
    if hasattr(value, 'tolist'): return value.tolist()
    return value


def canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'),
                      sort_keys=True, default=encode_value).encode('utf8')


def seal(payload, password):
    raw = canonical(payload)
    if len(raw) > MAX_BYTES - 1024: raise DataValidationError('Cadangan melebihi batas 128 MiB.')
    salt, nonce = os.urandom(16), os.urandom(12)
    return MAGIC + salt + nonce + AESGCM(key(password, salt)).encrypt(nonce, raw, MAGIC)


def unseal(path, password):
    password_bytes(password)
    try:
        with Path(path).open('rb') as file: raw = file.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES or len(raw) < len(MAGIC) + 44 or not raw.startswith(MAGIC):
            raise ValueError
        start = len(MAGIC); salt = raw[start:start+16]; nonce = raw[start+16:start+28]
        plain = AESGCM(key(password, salt)).decrypt(nonce, raw[start+28:], MAGIC)
        def unique(pairs):
            result = {}
            for k, v in pairs:
                if k in result: raise ValueError
                result[k] = v
            return result
        return json.loads(plain, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (OSError, ValueError, TypeError, InvalidTag, RecursionError, UnicodeError):
        raise DataValidationError(ERROR) from None


def publish(path, content):
    """Private complete file, atomic no-overwrite publication, no symlink following."""
    path = Path(path)
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix='.stargate-backup-', dir=path.parent)
        with os.fdopen(fd, 'wb') as file:
            if hasattr(os, 'fchmod'): os.fchmod(file.fileno(), 0o600)
            restrict_path(temporary)
            file.write(content); file.flush(); os.fsync(file.fileno())
        os.link(temporary, path)
    except OSError:
        raise DataValidationError('Cadangan tidak dapat disimpan. Pilih nama baru dan lokasi yang dapat ditulis.') from None
    finally:
        if temporary is not None: Path(temporary).unlink(missing_ok=True)
    return path


def photo_entry(content):
    return {'sha256': hashlib.sha256(content).hexdigest(),
            'data': base64.b64encode(content).decode('ascii')}

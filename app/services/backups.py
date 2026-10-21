"""Local logical data backups and atomic, owner-authorized data restoration.

The archive contains data only, never SQL, pickle, secrets or filesystem commands.
Restore deliberately discards face data and all sessions (approved Stage 13 policy).
"""
import base64
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import math
from pathlib import Path
import re
from threading import Event
import uuid

from sqlalchemy import Date, DateTime, Time, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.entities import Base, Role
from app.repositories.core import AuditRepository
from app.services.auth import AuthError, PERMISSIONS
from app.services.backup_codec import canonical, photo_entry, publish, seal, unseal, ERROR, MAX_BYTES
from app.services.database import DataValidationError
from app.services.tasks import TaskContext, TaskCancelled
from app.settings.defaults import DEFAULT_SETTINGS, validate_setting

TABLES = tuple(Base.metadata.sorted_tables)
RETENTION = timedelta(days=7)
REMOVED_PHOTO = 'resources/samples/profile-removed.svg'


def schema_signature():
    shape = {t.name: {c.name: str(c.type) for c in t.columns} for t in TABLES}
    return hashlib.sha256(canonical(shape)).hexdigest()


def revision(session):
    return session.execute(text('SELECT version_num FROM alembic_version')).scalar_one()


def typed_row(table, row):
    if not isinstance(row, dict) or set(row) != set(table.columns.keys()): raise ValueError
    converted = dict(row)
    for column in table.columns:
        value = row[column.name]
        if value is None:
            if not column.nullable: raise ValueError
        elif isinstance(column.type, DateTime):
            converted[column.name] = datetime.fromisoformat(value)
            if converted[column.name].utcoffset() is None: raise ValueError
        elif isinstance(column.type, Date): converted[column.name] = date.fromisoformat(value)
        elif isinstance(column.type, Time): converted[column.name] = time.fromisoformat(value)
    return converted


class BackupService:
    def __init__(self, auth, root, *, owner=None, config_file=None, resource_root=None):
        self.auth, self.root = auth, Path(root).resolve()
        self.resource_root = Path(resource_root or self.root)
        if owner is None:
            from database.maintenance import restore_engine
            owner = lambda: restore_engine(auth.database.engine, root=self.root, env_file=config_file)
        self.owner = owner
        folder = self.root/'.local/backups'
        if folder.is_dir() and not folder.is_symlink() and folder.resolve() == self.root/'.local/backups':
            try:self.expire_safety_copies(folder)
            except OSError:pass  # Retry on the next maintenance operation.

    def context(self, context):
        return context or TaskContext(Event(), lambda _: None)

    def capture(self, session, context):
        data = {}; photos = {}; total = 0
        for table in TABLES:
            context.checkpoint()
            # A backup must never resurrect remembered or interactive sessions.
            rows = [] if table.name == 'auth_sessions' else [dict(row) for row in
                    session.execute(select(table).order_by(table.c.id).limit(200_001)).mappings()]
            total += len(rows)
            if total > 200_000: raise DataValidationError('Cadangan melampaui batas 200.000 record.')
            if table.name == 'devices':
                for row in rows: row['secret_ref'] = None
            data[table.name] = rows
        for row in data['members']:
            relative = row['photo_path']
            if not relative.startswith('.local/member_photos/'): continue
            if not re.fullmatch(r'\.local/member_photos/[a-f0-9]{32}\.png', relative):
                raise DataValidationError('Lokasi foto profil tidak valid.')
            path = self.root / relative
            if path.is_symlink() or path.resolve().parent != self.root/'.local/member_photos':
                raise DataValidationError('Lokasi foto profil tidak valid.')
            try:
                with path.open('rb') as file: content = file.read(10*1024*1024+1)
            except OSError:
                raise DataValidationError('Foto profil tidak lengkap. Perbaiki aset sebelum mencadangkan.') from None
            if not content or len(content) > 10*1024*1024:
                raise DataValidationError('Ukuran foto profil tidak valid.')
            photos[relative] = photo_entry(content)
            if sum(len(p['data']) for p in photos.values()) > MAX_BYTES//2:
                raise DataValidationError('Aset foto terlalu besar untuk cadangan lokal ini.')
        now = self.auth.clock()
        return {'format': 1, 'schema': schema_signature(), 'revision': revision(session),
                'created_at': now.isoformat(), 'expires_at': (now+RETENTION).isoformat(),
                'restore_policy': 'reenroll', 'tables': data, 'photos': photos,
                'model_manifest_sha256': self.model_checksum()}

    @staticmethod
    def expire_safety_copies(folder):
        cutoff = datetime.now(timezone.utc).timestamp() - RETENTION.total_seconds()
        for path in folder.iterdir():
            if re.fullmatch(r'[a-f0-9]{32}\.sgbackup', path.name) and not path.is_symlink() and path.is_file():
                if path.stat().st_mtime <= cutoff: path.unlink()

    def model_checksum(self):
        path = self.resource_root/'models/manifest.json'
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

    def validate(self, payload, expected_revision):
        try:
            if not isinstance(payload, dict) or set(payload) != {'format','schema','revision','created_at',
                    'expires_at','restore_policy','tables','photos','model_manifest_sha256'}: raise ValueError
            if (payload['format'] != 1 or payload['schema'] != schema_signature()
                    or payload['revision'] != expected_revision or payload['restore_policy'] != 'reenroll'):
                raise ValueError
            created = datetime.fromisoformat(payload['created_at']); expires = datetime.fromisoformat(payload['expires_at'])
            if created.utcoffset() is None or expires.utcoffset() is None or expires-created != RETENTION: raise ValueError
            now = self.auth.clock()
            if created > now+timedelta(minutes=5) or now >= expires:
                raise DataValidationError('Cadangan kedaluwarsa atau waktu tidak sesuai. Retensi maksimal 7 hari.')
            data = payload['tables']; photos = payload['photos']
            if not isinstance(data, dict) or set(data) != {t.name for t in TABLES} or not isinstance(photos, dict): raise ValueError
            total = 0; converted = {}
            for table in TABLES:
                rows = data[table.name]
                if not isinstance(rows, list): raise ValueError
                total += len(rows)
                if total > 200_000: raise ValueError
                converted[table.name] = [typed_row(table, row) for row in rows]
                ids = [row['id'] for row in rows]
                if any(type(value) is not int or not 0 < value < 2**63-1 for value in ids) or len(set(ids)) != len(ids): raise ValueError
            if data['auth_sessions']: raise ValueError
            if not any(u['role'] == Role.SUPER_ADMIN.value and u['is_active'] for u in data['users']): raise ValueError
            for row in data['settings']: validate_setting(row['setting_key'], row['setting_value'])
            if {r['setting_key'] for r in data['settings']} != set(DEFAULT_SETTINGS): raise ValueError
            expected_photos = {r['photo_path'] for r in data['members'] if r['photo_path'].startswith('.local/member_photos/')}
            if set(photos) != expected_photos: raise ValueError
            for name, asset in photos.items():
                if not re.fullmatch(r'\.local/member_photos/[a-f0-9]{32}\.png', name): raise ValueError
                if not isinstance(asset, dict) or set(asset) != {'sha256','data'}: raise ValueError
                content = base64.b64decode(asset['data'], validate=True)
                if not 0 < len(content) <= 10*1024*1024 or hashlib.sha256(content).hexdigest() != asset['sha256']: raise ValueError
            for row in data['face_embeddings']:
                vector = row['embedding']
                if not isinstance(vector, list) or len(vector) != 512 or any(type(v) not in (float,int) or not math.isfinite(v) for v in vector): raise ValueError
            return converted
        except DataValidationError: raise
        except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
            raise DataValidationError(ERROR) from None

    def inspect(self, token, path, password):
        self.auth.authorize(token, 'backup')
        payload = unseal(path, password)
        def operation(session, actor):
            self.validate(payload, revision(session))
            return {'created_at': payload['created_at'], 'expires_at': payload['expires_at'],
                    'records': sum(len(rows) for rows in payload['tables'].values()),
                    'members': len(payload['tables']['members']), 'photos': len(payload['photos']),
                    'embeddings': len(payload['tables']['face_embeddings']),
                    'sha256': hashlib.sha256(canonical(payload)).hexdigest()}
        return self.auth._protected(token, 'backup', operation)

    def backup(self, token, path, password, context=None):
        context = self.context(context)
        self.auth.authorize(token, 'backup')
        saved = None
        def operation(session, actor):
            nonlocal saved
            payload = self.capture(session, context)
            context.progress(40)
            content = seal(payload, password)
            # Verify encryption and schema before publication, preserving cancellation.
            context.checkpoint()
            AuditRepository(session).append('backup.created', 'system', actor_id=actor.id,
                details={'record_count': sum(len(rows) for rows in payload['tables'].values())})
            saved = context.commit(lambda: publish(path, content))
            return {'records': sum(len(rows) for rows in payload['tables'].values()), 'expires_at': payload['expires_at']}
        try:
            result = self.auth._protected(token, 'backup', operation)
            context.progress(100)
            return result
        except BaseException:
            if saved is not None: saved.unlink(missing_ok=True)
            raise

    def restore(self, token, path, password, confirmation, context=None, *, expected_digest=None):
        self.auth.authorize(token, 'backup')
        try:
            return self._restore(token, path, password, confirmation, context, expected_digest=expected_digest)
        except (TaskCancelled, DataValidationError) as error:
            # Independent transaction after rollback. No filenames, error text, passwords or payloads.
            action = 'backup.restore_cancelled' if isinstance(error, TaskCancelled) else 'backup.restore_failed'
            try:
                self.auth._protected(token, 'backup', lambda session, actor:
                    AuditRepository(session).append(action, 'system', actor_id=actor.id))
            except Exception: pass  # The original safe error takes precedence if DB/session is unavailable.
            raise

    def _restore(self, token, path, password, confirmation, context=None, *, expected_digest=None):
        context = self.context(context)
        self.auth.authorize(token, 'backup')
        if confirmation != 'PULIHKAN':
            raise DataValidationError('Ketik PULIHKAN untuk menyetujui penggantian data dan registrasi wajah ulang.')
        payload = unseal(path, password)
        if expected_digest is not None and hashlib.sha256(canonical(payload)).hexdigest() != expected_digest:
            raise DataValidationError('Cadangan berubah. Periksa cadangan kembali.')
        safety = None
        commit_started = False
        try:
            with self.owner() as engine, engine.connect() as connection:
                transaction = connection.begin()
                try:
                    with Session(bind=connection) as session:
                        self.auth._lock(session)
                        actor, error = self.auth._validate(session, token)
                        if error: raise error
                        if 'backup' not in PERMISSIONS[actor.role]: raise AuthError('Anda tidak memiliki izin untuk tindakan ini.')
                        rows = self.validate(payload, revision(session))
                        # Exclude direct SQL writers too; all official writers share the advisory lock.
                        quote = connection.dialect.identifier_preparer.quote
                        names = ', '.join(quote(table.name) for table in TABLES)
                        connection.execute(text('LOCK TABLE '+names+' IN ACCESS EXCLUSIVE MODE'))
                        current = self.capture(session, context)
                        safety_dir = self.root/'.local/backups'
                        if (self.root/'.local').is_symlink() or safety_dir.is_symlink():
                            raise DataValidationError('Direktori cadangan pengaman tidak boleh berupa tautan.')
                        from app.services.private_files import restrict_path
                        safety_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                        restrict_path(safety_dir, directory=True)
                        self.expire_safety_copies(safety_dir)
                        safety = safety_dir/(uuid.uuid4().hex+'.sgbackup')
                        publish(safety, seal(current, password))
                        # Read back the mandatory recovery copy before touching database rows.
                        self.validate(unseal(safety, password), revision(session))
                        context.progress(35); context.checkpoint()
                        for table in reversed(TABLES):
                            session.execute(table.delete())
                        for index, table in enumerate(TABLES):
                            context.checkpoint()
                            values = rows[table.name]
                            if table.name in {'auth_sessions','face_embeddings'}: values = []
                            if table.name == 'members':
                                values = [dict(row, photo_path=REMOVED_PHOTO, revision=row['revision']+1) for row in values]
                            if table.name == 'devices': values = [dict(row, secret_ref=None) for row in values]
                            if values: session.execute(table.insert(), values)
                            # Transactional identity restart; SQL identifiers come solely from ORM metadata.
                            next_id = max((r['id'] for r in values), default=0)+1
                            connection.execute(text(f'ALTER TABLE {quote(table.name)} ALTER COLUMN id RESTART WITH {next_id}'))
                            context.progress(40+int(45*(index+1)/len(TABLES)))
                        AuditRepository(session).append('backup.restored', 'system',
                            details={'record_count': sum(len(v) for k,v in rows.items() if k not in {'face_embeddings','auth_sessions'}),
                                     'changed_fields': ['database','sessions','photo_path','embedding']})
                        session.flush()
                        def commit():
                            nonlocal commit_started
                            commit_started = True
                            transaction.commit()
                        context.commit(commit)
                except BaseException:
                    if transaction.is_active: transaction.rollback()
                    raise
        except (SQLAlchemyError, OSError):
            if commit_started:
                raise DataValidationError('Status commit pemulihan belum dapat dipastikan. Masuk kembali dan periksa data sebelum mencoba ulang; cadangan pengaman tersedia di folder cadangan lokal.') from None
            raise DataValidationError('Pemulihan gagal. Transaksi dibatalkan; data sebelumnya tetap tersedia. Periksa koneksi, izin pemulihan, dan ruang penyimpanan.') from None
        context.progress(100)
        # Face assets are never materialized from the archive. Remove unreferenced managed copies.
        from app.services.member_photos import PhotoStore
        cleanup_pending = 0
        try:
            with self.auth.database.transaction() as session:
                self.auth._lock(session)
                store = PhotoStore(self.root)
                if store.folder.resolve() != self.root/'.local/member_photos':
                    raise DataValidationError('Direktori foto tidak valid.')
                cleanup_pending = store.cleanup_orphans(session)
        except Exception: cleanup_pending = 1
        return {'safety_backup': str(safety), 'reenrollment_required': True, 'cleanup_pending': cleanup_pending}

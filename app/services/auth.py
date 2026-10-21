"""Authentication boundary. Every protected operation rechecks database state.

All auth transactions share the bootstrap advisory lock, including last-admin
checks. Independent SQLAlchemy sessions are created per call/worker thread.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import bcrypt
from sqlalchemy import func, select, update

from app.models.entities import AuthSession, Role, User
from app.repositories.core import AuditRepository, SettingsRepository, UserRepository, required
from app.services.bootstrap_admin import bootstrap_super_admin
from app.services.database import DataValidationError


PERMISSIONS = {
    Role.SUPER_ADMIN: frozenset({"dashboard", "members", "groups", "shifts", "devices",
                               "attendance", "reports", "settings", "users", "diagnostics", "audit", "backup"}),
    Role.ADMIN: frozenset({"dashboard", "members", "groups", "shifts", "devices",
                         "attendance", "reports", "settings", "diagnostics", "audit"}),
    Role.OPERATOR: frozenset({"dashboard", "members", "attendance", "reports", "diagnostics"}),
    Role.VIEWER: frozenset({"reports"}),
}


class AuthError(ValueError):
    pass


@dataclass(frozen=True)
class Principal:
    id: int
    username: str
    fullname: str
    role: Role
    must_change_password: bool
    is_active: bool = True


@dataclass(frozen=True)
class Login:
    principal: Principal
    token: str = field(repr=False)


@dataclass(frozen=True)
class TemporaryPassword:
    value: str = field(repr=False)


def password_hash(password):
    if not isinstance(password, str) or not 12 <= len(password.encode("utf-8")) <= 72:
        raise DataValidationError("Password harus 12 sampai 72 byte UTF-8.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def password_matches(password, encoded):
    if not isinstance(password, str) or not 1 <= len(password.encode("utf-8")) <= 72:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), encoded.encode("ascii"))


def digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def principal(user):
    return Principal(user.id, user.username, user.fullname, user.role,
                     user.must_change_password, user.is_active)


# Precomputed hash for timing parity on unknown/inactive usernames; no usable account.
_DUMMY = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6Ttxz7N99V5sOhTLbc0WQ7Sl5prSi"


class AuthService:
    def __init__(self, database, *, clock=None):
        self.database = database
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _lock(session):
        session.execute(select(func.pg_advisory_xact_lock(734_281_003)))

    @staticmethod
    def _audit(session, action, user=None, actor=None, fields=None):
        AuditRepository(session).append(action, "user", user.id if user else None,
            actor_id=actor.id if actor else None,
            details={"changed_fields": fields} if fields else None)

    @staticmethod
    def _revoke(session, user_id):
        session.execute(update(AuthSession).where(AuthSession.user_id == user_id,
                                                  AuthSession.revoked.is_(False)).values(revoked=True))

    def _issue(self, session, user, remember=False):
        now = self.clock()
        token = secrets.token_urlsafe(32)
        session.add(AuthSession(user_id=user.id, token_hash=digest(token), is_remember=remember,
            last_activity=now, expires_at=now + timedelta(days=30 if remember else 1)))
        return Login(principal(user), token)

    def bootstrap(self, username, fullname, password):
        with self.database.transaction() as session:
            return principal(bootstrap_super_admin(session, username, fullname, password))

    def login(self, username, password):
        error = None
        result = None
        with self.database.transaction() as session:
            self._lock(session)
            user = UserRepository(session).by_username(username.strip() if isinstance(username, str) else "")
            now = self.clock()
            if user is None or not user.is_active:
                password_matches(password, _DUMMY)
                error = AuthError("Username atau password tidak sesuai.")
                self._audit(session, "auth.login_failed")
            elif user.locked_until and now < user.locked_until:
                error = AuthError("Akun terkunci sementara. Tunggu masa penguncian, lalu coba lagi.")
                self._audit(session, "auth.login_locked", user)
            else:
                if user.locked_until:
                    user.failed_attempts, user.locked_until = 0, None
                if not password_matches(password, user.password_hash):
                    user.failed_attempts += 1
                    limit = SettingsRepository(session).get("account_lockout_attempts")
                    minutes = SettingsRepository(session).get("account_lockout_minutes")
                    if user.failed_attempts >= limit:
                        user.locked_until = now + timedelta(minutes=minutes)
                        self._revoke(session, user.id)
                    self._audit(session, "auth.login_failed", user)
                    error = AuthError("Username atau password tidak sesuai.")
                else:
                    user.failed_attempts, user.locked_until, user.last_login = 0, None, now
                    self._audit(session, "auth.login", user, user)
                    result = self._issue(session, user)
        # Failed attempts/audit must commit before an expected rejection is raised.
        if error:
            raise error
        return result

    def _validate(self, session, token, *, remember=False, allow_change=False, touch=False):
        record = session.scalar(select(AuthSession).where(AuthSession.token_hash == digest(token or "")))
        now = self.clock()
        if record is None or record.revoked or record.is_remember != remember:
            return None, AuthError("Sesi berakhir. Silakan masuk kembali.")
        user = session.get(User, record.user_id)
        idle = SettingsRepository(session).get("session_timeout_minutes")
        expired = now >= record.expires_at or (not remember and now >= record.last_activity + timedelta(minutes=idle))
        if expired or not user.is_active or (user.locked_until and now < user.locked_until):
            self._revoke(session, user.id)
            self._audit(session, "auth.session_expired", user, user)
            return None, AuthError("Sesi berakhir. Silakan masuk kembali.")
        if user.must_change_password and not allow_change:
            return None, AuthError("Ganti password awal atau sementara sebelum melanjutkan.")
        if touch:
            record.last_activity = now
        return user, None

    def _protected(self, token, permission, operation, *, allow_change=False, touch=False):
        result = None
        with self.database.transaction() as session:
            self._lock(session)
            user, error = self._validate(session, token, allow_change=allow_change, touch=touch)
            if not error and permission and permission not in PERMISSIONS[user.role]:
                error = AuthError("Akun Anda tidak memiliki izin untuk tindakan ini.")
                self._audit(session, "auth.access_denied", user, user)
            if not error:
                result = operation(session, user)
        if error:
            raise error
        return result

    def authorize(self, token, permission=None, *, touch=False):
        return self._protected(token, permission, lambda s, u: principal(u), touch=touch)

    def inspect(self, token, *, touch=False):
        return self._protected(token, None, lambda s, u: principal(u), allow_change=True, touch=touch)

    def logout(self, token):
        def operation(session, user):
            self._revoke(session, user.id)
            self._audit(session, "auth.logout", user, user)
        return self._protected(token, None, operation, allow_change=True)

    def close_session(self, token):
        # A clean close ends this interactive session but leaves remember credentials.
        with self.database.transaction() as session:
            self._lock(session)
            session.execute(update(AuthSession).where(AuthSession.token_hash == digest(token or ""),
                AuthSession.is_remember.is_(False)).values(revoked=True))

    def remember(self, token):
        def operation(session, user):
            session.execute(update(AuthSession).where(AuthSession.user_id == user.id,
                AuthSession.is_remember.is_(True)).values(revoked=True))
            return self._issue(session, user, remember=True)
        return self._protected(token, None, operation)

    def forget(self, remember_token):
        with self.database.transaction() as session:
            self._lock(session)
            session.execute(update(AuthSession).where(AuthSession.token_hash == digest(remember_token or ""),
                AuthSession.is_remember.is_(True)).values(revoked=True))

    def resume(self, remember_token):
        result = None
        with self.database.transaction() as session:
            self._lock(session)
            user, error = self._validate(session, remember_token, remember=True)
            if not error:
                user.last_login = self.clock()
                self._audit(session, "auth.remember_login", user, user)
                result = self._issue(session, user)
        if error:
            raise error
        return result

    def change_password(self, token, old_password, new_password):
        def operation(session, user):
            if not password_matches(old_password, user.password_hash):
                raise AuthError("Password saat ini tidak sesuai.")
            if old_password == new_password:
                raise DataValidationError("Gunakan password baru yang berbeda.")
            user.password_hash = password_hash(new_password)
            user.must_change_password, user.failed_attempts, user.locked_until = False, 0, None
            self._revoke(session, user.id)
            self._audit(session, "user.password_changed", user, user)
            return self._issue(session, user)
        return self._protected(token, None, operation, allow_change=True)

    def users(self, token):
        return self._protected(token, "users", lambda s, u: [principal(row) for row in
            s.scalars(select(User).order_by(User.username))])

    def create_user(self, token, username, fullname, role, password):
        def operation(session, actor):
            user = UserRepository(session).create_with_hash(username, fullname,
                password_hash(password), Role(role), actor_id=actor.id)
            return principal(user)
        return self._protected(token, "users", operation)

    def update_user(self, token, user_id, username, fullname, role, active):
        def operation(session, actor):
            user = session.get(User, user_id)
            if user is None:
                raise DataValidationError("Pengguna tidak ditemukan.")
            target_role = Role(role)
            if type(active) is not bool:
                raise DataValidationError("Status pengguna tidak valid.")
            if user.id == actor.id and (not active or target_role != Role.SUPER_ADMIN):
                raise DataValidationError("Anda tidak dapat menonaktifkan atau menurunkan peran akun sendiri.")
            if user.is_active and user.role == Role.SUPER_ADMIN and (not active or target_role != Role.SUPER_ADMIN):
                remaining = session.scalar(select(func.count()).select_from(User).where(
                    User.is_active.is_(True), User.role == Role.SUPER_ADMIN, User.id != user.id))
                if not remaining:
                    raise DataValidationError("Super Admin aktif terakhir harus dipertahankan.")
            changed = [name for name, value in {"username": required(username, 80),
                "fullname": required(fullname), "role": target_role, "is_active": active}.items()
                if getattr(user, name) != value]
            for name, value in {"username": required(username, 80), "fullname": required(fullname),
                                "role": target_role, "is_active": active}.items():
                setattr(user, name, value)
            if changed:
                self._revoke(session, user.id)
                self._audit(session, "user.updated" if active else "user.deactivated", user, actor, changed)
            return principal(user)
        return self._protected(token, "users", operation)

    def reset_password(self, token, user_id):
        def operation(session, actor):
            user = session.get(User, user_id)
            if user is None:
                raise DataValidationError("Pengguna tidak ditemukan.")
            if user.id == actor.id:
                raise DataValidationError("Gunakan Ganti password untuk akun sendiri.")
            temporary = secrets.token_urlsafe(18)
            user.password_hash = password_hash(temporary)
            user.must_change_password, user.failed_attempts, user.locked_until = True, 0, None
            self._revoke(session, user.id)
            self._audit(session, "user.password_reset", user, actor)
            return TemporaryPassword(temporary)
        return self._protected(token, "users", operation)

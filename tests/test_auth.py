"""Real PostgreSQL tests: commit on rejection, revocation and permission boundaries."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json

import bcrypt
import pytest
from sqlalchemy import func, select

from app.models.entities import AuthSession, AuditLog, Role, User
from app.services.auth import AuthError, AuthService, PERMISSIONS, digest
from app.services.database import DataConflict, DataValidationError
from database.seed.defaults import seed_defaults
from tests.test_database import store

pytestmark = pytest.mark.database
OLD = "Initial-test-2026!"
NEW = "Changed-test-2026!"


@pytest.fixture
def auth(store):
    now = [datetime(2026, 10, 18, 12, tzinfo=timezone.utc)]
    with store.db.transaction() as session:
        seed_defaults(session)
    service = AuthService(store.db, clock=lambda: now[0])
    service.bootstrap("root", "Pengelola Uji", OLD)
    first = service.login("ROOT", OLD)
    first = service.change_password(first.token, OLD, NEW)
    return service, first, now


def add_role(service, admin, role, username=None):
    username = username or role.value.lower()
    user = service.create_user(admin.token, username, "Akun Uji", role, OLD)
    login = service.login(username, OLD)
    return user, service.change_password(login.token, OLD, NEW)


def test_first_login_and_voluntary_password_change_preserve_hash_security(store):
    with store.db.transaction() as session:
        seed_defaults(session)
    service = AuthService(store.db)
    service.bootstrap("root", "Pengelola", OLD)
    login = service.login("root", OLD)
    assert not login.principal.must_change_password
    assert service.authorize(login.token, "users")
    grant = service.remember(login.token)
    assert service.resume(grant.token)
    with pytest.raises(AuthError, match="saat ini"):
        service.change_password(login.token, "wrong", NEW)
    with pytest.raises(DataValidationError):
        service.change_password(login.token, OLD, OLD)
    with pytest.raises(DataValidationError):
        service.change_password(login.token, OLD, "short")
    updated = service.change_password(login.token, OLD, NEW)
    assert not updated.principal.must_change_password
    assert service.authorize(updated.token, "users").role == Role.SUPER_ADMIN
    with pytest.raises(AuthError):
        service.inspect(login.token)
    with store.db.transaction() as session:
        user = session.scalar(select(User))
        assert user.password_hash != NEW and bcrypt.checkpw(NEW.encode(), user.password_hash.encode())
        hashes = list(session.scalars(select(AuthSession.token_hash)))
        assert digest(updated.token) in hashes and updated.token not in hashes
        audit = json.dumps([row.details for row in session.scalars(select(AuditLog))])
        assert OLD not in audit and NEW not in audit and updated.token not in audit
    assert updated.token not in repr(updated)


def test_failed_logins_commit_lock_and_unlock_at_exact_boundary(auth, store):
    service, admin, now = auth
    remember = service.remember(admin.token)
    for _ in range(5):
        with pytest.raises(AuthError):
            service.login("root", "incorrect")
    with store.db.transaction() as session:
        user = session.scalar(select(User))
        assert user.failed_attempts == 5
        assert user.locked_until == now[0] + timedelta(minutes=15)
        assert session.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "auth.login_failed")) == 5
    with pytest.raises(AuthError, match="terkunci"):
        service.login("root", NEW)
    with pytest.raises(AuthError):
        service.resume(remember.token)
    now[0] += timedelta(minutes=15)
    recovered = service.login("root", NEW)
    assert service.authorize(recovered.token, "dashboard")
    with store.db.transaction() as session:
        assert session.scalar(select(User)).failed_attempts == 0


def test_simultaneous_failures_cannot_lose_attempts(auth, store):
    service, _, _ = auth
    def bad_login(_):
        try:
            service.login("root", "incorrect")
        except AuthError:
            return True
    with ThreadPoolExecutor(max_workers=5) as executor:
        assert all(executor.map(bad_login, range(5)))
    with store.db.transaction() as session:
        assert session.scalar(select(User.failed_attempts)) == 5
        assert session.scalar(select(User.locked_until)) is not None


@pytest.mark.parametrize("role", list(Role))
def test_full_permission_matrix_enforced_at_service(auth, role):
    service, admin, _ = auth
    _, login = add_role(service, admin, role)
    for permission in PERMISSIONS[Role.SUPER_ADMIN]:
        if permission in PERMISSIONS[role]:
            assert service.authorize(login.token, permission).role == role
        else:
            with pytest.raises(AuthError, match="izin"):
                service.authorize(login.token, permission)
    if role != Role.SUPER_ADMIN:
        for action in (
            lambda: service.users(login.token),
            lambda: service.create_user(login.token, "intruder", "Intruder", Role.SUPER_ADMIN, OLD),
            lambda: service.update_user(login.token, admin.principal.id, "root", "Changed", Role.VIEWER, False),
            lambda: service.reset_password(login.token, admin.principal.id),
        ):
            with pytest.raises(AuthError, match="izin"):
                action()


def test_idle_boundary_input_touch_and_remember_restart(auth):
    service, admin, now = auth
    remembered = service.remember(admin.token)
    now[0] += timedelta(minutes=14, seconds=59)
    assert service.inspect(admin.token, touch=True)
    now[0] += timedelta(minutes=14, seconds=59)
    assert service.inspect(admin.token)
    now[0] += timedelta(seconds=1)
    with pytest.raises(AuthError, match="Sesi berakhir"):
        service.inspect(admin.token, touch=True)
    with pytest.raises(AuthError):
        service.resume(remembered.token)
    current = service.login("root", NEW)
    remembered = service.remember(current.token)
    service.close_session(current.token)
    now[0] += timedelta(days=2)
    # New service instance stands for process restart; refresh grant is distinct from idle session.
    restarted = AuthService(service.database, clock=lambda: now[0])
    resumed = restarted.resume(remembered.token)
    assert restarted.authorize(resumed.token, "users")
    with pytest.raises(AuthError):
        restarted.inspect(current.token)
    restarted.logout(resumed.token)
    with pytest.raises(AuthError):
        restarted.resume(remembered.token)


def test_remember_expiry_exactly_30_days_and_forget(auth):
    service, admin, now = auth
    grant = service.remember(admin.token)
    service.close_session(admin.token)
    now[0] += timedelta(days=30)
    with pytest.raises(AuthError):
        service.resume(grant.token)
    login = service.login("root", NEW)
    grant = service.remember(login.token)
    service.forget(grant.token)
    with pytest.raises(AuthError):
        service.resume(grant.token)
    with pytest.raises(AuthError):
        service.authorize(grant.token, "users")
    with pytest.raises(AuthError):
        service.resume(login.token)


def test_user_crud_case_unique_reset_and_revocation(auth, store):
    service, admin, _ = auth
    user, login = add_role(service, admin, Role.OPERATOR)
    grant = service.remember(login.token)
    with pytest.raises(DataConflict):
        service.create_user(admin.token, "OPERATOR", "Duplikat", Role.VIEWER, OLD)
    assert any(row.id == user.id for row in service.users(admin.token))
    changed = service.update_user(admin.token, user.id, "petugas", "Petugas Baru", Role.VIEWER, True)
    assert changed.role == Role.VIEWER
    with pytest.raises(AuthError):
        service.authorize(login.token, "members")
    with pytest.raises(AuthError):
        service.resume(grant.token)
    current = service.login("petugas", NEW)
    temporary = service.reset_password(admin.token, user.id)
    assert temporary.value not in repr(temporary)
    with pytest.raises(AuthError):
        service.inspect(current.token)
    with pytest.raises(AuthError):
        service.login("petugas", NEW)
    reset_login = service.login("petugas", temporary.value)
    assert not reset_login.principal.must_change_password
    assert service.authorize(reset_login.token, "reports")
    final = service.change_password(reset_login.token, temporary.value, "Final-password-2026!")
    assert service.authorize(final.token, "reports")
    service.update_user(admin.token, user.id, "petugas", "Petugas Baru", Role.VIEWER, False)
    with pytest.raises(AuthError):
        service.login("petugas", "Final-password-2026!")
    with pytest.raises(AuthError):
        service.inspect(final.token)
    with store.db.transaction() as session:
        actions = set(session.scalars(select(AuditLog.action)))
        assert {"user.created", "user.updated", "user.deactivated", "user.password_reset", "auth.login"} <= actions
        assert session.get(User, user.id) is not None
        assert temporary.value not in json.dumps([row.details for row in session.scalars(select(AuditLog))])


def test_bootstrap_and_self_admin_protection(auth):
    service, admin, _ = auth
    with pytest.raises(DataValidationError, match="sudah tersedia"):
        service.bootstrap("other", "Other", OLD)
    for role, active in ((Role.VIEWER, True), (Role.SUPER_ADMIN, False)):
        with pytest.raises(DataValidationError):
            service.update_user(admin.token, admin.principal.id, "root", "Root", role, active)
    with pytest.raises(DataValidationError):
        service.reset_password(admin.token, admin.principal.id)
    # A second Super Admin can deactivate another; both cannot demote the last account.
    _, second = add_role(service, admin, Role.SUPER_ADMIN)
    service.update_user(second.token, admin.principal.id, "root", "Root", Role.SUPER_ADMIN, False)
    with pytest.raises(AuthError):
        service.update_user(admin.token, second.principal.id, "other", "Other", Role.VIEWER, False)
    assert service.authorize(second.token, "users")


def test_invalid_tokens_unknown_users_and_inactive_are_denied(auth):
    service, admin, _ = auth
    for token in (None, "", "synthetic-invalid-token"):
        with pytest.raises(AuthError):
            service.users(token)
    for username in ("missing", "' OR 1=1 --", ""):
        with pytest.raises(AuthError, match="Username atau password"):
            service.login(username, OLD)
    user = service.create_user(admin.token, "inactive", "Inactive", Role.VIEWER, OLD)
    service.update_user(admin.token, user.id, "inactive", "Inactive", Role.VIEWER, False)
    with pytest.raises(AuthError, match="Username atau password"):
        service.login("inactive", OLD)


def test_optional_password_migration_preserves_accounts_and_sessions(auth, store):
    from alembic import command
    from database.runtime import alembic_config, upgrade, schema_status
    from sqlalchemy import inspect
    service, login, _ = auth
    with store.db.transaction() as session:
        original_hash = session.get(User, login.principal.id).password_hash
        original_sessions = session.scalar(select(func.count()).select_from(AuthSession))
    with store.migration.begin() as connection:
        command.downgrade(alembic_config(connection, application_role=store.config.user), '0004_devices')
        connection.execute(User.__table__.update().values(must_change_password=True))
        upgrade(connection, application_role=store.config.user)
        assert schema_status(connection)['at_head']
        column = next(c for c in inspect(connection).get_columns('users') if c['name']=='must_change_password')
        assert 'false' in column['default'].lower()
    with store.db.transaction() as session:
        user = session.get(User, login.principal.id)
        assert not user.must_change_password and user.password_hash == original_hash
        assert session.scalar(select(func.count()).select_from(AuthSession)) == original_sessions
    assert service.authorize(login.token, 'users')

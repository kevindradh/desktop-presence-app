import bcrypt
from sqlalchemy import func, select

from app.models.entities import Role, User
from app.repositories.core import AuditRepository, UserRepository
from app.services.database import DataValidationError


def bootstrap_super_admin(session, username, fullname, password):
    # Serialize first-admin creation across processes; lock is transaction scoped.
    session.execute(select(func.pg_advisory_xact_lock(734_281_003)))
    existing = session.scalar(select(User.id).where(User.role == Role.SUPER_ADMIN,
                                                   User.is_active.is_(True)).limit(1))
    if existing is not None:
        raise DataValidationError("Super Admin aktif sudah tersedia; bootstrap tidak mengubah akun.")
    if not isinstance(password, str) or not 12 <= len(password.encode("utf-8")) <= 72:
        raise DataValidationError("Password harus 12 sampai 72 byte UTF-8.")
    encoded = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")
    user = UserRepository(session).create_with_hash(username, fullname, encoded, Role.SUPER_ADMIN)
    AuditRepository(session).append("system.admin_bootstrapped", "user", user.id)
    return user

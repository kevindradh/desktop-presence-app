"""Disposable synthetic administration demo. Never selects the development database."""
from contextlib import contextmanager
from datetime import date, datetime, time, timezone
from pathlib import Path
from types import SimpleNamespace
import secrets
import uuid

from PyQt6.QtGui import QColor, QImage
from sqlalchemy import DDL, select
from sqlalchemy.schema import CreateSchema, DropSchema

from app.models.entities import AttendanceStatus, AttendanceType, DeviceType, Location, Role, User
from app.repositories.core import (AttendanceRepository, DeviceRepository, GroupRepository,
    MemberRepository, ShiftRepository, UserRepository)
from app.services.auth import AuthService, password_hash
from app.services.database import Database, create_database_engine
from database.runtime import connection_config, upgrade
from database.seed.defaults import seed_defaults


@contextmanager
def demo_database():
    schema = "stage3_test_" + uuid.uuid4().hex
    migrator = create_database_engine(connection_config("test", migration=True))
    scoped = application = None
    app_config = connection_config("test")
    try:
        with migrator.begin() as connection:
            connection.execute(CreateSchema(schema))
            quote = connection.dialect.identifier_preparer.quote
            connection.execute(DDL(f"GRANT USAGE ON SCHEMA {quote(schema)} TO {quote(app_config.user)}"))
        scoped = create_database_engine(connection_config("test", migration=True), schema=schema)
        with scoped.begin() as connection:
            upgrade(connection)
        application = create_database_engine(app_config, schema=schema)
        yield SimpleNamespace(db=Database(application), schema=schema, config=app_config, migration=scoped)
    finally:
        if application:
            application.dispose()
        if scoped:
            scoped.dispose()
        with migrator.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True, if_exists=True))
        migrator.dispose()


def seed_administration_demo(database, root, role=Role.SUPER_ADMIN):
    root = Path(root)
    (root / "synthetic").mkdir(parents=True, exist_ok=True)
    image = QImage(100, 100, QImage.Format.Format_RGB32)
    image.fill(QColor("#2d6240"))
    if not image.save(str(root / "synthetic/profile.png")):
        raise OSError("Synthetic photo could not be written")
    password = secrets.token_urlsafe(24)
    hashed = password_hash(password)
    with database.transaction() as session:
        seed_defaults(session)
        users = {}
        for entry in Role:
            user = UserRepository(session).create_with_hash("demo_" + entry.value.lower(),
                "Penguji " + entry.value.replace("_", " "), hashed, entry)
            user.must_change_password = False
            users[entry] = user.username
        group_a = GroupRepository(session).create("Kelas 10A", "Data sintetis untuk pengujian")
        group_b = GroupRepository(session).create("IT", "Data sintetis untuk pengujian")
        morning = ShiftRepository(session).create("Pagi", time(8), time(17), 10)
        night = ShiftRepository(session).create("Malam", time(20), time(4), 10)
        location = session.scalar(select(Location))
        device = DeviceRepository(session).create("Kamera sintetis", DeviceType.INTERNAL, location.id)
        for index in range(1, 26):
            member = MemberRepository(session).create(f"SG-TEST-{index:04}", f"Anggota Uji {index:02}",
                group_a.id if index <= 13 else group_b.id, "synthetic/profile.png",
                email=f"test{index}@example.invalid")
            if index == 1:
                ShiftRepository(session).assign(member.id, morning.id, date(2026, 10, 1), date(2026, 10, 18))
                AttendanceRepository(session).record(member_id=member.id, device_id=device.id, shift_id=morning.id,
                    event_type=AttendanceType.IN, timestamp=datetime(2026, 10, 18, 1, 5, tzinfo=timezone.utc),
                    work_date=date(2026, 10, 18), status=AttendanceStatus.PRESENT)
    auth = AuthService(database)
    return auth, auth.login(users[Role(role)], password)

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timezone
from types import SimpleNamespace
import uuid

import bcrypt
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import (Column, DDL, MetaData, Table, delete, func, inspect, select, update)
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.models.entities import (Attendance, AttendanceStatus, AttendanceType, AuditLog, Base,
    CalendarDay, Device, DeviceType, FaceAngle, FaceEmbedding, Location, Member, MemberGroup,
    MemberLeave, Role, Setting, Shift, ShiftAssignment, User)
from app.repositories.core import (AttendanceRepository, AuditRepository, DeviceRepository,
    EmbeddingRepository, GroupRepository, MemberRepository, SettingsRepository, ShiftRepository,
    UserRepository)
from app.services.bootstrap_admin import bootstrap_super_admin
from app.services.database import (DataConflict, Database, DatabaseUnavailable,
                                  DataValidationError, create_database_engine)
from database.runtime import alembic_config, connection_config, schema_status, upgrade
from database.seed.defaults import seed_defaults

pytestmark = pytest.mark.database


@pytest.fixture
def store():
    # Only an owned unique schema in stargate_test is disposable. Never drop public.
    schema = "stage3_test_" + uuid.uuid4().hex
    migrator_config = connection_config("test", migration=True)
    app_config = connection_config("test")
    admin = create_database_engine(migrator_config)
    migrator = application = None
    try:
        with admin.begin() as conn:
            conn.execute(CreateSchema(schema))
            quote = conn.dialect.identifier_preparer.quote
            conn.execute(DDL(f"GRANT USAGE ON SCHEMA {quote(schema)} TO {quote(app_config.user)}"))
        migrator = create_database_engine(migrator_config, schema=schema)
        with migrator.begin() as conn:
            upgrade(conn)
        application = create_database_engine(app_config, schema=schema)
        yield SimpleNamespace(db=Database(application), engine=application,
                              migration=migrator, schema=schema, config=app_config)
    finally:
        if application:
            application.dispose()
        if migrator:
            migrator.dispose()
        with admin.begin() as conn:
            assert schema.startswith("stage3_test_")
            conn.execute(DropSchema(schema, cascade=True))
        admin.dispose()


def graph(session):
    seed_defaults(session)
    location = session.scalar(select(Location))
    group = GroupRepository(session).create("Kelas Uji")
    member = MemberRepository(session).create("SG-TEST-001", "Anggota Uji", group.id,
                                               "synthetic/no-photo.jpg")
    shift = ShiftRepository(session).create("Malam", time(20), time(4), 10)
    device = DeviceRepository(session).create("Kamera Uji", DeviceType.USB, location.id)
    return group, member, shift, device


def record(session, member, shift, device, kind=AttendanceType.IN):
    return AttendanceRepository(session).record(member_id=member.id, device_id=device.id,
        shift_id=shift.id, event_type=kind, timestamp=datetime(2026, 10, 18, 13, tzinfo=timezone.utc),
        work_date=date(2026, 10, 18), status=AttendanceStatus.PRESENT)


def test_migration_schema_matches_models_and_can_roundtrip_in_isolation(store):
    with store.migration.begin() as conn:
        assert set(Base.metadata.tables) <= set(inspect(conn).get_table_names(schema=store.schema))
        assert schema_status(conn)["at_head"]
        assert schema_status(conn)["schema_valid"]
        context = MigrationContext.configure(conn, opts={"include_object":
            lambda obj, name, kind, reflected, compare_to: name != "alembic_version"})
        assert compare_metadata(context, Base.metadata) == []
        command.downgrade(alembic_config(conn), "base")
        assert not (set(inspect(conn).get_table_names(schema=store.schema)) & set(Base.metadata.tables))
        assert not schema_status(conn)["schema_valid"]
        assert set(schema_status(conn)["missing_tables"]) == set(Base.metadata.tables)
        upgrade(conn)
        assert schema_status(conn)["at_head"]
        # Public contains the same table: it must not conceal a missing test-schema column.
        conn.execute(DDL("ALTER TABLE members DROP COLUMN phone"))
        assert schema_status(conn)["missing_columns"] == {"members": ["phone"]}
        assert not schema_status(conn)["schema_valid"]
        conn.execute(DDL("ALTER TABLE members ADD COLUMN phone VARCHAR(40)"))
        assert schema_status(conn)["schema_valid"]


def test_seed_is_idempotent_and_preserves_admin_changes(store):
    with store.db.transaction() as session:
        assert seed_defaults(session) == {"settings_inserted": 12, "locations_inserted": 1}
        SettingsRepository(session).set("similarity_threshold", .65)
        count = session.scalar(select(func.count()).select_from(AuditLog))
        assert seed_defaults(session) == {"settings_inserted": 0, "locations_inserted": 0}
        assert SettingsRepository(session).get("similarity_threshold") == .65
        assert session.scalar(select(func.count()).select_from(AuditLog)) == count
        audit = AuditRepository(session).recent(action="setting.changed")[0]
        assert audit.details["old_value"] == .60 and audit.details["new_value"] == .65


def test_rollback_removes_business_rows_and_audit_together(store):
    with pytest.raises(RuntimeError):
        with store.db.transaction() as session:
            GroupRepository(session).create("Rollback Group")
            raise RuntimeError("simulate downstream failure")
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(MemberGroup)) == 0
        assert session.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_soft_delete_preserves_attendance_and_history_snapshot(store):
    with store.db.transaction() as session:
        group, member, shift, device = graph(session)
        event = record(session, member, shift, device)
        original_group_id = group.id
        other = GroupRepository(session).create("Group Baru")
        member.group_id = other.id
        MemberRepository(session).deactivate(member.id)
        assert not MemberRepository(session).get(member.id).is_active
        assert AttendanceRepository(session).history(member.id)[0].id == event.id
        assert event.group_id == original_group_id
        assert AuditRepository(session).recent(action="member.deactivated")
        member_id = member.id
    with store.db.transaction() as session:
        assert len(AttendanceRepository(session).history(member_id)) == 1
        assert MemberRepository(session).list()[1] == 0
        assert MemberRepository(session).list(active=False)[1] == 1


def test_relationships_schedule_leave_calendar_persist(store):
    with store.db.transaction() as session:
        group, member, shift, device = graph(session)
        assignment = ShiftRepository(session).assign(member.id, shift.id, date(2026, 10, 1))
        session.add_all([MemberLeave(member_id=member.id, starts_on=date(2026, 10, 20),
                         ends_on=date(2026, 10, 21)), CalendarDay(location_id=device.location_id,
                         calendar_date=date(2026, 10, 20), is_workday=False, label="Hari libur uji")])
        session.flush()
        assert member.group.id == group.id and group.members[0].id == member.id
        assert assignment.ends_on is None and shift.end_time < shift.start_time
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(MemberLeave)) == 1
        assert session.scalar(select(func.count()).select_from(CalendarDay)) == 1


def test_group_foreign_key_case_insensitive_member_unique_and_partial_rollback(store):
    with store.db.transaction() as session:
        group, member, shift, device = graph(session)
        group_id = group.id
    with pytest.raises(DataConflict):
        with store.db.transaction() as session:
            MemberRepository(session).create("sg-test-001", "Duplikat", group_id, "synthetic/path")
    with pytest.raises(DataConflict):
        with store.db.transaction() as session:
            GroupRepository(session).create("Should rollback")
            MemberRepository(session).create("NEW", "Orphan", -1, "synthetic/path")
    with pytest.raises(DataConflict):
        with store.db.transaction() as session:
            session.delete(session.get(MemberGroup, group_id))
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member)) == 1
        assert session.scalar(select(func.count()).select_from(MemberGroup)) == 1


def test_duplicate_in_out_constraint_but_breaks_can_repeat(store):
    with store.db.transaction() as session:
        _, member, shift, device = graph(session)
        record(session, member, shift, device)
        for event in [AttendanceType.BREAK_OUT, AttendanceType.BREAK_IN]*2:
            record(session, member, shift, device, event)
        ids = member.id, shift.id, device.id
    with pytest.raises(DataConflict):
        with store.db.transaction() as session:
            record(session, session.get(Member, ids[0]), session.get(Shift, ids[1]),
                   session.get(Device, ids[2]))
    with store.db.transaction() as session:
        assert len(AttendanceRepository(session).history(ids[0])) == 5


def test_vector_512_roundtrip_ranking_unique_members_and_inactive_filter(store):
    positive = [1.0]+[0.0]*511
    negative = [-1.0]+[0.0]*511
    with store.db.transaction() as session:
        group, member, _, _ = graph(session)
        other = MemberRepository(session).create("OTHER", "Other", group.id, "synthetic/path")
        repo = EmbeddingRepository(session)
        for angle in FaceAngle:
            repo.create(member.id, positive, angle, "arcface-test-v1")
        repo.create(other.id, negative, FaceAngle.FRONT, "arcface-test-v1")
        repo.create(other.id, positive, FaceAngle.LEFT, "different-model")
        results = repo.nearest(positive, model_version="arcface-test-v1")
        assert [r.member_id for r in results] == [member.id, other.id]
        assert results[0].similarity == pytest.approx(1) and results[1].similarity == pytest.approx(-1)
        stored = session.scalar(select(FaceEmbedding.embedding).where(FaceEmbedding.member_id == member.id))
        assert len(stored) == 512 and float(stored[0]) == 1
        MemberRepository(session).deactivate(member.id)
        assert [r.member_id for r in repo.nearest(positive,model_version="arcface-test-v1")] == [other.id]
        with pytest.raises(DataValidationError):
            repo.create(member.id, positive, FaceAngle.FRONT, "arcface-test-v1")


@pytest.mark.parametrize("vector", [[1]*511, [0]*512, [float('nan')]*512, [float('inf')]*512])
def test_invalid_vector_rejected_without_values_in_error(store, vector):
    with store.db.transaction() as session:
        _, member, _, _ = graph(session)
        with pytest.raises(DataValidationError):
            EmbeddingRepository(session).create(member.id,vector,FaceAngle.FRONT,"arcface-test-v1")
        assert session.scalar(select(func.count()).select_from(FaceEmbedding)) == 0


@pytest.mark.parametrize("operation", ["audit_update","audit_delete","user_delete","member_delete","revision_update"])
def test_app_cannot_modify_audit_or_delete_protected_entities(store, operation):
    with store.engine.begin() as conn:
        target = {"audit_update": update(AuditLog).values(action="changed"),
                  "audit_delete": delete(AuditLog), "user_delete": delete(User),
                  "member_delete": delete(Member)}
        with pytest.raises(DBAPIError) as error:
            with conn.begin_nested():
                if operation == "revision_update":
                    table = Table('alembic_version', MetaData(), Column('version_num'))
                    conn.execute(update(table).values(version_num="tampered"))
                else:
                    conn.execute(target[operation])
        assert error.value.orig.sqlstate == "42501"


def test_audit_rejects_sensitive_or_arbitrary_payload(store):
    with store.db.transaction() as session:
        repo = AuditRepository(session)
        for details in [{"password":"never-store"}, {"embedding":[1]*512},
                        {"old_value":"secret"}, {"setting_key":"password", "new_value":"secret"}]:
            with pytest.raises(DataValidationError):
                repo.append("system.test","system",details=details)
        assert session.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_bootstrap_is_hashed_unique_and_no_password_in_audit(store):
    with store.db.transaction() as session:
        user = bootstrap_super_admin(session,"test_admin","Admin Uji","synthetic-password-only")
        assert bcrypt.checkpw(b"synthetic-password-only",user.password_hash.encode())
        assert not user.must_change_password
        assert UserRepository(session).by_username("TEST_ADMIN").id == user.id
        assert "synthetic-password-only" not in str([e.details for e in AuditRepository(session).recent()])
    with pytest.raises(DataValidationError):
        with store.db.transaction() as session:
            bootstrap_super_admin(session,"second","Other","another-test-password")
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_search_values_are_parameters_and_wildcards_are_literal(store):
    with store.db.transaction() as session:
        group, _, _, _ = graph(session)
        MemberRepository(session).create("LITERAL", "Anggota 100%_Uji", group.id, "synthetic/path")
        items, count = MemberRepository(session).list(search="%_")
        assert count == 1 and items[0].member_code == "LITERAL"
        assert MemberRepository(session).list(search="'; DROP TABLE users; --")[1] == 0
        assert session.scalar(select(func.count()).select_from(Member)) == 2


def test_unavailable_connection_exposes_only_safe_error(store):
    engine = create_database_engine(replace(store.config, port=1))
    try:
        with pytest.raises(DatabaseUnavailable) as error:
            with Database(engine).transaction() as session:
                session.scalar(select(func.count()).select_from(Member))
        assert store.config.password not in str(error.value)
        assert "Database tidak dapat diakses" in str(error.value)
    finally:
        engine.dispose()


def test_bootstrap_concurrency_creates_exactly_one_admin(store):
    def attempt(number):
        try:
            with store.db.transaction() as session:
                bootstrap_super_admin(session, f"admin{number}", "Admin Uji", "only-synthetic-password")
            return True
        except DataValidationError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, [1, 2])) == [False, True]
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert len(AuditRepository(session).recent(action="system.admin_bootstrapped")) == 1


@pytest.mark.parametrize("kind", ["negative_grace", "zero_shift", "invalid_fps", "reversed_schedule",
                                  "reversed_leave", "plaintext_password", "invalid_user_role"])
def test_database_rejects_invalid_records_and_rolls_back_all_rows(store, kind):
    with pytest.raises((DataConflict, DataValidationError)):
        with store.db.transaction() as session:
            _, member, shift, device = graph(session)
            if kind == "negative_grace":
                shift.grace_minutes = -1
            elif kind == "zero_shift":
                shift.end_time = shift.start_time
            elif kind == "invalid_fps":
                device.fps = 0
            elif kind == "reversed_schedule":
                ShiftRepository(session).assign(member.id, shift.id, date(2026,10,20), date(2026,10,1))
            elif kind == "reversed_leave":
                session.add(MemberLeave(member_id=member.id, starts_on=date(2026,10,20), ends_on=date(2026,10,1)))
            elif kind == "plaintext_password":
                session.add(User(username="plain", fullname="Plain", password_hash="plaintext", role=Role.ADMIN))
            elif kind == "invalid_user_role":
                UserRepository(session).create_with_hash("wrong-role", "Wrong", "$2b$12$"+"a"*53, "NOT_A_ROLE")
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member)) == 0
        assert session.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_commit_returns_timezone_aware_timestamps_and_survives_new_engine(store):
    with store.db.transaction() as session:
        _, member, shift, device = graph(session)
        event = record(session, member, shift, device)
        member_id, event_id = member.id, event.id
        assert member.created_at.utcoffset() is not None
    another = create_database_engine(store.config, schema=store.schema)
    try:
        with Database(another).transaction() as session:
            assert session.get(Member, member_id).full_name == "Anggota Uji"
            stored = session.get(Attendance, event_id)
            assert stored.attendance_time.utcoffset() is not None
            assert stored.attendance_time == datetime(2026,10,18,13,tzinfo=timezone.utc)
            assert stored.work_date == date(2026,10,18)
    finally:
        another.dispose()

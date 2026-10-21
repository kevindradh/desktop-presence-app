from tests.permissions import assert_private_path
"""Stage 5 real PostgreSQL tests. No real identity, photo or public data used."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from pathlib import Path

import pytest
from PyQt6.QtGui import QImage, QColor
from sqlalchemy import func, select

from app.models.entities import Attendance, AuditLog, FaceAngle, FaceEmbedding, Member, MemberGroup, Role, ShiftAssignment
from app.repositories.core import EmbeddingRepository, GroupRepository, MemberRepository
from app.services.administration import AdministrationService, validate_member, validate_shift
from app.services.auth import AuthError
from app.services.database import DataConflict, DataValidationError
from tests.test_auth import auth, add_role
from tests.test_database import store, graph, record

pytestmark = pytest.mark.database


@pytest.fixture
def administration(auth, tmp_path):
    service, admin, now = auth
    return AdministrationService(service, tmp_path), admin, now


@pytest.fixture
def data(store):
    with store.db.transaction() as session:
        group, member, shift, device = graph(session)
        second = GroupRepository(session).create("IT")
        event = record(session, member, shift, device)
        for index in range(24):
            MemberRepository(session).create(f"SG-{index:03}", f"Anggota Uji {index:02}",
                second.id if index % 2 else group.id, "synthetic/profile.png")
        return member.id, group.id, second.id, shift.id, device.id, event.id


@pytest.fixture
def photo(tmp_path):
    path = tmp_path / "synthetic.png"
    image = QImage(40, 30, QImage.Format.Format_RGB32)
    image.fill(QColor("#2d6240"))
    assert image.save(str(path))
    return path


def test_groups_crud_unique_stale_protected_delete_and_audit(administration, store, data):
    service, login, _ = administration
    created = service.save_group(login.token, "Grup Baru", "Deskripsi")
    assert created.member_count == 0
    with pytest.raises(DataConflict):
        service.save_group(login.token, "GRUP BARU")
    changed = service.save_group(login.token, "Grup Baru Edit", "Baru", group_id=created.id, revision=created.revision)
    assert changed.revision == created.revision + 1
    with pytest.raises(DataValidationError, match="diubah"):
        service.save_group(login.token, "Timpa", group_id=created.id, revision=created.revision)
    with pytest.raises(DataValidationError, match="digunakan"):
        service.delete_group(login.token, data[1], 1)
    service.delete_group(login.token, changed.id, changed.revision)
    assert changed.id not in {row.id for row in service.groups(login.token)}
    with store.db.transaction() as session:
        actions = set(session.scalars(select(AuditLog.action).where(AuditLog.actor_id == login.principal.id)))
        assert {"group.created", "group.updated", "group.deleted"} <= actions
        assert session.get(MemberGroup, data[1]) is not None


def test_shift_day_night_crud_and_references(administration, data):
    service, login, _ = administration
    day = service.save_shift(login.token, "Pagi", time(8), time(17), 10)
    night = service.save_shift(login.token, "Malam Baru", time(20), time(4), 10)
    assert not day.overnight and night.overnight
    with pytest.raises(DataValidationError, match="digunakan"):
        service.save_shift(login.token, "PAGI", time(7), time(16), 5)
    day2 = service.save_shift(login.token, "Pagi Edit", time(7), time(16), 5, shift_id=day.id, revision=day.revision)
    with pytest.raises(DataValidationError, match="diubah"):
        service.delete_shift(login.token, day.id, day.revision)
    service.delete_shift(login.token, day2.id, day2.revision)
    with pytest.raises(DataValidationError, match="digunakan"):
        service.delete_shift(login.token, data[3], 1)
    with pytest.raises(DataValidationError, match="direferensikan"):
        service.save_shift(login.token, "Malam", time(21), time(4), 10, shift_id=data[3], revision=1)
    renamed = service.save_shift(login.token, "Shift Malam", time(20), time(4), 10, shift_id=data[3], revision=1)
    assert renamed.name == "Shift Malam"


def test_member_filters_pagination_literals_edit_and_historical_group(administration, store, data):
    service, login, _ = administration
    first = service.members(login.token)
    assert first.total == 25 and len(first.rows) == 10
    last = service.members(login.token, offset=100)
    assert last.offset == 20 and len(last.rows) == 5
    assert service.members(login.token, search="Anggota Uji 01").total == 1
    assert service.members(login.token, group_id=data[2]).total == 12
    assert service.members(login.token, search="' OR 1=1 --").total == 0
    assert service.members(login.token, search="%").total == 0
    detail = service.member(login.token, data[0])
    assert detail.history_total == 1 and detail.history[0].group_name == "Kelas Uji"
    row = detail.member
    updated = service.update_member(login.token, row.id, row.revision, "SG-RENAMED", "Nama Unicode 李", data[2],
        email="user@example.invalid", phone="+62 812-000", position="Operator")
    assert updated.group_name == "IT" and updated.revision == row.revision + 1
    with pytest.raises(DataValidationError, match="diubah"):
        service.update_member(login.token, row.id, row.revision, "STALE", "Timpa", data[1])
    detail = service.member(login.token, row.id)
    assert detail.history[0].group_name == "Kelas Uji"
    with store.db.transaction() as session:
        assert session.get(Attendance, data[-1]).group_id == data[1]
        audit = session.scalar(select(AuditLog).where(AuditLog.action == "member.updated"))
        assert audit.actor_id == login.principal.id and "group_id" in audit.details["changed_fields"]


def test_member_soft_delete_preserves_everything_and_blocks_matching(administration, store, data):
    service, login, _ = administration
    with store.db.transaction() as session:
        EmbeddingRepository(session).create(data[0], [1.0] + [0.0] * 511, FaceAngle.FRONT, "synthetic")
    row = service.member(login.token, data[0]).member
    inactive = service.deactivate_member(login.token, row.id, row.revision)
    assert not inactive.active
    assert service.members(login.token).total == 24
    assert service.members(login.token, active=False).total == 1
    assert service.members(login.token, active=None).total == 25
    assert service.member(login.token, row.id).history_total == 1
    with store.db.transaction() as session:
        assert session.get(Member, row.id) is not None
        assert session.scalar(select(func.count()).select_from(FaceEmbedding)) == 0
        assert not EmbeddingRepository(session).nearest([1.0] + [0.0] * 511, model_version="synthetic")
    assert not service.deactivate_member(login.token, row.id, inactive.revision).active


def test_photo_managed_copy_and_atomic_rollback(administration, store, data, photo, tmp_path):
    service, login, _ = administration
    row = service.member(login.token, data[0]).member
    changed = service.update_member(login.token, row.id, row.revision, row.code, row.name, row.group_id, photo_source=photo)
    stored = tmp_path / changed.photo
    assert stored.is_file(); assert_private_path(stored)
    assert_private_path(stored.parent, directory=True)
    photo.unlink()
    assert not QImage(str(stored)).isNull()
    duplicate = service.members(login.token, search="SG-000").rows[0]
    before = set(service.photos.folder.iterdir())
    with pytest.raises(DataConflict):
        service.update_member(login.token, row.id, changed.revision, duplicate.code, "Do not commit", row.group_id, photo_source=stored)
    assert set(service.photos.folder.iterdir()) == before
    assert service.member(login.token, row.id).member.code == row.code
    assert service.member(login.token, row.id).member.revision == changed.revision
    with store.db.transaction() as session:
        logs = list(session.scalars(select(AuditLog).where(AuditLog.action == "member.updated")))
        assert len(logs) == 1 and "photo_path" in logs[0].details["changed_fields"]
        assert str(stored) not in str(logs[0].details)


def test_assignments_nonoverlap_inclusive_boundary_end_and_history(administration, data):
    service, login, _ = administration
    member = service.member(login.token, data[0]).member
    assignment = service.assign_shift(login.token, member.id, member.revision, data[3], date(2026, 10, 1), None)
    detail = service.member(login.token, member.id)
    assert len(detail.assignments) == 1
    with pytest.raises(DataValidationError, match="tumpang"):
        service.assign_shift(login.token, member.id, detail.member.revision, data[3], date(2026, 10, 18))
    with pytest.raises(DataValidationError, match="riwayat"):
        service.end_assignment(login.token, member.id, detail.member.revision, assignment, date(2026, 10, 17))
    service.end_assignment(login.token, member.id, detail.member.revision, assignment, date(2026, 10, 18))
    detail = service.member(login.token, member.id)
    with pytest.raises(DataValidationError, match="tumpang"):
        service.assign_shift(login.token, member.id, detail.member.revision, data[3], date(2026, 10, 18), date(2026, 10, 20))
    service.assign_shift(login.token, member.id, detail.member.revision, data[3], date(2026, 10, 19), None)
    assert len(service.member(login.token, member.id).assignments) == 2
    with pytest.raises(DataValidationError):
        service.end_assignment(login.token, member.id, detail.member.revision, assignment, date(2026, 11, 1))


def test_parallel_assignments_and_edits_do_not_overwrite(administration, data):
    service, login, _ = administration
    member = service.member(login.token, data[0]).member
    def assign(_):
        try:
            return service.assign_shift(login.token, member.id, member.revision, data[3], date(2026, 10, 1))
        except DataValidationError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(assign, range(2)))
    assert sum(value is not None for value in results) == 1
    assert len(service.member(login.token, member.id).assignments) == 1


@pytest.mark.parametrize("role", list(Role))
def test_role_boundaries_all_admin_actions(administration, data, role):
    service, login, _ = administration
    _, account = add_role(service.auth, login, role)
    if role == Role.VIEWER:
        for operation in (lambda: service.members(account.token), lambda: service.member(account.token, data[0]),
                          lambda: service.register_member(account.token)):
            with pytest.raises(AuthError):
                operation()
    else:
        assert service.members(account.token).total == 25
        if role == Role.OPERATOR:
            assert not service.member(account.token, data[0]).can_assign
            row = service.member(account.token, data[0]).member
            assert service.update_member(account.token, row.id, row.revision, row.code, "Edit Operator", row.group_id)
        with pytest.raises(DataValidationError, match="capture"):
            service.register_member(account.token, member_code="NEW")
    actions = (lambda: service.groups(account.token), lambda: service.shifts(account.token),
        lambda: service.save_group(account.token, "Unauthorized"),
        lambda: service.delete_group(account.token, data[1], 1),
        lambda: service.save_shift(account.token, "Unauthorized", time(8), time(17), 10),
        lambda: service.delete_shift(account.token, data[3], 1),
        lambda: service.assign_shift(account.token, data[0], 1, data[3], date(2026, 10, 1)),
        lambda: service.end_assignment(account.token, data[0], 1, 999, date(2026, 10, 1)))
    if role in {Role.OPERATOR, Role.VIEWER}:
        for action in actions:
            with pytest.raises(AuthError):
                action()
    else:
        assert service.groups(account.token) and service.shifts(account.token)


def test_revoked_session_missing_records_and_invalid_payloads(administration, data):
    service, login, _ = administration
    row = service.member(login.token, data[0]).member
    with pytest.raises(DataValidationError):
        service.member(login.token, 99999)
    with pytest.raises(DataValidationError):
        service.update_member(login.token, row.id, row.revision, row.code, "", row.group_id)
    with pytest.raises(DataValidationError):
        service.update_member(login.token, row.id, row.revision, row.code, row.name, 99999)
    for parameters in ({"offset":-1},{"limit":11},{"active":"true"},{"group_id":True}):
        with pytest.raises(DataValidationError):
            service.members(login.token, **parameters)
    with pytest.raises(DataValidationError):
        service.assign_shift(login.token, row.id, row.revision, data[3], date(2026, 10, 20), date(2026, 10, 19))
    service.auth.logout(login.token)
    with pytest.raises(AuthError):
        service.save_group(login.token, "Session expired")

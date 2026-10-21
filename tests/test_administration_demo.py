"""Verify disposable demo creation and cleanup without touching public accounts."""
import pytest
from sqlalchemy import func, inspect, select

from app.models.entities import Member, Role, User
from app.services.administration import AdministrationService
from app.services.database import create_database_engine
from database.demo import demo_database, seed_administration_demo
from database.runtime import connection_config

pytestmark = pytest.mark.database


def counts(engine):
    with engine.connect() as connection:
        return (connection.scalar(select(func.count()).select_from(User)),
                connection.scalar(select(func.count()).select_from(Member)))


@pytest.mark.parametrize("role", list(Role))
def test_demo_role_data_and_cleanup_are_isolated(role, tmp_path, qt_app):
    engine = create_database_engine(connection_config("test"))
    try:
        before = counts(engine)
        with demo_database() as store:
            schema = store.schema
            service, login = seed_administration_demo(store.db, tmp_path, role)
            assert service.authorize(login.token, "reports").role == role
            if role != Role.VIEWER:
                page = AdministrationService(service, tmp_path).members(login.token)
                assert page.total == 25 and len(page.rows) == 10
                detail = AdministrationService(service, tmp_path).member(login.token, page.rows[0].id)
                assert detail.history_total == 1
            assert counts(engine) == before
        assert schema not in inspect(engine).get_schema_names()
        assert counts(engine) == before
    finally:
        engine.dispose()


def test_failed_demo_scope_is_also_removed():
    engine = create_database_engine(connection_config("test", migration=True))
    try:
        with pytest.raises(RuntimeError):
            with demo_database() as store:
                schema = store.schema
                raise RuntimeError("synthetic demo failure")
        assert schema not in inspect(engine).get_schema_names()
    finally:
        engine.dispose()


@pytest.mark.parametrize("role", ["super-admin", "viewer"])
def test_demo_cli_opens_and_closes_cleanly_without_public_changes(role):
    import subprocess
    import sys
    from pathlib import Path
    engine = create_database_engine(connection_config("test"))
    try:
        before = counts(engine)
        code = r'''
import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication,QMessageBox
from scripts.demo_administration import main
original=QApplication.exec
messages=[]
QMessageBox.critical=lambda *args: messages.append(True)
def run(application):
    windows=[w for w in application.topLevelWidgets() if hasattr(w,'shell')]
    assert len(windows)==1 and windows[0].login is not None
    assert 'MODE UJI' in windows[0].windowTitle()
    QTimer.singleShot(300,application.closeAllWindows)
    return original()
QApplication.exec=run
sys.argv=['demo_administration','--role',sys.argv[1]]
assert main()==0
assert not messages
'''
        result = subprocess.run([sys.executable, "-c", code, role], cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert counts(engine) == before
    finally:
        engine.dispose()

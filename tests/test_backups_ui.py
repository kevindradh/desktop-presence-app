"""Native-capable audit form focus, recovery confirmation and worker lifecycle."""
from contextlib import contextmanager
from pathlib import Path
import os
import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QFileDialog
from sqlalchemy import select
from app.models.entities import Member
from tests.test_backups import backup,store,auth,PASSWORD
from tests.test_session_ui import views,sign_in,activate
from tests.test_administration_ui import open_page
from tests.test_auth import NEW

pytestmark=pytest.mark.database


def test_audit_filter_preserves_focus_and_requires_explicit_load(backup,views,wait_until):
    service,login,now,root=backup;view=views(service.auth);sign_in(view,'root',NEW,wait_until)
    page=open_page(view,'audit',wait_until);activate(view)
    page.action.setFocus();page.action.setText('auth.login')
    for _ in range(3):view._check_session();QTest.qWait(100);assert page.action.hasFocus()
    from threading import Event
    wait_until(lambda:not view.jobs.tasks.busy)
    entered,release=Event(),Event()
    def poll():
        entered.set();assert release.wait(5)
        return service.auth.inspect(view.login.token)
    assert view.jobs.run(poll,lambda result:None,blocks_ui=False)
    try:
        wait_until(entered.is_set)
        page.load_button.click()
        assert view.jobs.queued is not None and page.pending
    finally:release.set()
    wait_until(lambda:not page.pending)
    assert page.table.rowCount()>0
    page.action.setText('member.created');assert page.table.rowCount()==0


def test_backup_inspect_and_restore_with_login_and_reenroll(backup,store,views,wait_until,monkeypatch):
    service,login,now,root=backup;view=views(service.auth);view.backup_service=service
    sign_in(view,'root',NEW,wait_until);page=open_page(view,'backup',wait_until)
    path=root/'ui.sgbackup'
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a:(str(path),''))
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a:(str(path),''))
    page.password.setText(PASSWORD);page.repeat.setText('different');page.backup_button.click()
    assert not path.exists() and 'sama' in view.error_message.text()
    page.repeat.setText(PASSWORD);page.backup_button.click();wait_until(lambda:not page.busy,timeout=15000)
    assert path.exists() and not page.password.text()
    page.password.setText(PASSWORD);page.choose_button.click();wait_until(lambda:not page.busy,timeout=15000)
    assert page.reviewed is not None and not page.restore_button.isEnabled()
    page.confirmation.setText('PULIHKAN');assert page.restore_button.isEnabled()
    with store.db.transaction() as session:session.scalar(select(Member)).full_name='Changed UI'
    destination=os.environ.get('STARGATE_BACKUP_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True,exist_ok=True);assert view.grab().save(str(Path(destination)/'stage-13-backup.png'))
    from threading import Event
    entered,release=Event(),Event()
    wait_until(lambda:not view.jobs.tasks.busy)
    def poll():
        entered.set();assert release.wait(5)
        return service.auth.inspect(view.login.token)
    assert view.jobs.run(poll,lambda result:None,blocks_ui=False)
    try:
        wait_until(entered.is_set)
        page.restore_button.click()
        assert page.preparing and view._maintenance
    finally:release.set()
    wait_until(lambda:not page.busy and view.login is None,timeout=20000)
    assert 'registrasi wajah ulang' in view.error_message.text() and not view._maintenance
    with store.db.transaction() as session:assert session.scalar(select(Member)).full_name!='Changed UI'
    sign_in(view,'root',NEW,wait_until);assert view.login is not None


def test_backup_password_change_invalidates_review(backup,views,wait_until,monkeypatch):
    service,login,now,root=backup;path=root/'inspect.sgbackup';service.backup(login.token,path,PASSWORD)
    view=views(service.auth);view.backup_service=service;sign_in(view,'root',NEW,wait_until)
    page=open_page(view,'backup',wait_until);monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a:(str(path),''))
    page.password.setText(PASSWORD);page.choose_button.click();wait_until(lambda:not page.busy,timeout=15000)
    page.confirmation.setText('PULIHKAN');assert page.restore_button.isEnabled()
    page.password.setText('Changed-password-2026!');assert page.reviewed is None and not page.restore_button.isEnabled()


def test_demo_recovery_navigation_and_mutation(backup,store,qt_app,wait_until):
    import logging
    from app.ui.backups_demo import BackupsDemo,DEMO_USER,DEMO_PASSWORD
    from app.settings.config import load_config
    from app.services.errors import ErrorReporter
    from app.models.entities import Role
    service,login,now,root=backup
    service.auth.create_user(login.token,DEMO_USER,'Penguji pemulihan',Role.SUPER_ADMIN,'Demo-initial-2026!')
    demo_login=service.auth.change_password(service.auth.login(DEMO_USER,'Demo-initial-2026!').token,'Demo-initial-2026!',DEMO_PASSWORD)
    logger=logging.Logger('backup-demo-test');logger.addHandler(logging.NullHandler())
    window=BackupsDemo(load_config(root,environ={}),logger,ErrorReporter(logger),service.auth,demo_login,store.migration)
    window.show()
    try:
        wait_until(lambda:not window.jobs.tasks.busy,timeout=10000)
        assert window.shell.heading.text()=='Cadangan dan pemulihan'
        window.mutate_button.click();wait_until(lambda:not window.jobs.tasks.busy,timeout=10000)
        with store.db.transaction() as session:assert session.scalar(select(Member.full_name))=='DIUBAH SESUDAH BACKUP'
        window.logout();wait_until(lambda:window.login is None and not window.jobs.tasks.busy,timeout=10000)
        window.login_demo_button.click();wait_until(lambda:window.login is not None and not window.jobs.tasks.busy,timeout=10000)
        assert window.login.principal.username==DEMO_USER
    finally:
        window.close();wait_until(lambda:not window.isVisible(),timeout=10000);window.deleteLater()

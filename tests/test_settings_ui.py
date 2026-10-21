"""Settings UI persistence and worker options, without real faces or camera capture."""
import os
from pathlib import Path
import pytest
from PyQt6.QtTest import QTest
from app.services.settings import SettingsService
from app.ui.enrollment import EnrollmentDialog
from tests.test_auth import auth, NEW, add_role
from tests.test_database import store, graph
from tests.test_session_ui import views, sign_in, activate
from tests.test_administration_ui import open_page, settled
from app.models.entities import Role

pytestmark = pytest.mark.database


def test_settings_edit_focus_persist_restart_and_worker_snapshot(auth, store, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, 'root', NEW, wait_until)
    page = open_page(view, 'settings', wait_until)
    page.fields['similarity_threshold'].setValue(.65)
    page.fields['recognition_timeout'].setValue(4)
    page.fields['anti_spoof_threshold'].setValue(.90)
    page.fields['anti_spoof_enabled'].setChecked(False)
    page.fields['duplicate_window'].setValue(90)
    page.fields['auto_checkout'].setChecked(True)
    field = page.fields['similarity_threshold']
    activate(view)
    field.setFocus()
    for _ in range(3):
        view._check_session()
        settled(view, wait_until)
        QTest.qWait(30)
        assert field.hasFocus() and field.value() == .65
    assert 'NONAKTIF' in page.warning.text()
    page.save_button.click()
    settled(view, wait_until)
    assert 'tersimpan' in page.message.text()
    destination = os.environ.get('STARGATE_SETTINGS_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True, exist_ok=True)
        assert view.grab().save(str(Path(destination) / 'stage-09-settings.png'))
    # Construct real dialog/controller; camera/model processes stay unopened.
    with store.db.transaction() as session:
        group, member, _, _ = graph(session)
        member_id, revision = member.id, member.revision
        from app.repositories.core import EmbeddingRepository
        import numpy as np
        from app.models.entities import FaceAngle
        EmbeddingRepository(session).create(member_id, np.ones(512), FaceAngle.FRONT, model_version='synthetic-v1')
    binding = view.enrollment_service.begin(view.login.token, member_id=member_id, revision=revision, purpose='verification')
    dialog = EnrollmentDialog(view, binding, dict(code='SYN', name='Sintetis'))
    options = dialog.lab.inference.options
    assert options.similarity_threshold == .65 and options.liveness_threshold == .90
    assert not options.liveness_enabled and options.recognition_timeout == 4
    changed = dict(page.saved, similarity_threshold=.70, anti_spoof_enabled=True)
    view.settings_service.save(view.login.token, changed, page.saved)
    assert dialog.lab.inference.options == options
    dialog.reject()
    binding = view.enrollment_service.begin(view.login.token)
    registration = EnrollmentDialog(view, binding, dict(code='SYN', name='Sintetis'))
    assert registration.lab.inference.options.liveness_enabled
    assert registration.lab.inference.options.liveness_threshold == .85
    assert registration.lab.inference.options.similarity_threshold == .70
    registration.reject()
    view.close()
    wait_until(lambda: not view.isVisible(), timeout=10000)
    restarted = views(service)
    sign_in(restarted, 'root', NEW, wait_until)
    page = open_page(restarted, 'settings', wait_until)
    assert page.fields['similarity_threshold'].value() == .70
    assert page.fields['duplicate_window'].value() == 90
    assert page.fields['auto_checkout'].isChecked()


def test_settings_stale_error_preserves_edit_until_explicit_reload(auth, views, wait_until):
    view = views(auth[0]); sign_in(view, 'root', NEW, wait_until)
    page = open_page(view, 'settings', wait_until)
    initial = dict(page.saved)
    view.settings_service.save(view.login.token, dict(initial, similarity_threshold=.70), initial)
    page.fields['similarity_threshold'].setValue(.65)
    page.save_button.click(); settled(view, wait_until)
    assert 'sesi lain' in view.error_message.text() and page.fields['similarity_threshold'].value() == .65
    page.reload_button.click(); settled(view, wait_until)
    assert page.fields['similarity_threshold'].value() == .70


@pytest.mark.parametrize('role', [Role.OPERATOR, Role.VIEWER])
def test_settings_route_unavailable_for_lower_roles(auth, views, wait_until, role):
    service, root, _ = auth
    add_role(service, root, role)
    view = views(service); sign_in(view, role.value.lower(), NEW, wait_until)
    assert 'settings' not in view.shell.administrative_pages
    view.navigate('settings'); settled(view, wait_until)
    assert 'tidak memiliki izin' in view.error_message.text()

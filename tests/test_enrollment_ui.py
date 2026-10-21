import os
from pathlib import Path
import pytest
from PyQt6.QtCore import QPoint,QRect,QTimer
from PyQt6.QtTest import QTest
from sqlalchemy import select,func
from app.models.entities import Member,FaceEmbedding
from app.ui.enrollment import EnrollmentDialog
from tests.test_auth import auth,NEW
from tests.test_database import store
from tests.test_session_ui import views,sign_in
from tests.test_administration_ui import open_page,settled
from tests.support.ai_workers import streaming_camera
from tests.support.enrollment_workers import SyntheticEnrollmentTarget

pytestmark=pytest.mark.database


def ready(auth,views,wait_until):
    view=views(auth[0])
    sign_in(view,'root',NEW,wait_until)
    page=open_page(view,'members',wait_until)
    # A real group via authorized administration service.
    view.administration.save_group(view.login.token,'Capture UI')
    page.refresh()
    settled(view,wait_until)
    page.code.setText('CAP-UI-1')
    page.name.setText('Anggota Sintetis UI')
    page.group.setCurrentIndex(1)
    return view,page


def install(view,monkeypatch):
    import app.ui.session_window as module
    original=module.EnrollmentDialog
    def create(controller,binding,fields):
        return original(controller,binding,fields,target=SyntheticEnrollmentTarget(controller.enrollment_service.key,binding),capture_target=streaming_camera)
    monkeypatch.setattr(module,'EnrollmentDialog',create)


def capture_all(dialog,wait_until):
    assert dialog.lab.consent is None and dialog.lab.start_button.isEnabled()
    dialog.lab.start_button.click()
    wait_until(lambda:dialog.lab.last_result is not None,timeout=8000)
    assert not dialog.save_button.isEnabled()
    for i in range(5):
        dialog.lab.reference_button.click()
        if i<4:
            wait_until(lambda:dialog.lab.last_result and dialog.lab.last_result['captured']==i+1,timeout=5000)
        else:
            wait_until(lambda:dialog.packet is not None,timeout=5000)
    wait_until(lambda:not dialog.busy,timeout=6000)
    assert dialog.save_button.isEnabled()


def test_ui_register_reregister_and_no_partial_before_save(auth,store,views,wait_until,monkeypatch):
    view,page=ready(auth,views,wait_until)
    install(view,monkeypatch)
    assert page.capture_button.isEnabled() and not page.save_button.isEnabled()
    page.capture_button.click()
    settled(view,wait_until)
    wait_until(lambda:view.enrollment_dialog is not None)
    dialog=view.enrollment_dialog
    assert dialog.cancel_button.text()=='Batal' and dialog.save_button.text()=='Simpan'
    assert dialog.cancel_button.y()==dialog.save_button.y()
    assert abs(dialog.cancel_button.width()-dialog.save_button.width())<=1
    destination=os.environ.get('STARGATE_ENROLLMENT_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True,exist_ok=True)
        assert dialog.grab().save(str(Path(destination)/'enrollment-guide-step1.png'))
    capture_all(dialog,wait_until)
    for width,height in ((900,720),(1120,820)):
        dialog.resize(width,height)
        QTest.qWait(50)
        assert dialog.rect().contains(dialog.cancel_button.geometry())
        assert dialog.rect().contains(dialog.save_button.geometry())
        assert dialog.rect().contains(QRect(dialog.lab.preview.mapTo(dialog,QPoint()),dialog.lab.preview.size()))
        assert dialog.lab.preview.width()>=640 and dialog.lab.preview.height()>=360
        assert dialog.lab.preview.rect().contains(dialog.lab.guide.geometry())
    with store.db.transaction() as session:
        assert session.scalar(select(Member).where(Member.member_code=='CAP-UI-1')) is None
    destination=os.environ.get('STARGATE_ENROLLMENT_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True,exist_ok=True)
        assert dialog.grab().save(str(Path(destination)/'stage-08-capture-synthetic.png'))
    dialog.save_button.click()
    wait_until(lambda:view.enrollment_dialog is None,timeout=10000)
    settled(view,wait_until)
    assert page.total==1
    page.table.selectRow(0)
    settled(view,wait_until)
    member_id=page.selected.id
    assert page.capture_button.text()=='Registrasi wajah'
    page.capture_button.click()
    settled(view,wait_until)
    capture_all(view.enrollment_dialog,wait_until)
    view.enrollment_dialog.save_button.click()
    wait_until(lambda:view.enrollment_dialog is None,timeout=10000)
    settled(view,wait_until)
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==1
        assert session.scalar(select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.member_id==member_id))==5


def test_stop_discards_complete_capture_and_restart_can_capture_again(auth,store,views,wait_until,monkeypatch):
    view,page=ready(auth,views,wait_until)
    install(view,monkeypatch)
    page.capture_button.click()
    settled(view,wait_until)
    dialog=view.enrollment_dialog
    capture_all(dialog,wait_until)
    assert dialog.lab.stop_button.isEnabled()
    dialog.lab.stop_button.click()
    assert dialog.packet is None and not dialog.save_button.isEnabled()
    assert dialog.lab.latest is None and dialog.lab.completed_photo is None
    assert dialog.lab.preview.text()=='' and dialog.lab.preview.pixmap().isNull()
    assert dialog.lab.guide.text().startswith('1/5')
    assert dialog.lab.start_button.isEnabled()
    capture_all(dialog,wait_until)
    assert dialog.packet is not None and dialog.save_button.isEnabled()
    dialog.cancel_button.click()
    wait_until(lambda:view.enrollment_dialog is None,timeout=10000)
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==0


def test_auto_capture_completes_without_capture_click_and_still_requires_save(auth,store,views,wait_until,monkeypatch):
    view,page=ready(auth,views,wait_until)
    install(view,monkeypatch)
    page.capture_button.click()
    settled(view,wait_until)
    dialog=view.enrollment_dialog
    dialog.lab.start_button.click()
    wait_until(lambda:dialog.packet is not None,timeout=20000)
    wait_until(lambda:not dialog.busy,timeout=8000)
    assert dialog.lab.complete and dialog.save_button.isEnabled()
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==0
        assert session.scalar(select(func.count()).select_from(FaceEmbedding))==0
    dialog.save_button.click()
    wait_until(lambda:view.enrollment_dialog is None,timeout=10000)
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==1
        assert session.scalar(select(func.count()).select_from(FaceEmbedding))==5


@pytest.mark.parametrize('action',['cancel','logout','password','close','timeout'])
def test_capture_cancel_and_session_end_leave_no_member(auth,store,views,wait_until,monkeypatch,action):
    view,page=ready(auth,views,wait_until)
    install(view,monkeypatch)
    page.capture_button.click()
    settled(view,wait_until)
    dialog=view.enrollment_dialog
    dialog.lab.start_button.click()
    wait_until(lambda:dialog.lab.last_result is not None,timeout=8000)
    dialog.lab.reference_button.click()
    wait_until(lambda:dialog.lab.last_result and dialog.lab.last_result['captured']==1,timeout=5000)
    if action=='cancel':dialog.cancel_button.click()
    elif action=='logout':view.logout()
    elif action=='password':view.open_password()
    elif action=='close':view.close()
    else:
        from datetime import timedelta
        auth[2][0]+=timedelta(minutes=16)
        view._check_session()
    wait_until(lambda:view.enrollment_dialog is None,timeout=10000)
    assert not dialog.lab.cameras.busy and not dialog.lab.inference.active
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Member))==0
        assert session.scalar(select(func.count()).select_from(FaceEmbedding))==0


def test_stored_face_verification_after_window_restart(auth,store,views,wait_until,monkeypatch):
    from tests.test_enrollment_capture import packet
    view,page=ready(auth,views,wait_until)
    install(view,monkeypatch)
    # Seed exclusively through the real signed enrollment service, with synthetic data.
    service=view.enrollment_service
    row=service.save(view.login.token,packet(service,service.begin(view.login.token)),
        code='CAP-UI-1',name='Anggota Sintetis UI',group_id=page.group.currentData())
    view.close()
    wait_until(lambda:not view.isVisible(),timeout=8000)
    restarted=views(auth[0])
    sign_in(restarted,'root',NEW,wait_until)
    page=open_page(restarted,'members',wait_until)
    page.table.selectRow(0)
    settled(restarted,wait_until)
    assert page.verify_button.isEnabled()
    page.verify_button.click()
    settled(restarted,wait_until)
    dialog=restarted.enrollment_dialog
    assert dialog.verification
    dialog.lab.start_button.click()
    wait_until(lambda:dialog.lab.last_result is not None,timeout=8000)
    dialog.lab.reference_button.click()
    wait_until(lambda:dialog.packet is not None,timeout=5000)
    dialog.save_button.click()
    wait_until(lambda:'Cocok dengan anggota terpilih' in dialog.message.text(),timeout=10000)
    dialog.cancel_button.click()
    wait_until(lambda:restarted.enrollment_dialog is None,timeout=8000)
    with store.db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.member_id==row.id))==5

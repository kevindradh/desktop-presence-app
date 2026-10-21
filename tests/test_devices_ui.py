"""Stage 6 UI with isolated PostgreSQL and synthetic camera workers."""
import pytest
from PyQt6.QtCore import QItemSelectionModel
from PyQt6.QtWidgets import QLineEdit, QMessageBox

from app.services.device_secrets import DeviceSecretStore
from tests.test_auth import auth, NEW
from tests.test_credentials import MemoryKeyring
from tests.test_database import store
from tests.test_session_ui import views, sign_in
from tests.test_administration_ui import settled, open_page, answer
from tests.support.camera_workers import streaming, hung_open, recovering

pytestmark = pytest.mark.database


def ready(auth, views, wait_until):
    view = views(auth[0])
    view.devices_service.secrets = DeviceSecretStore(view.config, backend=MemoryKeyring())
    view.cameras.capture_target = streaming
    sign_in(view, "root", NEW, wait_until)
    return view, open_page(view, "devices", wait_until)


def create(page, view, wait_until, name="Webcam", index=0):
    page.new_button.click()
    page.name.setText(name)
    page.camera_index.setValue(index)
    page.location.setCurrentIndex(1)
    assert page.save_button.isEnabled()
    page.save_button.click()
    settled(view, wait_until)
    page.table.selectRow(next(i for i,r in enumerate(page.rows) if r.name == name))
    assert page.preview_button.isEnabled() and page.test_button.isEnabled()
    return page.selected.id


def test_device_form_crud_rtsp_masking_and_type_change(auth, views, wait_until):
    view,page = ready(auth,views,wait_until)
    assert not page.save_button.isEnabled() and not page.preview_button.isEnabled()
    create(page,view,wait_until)
    page.name.setText("Webcam edit")
    page.save_button.click()
    settled(view,wait_until)
    assert page.rows[0].name == "Webcam edit"
    page.new_button.click()
    page.kind.setCurrentIndex(page.kind.findData("RTSP"))
    page.name.setText("IP contoh")
    page.location.setCurrentIndex(1)
    assert not page.save_button.isEnabled() and not page.camera_index.isEnabled()
    page.rtsp.setText("rtsp://synthetic:secret@127.0.0.1:9/private?token=hidden")
    assert page.rtsp.echoMode() == QLineEdit.EchoMode.Password
    page.show_source.setChecked(True)
    assert page.rtsp.echoMode() == QLineEdit.EchoMode.Normal
    page.save_button.click()
    settled(view,wait_until)
    page.table.selectRow(next(i for i,r in enumerate(page.rows) if r.kind.value == "RTSP"))
    assert not page.rtsp.text() and not page.show_source.isChecked()
    assert page.rtsp.echoMode() == QLineEdit.EchoMode.Password
    assert "secret" not in page.table.item(page.table.currentRow(),2).text()
    assert page.save_button.isEnabled()
    page.rtsp.setText("rtsp://other:secret@127.0.0.1:9/private")
    page.kind.setCurrentIndex(page.kind.findData("USB"))
    assert not page.rtsp.text() and page.camera_index.isEnabled()
    page.save_button.click()
    settled(view,wait_until)
    assert not view.devices_service.secrets.credentials._backend().entries
    page.table.selectRow(0)
    page.delete_button.click()
    answer(page,QMessageBox.StandardButton.No,wait_until)
    assert len(page.rows)==2
    page.delete_button.click()
    answer(page,QMessageBox.StandardButton.Yes,wait_until)
    settled(view,wait_until)
    assert len(page.rows)==1


def test_preview_two_streams_stop_and_navigation_release(auth, views, wait_until):
    view,page = ready(auth,views,wait_until)
    first=create(page,view,wait_until,"Pertama",0)
    second=create(page,view,wait_until,"Kedua",1)
    selection=page.table.selectionModel()
    for row in range(2):
        selection.select(page.table.model().index(row,0),QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows)
    assert not page.test_button.isEnabled() and page.preview_button.isEnabled()
    page.preview_button.click()
    settled(view,wait_until)
    wait_until(lambda: all(view.cameras.nodes[i].frames>=2 for i in (first,second)),timeout=8000)
    assert page.stop_button.isEnabled()
    assert all(not page.cards[i][1].pixmap().isNull() for i in (first,second))
    import os
    from pathlib import Path
    evidence=os.environ.get("STARGATE_DEVICE_EVIDENCE")
    if evidence:
        folder=Path(evidence)
        folder.mkdir(parents=True,exist_ok=True)
        assert view.grab().save(str(folder/"stage-06-devices-synthetic.png"))
        from PyQt6.QtWidgets import QScrollArea
        scroll=page.parentWidget()
        while not isinstance(scroll,QScrollArea):
            scroll=scroll.parentWidget()
        scroll.ensureWidgetVisible(page.cards[first][0])
        from PyQt6.QtTest import QTest
        QTest.qWait(100)
        assert view.grab().save(str(folder/"stage-06-preview-synthetic.png"))
    view.navigate("dashboard")
    settled(view,wait_until)
    wait_until(lambda: not view.cameras.busy,timeout=6000)
    assert all(n.process is None and n.pixels is None for n in view.cameras.nodes.values())
    page=open_page(view,"devices",wait_until)
    page.table.selectRow(0)
    page.test_button.click()
    settled(view,wait_until)
    wait_until(lambda: not view.cameras.busy,timeout=8000)
    assert view.cameras.nodes[page.selected.id].state=="test_ok"


def test_local_disconnect_requires_manual_restart(auth,views,wait_until,tmp_path):
    view,page=ready(auth,views,wait_until)
    device=create(page,view,wait_until,name=str(tmp_path/"remapped"))
    view.cameras.capture_target=recovering
    page.preview_button.click()
    settled(view,wait_until)
    wait_until(lambda:not view.cameras.busy,timeout=6000)
    node=view.cameras.nodes[device]
    assert node.state=="failed" and node.attempts==0 and node.process is None
    assert "manual" in page.cards[device][2].text()
    assert page.preview_button.isEnabled() and not page.stop_button.isEnabled()
    page.preview_button.click()
    settled(view,wait_until)
    wait_until(lambda:view.cameras.nodes[device].frames>0,timeout=6000)


@pytest.mark.parametrize("action",["logout","password","close","expired"])
def test_session_actions_stop_owned_camera(auth,views,wait_until,action):
    view,page=ready(auth,views,wait_until)
    device=create(page,view,wait_until)
    view.cameras.capture_target=hung_open
    page.preview_button.click()
    settled(view,wait_until)
    wait_until(lambda: device in view.cameras.nodes and view.cameras.busy)
    if action=="logout":
        view.logout()
    elif action=="password":
        view.open_password()
    elif action=="close":
        view.close()
    else:
        from datetime import timedelta
        auth[2][0]+=timedelta(minutes=16)
        view._check_session()
    wait_until(lambda: not view.cameras.busy,timeout=6000)
    wait_until(lambda: not view.jobs.tasks.busy,timeout=10000)
    assert view.cameras.nodes[device].process is None
    if action in {"logout","expired"}:
        assert view.login is None
    if action=="close":
        wait_until(lambda: not view.isVisible(),timeout=5000)

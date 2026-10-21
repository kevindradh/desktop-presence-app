"""UI-to-database attendance pipeline with signed synthetic inference and camera."""
from datetime import timedelta
import os
from pathlib import Path
from threading import Event
import time
import pytest
from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtTest import QTest
from app.services.database import DatabaseUnavailable
from app.services.settings import SettingsService
from tests.test_auth import auth, NEW
from tests.test_database import store
from tests.test_session_ui import views, sign_in
from tests.test_administration_ui import open_page
from tests.test_attendance import attendance, rows
from tests.support.ai_workers import streaming_camera
from tests.support.attendance_workers import SyntheticAttendanceTarget

pytestmark=pytest.mark.database


class Sound:
    def __init__(self,store):self.store=store;self.plays=0
    def play(self):
        assert rows(self.store), 'Success sound must follow a committed attendance'
        self.plays+=1
    def status(self):return QSoundEffect.Status.Ready


def ready(attendance, views, wait_until, store, *, status='ready',delay=0):
    data=attendance
    data.service.monotonic=time.monotonic
    view=views(data.auth)
    view.attendance_service=data.service
    view.cameras.capture_target=streaming_camera
    sign_in(view,'root',NEW,wait_until)
    page=open_page(view,'attendance',wait_until)
    page.target_factory=lambda key,binding:SyntheticAttendanceTarget(key,binding,status,delay)
    page.sound=Sound(store)
    page.consent.setChecked(True)
    page.device_table.selectRow(next(i for i,row in enumerate(page.rows) if row.id==data.device))
    assert page.start_button.isEnabled()
    return view,page


def test_camera_inference_commit_feedback_sound_history_and_latch(attendance, store, views, wait_until):
    view,page=ready(attendance,views,wait_until,store)
    page.start_button.click()
    wait_until(lambda:page.sound.plays==1,timeout=12000)
    wait_until(lambda:page.history.rowCount()==1,timeout=6000)
    assert 'berhasil tersimpan' in page.message.text()
    assert rows(store)[0].attendance_type.value=='IN'
    destination=os.environ.get('STARGATE_ATTENDANCE_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True,exist_ok=True)
        assert view.grab().save(str(Path(destination)/'stage-10-attendance-synthetic.png'))
    attendance.now[0]+=timedelta(seconds=61)
    QTest.qWait(500)
    assert len(rows(store))==1 and page.sound.plays==1
    page.stop_button.click()
    wait_until(lambda:not page.busy and not view.cameras.busy,timeout=8000)
    page.start_button.click()
    wait_until(lambda:page.sound.plays==2,timeout=12000)
    assert rows(store)[1].attendance_type.value=='OUT'
    page.stop_button.click()
    wait_until(lambda:not page.busy,timeout=8000)
    member_page=open_page(view,'members',wait_until)
    member_page.table.selectRow(0)
    wait_until(lambda:member_page.detail is not None)
    assert member_page.detail.history_total==2


@pytest.mark.parametrize('action',['stop','navigation','password','logout','close','timeout'])
def test_attendance_lifecycle_releases_workers_and_camera(attendance, store, views, wait_until, auth, action):
    view,page=ready(attendance,views,wait_until,store,status='spoof')
    page.start_button.click()
    wait_until(lambda:page.nodes and all(n.inference.state=='ready' for n in page.nodes.values()),timeout=10000)
    if action=='stop':page.stop_button.click()
    elif action=='navigation':view.navigate('members')
    elif action=='password':view.open_password()
    elif action=='logout':view.logout()
    elif action=='close':view.close()
    else:
        auth[2][0]+=timedelta(minutes=16)
        view._check_session()
    wait_until(lambda:not page.busy and not view.cameras.busy,timeout=12000)
    assert not attendance.service.flows and not rows(store) and page.sound.plays==0


def test_spoof_never_reaches_storage_and_error_never_plays_success(attendance, store, views, wait_until):
    view,page=ready(attendance,views,wait_until,store,status='spoof')
    page.start_button.click()
    wait_until(lambda:page.nodes and any('Spoof Detected' in n.status.text() for n in page.nodes.values()),timeout=10000)
    assert not rows(store) and page.sound.plays==0
    page.stop()
    wait_until(lambda:not page.busy,timeout=8000)
    page.target_factory=SyntheticAttendanceTarget
    def unavailable(*args):raise DatabaseUnavailable()
    attendance.service.submit=unavailable
    page.start_button.click()
    wait_until(lambda:view.login is None,timeout=12000)
    wait_until(lambda:not page.busy and not view.cameras.busy,timeout=8000)
    assert not rows(store) and page.sound.plays==0


def test_setting_change_during_inference_requires_restart_and_no_commit(attendance, store, views, wait_until):
    view,page=ready(attendance,views,wait_until,store,delay=.5)
    page.start_button.click()
    wait_until(lambda:page.nodes and any(n.inference.state=='busy' for n in page.nodes.values()),timeout=12000)
    settings=SettingsService(attendance.auth)
    before=settings.load(view.login.token)
    settings.save(view.login.token,dict(before,similarity_threshold=.65),before)
    wait_until(lambda:not page.busy,timeout=10000)
    assert not rows(store) and page.sound.plays==0 and 'Pengaturan berubah' in page.message.text()


def test_two_camera_pipeline_stores_one_event_and_does_not_auto_out_while_present(attendance, store, views, wait_until):
    from PyQt6.QtCore import QItemSelectionModel
    view,page=ready(attendance,views,wait_until,store)
    index=next(i for i,row in enumerate(page.rows) if row.id==attendance.second)
    page.device_table.selectionModel().select(page.device_table.model().index(index,0),
        QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    assert len(page.device_table.selectionModel().selectedRows())==2
    page.start_button.click()
    wait_until(lambda:len(page.nodes)==2 and page.sound.plays==1,timeout=15000)
    QTest.qWait(500)
    attendance.now[0]+=timedelta(seconds=61)
    QTest.qWait(500)
    assert len(rows(store))==1 and page.sound.plays==1
    page.stop_button.click()
    wait_until(lambda:not page.busy and not view.cameras.busy,timeout=10000)


def test_refresh_stays_enabled_during_scans_and_queues_one_manual_reload(attendance, store, views, wait_until, monkeypatch):
    view,page=ready(attendance,views,wait_until,store)
    page.start_button.click()
    wait_until(lambda:page.history.rowCount()==1 and not page.reloading,timeout=12000)

    changes=[]
    class EnabledChanges(QObject):
        def eventFilter(self, watched, event):
            if event.type()==QEvent.Type.EnabledChange:
                changes.append(watched.isEnabled())
            return False
    observer=EnabledChanges(page.reload_button)
    page.reload_button.installEventFilter(observer)
    submit=attendance.service.submit
    setup=attendance.service.setup
    calls=[]
    loads=[]
    block,started,release=Event(),Event(),Event()
    def submitting(*args):
        calls.append(True)
        if block.is_set():
            started.set()
            assert release.wait(5), 'Test must release the in-flight scan'
        else:
            time.sleep(.1)
        return submit(*args)
    def loading(*args):
        loads.append(True)
        return setup(*args)
    monkeypatch.setattr(attendance.service,'submit',submitting)
    monkeypatch.setattr(attendance.service,'setup',loading)
    try:
        wait_until(lambda:len(calls)>=3,timeout=8000)
        assert changes==[] and page.reload_button.isEnabled() and loads==[]
        block.set()
        wait_until(started.is_set,timeout=8000)
        page.reload_button.click()
        assert not page.reload_button.isEnabled() and page.reload_requested
        page.reload()  # Repeated requests coalesce while a scan is in flight.
        assert loads==[]
        release.set()
        wait_until(lambda:len(loads)==1 and page.reload_button.isEnabled(),timeout=8000)
        assert changes==[False,True]
        assert page.history.rowCount()==1 and len(rows(store))==1
    finally:
        release.set()
        page.stop()
        wait_until(lambda:not page.busy and not view.cameras.busy,timeout=10000)

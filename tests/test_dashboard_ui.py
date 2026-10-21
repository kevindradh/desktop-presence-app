"""Automatic refresh across terminals, stable controls and bounded lifecycle."""
import copy
from datetime import timedelta
import os
from pathlib import Path
from threading import Event
import time

import pytest
from PyQt6.QtCore import QDate, QPoint, Qt
from PyQt6.QtTest import QTest

from app.services.attendance import AttendanceService
from app.services.auth import AuthService
from app.services.database import DatabaseUnavailable
from app.services.devices import DevicesService
from tests.test_auth import auth, NEW
from tests.test_database import store
from tests.test_attendance import attendance, scan, DAY
from tests.test_session_ui import views, sign_in, activate

pytestmark=pytest.mark.database


def ready(data, views, wait_until):
    view=views(data.auth)
    view.dashboard_service.clock=lambda:data.now[0]
    sign_in(view,'root',NEW,wait_until)
    page=view.shell.administrative_pages['dashboard']
    page.timer.setInterval(50)
    wait_until(lambda:page.snapshot is not None,timeout=10000)
    return view,page


def test_dashboard_updates_from_other_terminal_without_refresh_and_keeps_focus(attendance, store, views, wait_until):
    data=attendance
    view,page=ready(data,views,wait_until)
    activate(view)
    page.date.setFocus()
    wait_until(page.date.hasFocus)
    original_date=page.date.date()
    other=copy.copy(data)
    other.auth=AuthService(store.db,clock=data.auth.clock)
    other.service=AttendanceService(other.auth,view.config,DevicesService(other.auth,view.config),clock=lambda:data.now[0],monotonic=lambda:data.mono[0])
    data.now[0]+=timedelta(minutes=11)
    assert scan(other).saved
    wait_until(lambda:page.snapshot.present==1 and page.feed.rowCount()==1,timeout=8000)
    assert page.counters['late'].text()=='1' and page.date.hasFocus() and page.date.date()==original_date
    QTest.qWait(250)
    assert page.feed.rowCount()==1 and page.date.hasFocus()
    destination=os.environ.get('STARGATE_DASHBOARD_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True,exist_ok=True)
        assert view.grab().save(str(Path(destination)/'stage-11-dashboard.png'))


@pytest.mark.parametrize('return_today',[False,True])
def test_date_filter_change_during_load_drops_old_result(attendance, views, wait_until, monkeypatch,return_today):
    view,page=ready(attendance,views,wait_until)
    service=view.dashboard_service
    load=service.load
    began,release=Event(),Event()
    calls=[]
    def slow(token,day):
        calls.append(day)
        if len(calls)==1:
            began.set()
            assert release.wait(5)
        return load(token,day)
    monkeypatch.setattr(service,'load',slow)
    page.reload()
    try:
        wait_until(began.is_set)
        previous=DAY-timedelta(days=1)
        page.date.setDate(QDate(previous.year,previous.month,previous.day))
        assert not page.follow_today and page.snapshot is None
        if return_today:
            QTest.mouseClick(page.today, Qt.MouseButton.LeftButton)
            assert page.follow_today and page.date.date().toPyDate()==DAY
        expected=DAY if return_today else previous
        release.set()
        wait_until(lambda:page.snapshot is not None and page.snapshot.work_date==expected,timeout=8000)
        assert page.snapshot.pending==(1 if return_today else 0)
    finally:
        release.set()


def test_dashboard_rolls_date_only_when_follow_today_is_enabled(attendance, views, wait_until):
    view,page=ready(attendance,views,wait_until)
    attendance.now[0]+=timedelta(days=1)
    wait_until(lambda:page.snapshot is not None and page.snapshot.work_date==DAY+timedelta(days=1),timeout=8000)
    selected=DAY
    page.date.setDate(QDate(selected.year,selected.month,selected.day))
    wait_until(lambda:page.snapshot is not None and page.snapshot.work_date==selected,timeout=8000)
    attendance.now[0]+=timedelta(days=1)
    QTest.qWait(250)
    assert page.snapshot.work_date==selected
    QTest.mouseClick(page.today,Qt.MouseButton.LeftButton)
    wait_until(lambda:page.snapshot is not None and page.snapshot.work_date==DAY+timedelta(days=2),timeout=8000)


def test_dashboard_empty_date_keyboard_filter_and_desktop_sizes(attendance, views, wait_until):
    view,page=ready(attendance,views,wait_until)
    activate(view)
    previous=DAY-timedelta(days=1)
    page.date.setDate(QDate(previous.year,previous.month,previous.day))
    wait_until(lambda:page.snapshot is not None and page.snapshot.work_date==previous,timeout=8000)
    QTest.mouseClick(page.date, Qt.MouseButton.LeftButton,
                     pos=QPoint(page.date.width()-8,page.date.height()//2))
    wait_until(lambda:page.date.calendarWidget().isVisible())
    QTest.keyClick(page.date.calendarWidget(), Qt.Key.Key_Escape)
    wait_until(lambda:not page.date.calendarWidget().isVisible())
    activate(view)
    page.date.setFocus()
    wait_until(page.date.hasFocus)
    # Qt visits the day, month and year sections before leaving the date field.
    for _ in range(3):
        QTest.keyClick(page.date, Qt.Key.Key_Tab)
        if page.today.hasFocus():
            break
    assert page.today.hasFocus()
    QTest.keyClick(page.today, Qt.Key.Key_Space)
    assert page.follow_today and page.date.date().toPyDate()==DAY
    wait_until(lambda:not page.busy)
    previous=DAY-timedelta(days=1)
    page.date.setDate(QDate(previous.year,previous.month,previous.day))
    wait_until(lambda:page.snapshot is not None and page.snapshot.work_date==previous,timeout=8000)
    assert not page.follow_today
    assert page.feed_empty.isVisible() and page.feed.rowCount()==0
    assert page.counters['present'].text()=='0'
    for width,height in ((1000,740),(1180,820),(1440,900)):
        view.resize(width,height)
        QTest.qWait(50)
        cards=[value.parentWidget() for value in page.counters.values()]
        for value in page.counters.values():
            assert value.parentWidget().rect().contains(value.geometry())
        for index,card in enumerate(cards):
            assert page.rect().contains(card.geometry())
            assert all(not card.geometry().intersects(other.geometry()) for other in cards[index+1:])
        assert page.date.geometry().right()<page.today.geometry().left()
        scroll=view.shell.pages.currentWidget()
        assert scroll.horizontalScrollBar().maximum()==0
        destination=os.environ.get('STARGATE_DASHBOARD_EVIDENCE')
        if destination:
            Path(destination).mkdir(parents=True,exist_ok=True)
            assert view.grab().save(str(Path(destination)/f'dashboard-empty-{width}.png'))


def test_failure_marks_stale_and_recovers_without_fake_zeros(attendance, views, wait_until, monkeypatch):
    view,page=ready(attendance,views,wait_until)
    assert page.counters['pending'].text()=='1'
    load=view.dashboard_service.load
    def fail(*args):raise DatabaseUnavailable()
    monkeypatch.setattr(view.dashboard_service,'load',fail)
    wait_until(lambda:'belum diperbarui' in page.status.text(),timeout=8000)
    assert page.status.isVisible()
    assert page.counters['pending'].text()=='1'
    monkeypatch.setattr(view.dashboard_service,'load',load)
    wait_until(lambda:not page.status.isVisible(),timeout=8000)
    assert page.status.text()==''


def test_initial_dashboard_failure_does_not_claim_empty_data(attendance, views, wait_until, monkeypatch):
    view=views(attendance.auth)
    view.dashboard_service.clock=lambda:attendance.now[0]
    load=view.dashboard_service.load
    def fail(*args):raise DatabaseUnavailable()
    monkeypatch.setattr(view.dashboard_service,'load',fail)
    sign_in(view,'root',NEW,wait_until)
    page=view.shell.administrative_pages['dashboard']
    page.timer.setInterval(50)
    wait_until(lambda:'belum diperbarui' in page.status.text(),timeout=8000)
    assert page.snapshot is None
    assert all(value.text()=='...' for value in page.counters.values())
    assert not page.feed_empty.isVisible()
    assert all(chart.empty_text=='Data kehadiran belum tersedia.' for chart in page.charts.values())
    monkeypatch.setattr(view.dashboard_service,'load',load)
    wait_until(lambda:page.snapshot is not None,timeout=8000)
    assert page.counters['pending'].text()=='1'


@pytest.mark.parametrize('action',['navigation','logout','close'])
def test_dashboard_leaving_during_load_does_not_keep_polling(attendance, views, wait_until, monkeypatch, action):
    view,page=ready(attendance,views,wait_until)
    load=view.dashboard_service.load
    began,release=Event(),Event()
    calls=[]
    def slow(*args):
        calls.append(True)
        began.set()
        assert release.wait(5)
        return load(*args)
    monkeypatch.setattr(view.dashboard_service,'load',slow)
    page.reload()
    try:
        wait_until(began.is_set)
        if action=='navigation':view.navigate('members')
        elif action=='logout':view.logout()
        else:view.close()
        release.set()
        wait_until(lambda:not page.busy,timeout=8000)
        if action=='navigation':wait_until(lambda:view.shell.heading.text()=='Anggota')
        elif action=='logout':wait_until(lambda:view.login is None)
        else:wait_until(lambda:not view.isVisible(),timeout=10000)
        count=len(calls)
        QTest.qWait(250)
        assert len(calls)==count
    finally:
        release.set()


def test_dashboard_revoked_session_clears_data(attendance, views, wait_until):
    view,page=ready(attendance,views,wait_until)
    attendance.auth.logout(view.login.token)
    wait_until(lambda:view.login is None,timeout=8000)


def test_polling_keeps_camera_stream_and_ui_heartbeat_running(attendance, views, wait_until):
    from database.attendance_demo import synthetic_camera
    view,page=ready(attendance,views,wait_until)
    view.cameras.capture_target=synthetic_camera
    capture=attendance.service.begin(attendance.token,[attendance.device],'IN')[0]
    view.cameras.start_many([capture.spec])
    try:
        wait_until(lambda:view.cameras.nodes[attendance.device].frames>=3,timeout=10000)
        first=view.cameras.nodes[attendance.device].frames
        heartbeat=view.shell.heartbeat_count
        QTest.qWait(500)
        assert view.cameras.nodes[attendance.device].frames>first
        assert view.shell.heartbeat_count>heartbeat and page.snapshot is not None
    finally:
        view.cameras.stop_all()
        attendance.service.cancel_all()
        wait_until(lambda:not view.cameras.busy,timeout=10000)


def test_dashboard_demo_seed_and_terminal_button(store, tmp_path, qt_app, wait_until):
    import logging
    from app.services.errors import ErrorReporter
    from app.settings.config import load_config
    from app.ui.dashboard_demo import DashboardDemo
    from app.ui.theme import apply_theme
    from database.dashboard_demo import seed_dashboard_demo
    config=load_config(tmp_path,environ={})
    data=seed_dashboard_demo(store,config)
    logger=logging.Logger('demo-dashboard-test');logger.addHandler(logging.NullHandler())
    apply_theme(qt_app)
    view=DashboardDemo(config,logger,ErrorReporter(logger),data)
    view.show()
    page=view.shell.administrative_pages['dashboard']
    page.timer.setInterval(50)
    try:
        wait_until(lambda:page.snapshot is not None,timeout=10000)
        snap=page.snapshot
        assert (snap.registered,snap.present,snap.late,snap.absent,snap.on_leave,snap.pending)==(5,2,1,1,1,1)
        destination=os.environ.get('STARGATE_DASHBOARD_EVIDENCE')
        if destination:
            Path(destination).mkdir(parents=True,exist_ok=True)
            assert view.grab().save(str(Path(destination)/'stage-11-demo.png'))
            assert page.grab().save(str(Path(destination)/'dashboard-full-synthetic.png'))
        # Queue a click made while a background session check is running.
        wait_until(lambda:not view.jobs.tasks.busy)
        entered,release=Event(),Event()
        def poll():
            entered.set()
            assert release.wait(5)
            return data.auth.inspect(data.login.token)
        assert view.jobs.run(poll,lambda result:None,blocks_ui=False)
        try:
            wait_until(entered.is_set)
            view.scan_button.click()
            assert view.jobs.queued is not None
        finally:release.set()
        wait_until(lambda:page.snapshot.present==3,timeout=10000)
        assert page.snapshot.late==2 and page.snapshot.pending==0 and len(page.snapshot.activity)==3
        wait_until(lambda:not view.jobs.tasks.busy and view.end_button.isEnabled())
        view.end_button.click()
        wait_until(lambda:page.snapshot.updated.hour==17,timeout=10000)
        assert page.snapshot.absent==1
    finally:
        view.close()
        wait_until(lambda:not view.isVisible(),timeout=12000)
        view.deleteLater()
        qt_app.processEvents()

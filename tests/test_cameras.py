from dataclasses import replace
import time

import pytest
from PyQt6.QtTest import QTest

from app.services.camera_capture import CaptureSpec, FRAME_BYTES
from app.services.cameras import CameraManager, FINAL
from app.services.database import DataValidationError
from app.settings.config import load_config
from tests.support.camera_workers import failing, frozen_read, hung_open, recovering, streaming


def spec(index=0, device_id=1, **changes):
    return replace(CaptureSpec(device_id,"Sintetis","USB",index,640,480,30), **changes)


@pytest.fixture
def managers(qt_app, tmp_path, wait_until):
    created=[]
    def create(target=streaming, **settings):
        defaults=dict(camera_open_timeout=1,camera_read_timeout=1,camera_reconnect_attempts=0)
        defaults.update(settings)
        config=replace(load_config(tmp_path,environ={}),**defaults)
        manager=CameraManager(config,capture_target=target)
        created.append(manager)
        return manager
    yield create
    for manager in created:
        manager.stop_all()
        wait_until(lambda: not manager.busy,timeout=6000)
        manager.shutdown_now()
        manager.deleteLater()
    qt_app.processEvents()


def test_preview_frame_rgb_and_clean_repeated_open_stop(managers,wait_until):
    manager=managers()
    frames=[]
    manager.frame_ready.connect(lambda device,image: frames.append(image))
    for _ in range(2):
        manager.start_many([spec()])
        wait_until(lambda: manager.nodes[1].frames>=2,timeout=6000)
        image=next(image for image in reversed(frames) if not image.isNull())
        assert image.pixelColor(0,0).getRgb()[:3]==(20,100,60)
        assert manager.nodes[1].actual_size==(640,480)
        manager.stop_all()
        wait_until(lambda: not manager.busy)
        assert manager.nodes[1].process is None and manager.nodes[1].pixels is None
        assert frames[-1].isNull()


def test_connection_check_stops_without_displaying_frames(managers,wait_until):
    manager=managers()
    images=[]
    manager.frame_ready.connect(lambda device,image: images.append(image))
    manager.start_many([spec()],test=True)
    wait_until(lambda: not manager.busy,timeout=6000)
    assert manager.nodes[1].state=="test_ok" and manager.nodes[1].frames==1
    assert all(image.isNull() for image in images)


def test_multicamera_limit_and_duplicate_source(managers,wait_until):
    manager=managers()
    with pytest.raises(DataValidationError):
        manager.start_many([spec(),spec(device_id=2,kind="INTERNAL")])
    manager.start_many([spec(),spec(index=1,device_id=2)])
    wait_until(lambda: all(n.frames for n in manager.nodes.values()),timeout=6000)
    with pytest.raises(DataValidationError):
        manager.start_many([spec(index=2,device_id=3)])
    assert len([n for n in manager.nodes.values() if n.state not in FINAL])==2


def test_latest_frame_slot_does_not_queue_backlog(managers,wait_until):
    manager=managers()
    manager.start_many([spec()])
    wait_until(lambda: manager.nodes[1].frames>=1,timeout=6000)
    manager.timer.stop()
    node=manager.nodes[1]
    before=node.frames
    QTest.qWait(200)
    manager.poll()
    assert node.frames==before+1 and node.last_sequence>node.frames
    assert len(node.pixels)==FRAME_BYTES
    manager.timer.start()


def test_hung_open_is_bounded_and_process_reaped(managers,wait_until):
    manager=managers(hung_open)
    started=time.monotonic()
    manager.start_many([spec()])
    wait_until(lambda: not manager.busy,timeout=6000)
    node=manager.nodes[1]
    assert node.state=="failed" and node.process is None and time.monotonic()-started<4


def test_stale_frame_cleared_before_read_watchdog(managers,wait_until):
    manager=managers(frozen_read,camera_read_timeout=2)
    images=[]
    manager.frame_ready.connect(lambda device,image: images.append(image))
    manager.start_many([spec()])
    wait_until(lambda: any(not image.isNull() for image in images),timeout=6000)
    wait_until(lambda: images[-1].isNull(),timeout=1800)
    assert manager.nodes[1].state=="streaming"
    wait_until(lambda: not manager.busy,timeout=4000)
    assert manager.nodes[1].state=="failed"


def test_reconnect_attempts_bounded_and_secret_discarded(managers,wait_until):
    manager=managers(failing,camera_reconnect_attempts=2)
    secret="rtsp://synthetic:private@127.0.0.1:9/private?token=private"
    specification=spec(kind="RTSP",rtsp_source=secret)
    assert secret not in repr(specification)
    manager.start_many([specification])
    wait_until(lambda: not manager.busy,timeout=10000)
    node=manager.nodes[1]
    assert node.state=="failed" and node.attempts==2 and not node.spec.rtsp_source


def test_reconnect_recovers_and_stop_during_backoff(managers,wait_until,tmp_path):
    manager=managers(recovering,camera_reconnect_attempts=1)
    manager.start_many([spec(name=str(tmp_path/"retry"),kind="RTSP",rtsp_source="rtsp://127.0.0.1:9/synthetic")])
    wait_until(lambda: manager.nodes[1].state=="streaming",timeout=7000)
    assert manager.nodes[1].attempts==1
    manager.stop_all()
    wait_until(lambda: not manager.busy)
    second=managers(failing,camera_reconnect_attempts=1)
    second.start_many([spec(kind="RTSP",rtsp_source="rtsp://127.0.0.1:9/synthetic")])
    wait_until(lambda: second.nodes[1].state=="retry_wait",timeout=6000)
    second.stop_all()
    assert not second.busy and second.nodes[1].state=="stopped"


def test_shutdown_force_cleans_owned_hung_process(managers,wait_until):
    manager=managers(hung_open)
    manager.start_many([spec()])
    manager.shutdown_now()
    assert not manager.busy and manager.nodes[1].process is None


@pytest.mark.parametrize("kind",["USB","INTERNAL"])
def test_local_failure_does_not_reopen_reassigned_index(managers,wait_until,tmp_path,kind):
    # First capture fails; reopening the same index would yield a different source.
    manager=managers(recovering,camera_reconnect_attempts=3)
    source=spec(kind=kind,name=str(tmp_path/"index-remapped"))
    manager.start_many([source])
    wait_until(lambda:not manager.busy,timeout=6000)
    node=manager.nodes[1]
    QTest.qWait(1800)
    assert node.state=="failed" and node.attempts==0 and node.frames==0
    assert node.process is None and node.pixels is None
    # An explicit manual action can start again after the user verifies the index.
    manager.start_many([source])
    wait_until(lambda:manager.nodes[1].frames>0,timeout=6000)

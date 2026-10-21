from dataclasses import replace
import numpy as np
import pytest
from app.services.inference import InferenceController
from app.settings.config import load_config
from tests.support.ai_workers import echo,hang_load,hang_inference,failure


@pytest.fixture
def controllers(qt_app,tmp_path,wait_until):
    created=[]
    def create(target=echo,load_timeout=5,timeout=1):
        config=replace(load_config(tmp_path,environ={}),recognition_timeout=timeout)
        item=InferenceController(config,target=target,load_timeout=load_timeout)
        created.append(item)
        return item
    yield create
    for item in created:
        item.stop()
        wait_until(lambda:not item.active,timeout=6000)
        item.shutdown_now()
        item.deleteLater()
    qt_app.processEvents()


def test_model_worker_protocol_backpressure_clear_and_restart(controllers,wait_until):
    worker=controllers()
    results=[]
    worker.result.connect(results.append)
    assert worker.start() and not worker.start()
    wait_until(lambda:worker.state=='ready',timeout=6000)
    image=np.full((96,96,3),100,np.uint8)
    assert worker.submit(image,reference=True)
    assert not worker.submit(image)
    wait_until(lambda:worker.state=='ready')
    assert results[-1]['has_reference']
    assert np.frombuffer(worker.pixels,dtype=np.uint8).sum()==0
    assert worker.clear_reference()
    wait_until(lambda:worker.state=='ready')
    assert results[-1]['event']=='cleared'
    with pytest.raises(ValueError):
        worker.submit(np.zeros((541,960,3),np.uint8))
    worker.stop()
    wait_until(lambda:not worker.active)
    assert worker.pixels is None
    assert worker.start()
    wait_until(lambda:worker.state=='ready',timeout=6000)
    assert worker.submit(image)
    wait_until(lambda:worker.state=='ready')
    assert not results[-1]['has_reference']


@pytest.mark.parametrize('target',[hang_load,hang_inference])
def test_model_hang_deadline_reaps_process_and_frame(controllers,wait_until,target):
    worker=controllers(target=target,load_timeout=1,timeout=.25)
    worker.start()
    if target==hang_inference:
        wait_until(lambda:worker.state=='ready',timeout=6000)
        worker.submit(np.ones((96,96,3),np.uint8))
    wait_until(lambda:not worker.active,timeout=6000)
    assert worker.state=='timeout' and worker.pixels is None


def test_model_load_error_and_emergency_shutdown(controllers,wait_until):
    worker=controllers(target=failure)
    worker.start()
    wait_until(lambda:not worker.active,timeout=6000)
    assert worker.state=='failed'
    hanging=controllers(target=hang_load)
    hanging.start()
    hanging.shutdown_now()
    assert not hanging.active and hanging.pixels is None


def test_late_result_is_discarded_even_if_already_waiting_in_pipe(controllers,wait_until):
    worker=controllers(timeout=1)
    worker.start()
    wait_until(lambda:worker.state=='ready',timeout=6000)
    worker.timer.stop()
    received=[]
    worker.result.connect(received.append)
    assert worker.submit(np.ones((96,96,3),np.uint8))
    wait_until(lambda:worker.connection.poll(),timeout=3000)
    worker.clock=lambda:worker.deadline+1
    worker.poll()
    assert worker.state=='stopping' and worker.final_state=='timeout' and not received
    worker.timer.start()
    wait_until(lambda:not worker.active,timeout=6000)

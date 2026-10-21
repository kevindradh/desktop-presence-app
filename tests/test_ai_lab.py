import os
from pathlib import Path
import pytest
from app.settings.config import load_config
from app.ui.ai_lab import AiLab
from tests.support.ai_workers import echo,streaming_camera,hang_inference


@pytest.fixture
def labs(qt_app,tmp_path,wait_until):
    created=[]
    def make(target=echo):
        lab=AiLab(load_config(tmp_path,environ={}),capture_target=streaming_camera,inference_target=target)
        lab.show()
        created.append(lab)
        return lab
    yield make
    for lab in created:
        lab.close()
        wait_until(lambda:not lab.isVisible(),timeout=8000)
        assert not lab.cameras.busy and not lab.inference.active
        lab.deleteLater()
    qt_app.processEvents()


def test_lab_consent_reference_compare_clear_record_and_stop(labs,wait_until):
    lab=labs()
    assert not lab.start_button.isEnabled() and not lab.cameras.busy
    lab.consent.setChecked(True)
    lab.start_button.click()
    wait_until(lambda:lab.last_result is not None,timeout=8000)
    assert lab.preview.pixmap() and not lab.preview.pixmap().isNull()
    assert lab.reference_button.isEnabled()
    lab.reference_button.click()
    wait_until(lambda:lab.reference_active,timeout=5000)
    wait_until(lambda:lab.last_result['similarity'] is not None,timeout=5000)
    assert 'Cocok' in lab.detail.text()
    destination=os.environ.get('STARGATE_AI_EVIDENCE')
    if destination:
        Path(destination).mkdir(parents=True,exist_ok=True)
        assert lab.grab().save(str(Path(destination)/'stage-07-lab-synthetic.png'))
    lab.record_button.click()
    assert len(lab.results)==1 and set(lab.results[0])=={'condition','status','live_score','similarity','elapsed_ms'}
    lab.clear_button.click()
    wait_until(lambda:not lab.reference_active,timeout=5000)
    lab.consent.setChecked(False)
    wait_until(lambda:not lab.inference.active and not lab.cameras.busy,timeout=6000)
    assert not lab.start_button.isEnabled() and lab.latest is None and lab.last_result is None


def test_lab_close_during_model_inference_releases_everything(labs,wait_until):
    lab=labs(hang_inference)
    lab.consent.setChecked(True)
    lab.start_button.click()
    wait_until(lambda:lab.inference.state=='busy',timeout=8000)
    lab.close()
    wait_until(lambda:not lab.isVisible(),timeout=8000)
    assert lab.latest is None and not lab.reference_active and not lab.results

"""Real pinned models on nonbiometric generated inputs; not accuracy evidence."""
from pathlib import Path
import numpy as np
import pytest
from ai.models import verified_assets
from ai.engine import FaceEngine
from ai.contracts import EngineOptions
from ai.detector.retinaface import RetinaFace
from ai.recognizer.arcface import ArcFace
from ai.liveness.minifasnet import MiniFASNet

ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.models


@pytest.fixture(scope='module')
def components():
    assets=verified_assets(ROOT,ROOT/'resources/models')
    engine=FaceEngine(ROOT,ROOT/'resources/models')
    return assets,engine.detector,engine.recognizer,engine.liveness


def test_real_models_generated_input_no_face_embedding_and_liveness(components):
    assets,detector,recognizer,liveness=components
    blank=np.zeros((240,320,3),np.uint8)
    assert detector.detect(blank)==()
    engine=FaceEngine(ROOT,ROOT/'resources/models',components=(detector,recognizer,liveness))
    assert engine.analyze(blank).status=='no_face'
    crop=np.random.default_rng(9).integers(0,256,(112,112,3),dtype=np.uint8)
    one=recognizer.embed(crop)
    two=recognizer.embed(crop.copy())
    assert one.shape==(512,) and np.linalg.norm(one)==pytest.approx(1)
    assert np.dot(one,two)==pytest.approx(1,abs=1e-5)
    assert recognizer.landmarks.taskname=='landmark_2d_106'
    assert recognizer.recognizer.session.get_providers()==['CPUExecutionProvider']
    score,label=liveness.score(np.full((240,320,3),127,np.uint8),(80,40,200,200))
    assert 0<=score<=1 and label in (0,1,2)


def test_real_alignment_api_runs_but_generated_texture_is_not_identity(components):
    from insightface.app.common import Face
    _,_,recognizer,_=components
    image=np.random.default_rng(12).integers(0,256,(240,320,3),dtype=np.uint8)
    points=recognizer.landmarks.get(image,Face(bbox=np.array([60,30,220,210],np.float32)))
    assert points.shape==(106,2) and np.isfinite(points).all()


def test_real_detector_alignment_and_embedding_on_bundled_public_fixture(components):
    # Installed scikit-image NASA astronaut fixture; never copied into project/evidence.
    # A static source image is not a physical print/replay attack or genuine camera trial.
    import cv2
    import skimage
    from ai.embedding.search import cosine_similarity
    _,detector,recognizer,liveness=components
    image=cv2.imread(str(Path(skimage.__file__).parent/'data/astronaut.png'))
    assert image is not None
    detections=detector.detect(image)
    assert detections
    aligned,points=recognizer.align(image,detections[0].box)
    assert aligned.shape==(112,112,3) and points.shape==(5,2)
    first=recognizer.embed(aligned)
    second=recognizer.embed(aligned.copy())
    assert cosine_similarity(first,second)>.999
    live_engine=FaceEngine(ROOT,ROOT/'resources/models',components=(detector,recognizer,liveness))
    result=live_engine.analyze(image)
    assert result.status in ('ready','spoof')
    assert 0<=result.live_score<=1
    if result.status=='ready':
        assert result.live_class==1 and result.live_score>=.85 and result.embedding is not None
    else:
        assert result.embedding is None


def test_real_model_process_generated_input_ready_result_and_cleanup(qt_app,wait_until):
    from app.settings.config import load_config
    from app.services.inference import InferenceController
    worker=InferenceController(load_config(ROOT,environ={}))
    results=[]
    worker.result.connect(results.append)
    try:
        worker.start()
        wait_until(lambda:worker.state in ('ready','failed','timeout'),timeout=32000)
        assert worker.state=='ready'
        assert worker.submit(np.zeros((240,320,3),np.uint8))
        wait_until(lambda:worker.state in ('ready','failed','timeout'),timeout=6000)
        assert worker.state=='ready' and results[-1]['status']=='no_face'
        assert all('embedding' not in item for item in results)
    finally:
        worker.stop()
        wait_until(lambda:not worker.active,timeout=6000)
        worker.shutdown_now()
        worker.deleteLater()

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np
import pytest

from ai.contracts import Detection,EngineOptions,InputError,InferenceTimeout,ModelError,image_bgr
from ai.engine import FaceEngine,face_quality
from ai.models import verified_assets,ASSETS
from ai.recognizer.arcface import FIVE_POINTS,five_points,unit_embedding
from ai.liveness.minifasnet import context_crop,tensor_bgr
from ai.embedding.search import cosine_similarity


def frame():
    return np.random.default_rng(7).integers(40,220,(240,320,3),dtype=np.uint8)


class Detector:
    def __init__(self,detections):
        self.detections=detections
    def detect(self,image):
        return self.detections


class Recognizer:
    def __init__(self):
        self.box=None
        self.calls=0
    def align(self,image,box):
        self.box=box
        return np.zeros((112,112,3),np.uint8),np.array([[80,70],[120,70],[100,90],[85,110],[115,110]])
    def embed(self,aligned):
        self.calls+=1
        return unit_embedding(np.arange(512)+1)


class Liveness:
    def __init__(self,score=.95,label=1):
        self.score_value,self.label=score,label
    def score(self,image,box):
        return self.score_value,self.label


def engine(detections=None,score=.95,label=1,options=None,**kw):
    recognizer=Recognizer()
    return FaceEngine(Path('.'),Path('.'),options,components=(Detector(detections if detections is not None else [Detection((40,30,200,210),.99)]),recognizer,Liveness(score,label)),**kw)


def test_ready_normalized_embedding_defaults_and_no_biometric_repr():
    value=engine()
    result=value.analyze(frame())
    assert result.status=='ready' and result.embedding.shape==(512,)
    assert np.linalg.norm(result.embedding)==pytest.approx(1)
    assert not result.embedding.flags.writeable
    assert 'array' not in repr(result) and '80' not in repr(result)
    assert EngineOptions()==EngineOptions(.60,True,.85,3.,'Auto')


def test_no_face_multiple_and_deterministic_recognition_target():
    assert engine([]).analyze(frame()).status=='no_face'
    candidates=[Detection((50,40,150,150),.99),Detection((40,30,200,210),.8)]
    value=engine(candidates)
    assert value.analyze(frame()).status=='multiple_faces'
    result=value.analyze(frame(),purpose='recognition')
    assert result.status=='ready' and result.box==(40,30,200,210) and result.face_count==2
    with pytest.raises(ValueError):
        value.analyze(frame(),purpose='unknown')


@pytest.mark.parametrize('score,label',[(.84,1),(.9,0),(.9,2)])
def test_spoof_never_emits_embedding(score,label):
    value=engine(score=score,label=label)
    result=value.analyze(frame())
    assert result.status=='spoof' and result.embedding is None
    assert value.recognizer.calls==0


def test_threshold_inclusive_and_explicit_liveness_disabled():
    assert engine(score=.85).analyze(frame()).status=='ready'
    assert engine(score=.01,options=EngineOptions(liveness_enabled=False)).analyze(frame()).status=='ready'
    bad=engine()
    bad.liveness=None
    with pytest.raises(ModelError):
        bad.analyze(frame())


@pytest.mark.parametrize('score,label',[(float('nan'),1),(-1,1),(2,1),(.99,4)])
def test_invalid_liveness_output_fails_closed(score,label):
    with pytest.raises(ModelError):
        engine(score=score,label=label).analyze(frame())


def test_quality_small_clipped_dark_bright_and_blur():
    image=frame()
    assert face_quality(image,(20,20,60,60))=='too_small'
    assert face_quality(image,(0,20,160,200))=='partial_face'
    assert face_quality(np.zeros_like(image),(40,30,200,210))=='lighting'
    assert face_quality(np.full_like(image,255),(40,30,200,210))=='lighting'
    assert face_quality(np.full_like(image,120),(40,30,200,210))=='blurred'
    assert engine([Detection((20,20,60,60),.9)]).analyze(image).status=='too_small'


def test_timeout_after_slow_stage_cannot_produce_success():
    clock=[0.]
    value=engine(clock=lambda:clock[0])
    class Slow:
        def detect(self,image):
            clock[0]=3.
            return [Detection((40,30,200,210),.99)]
    value.detector=Slow()
    with pytest.raises(InferenceTimeout):
        value.analyze(frame())


@pytest.mark.parametrize('image',[None,np.zeros((10,10,3),np.uint8),np.zeros((100,100),np.uint8),np.zeros((100,100,4),np.uint8),np.zeros((100,100,3),np.float32)])
def test_invalid_images(image):
    with pytest.raises(InputError):
        image_bgr(image)


@pytest.mark.parametrize('options',[{'similarity_threshold':True},{'liveness_threshold':float('nan')},{'recognition_timeout':0},{'liveness_enabled':1},{'max_face_size':'large'}])
def test_options_fail_closed(options):
    with pytest.raises(ValueError):
        EngineOptions(**options)


def test_five_points_geometry_and_invalid_landmarks():
    points=np.zeros((106,2),np.float32)
    points[list(FIVE_POINTS)]=[[80,70],[120,70],[100,90],[85,110],[115,110]]
    assert five_points(points,(40,30,200,210)).shape==(5,2)
    points[38]=points[88]
    with pytest.raises(ValueError):
        five_points(points,(40,30,200,210))
    with pytest.raises(ModelError):
        five_points(np.full((106,2),np.nan),(0,0,200,200))


def test_liveness_bgr_range_and_context_crop_boundary():
    image=np.full((160,200,3),(20,100,255),np.uint8)
    for box in ((0,0,80,100),(120,60,200,160),(40,30,100,120)):
        patch=context_crop(image,box)
        assert patch.shape==(80,80,3) and tuple(patch[0,0])==(20,100,255)
        tensor=tensor_bgr(patch)
        assert tuple(tensor.shape)==(1,3,80,80)
        assert tensor[0,:,0,0].tolist()==[20.,100.,255.]


def test_embedding_norm_cosine_known_unknown_and_invalid():
    unit=np.zeros(512);unit[0]=1
    assert cosine_similarity(unit,unit*20)==pytest.approx(1)
    assert cosine_similarity(unit,-unit)==pytest.approx(-1)
    assert cosine_similarity(unit,np.roll(unit,1))==pytest.approx(0)
    for value in ([],np.zeros(512),np.full(512,np.inf),np.ones(511)):
        with pytest.raises(ModelError):
            unit_embedding(value)


def test_pinned_assets_missing_or_corrupted_never_load(tmp_path):
    with pytest.raises(ModelError):
        verified_assets(tmp_path,tmp_path)
    (tmp_path/'models').mkdir()
    entries=[]
    import hashlib
    for name in ASSETS:
        path='source.py' if name=='minifasnet-source' else name+'.bin'
        (tmp_path/path).write_bytes(b'synthetic-model')
        entries.append(dict(id=name,path=path,sha256=hashlib.sha256(b'synthetic-model').hexdigest()))
    (tmp_path/'models/manifest.json').write_text(json.dumps({'assets':entries}))
    assert verified_assets(tmp_path,tmp_path)['version'].startswith('arcface-r50')
    (tmp_path/'arcface-weights.bin').write_bytes(b'corrupt')
    with pytest.raises(ModelError):
        verified_assets(tmp_path,tmp_path)

from dataclasses import replace
import base64
import hashlib
import hmac
import json
import time
import numpy as np
import pytest
from ai.contracts import Analysis
from ai.enrollment import CaptureDraft,CaptureError,ANGLES,pose_ratios,angle_matches
from ai.recognizer.arcface import unit_embedding


def analysis(angle='FRONT',**changes):
    points=np.array([[80,70],[120,70],[100,90],[85,110],[115,110]],np.float32)
    if angle=='LEFT':points[2,0]+=8
    if angle=='RIGHT':points[2,0]-=8
    if angle=='UP':points[2,1]-=6
    if angle=='DOWN':points[2,1]+=6
    return replace(Analysis('ready',1,(40,30,200,210),tuple(map(tuple,points)),.99,1,
        unit_embedding(np.arange(512)+1),10,'synthetic'),**changes)


def packet(service,binding,*,offset=0):
    draft=CaptureDraft(binding=binding,key=service.key,model_version='synthetic-v1',clock=service.clock)
    frame=np.full((240,320,3),(20,100,60),np.uint8)
    for angle in ANGLES:
        value=analysis(angle)
        if offset:value=replace(value,embedding=unit_embedding(np.roll(value.embedding,offset)))
        draft.add(value,frame)
    result=draft.seal()
    draft.clear()
    return result


def test_five_angles_reject_duplicate_pose_and_sign_complete_only():
    class Service:
        key=b'key'
        clock=staticmethod(time.monotonic)
    draft=CaptureDraft(binding={'nonce':'test'},key=b'key',model_version='test')
    frame=np.full((240,320,3),100,np.uint8)
    with pytest.raises(CaptureError,match='belum lengkap'):draft.seal()
    draft.add(analysis(),frame)
    with pytest.raises(CaptureError,match='Sudut'):draft.add(analysis(),frame)
    for angle in ANGLES[1:]:draft.add(analysis(angle),frame)
    result=draft.seal()
    assert hmac.compare_digest(result.signature,hmac.new(b'key',result.body,hashlib.sha256).hexdigest())
    data=json.loads(result.body)
    assert [s['angle'] for s in data['samples']]==list(ANGLES)
    assert base64.b64decode(data['photo']).startswith(b'\x89PNG')
    assert 'vector' not in repr(result)
    draft.clear()
    assert not draft.samples and draft.photo is None


@pytest.mark.parametrize('changes',[{'status':'no_face'},{'status':'spoof'},{'face_count':2},{'embedding':None}])
def test_capture_invalid_analysis_cannot_add(changes):
    draft=CaptureDraft(binding={},key=b'key',model_version='test')
    with pytest.raises(CaptureError):draft.add(analysis(**changes),np.zeros((240,320,3),np.uint8))
    assert not draft.samples


def test_capture_different_identity_expiration_and_pose_invariance():
    now=[0.]
    draft=CaptureDraft(binding={},key=b'key',model_version='test',clock=lambda:now[0])
    frame=np.full((240,320,3),100,np.uint8)
    draft.add(analysis(),frame)
    with pytest.raises(CaptureError,match='berbeda'):
        draft.add(analysis('LEFT',embedding=-analysis().embedding),frame)
    now[0]=901
    with pytest.raises(CaptureError,match='kedaluwarsa'):draft.add(analysis('LEFT'),frame)
    points=np.asarray(analysis().points)
    assert pose_ratios(points)==pytest.approx(pose_ratios(points*2+100))
    assert not angle_matches('LEFT',(0,.5,40),(0,.5,0))
    with pytest.raises(CaptureError):pose_ratios(np.zeros((5,2)))

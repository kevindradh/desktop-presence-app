from dataclasses import replace

import numpy as np
import pytest

from ai.enrollment import ANGLES,AutoCapture,CaptureDraft
from tests.test_enrollment_capture import analysis


def setup():
    now=[0.]
    draft=CaptureDraft(binding={},key=b'synthetic',model_version='synthetic',clock=lambda:now[0])
    return now,draft,AutoCapture(draft,clock=lambda:now[0]),np.zeros((240,320,3),np.uint8)


def test_auto_capture_requires_time_and_observations_for_each_of_five_poses():
    now,draft,automatic,frame=setup()
    for index,angle in enumerate(ANGLES):
        assert not automatic.consider(analysis(angle),frame)
        now[0]+=.31
        assert not automatic.consider(analysis(angle),frame)
        assert len(draft.samples)==index
        now[0]+=.31
        assert automatic.consider(analysis(angle),frame)
        assert len(draft.samples)==index+1
        assert automatic.embedding is None
    assert draft.expected is None and draft.seal().body


@pytest.mark.parametrize('bad',[analysis(status='no_face'),analysis(status='spoof'),
    analysis(face_count=2),analysis(live_score=.84),analysis(embedding=None)])
def test_invalid_analysis_resets_stability_without_adding_a_sample(bad):
    now,draft,automatic,frame=setup()
    automatic.consider(analysis(),frame)
    previous=automatic.embedding
    now[0]+=.4
    assert not automatic.consider(bad,frame)
    assert np.count_nonzero(previous)==0
    now[0]+=.4
    assert not automatic.consider(analysis(),frame)
    assert not draft.samples


def test_wrong_pose_different_identity_motion_or_gap_cannot_advance():
    now,draft,automatic,frame=setup()
    draft.add(analysis(),frame)
    for i in range(5):
        now[0]+=.4
        assert not automatic.consider(analysis(),frame)
    assert len(draft.samples)==1
    automatic.consider(analysis('LEFT'),frame)
    now[0]+=.7
    assert not automatic.consider(analysis('LEFT',embedding=-analysis().embedding),frame)
    assert automatic.observations==0
    automatic.consider(analysis('LEFT'),frame)
    now[0]+=2.1
    assert not automatic.consider(analysis('LEFT'),frame)
    assert automatic.observations==1
    points=np.array(analysis('LEFT').points)
    points[2,0]+=3
    now[0]+=.31
    assert not automatic.consider(replace(analysis('LEFT'),points=tuple(map(tuple,points))),frame)
    assert automatic.observations==1 and len(draft.samples)==1


def test_three_fast_observations_are_insufficient_and_face_translation_resets_window():
    now,draft,automatic,frame=setup()
    for _ in range(3):
        assert not automatic.consider(analysis(),frame)
        now[0]+=.1
    assert not draft.samples
    now[0]+=.4
    moved=replace(analysis(),box=(80,30,240,210))
    assert not automatic.consider(moved,frame)
    assert automatic.observations==1 and not draft.samples

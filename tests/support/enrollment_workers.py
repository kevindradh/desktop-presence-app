"""Synthetic capture protocol; never reads real cameras or neural weights."""
from dataclasses import dataclass,field
import numpy as np
import time,json,hmac,hashlib
from ai.enrollment import CaptureDraft,ANGLES,CapturePacket
from tests.test_enrollment_capture import analysis


@dataclass(repr=False)
class SyntheticEnrollmentTarget:
    key: bytes=field(repr=False)
    binding: dict=field(repr=False)

    def __call__(self,root,model_dir,options,pixels,shape,lock,connection):
        draft=CaptureDraft(binding=self.binding,key=self.key,model_version='synthetic-v1')
        connection.send({'event':'ready'})
        while True:
            command=connection.recv()
            if command=='stop':break
            with lock:
                h,w=map(int,shape[:])
                image=np.frombuffer(pixels,dtype=np.uint8,count=h*w*3).copy().reshape(h,w,3)
                np.frombuffer(pixels,dtype=np.uint8).fill(0)
                shape[:]=(0,0)
            expected=draft.expected
            verification=self.binding.get('purpose')=='verification'
            if command=='capture' and not verification:
                # Synthetic pose coordinates use 240x320 space; synthetic profile is independent.
                draft.add(analysis(expected),np.full((240,320,3),(20,100,60),np.uint8))
            response=dict(event='result',status='ready',face_count=1,box=(10,10,80,80),points=(),
                live_score=.99,live_class=1,elapsed_ms=10.,has_reference=False,similarity=None,matched=False,
                captured=len(draft.samples),expected=draft.expected,capture_message='')
            if draft.expected is None:response['packet']=draft.seal()
            if command=='capture' and verification:
                body=json.dumps(dict(kind='probe',binding=self.binding,created=time.monotonic(),
                    model_version='synthetic-v1',vector=analysis().embedding.tolist())).encode()
                response['packet']=CapturePacket(body,hmac.new(self.key,body,hashlib.sha256).hexdigest())
            connection.send(response)
            image.fill(0)
        draft.clear()
        connection.close()

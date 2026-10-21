"""Private capture worker. Complete bundles cross IPC only after five validated poses."""
from dataclasses import dataclass,field,replace
import os
import hashlib,hmac,json,time
import numpy as np
from ai.enrollment import CaptureDraft,CaptureError,CapturePacket
from ai.contracts import InferenceTimeout


@dataclass(repr=False)
class EnrollmentTarget:
    key: bytes=field(repr=False)
    binding: dict=field(repr=False)

    def __call__(self,root,model_dir,options,pixels,shape,lock,connection):
        null=os.open(os.devnull,os.O_WRONLY)
        os.dup2(null,1);os.dup2(null,2);os.close(null)
        draft=None
        try:
            from ai.engine import FaceEngine
            if self.binding.get('purpose')!='verification':
                options=replace(options,liveness_enabled=True,liveness_threshold=.85)
            engine=FaceEngine(root,model_dir,options)
            draft=CaptureDraft(binding=self.binding,key=self.key,model_version=engine.model_version,identity_threshold=options.similarity_threshold)
            connection.send({'event':'ready','version':engine.model_version})
            while True:
                command=connection.recv()
                if command=='stop':
                    break
                if command not in ('analyze','capture'):
                    raise ValueError
                with lock:
                    height,width=map(int,shape[:])
                    if not 16<=height<=540 or not 16<=width<=960:
                        raise ValueError
                    frame=np.frombuffer(pixels,dtype=np.uint8,count=height*width*3).copy().reshape(height,width,3)
                    np.frombuffer(pixels,dtype=np.uint8).fill(0)
                    shape[:]=(0,0)
                try:
                    analysis=engine.analyze(frame)
                    message=''
                    verification=self.binding.get('purpose')=='verification'
                    if command=='capture' and not verification:
                        try:
                            draft.add(analysis,frame)
                        except CaptureError as error:
                            message=str(error)
                    response=dict(event='result',status=analysis.status,face_count=analysis.face_count,
                        box=analysis.box,points=analysis.points,live_score=analysis.live_score,live_class=analysis.live_class,
                        elapsed_ms=analysis.elapsed_ms,has_reference=False,similarity=None,matched=False,
                        captured=len(draft.samples),expected=draft.expected,capture_message=message)
                    if verification and command=='capture' and analysis.status=='ready':
                        body=json.dumps(dict(kind='probe',binding=self.binding,created=time.monotonic(),
                            model_version=engine.model_version,vector=analysis.embedding.tolist()),allow_nan=False).encode()
                        response['packet']=CapturePacket(body,hmac.new(self.key,body,hashlib.sha256).hexdigest())
                    if not verification and draft.expected is None:
                        response['packet']=draft.seal()
                    if 'packet' in response:
                        connection.send(response)
                        draft.clear()
                        while connection.recv()!='stop':
                            pass
                        break
                    connection.send(response)
                finally:
                    frame.fill(0)
                    if 'analysis' in locals():
                        del analysis
        except EOFError:
            pass
        except Exception as error:
            try:
                connection.send({'event':'timeout' if isinstance(error,InferenceTimeout) else 'error'})
            except (OSError,BrokenPipeError):
                pass
        finally:
            if draft is not None:
                draft.clear()
            np.frombuffer(pixels,dtype=np.uint8).fill(0)
            shape[:]=(0,0)
            connection.close()

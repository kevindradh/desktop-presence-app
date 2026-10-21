"""Composable CPU engine. Call in an isolated process for hard native-call deadlines."""
import time
import cv2
import numpy as np
from ai.contracts import Analysis,EngineOptions,InferenceTimeout,ModelError,image_bgr
from ai.models import verified_assets
from ai.detector.retinaface import RetinaFace
from ai.recognizer.arcface import ArcFace
from ai.liveness.minifasnet import MiniFASNet


def face_quality(image,box):
    x1,y1,x2,y2=box
    height,width=image.shape[:2]
    if min(x2-x1,y2-y1)<64:
        return "too_small"
    if x1<2 or y1<2 or x2>width-2 or y2>height-2:
        return "partial_face"
    gray=cv2.cvtColor(image[y1:y2,x1:x2],cv2.COLOR_BGR2GRAY)
    brightness=float(gray.mean())
    if not 30<=brightness<=225:
        return "lighting"
    if cv2.Laplacian(gray,cv2.CV_64F).var()<35:
        return "blurred"
    return None


class FaceEngine:
    def __init__(self,root,model_dir,options=None,*,components=None,clock=time.monotonic):
        self.options=options or EngineOptions()
        self.clock=clock
        if components is None:
            assets=verified_assets(root,model_dir)
            try:
                self.detector=RetinaFace(assets)
                self.recognizer=ArcFace(assets)
                self.liveness=MiniFASNet(assets) if self.options.liveness_enabled else None
            except Exception:
                raise ModelError() from None
            self.model_version=assets["version"]
        else:
            self.detector,self.recognizer,self.liveness=components
            self.model_version="synthetic-test-only"

    def analyze(self,image,*,purpose="registration"):
        image=image_bgr(image)
        if purpose not in {"registration","recognition"}:
            raise ValueError("Tujuan pemeriksaan tidak valid.")
        began=self.clock()
        def checkpoint():
            if self.clock()-began>=self.options.recognition_timeout:
                raise InferenceTimeout()
        count=0
        box=None
        points=()
        score=None
        label=None
        def result(status,embedding=None):
            checkpoint()
            return Analysis(status,count,box,points,score,label,embedding,
                (self.clock()-began)*1000,self.model_version)
        checkpoint()
        detections=self.detector.detect(image)
        checkpoint()
        count=len(detections)
        if not count:
            return result("no_face")
        # Registration rejects multiple faces; recognition selects largest, then score/x/y.
        if count>1 and purpose=="registration":
            return result("multiple_faces")
        target=min(detections,key=lambda d:(-d.area,-d.confidence,d.box))
        box=target.box
        quality=face_quality(image,box)
        if quality:
            return result(quality)
        try:
            aligned,landmarks=self.recognizer.align(image,box)
        except ValueError:
            return result("alignment")
        checkpoint()
        points=tuple(tuple(float(v) for v in point) for point in landmarks)
        if self.options.liveness_enabled:
            if self.liveness is None:
                raise ModelError()
            score,label=self.liveness.score(image,box)
            if not np.isfinite(score) or not 0<=score<=1 or label not in (0,1,2):
                raise ModelError()
            checkpoint()
            if label!=1 or score<self.options.liveness_threshold:
                return result("spoof")
        embedding=self.recognizer.embed(aligned)
        return result("ready",embedding)

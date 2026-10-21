"""Pinned MiniVision Caffe RetinaFace; never starts a second detector."""
import cv2
import numpy as np
from ai.contracts import Detection,ModelError,image_bgr


class RetinaFace:
    def __init__(self,assets):
        try:
            self.net=cv2.dnn.readNetFromCaffe(str(assets["retinaface-config"]),str(assets["retinaface-weights"]))
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        except Exception:
            raise ModelError() from None

    def detect(self,image):
        image=image_bgr(image)
        height,width=image.shape[:2]
        # Upstream detector was evaluated around 192². Preserve aspect, no enlargement.
        scale=min(1.,192/(height*width)**.5)
        size=(max(16,int(width*scale)),max(16,int(height*scale)))
        resized=cv2.resize(image,size,interpolation=cv2.INTER_LINEAR)
        self.net.setInput(cv2.dnn.blobFromImage(resized,1.,mean=(104,117,123),swapRB=False),"data")
        output=np.asarray(self.net.forward("detection_out"))
        if output.size%7 or not np.isfinite(output).all():
            raise ModelError()
        candidates=[]
        for row in output.reshape(-1,7):
            if row[0]<0 or row[1]!=1 or row[2]<.6:
                continue
            if row[2]>1:
                raise ModelError()
            x1,y1,x2,y2=row[3:7]*np.array([width,height,width,height])
            box=(max(0,int(x1)),max(0,int(y1)),min(width,int(x2)+1),min(height,int(y2)+1))
            if box[2]>box[0] and box[3]>box[1]:
                candidates.append(Detection(box,float(row[2])))
        # Caffe DetectionOutput already performs NMS; deterministic largest target first.
        return tuple(sorted(candidates,key=lambda d:(-d.area,-d.confidence,d.box)))

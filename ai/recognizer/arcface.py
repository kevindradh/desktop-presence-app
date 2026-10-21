"""106-point landmarks -> five-point ArcFace alignment; CPU InsightFace models only."""
import cv2
import numpy as np
from ai.contracts import ModelError

FIVE_POINTS=(38,88,86,52,61)


def five_points(landmarks,box):
    points=np.asarray(landmarks,dtype=np.float32)
    if points.shape!=(106,2) or not np.isfinite(points).all():
        raise ModelError()
    selected=points[list(FIVE_POINTS)].copy()
    x1,y1,x2,y2=box
    width,height=x2-x1,y2-y1
    # Reject degenerate/misordered geometry rather than embedding arbitrary crops.
    if not (selected[0,0]<selected[1,0] and selected[3,0]<selected[4,0]
        and selected[:2,1].mean()<selected[2,1]<selected[3:,1].mean()
        and np.linalg.norm(selected[1]-selected[0])>=width*.1
        and (selected[:,0]>=x1-width*.2).all() and (selected[:,0]<=x2+width*.2).all()
        and (selected[:,1]>=y1-height*.2).all() and (selected[:,1]<=y2+height*.2).all()):
        raise ValueError("Posisi wajah belum sesuai. Hadapkan wajah ke kamera.")
    return selected


def unit_embedding(vector):
    try:
        vector=np.asarray(vector,dtype=np.float32).reshape(-1)
        if vector.shape!=(512,) or not np.isfinite(vector).all():
            raise ValueError
        length=float(np.linalg.norm(vector.astype(np.float64)))
        if not np.isfinite(length) or length<=1e-12:
            raise ValueError
        result=(vector/length).astype(np.float32)
        result.setflags(write=False)
        return result
    except (TypeError,ValueError,OverflowError):
        raise ModelError() from None


class ArcFace:
    def __init__(self,assets):
        try:
            from insightface.model_zoo import get_model
            import onnxruntime as ort
            ort.disable_telemetry_events()
            options=ort.SessionOptions()
            options.intra_op_num_threads=2
            options.inter_op_num_threads=1
            options.log_severity_level=3
            self.landmarks=get_model(str(assets["face-landmarks"]),providers=["CPUExecutionProvider"],sess_options=options,download=False)
            self.recognizer=get_model(str(assets["arcface-weights"]),providers=["CPUExecutionProvider"],sess_options=options,download=False)
            if self.landmarks.taskname!="landmark_2d_106" or self.recognizer.taskname!="recognition" or tuple(self.recognizer.input_size)!=(112,112):
                raise ValueError
        except Exception:
            raise ModelError() from None

    def align(self,image,box):
        from insightface.app.common import Face
        from insightface.utils.face_align import norm_crop
        face=Face(bbox=np.array(box,dtype=np.float32))
        points=five_points(self.landmarks.get(image,face),box)
        return norm_crop(image,points,image_size=112),points

    def embed(self,aligned_bgr):
        if aligned_bgr.shape!=(112,112,3) or aligned_bgr.dtype!=np.uint8:
            raise ModelError()
        # get_feat owns BGR->RGB and (pixel-127.5)/127.5 exactly once.
        return unit_embedding(self.recognizer.get_feat(aligned_bgr))

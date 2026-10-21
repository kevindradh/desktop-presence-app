"""Private, in-memory model contracts. No automatic serialization or logging."""
from dataclasses import dataclass, field
import math
import numpy as np


class ModelError(RuntimeError):
    def __init__(self):
        super().__init__("Model AI tidak tersedia atau tidak valid. Periksa berkas model dan checksum.")


class InputError(ValueError):
    def __init__(self):
        super().__init__("Input harus gambar BGR uint8 yang valid dan berukuran paling besar 4096×4096.")


class InferenceTimeout(TimeoutError):
    def __init__(self):
        super().__init__("Batas waktu pemeriksaan wajah terlampaui. Silakan coba lagi.")


@dataclass(frozen=True)
class EngineOptions:
    similarity_threshold: float = .60
    liveness_enabled: bool = True
    liveness_threshold: float = .85
    recognition_timeout: float = 3.
    max_face_size: str = "Auto"

    def __post_init__(self):
        for value in (self.similarity_threshold,self.liveness_threshold):
            if type(value) not in (float,int) or not math.isfinite(value) or not 0<=value<=1:
                raise ValueError("Ambang AI tidak valid.")
        if type(self.recognition_timeout) not in (float,int) or not math.isfinite(self.recognition_timeout) or not 0<self.recognition_timeout<=300:
            raise ValueError("Batas waktu AI tidak valid.")
        if type(self.liveness_enabled) is not bool or self.max_face_size!="Auto":
            raise ValueError("Opsi AI tidak valid.")

    @classmethod
    def from_config(cls,config):
        return cls(config.similarity_threshold,config.liveness_enabled,config.liveness_threshold,config.recognition_timeout,getattr(config,'max_face_size','Auto'))


def image_bgr(image):
    if not isinstance(image,np.ndarray) or image.dtype!=np.uint8 or image.ndim!=3 or image.shape[2]!=3:
        raise InputError()
    height,width=image.shape[:2]
    if not 16<=height<=4096 or not 16<=width<=4096:
        raise InputError()
    return np.ascontiguousarray(image)


@dataclass(frozen=True)
class Detection:
    box: tuple[int,int,int,int]
    confidence: float

    @property
    def area(self):
        x1,y1,x2,y2=self.box
        return (x2-x1)*(y2-y1)


@dataclass(frozen=True,repr=False)
class Analysis:
    status: str
    face_count: int
    box: tuple | None = None
    points: tuple = field(default=(),repr=False)
    live_score: float | None = None
    live_class: int | None = None
    embedding: np.ndarray | None = field(default=None,repr=False,compare=False)
    elapsed_ms: float = 0
    model_version: str = ""

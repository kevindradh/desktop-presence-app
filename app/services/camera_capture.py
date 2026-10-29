"""Isolated capture process. No database, Qt widgets, frame files or raw errors."""
from dataclasses import dataclass, field
import hashlib
import os
import sys
import time
from app.services.worker_output import silence_worker_output

PREVIEW_WIDTH, PREVIEW_HEIGHT = 960, 540
FRAME_BYTES = PREVIEW_WIDTH * PREVIEW_HEIGHT * 3


@dataclass(frozen=True)
class CaptureSpec:
    device_id: int
    name: str
    kind: str
    camera_index: int
    width: int
    height: int
    fps: int
    rtsp_source: str = field(default="", repr=False)

    @property
    def identity(self):
        if self.kind == "RTSP":
            return "rtsp:" + hashlib.sha256(self.rtsp_source.encode()).hexdigest()
        return f"local:{self.camera_index}"


def capture_process(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    # Native FFmpeg/OpenCV diagnostics can contain credential-bearing URLs.
    # Redirect before importing the capture runtime; parent receives fixed codes only.
    silence_worker_output()
    os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
    os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
    import cv2
    import numpy as np
    cv2.setLogLevel(0)
    camera = None
    try:
        if spec.kind == "RTSP":
            camera = cv2.VideoCapture()
            camera.open(spec.rtsp_source, cv2.CAP_FFMPEG, [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, int(open_timeout * 1000),
                cv2.CAP_PROP_READ_TIMEOUT_MSEC, int(read_timeout * 1000)])
        else:
            backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else (
                cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_V4L2)
            camera = cv2.VideoCapture(spec.camera_index, backend)
        if not camera.isOpened():
            messages.send(("error", None))
            return
        if spec.kind != "RTSP":
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, spec.width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, spec.height)
            camera.set(cv2.CAP_PROP_FPS, spec.fps)
        messages.send(("opened", None))
        sequence = 0
        while not stop.is_set():
            began = time.monotonic()
            success, frame = camera.read()
            if not success or frame is None or frame.size == 0 or frame.ndim != 3 or frame.shape[2] != 3:
                messages.send(("error", None))
                break
            original_height, original_width = frame.shape[:2]
            scale = min(1.0, PREVIEW_WIDTH / original_width, PREVIEW_HEIGHT / original_height)
            if scale < 1:
                frame = cv2.resize(frame, (max(1, int(original_width * scale)), max(1, int(original_height * scale))))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb.shape[:2]
            if lock.acquire(timeout=.02):
                try:
                    size = width * height * 3
                    np.frombuffer(pixels, dtype=np.uint8, count=size)[:] = rgb.reshape(-1)
                    sequence += 1
                    metadata[:] = (sequence, width, height, time.monotonic(), original_width, original_height)
                finally:
                    lock.release()
            stop.wait(max(0, 1 / spec.fps - (time.monotonic() - began)))
    except BaseException:
        try:
            messages.send(("error", None))
        except (OSError, BrokenPipeError):
            pass
    finally:
        if camera is not None:
            camera.release()
        messages.close()

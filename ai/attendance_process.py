"""Face pipeline worker: signed ephemeral probes, no image/vector persistence."""
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import os
import time
import numpy as np
from ai.contracts import InferenceTimeout
from ai.enrollment import CapturePacket


def signed_packet(key, binding, sequence, created, *, analysis=None):
    payload = dict(binding=binding, sequence=sequence, created=created,
                   kind='face' if analysis is not None else 'absence')
    if analysis is not None:
        payload.update(vector=analysis.embedding.tolist(), model_version=analysis.model_version,
                       live_score=analysis.live_score, live_class=analysis.live_class)
    body = json.dumps(payload, allow_nan=False).encode()
    return CapturePacket(body, hmac.new(key, body, hashlib.sha256).hexdigest())


@dataclass(repr=False)
class AttendanceTarget:
    key: bytes = field(repr=False)
    binding: dict = field(repr=False)

    def __call__(self, root, model_dir, options, pixels, shape, lock, connection):
        null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null, 1); os.dup2(null, 2); os.close(null)
        try:
            from ai.engine import FaceEngine
            engine = FaceEngine(root, model_dir, options)
            connection.send(dict(event='ready', version=engine.model_version))
            sequence = 0
            absent_since = None
            absence_sent = False
            while connection.recv() != 'stop':
                with lock:
                    height, width = map(int, shape[:])
                    if not 16 <= height <= 540 or not 16 <= width <= 960:
                        raise ValueError
                    frame = np.frombuffer(pixels, dtype=np.uint8, count=height*width*3).copy().reshape(height, width, 3)
                    np.frombuffer(pixels, dtype=np.uint8).fill(0)
                    shape[:] = (0, 0)
                began = time.monotonic()
                try:
                    analysis = engine.analyze(frame, purpose='recognition')
                    response = dict(event='result', status=analysis.status, face_count=analysis.face_count,
                        box=analysis.box, points=analysis.points, live_score=analysis.live_score,
                        live_class=analysis.live_class, elapsed_ms=analysis.elapsed_ms)
                    if analysis.status == 'no_face':
                        if absent_since is None:
                            absent_since = began
                        if not absence_sent and began-absent_since >= 1:
                            sequence += 1
                            response['packet'] = signed_packet(self.key, self.binding, sequence, began)
                            absence_sent = True
                    else:
                        absent_since = None
                        absence_sent = False
                    if analysis.status == 'ready':
                        sequence += 1
                        response['packet'] = signed_packet(self.key, self.binding, sequence, began, analysis=analysis)
                    connection.send(response)
                finally:
                    frame.fill(0)
                    if 'analysis' in locals():
                        del analysis
        except EOFError:
            pass
        except Exception as error:
            try:
                connection.send(dict(event='timeout' if isinstance(error, InferenceTimeout) else 'error'))
            except (OSError, BrokenPipeError):
                pass
        finally:
            np.frombuffer(pixels, dtype=np.uint8).fill(0)
            shape[:] = (0, 0)
            connection.close()

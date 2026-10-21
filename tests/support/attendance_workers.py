"""Controlled worker with the production signed probe format; no real models/camera."""
from dataclasses import dataclass, field
import time
import numpy as np
from dataclasses import replace
from ai.attendance_process import signed_packet
from tests.test_enrollment_capture import analysis


@dataclass(repr=False)
class SyntheticAttendanceTarget:
    key: bytes = field(repr=False)
    binding: dict = field(repr=False)
    status: str = 'ready'
    delay: float = 0

    def __call__(self, root, model_dir, options, pixels, shape, lock, connection):
        connection.send(dict(event='ready'))
        sequence = 0
        while connection.recv() != 'stop':
            with lock:
                np.frombuffer(pixels,dtype=np.uint8).fill(0)
                shape[:] = (0,0)
            began=time.monotonic()
            time.sleep(self.delay)
            value = replace(analysis(),model_version='synthetic-v1')
            response = dict(event='result',status=self.status,face_count=1,box=(10,10,80,80),points=(),
                live_score=.99,live_class=1,elapsed_ms=10.)
            if self.status == 'ready':
                sequence += 1
                response['packet'] = signed_packet(self.key,self.binding,sequence,began,analysis=value)
            connection.send(response)
        connection.close()

"""Synthetic capture targets. They never open a camera or network connection."""
from pathlib import Path
import time


def streaming(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    messages.send(("opened", None))
    sequence = 0
    while not stop.is_set():
        with lock:
            memoryview(pixels).cast("B")[:6] = bytes((20,100,60,40,120,80))
            sequence += 1
            metadata[:] = (sequence,2,1,time.monotonic(),640,480)
        stop.wait(.005)
    messages.close()


def failing(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    messages.send(("error", None))
    messages.close()


def hung_open(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    time.sleep(60)


def frozen_read(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    messages.send(("opened", None))
    with lock:
        memoryview(pixels).cast("B")[:6] = bytes((20,100,60,40,120,80))
        metadata[:] = (1,2,1,time.monotonic(),640,480)
    time.sleep(60)


def recovering(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    marker = Path(spec.name)
    if not marker.exists():
        marker.write_text("synthetic retry marker")
        messages.send(("error", None))
        messages.close()
        return
    streaming(spec,pixels,metadata,lock,messages,stop,open_timeout,read_timeout)

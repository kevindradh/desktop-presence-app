"""Controlled AI protocol doubles, no models or biometric inputs."""
import time
import numpy as np


def echo(root,model_dir,options,pixels,shape,lock,connection):
    reference=False
    connection.send({'event':'ready'})
    while True:
        command=connection.recv()
        if command=='stop':
            break
        if command=='clear':
            reference=False
            connection.send({'event':'cleared'})
            continue
        with lock:
            assert shape[0]>0 and shape[1]>0
            np.frombuffer(pixels,dtype=np.uint8).fill(0)
            shape[:]=(0,0)
        if command=='reference':
            reference=True
        connection.send(dict(event='result',status='ready',face_count=1,box=(10,10,80,80),points=(),live_score=.99,
            live_class=1,elapsed_ms=10.,has_reference=reference,similarity=1. if reference else None,matched=reference))
    connection.close()


def hang_load(*args):
    time.sleep(60)


def hang_inference(root,model_dir,options,pixels,shape,lock,connection):
    connection.send({'event':'ready'})
    connection.recv()
    time.sleep(60)


def failure(root,model_dir,options,pixels,shape,lock,connection):
    connection.send({'event':'error'})
    connection.close()


def streaming_camera(spec,pixels,metadata,lock,messages,stop,open_timeout,read_timeout):
    messages.send(('opened',None))
    sequence=0
    while not stop.is_set():
        with lock:
            memoryview(pixels).cast('B')[:96*96*3]=bytes((20,100,60))*(96*96)
            sequence+=1
            metadata[:]=(sequence,96,96,time.monotonic(),640,480)
        stop.wait(.02)
    messages.close()

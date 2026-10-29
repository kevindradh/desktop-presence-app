"""Exercise acknowledged shutdown, native-teardown hangs and unexpected crashes."""
import multiprocessing as mp
import os
import time

import pytest
from app.services.package_probe import stop_model_probe


def probe_worker(connection,pixels,shape,behavior):
    connection.send('ready')
    assert connection.recv()=='stop'
    if behavior!='dirty':
        memoryview(pixels).cast('B')[:]=bytes(len(pixels))
        shape[:]=(0,0)
    if behavior not in {'no_ack','no_ack_exit'}:connection.send({'event':'stopped'})
    if behavior=='crash':os._exit(7)
    if behavior=='flush_failure':os._exit(120)
    if behavior in {'hang','dirty','no_ack'}:time.sleep(60)
    connection.close()


@pytest.mark.parametrize('behavior,expected,forced',[
    ('normal',True,False),('hang',True,True),('dirty',False,True),
    ('no_ack',False,True),('crash',False,False),('missing_ack',False,False),
    ('flush_failure',False,False)])
def test_shutdown_requires_acknowledgement_wiped_memory_and_known_exit(behavior,expected,forced):
    ctx=mp.get_context('spawn')
    pixels=ctx.RawArray('B',64)
    memoryview(pixels).cast('B')[:]=b'\x01'*64
    shape=ctx.RawArray('i',[8,8])
    parent,child=ctx.Pipe()
    target_behavior='no_ack_exit' if behavior=='missing_ack' else behavior
    process=ctx.Process(target=probe_worker,args=(child,pixels,shape,target_behavior))
    process.start();child.close()
    try:
        assert parent.poll(15) and parent.recv()=='ready'
        success,details=stop_model_probe(process,parent,pixels,shape,ack_timeout=.5,exit_timeout=.5,reap_timeout=3)
        assert success is expected,details
        assert details['forced_termination'] is forced
        assert details['reaped'] and not process.is_alive()
        if behavior=='crash':assert details['exit_code']==7
        if behavior=='flush_failure':assert details['exit_code']==120
        if expected:assert details['buffers_cleared'] and details['stop_acknowledged']
    finally:
        parent.close()
        if process.is_alive():process.kill();process.join(5)
        process.close()

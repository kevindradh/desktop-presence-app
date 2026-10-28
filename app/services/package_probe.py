"""Offline, non-invasive frozen-runtime probe. No credentials, real camera or database writes."""
import json
import multiprocessing as mp


def stop_model_probe(process,connection,pixels,shape,*,ack_timeout=5,exit_timeout=3,reap_timeout=5):
    """Confirm memory cleanup before reaping this disposable probe process."""
    import numpy as np
    import signal
    import sys
    acknowledged=False
    try:
        connection.send('stop')
        if connection.poll(ack_timeout):
            response=connection.recv()
            acknowledged=isinstance(response,dict) and response.get('event')=='stopped'
    except (EOFError,OSError):
        pass
    cleared=acknowledged and tuple(shape[:])==(0,0) and not np.any(np.frombuffer(pixels,dtype=np.uint8))
    process.join(exit_timeout)
    before=process.exitcode
    forced=False
    if process.is_alive():
        forced=True
        process.terminate()
        process.join(reap_timeout)
        if process.is_alive():
            process.kill()
            process.join(reap_timeout)
    code=process.exitcode
    controlled={-signal.SIGTERM} if sys.platform=='win32' else {-signal.SIGTERM,-signal.SIGKILL}
    clean_exit=not process.is_alive() and (code==0 or (forced and before is None and code in controlled))
    result={'stop_acknowledged':acknowledged,'buffers_cleared':bool(cleared),
        'graceful_exit':not forced and code==0,'forced_termination':forced,
        'exit_code_before_cleanup':before,'exit_code':code,'reaped':not process.is_alive()}
    return bool(acknowledged and cleared and clean_exit),result


def spawned_probe(connection):
    connection.send('stargate-worker-ok')
    connection.close()


def model_diagnostics(root, model_dir, connection):
    """Only model-init step names/types/stack locations; never exception text or locals."""
    import traceback
    from pathlib import Path
    step='assets'
    try:
        from ai.models import verified_assets
        assets=verified_assets(root,model_dir)
        connection.send({'step':step,'ok':True})
        from ai.detector.retinaface import RetinaFace
        from ai.recognizer.arcface import ArcFace
        from ai.liveness.minifasnet import MiniFASNet
        for step,constructor in (('detector',RetinaFace),('recognizer',ArcFace),('liveness',MiniFASNet)):
            model=constructor(assets)
            connection.send({'step':step,'ok':True})
            del model
    except Exception as error:
        cause=error.__context__ or error
        connection.send({'step':step,'ok':False,'error_type':type(cause).__name__,
            'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno}
                      for f in traceback.extract_tb(cause.__traceback__)]})
    finally:connection.close()


def check_package(config, *, verify_models=False):
    checks={};process=None;diagnostics=[];worker_event=None;shutdown=None
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QImageReader
        import os
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        app=QApplication.instance() or QApplication([])
        checks['qt_image_plugins']={b'png',b'jpeg'} <= set(bytes(x) for x in QImageReader.supportedImageFormats())
        for name in ('resources/sounds/success.wav','resources/samples/profile-removed.svg',
                     'resources/branding/stargate.png','resources/branding/stargate.ico',
                     'models/manifest.json','database/migrations/env.py'):
            checks[name]=(config.resource_root/name).is_file()
        # Explicitly import native/report/DB dependencies; never connect to a server here.
        import cv2,numpy,onnxruntime,torch,psycopg,cryptography,keyring,pandas,openpyxl,reportlab
        onnxruntime.disable_telemetry_events()
        checks['native_libraries']=True
        receive,send=mp.get_context('spawn').Pipe(duplex=False)
        process=mp.get_context('spawn').Process(target=spawned_probe,args=(send,))
        process.start();send.close()
        checks['spawn']=receive.poll(20) and receive.recv()=='stargate-worker-ok'
        process.join(10);checks['worker_exit']=process.exitcode==0
        receive.close()
        config.log_dir.mkdir(parents=True,exist_ok=True)
        from tempfile import TemporaryFile
        with TemporaryFile(dir=config.log_dir) as stream:stream.write(b'probe')
        checks['writable_user_data']=True
        if verify_models:
            from ai.process import inference_process
            from ai.contracts import EngineOptions
            ctx=mp.get_context('spawn')
            pixels=ctx.RawArray('B',540*960*3);shape=ctx.RawArray('i',2);lock=ctx.Lock()
            parent,child=ctx.Pipe()
            process=ctx.Process(target=inference_process,args=(config.resource_root,config.model_dir,
                EngineOptions(),pixels,shape,lock,child))
            process.start();child.close()
            ready=parent.recv() if parent.poll(60) else {}
            worker_event=ready.get('event','no_response')
            checks['pinned_ai_models']=ready.get('event')=='ready'
            if checks['pinned_ai_models']:
                with lock:shape[:]=(240,320)
                parent.send('analyze')
                result=parent.recv() if parent.poll(20) else {}
                checks['ai_worker_blank_frame']=result.get('event')=='result' and result.get('status')=='no_face'
                checks['ai_worker_exit'],shutdown=stop_model_probe(process,parent,pixels,shape)
                checks['ai_worker_stop_ack']=shutdown['stop_acknowledged']
                checks['ai_worker_buffers_cleared']=shutdown['buffers_cleared']
            parent.close()
            if not checks['pinned_ai_models']:
                if process.is_alive():process.terminate();process.join(5)
                receive,send=ctx.Pipe(duplex=False)
                process=ctx.Process(target=model_diagnostics,args=(config.resource_root,config.model_dir,send))
                process.start();send.close()
                import time
                deadline=time.monotonic()+60
                while time.monotonic()<deadline:
                    if receive.poll(.2):
                        try:diagnostics.append(receive.recv())
                        except EOFError:break
                    elif not process.is_alive():break
                process.join(5);receive.close()
        report={'package_check':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
        if diagnostics:report['model_diagnostics']=diagnostics
        if verify_models:report['ai_worker_event']=worker_event
        if shutdown is not None:report['ai_worker_shutdown']=shutdown
        print(json.dumps(report,indent=2))
        return 0 if all(checks.values()) else 2
    except Exception as error:
        print(json.dumps({'package_check':'FAIL','error_type':type(error).__name__,'checks':checks}))
        return 2
    finally:
        if process is not None and process.is_alive():process.terminate();process.join(5)

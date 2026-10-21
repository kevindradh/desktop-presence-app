"""Explicit camera/model smoke. Numeric diagnostics only, no images/embeddings stored."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera-index',type=int,default=0)
    parser.add_argument('--samples',type=int,default=8)
    parser.add_argument('--output',type=Path,default=ROOT/'.local/stage-07-camera.json')
    args=parser.parse_args()
    if not 0<=args.camera_index<=15 or not 1<=args.samples<=100:
        parser.error('Nomor kamera 0–15 dan jumlah sampel 1–100 diperlukan.')
    import numpy as np
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtTest import QTest
    from app.settings.config import load_config
    from app.services.camera_capture import CaptureSpec
    from app.services.cameras import CameraManager
    from app.services.inference import InferenceController
    config=load_config(ROOT)
    app=QCoreApplication([])
    camera=CameraManager(config)
    worker=InferenceController(config)
    pending=[None,0.]
    results=[]
    def frame(device,image):
        if image.isNull():
            pending[0]=None
            return
        pointer=image.constBits()
        pointer.setsize(image.sizeInBytes())
        data=np.frombuffer(pointer,dtype=np.uint8).reshape(image.height(),image.bytesPerLine())[:,:image.width()*3]
        pending[:]=[np.ascontiguousarray(data.reshape(image.height(),image.width(),3)[:,:,::-1]),time.monotonic()]
    def analyzed(response):
        if response['event']=='result':
            results.append({key:response[key] for key in ('status','face_count','live_score','live_class','elapsed_ms')})
    camera.frame_ready.connect(frame)
    worker.result.connect(analyzed)
    began=time.monotonic()
    try:
        worker.start()
        camera.start_many([CaptureSpec(1,'Kamera uji','USB',args.camera_index,1280,720,15)])
        while time.monotonic()-began<45 and len(results)<args.samples:
            app.processEvents()
            if worker.state in ('failed','timeout') or camera.nodes[1].state=='failed':
                break
            if worker.state=='ready' and pending[0] is not None and time.monotonic()-pending[1]<1:
                worker.submit(pending[0])
            QTest.qWait(10)
    finally:
        if pending[0] is not None:
            pending[0].fill(0)
        pending[0]=None
        camera.stop_all()
        worker.stop()
        deadline=time.monotonic()+5
        while time.monotonic()<deadline and (camera.busy or worker.active):
            app.processEvents()
            QTest.qWait(10)
        camera.shutdown_now()
        worker.shutdown_now()
    report=dict(date=time.strftime('%Y-%m-%d'),camera_index=args.camera_index,
        samples=results,requested_samples=args.samples,completed=len(results)==args.samples,
        images_saved=0,embeddings_saved=0,device_released=not camera.busy and not worker.active,
        accuracy_claim=False,liveness_acceptance_claim=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['completed'] and report['device_released'] else 1


if __name__=='__main__':
    raise SystemExit(main())

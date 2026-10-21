"""Explicit real-camera smoke test; saves metadata only, never images."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indices",type=int,nargs="+",default=[0,1])
    parser.add_argument("--output",type=Path,default=ROOT/".local/stage-06-cameras.json")
    args=parser.parse_args()
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtTest import QTest
    from app.services.camera_capture import CaptureSpec
    from app.services.cameras import CameraManager
    from app.settings.config import load_config
    app=QApplication([])
    config=replace(load_config(ROOT),camera_open_timeout=8,camera_reconnect_attempts=0)
    manager=CameraManager(config)
    results=[]
    def wait(predicate,seconds=15):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            app.processEvents()
            if predicate():
                return True
            QTest.qWait(10)
        return False
    def run(title,specs,test=False,expected="streaming"):
        began=time.monotonic()
        manager.start_many(specs,test=test)
        reached=wait(lambda: all(manager.nodes[s.device_id].state==expected and
            (expected!="streaming" or manager.nodes[s.device_id].frames>=60) for s in specs))
        details=[dict(index=s.camera_index,state=manager.nodes[s.device_id].state,
            frames=manager.nodes[s.device_id].frames,size=manager.nodes[s.device_id].actual_size) for s in specs]
        manager.stop_all()
        released=wait(lambda:not manager.busy,5)
        clean=all(manager.nodes[s.device_id].process is None and manager.nodes[s.device_id].pixels is None for s in specs)
        results.append(dict(case=title,passed=reached and released and clean,
            elapsed_seconds=round(time.monotonic()-began,2),devices=details,released=released and clean))
    specs=[CaptureSpec(i+1,f"Kamera {index}","USB",index,1280,720,30) for i,index in enumerate(args.indices)]
    try:
        for spec in specs:
            run(f"local-{spec.camera_index}-preview",[spec])
            run(f"local-{spec.camera_index}-reopen-test",[spec],test=True,expected="test_ok")
        run("multiple-local-cameras",specs)
        run("missing-local-camera",[CaptureSpec(90,"Tidak tersedia","USB",15,640,480,15)],expected="failed")
        # Synthetic credentials, closed localhost port. Tests failure handling only.
        run("invalid-rtsp-localhost",[CaptureSpec(91,"RTSP gagal","RTSP",0,640,480,15,
            "rtsp://synthetic:secret@127.0.0.1:9/private?token=hidden")],expected="failed")
    finally:
        manager.shutdown_now()
    report=dict(date=time.strftime("%Y-%m-%d"),results=results,images_saved=False,
        real_rtsp="NOT RUN: source unavailable",physical_unplug="NOT RUN: manual test required")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if all(r["passed"] for r in results) else 1


if __name__=="__main__":
    raise SystemExit(main())

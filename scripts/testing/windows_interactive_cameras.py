"""Installed-runtime camera check; records metadata and never saves frames."""
import multiprocessing
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    assert getattr(sys,'frozen',False)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--indices',type=int,nargs='+',choices=range(16),default=[0,1])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from dataclasses import replace
    from PyQt6.QtWidgets import QApplication
    from app.settings.paths import runtime_paths
    from app.settings.config import load_config
    from app.services.camera_capture import CaptureSpec
    from app.services.cameras import CameraManager
    root=Path(os.environ['LOCALAPPDATA'])/'StarGate-Parallels-0141'
    assert (root/'.local/managed-postgres/state.json').is_file()
    paths=runtime_paths(data_dir=root)
    config=replace(load_config(root,bundle_root=paths.resources),camera_open_timeout=8,camera_reconnect_attempts=0)
    app=QApplication([])
    manager=CameraManager(config)
    results=[]
    trace=[]
    def changed(identifier):
        node=manager.nodes[identifier]
        trace.append({'state':node.state,'frames':node.frames,'opened':bool(node.opened_at),
            'seconds':round(time.monotonic()-node.began,3)})
    manager.changed.connect(changed)
    def wait(predicate,seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            app.processEvents()
            if predicate():return True
            time.sleep(.01)
        return False
    def run(name,specs,expected='streaming'):
        began=time.monotonic()
        trace.clear()
        manager.start_many(specs)
        reached=wait(lambda:all(manager.nodes[s.device_id].state==expected and
            (expected!='streaming' or manager.nodes[s.device_id].frames>=30) for s in specs),18)
        details=[{'index':s.camera_index,'state':manager.nodes[s.device_id].state,
            'frames':manager.nodes[s.device_id].frames,'size':manager.nodes[s.device_id].actual_size} for s in specs]
        manager.stop_all()
        released=wait(lambda:not manager.busy,6)
        clean=all(manager.nodes[s.device_id].process is None and manager.nodes[s.device_id].pixels is None for s in specs)
        result={'case':name,'passed':reached and released and clean,'released':released and clean,
            'seconds':round(time.monotonic()-began,2),'devices':details,'state_trace':list(trace)}
        results.append(result)
        print(json.dumps(result),flush=True)
    specs=[CaptureSpec(index+1,'Uji kamera '+str(index),'USB',index,1280,720,30) for index in args.indices]
    try:
        for spec in specs:run('preview-'+str(spec.camera_index),[spec])
        available=[s for s in specs if any(r['passed'] and r['devices'][0]['index']==s.camera_index for r in results)]
        for spec in available:run('reopen-'+str(spec.camera_index),[spec])
        if len(available)==2:run('simultaneous',available)
        run('unavailable-index',[CaptureSpec(90,'Tidak tersedia','USB',15,640,480,15)],'failed')
    finally:manager.shutdown_now()
    report={'results':results,'images_saved':False,'embeddings_saved':False,
        'requested_indices':args.indices,'other_cameras':'deferred by user',
        'physical_unplug':'not tested','real_rtsp':'not available'}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return 0 if all(row['passed'] for row in results) else 1


if __name__=='__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())

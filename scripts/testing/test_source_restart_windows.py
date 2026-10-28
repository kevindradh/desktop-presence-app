"""Cold-process source startup check without rebooting Windows or opening a camera."""
import json
import logging
import os
from pathlib import Path
import sys
import time

SOURCE=Path('C:/StarGate-source-0143')
DATA=Path(os.environ['LOCALAPPDATA'])/'StarGate-Source-UAT0143'
OUTPUT=Path('C:/StarGate-build/source-evidence-0143/restart-check.json')


def main():
    assert sys.platform=='win32' and (DATA/'.local/managed-postgres/state.json').is_file()
    sys.path.insert(0,str(SOURCE))
    os.environ['QT_QPA_PLATFORM']='offscreen'
    from PyQt6.QtWidgets import QApplication
    from app.settings.config import load_config
    from app.services.local_database import verify_runtime,run_tool,stop_local
    from app.services.database import Database,create_database_engine
    from app.services.auth import AuthService
    from app.services.credential_store import CredentialStore
    from app.services.errors import ErrorReporter
    from app.services.inference import InferenceController
    from app.ui.session_window import SessionWindow
    app=QApplication([])
    app.setQuitOnLastWindowClosed(False)
    config=load_config(DATA,bundle_root=SOURCE)
    runtime=verify_runtime(SOURCE)
    folder=DATA/'.local/managed-postgres'
    stop_local(DATA,SOURCE)
    assert run_tool(runtime,'pg_ctl','-D',folder/'data','status').returncode!=0
    database=Database(create_database_engine(config.database))
    logger=logging.Logger('source-restart-check')
    logger.addHandler(logging.NullHandler())
    window=SessionWindow(config,logger,ErrorReporter(logger),AuthService(database),CredentialStore(config))
    window.show()
    def wait(predicate,seconds):
        limit=time.monotonic()+seconds
        while time.monotonic()<limit:
            app.processEvents()
            if predicate():return
            time.sleep(.01)
        raise TimeoutError('Source startup check timed out')
    try:
        wait(lambda:window._entry_state=='setup' and not window.jobs.tasks.busy,90)
        assert run_tool(runtime,'pg_ctl','-D',folder/'data','status').returncode==0
        worker=InferenceController(config)
        began=time.monotonic()
        assert worker.start()
        try:
            wait(lambda:worker.state in {'ready','failed','timeout'},40)
            assert worker.state=='ready',worker.state
            load_seconds=round(time.monotonic()-began,3)
        finally:
            worker.stop()
            wait(lambda:not worker.active,10)
            worker.timer.stop()
        result={'database_before':'stopped','startup_path':'production SessionWindow._initialize',
                'database_auto_started':True,'bootstrap_page_reached':True,
                'model_path':str(config.model_dir),'production_inference_controller':'ready',
                'model_load_seconds':load_seconds,'model_load_timeout_seconds':30,
                'camera_opened':False,'faces_processed':False,'windows_rebooted':False,
                'environment':'Windows11 ARM64 Parallels, CPython3.11.17 x64, source kit'}
        OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps(result),flush=True)
    finally:
        window.close()
        wait(lambda:not window.isVisible() and not window.jobs.tasks.busy,15)
        window.timer.stop()
        window.checkout_timer.stop()
        window.cameras.shutdown_now()
        database.close()
        stop_local(DATA,SOURCE)
    return 0


if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())

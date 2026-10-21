"""Nonblocking persistent model process, bounded shared input and hard deadlines."""
import multiprocessing as mp
import time
import numpy as np
from PyQt6.QtCore import QObject,QTimer,pyqtSignal
from ai.contracts import EngineOptions,image_bgr
from ai.process import inference_process

FRAME_BYTES=960*540*3


class InferenceController(QObject):
    changed=pyqtSignal(str)
    result=pyqtSignal(dict)

    def __init__(self,config,parent=None,*,target=inference_process,clock=time.monotonic,load_timeout=30):
        super().__init__(parent)
        self.config,self.target,self.clock=config,target,clock
        self.load_timeout=load_timeout
        self.options=EngineOptions.from_config(config)
        self.context=mp.get_context("spawn")
        self.state="stopped"
        self.process=self.connection=self.pixels=self.shape=self.lock=None
        self.deadline=self.stop_at=0
        self.terminate_sent=self.kill_sent=False
        self.final_state="stopped"
        self.timer=QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    def _state(self,state):
        self.state=state
        self.changed.emit(state)

    @property
    def active(self):
        return self.process is not None

    def start(self):
        if self.active:
            return False
        self.pixels=self.context.RawArray("B",FRAME_BYTES)
        self.shape=self.context.RawArray("i",2)
        self.lock=self.context.Lock()
        receive,send=self.context.Pipe()
        self.connection=receive
        self.process=self.context.Process(target=self.target,name="StarGateFaceEngine",daemon=True,
            args=(self.config.resource_root,self.config.model_dir,self.options,self.pixels,self.shape,self.lock,send))
        try:
            self.process.start()
        except Exception:
            self.stop(final_state="failed")
            return False
        finally:
            send.close()
        self.deadline=self.clock()+self.load_timeout
        self._state("loading")
        return True

    def submit(self,frame,*,reference=False,capture=False):
        if self.state!="ready":
            return False
        frame=image_bgr(frame)
        height,width=frame.shape[:2]
        if height>540 or width>960:
            raise ValueError("Ukuran frame pemeriksaan melampaui batas.")
        if not self.lock.acquire(timeout=0):
            return False
        try:
            np.frombuffer(self.pixels,dtype=np.uint8,count=frame.size)[:]=frame.reshape(-1)
            self.shape[:]=(height,width)
        finally:
            self.lock.release()
        try:
            self.connection.send("capture" if capture else ("reference" if reference else "analyze"))
        except (OSError,EOFError):
            self.stop(final_state="failed")
            return False
        self.deadline=self.clock()+self.options.recognition_timeout
        self._state("busy")
        return True

    def clear_reference(self):
        if self.state!="ready":
            return False
        try:
            self.connection.send("clear")
        except (OSError,EOFError):
            self.stop(final_state="failed")
            return False
        self.deadline=self.clock()+self.options.recognition_timeout
        self._state("busy")
        return True

    def stop(self,*,final_state="stopped"):
        if not self.active:
            self._state(final_state)
            return
        if self.state=="stopping":
            return
        self.final_state=final_state
        self.stop_at=self.clock()
        self.terminate_sent=self.kill_sent=False
        try:
            self.connection.send("stop")
        except (OSError,EOFError,BrokenPipeError):
            pass
        self._state("stopping")

    def _release(self):
        if self.connection is not None:
            self.connection.close()
        if self.process is not None:
            if self.process.pid is not None:
                self.process.join(0)
            self.process.close()
        if self.pixels is not None:
            np.frombuffer(self.pixels,dtype=np.uint8).fill(0)
        self.process=self.connection=self.pixels=self.shape=self.lock=None
        self._state(self.final_state)

    def poll(self):
        if not self.active:
            return
        now=self.clock()
        if self.state=="stopping":
            if self.process.pid is None or not self.process.is_alive():
                self._release()
            elif now-self.stop_at>=.5 and not self.terminate_sent:
                self.process.terminate()
                self.terminate_sent=True
            elif now-self.stop_at>=1 and not self.kill_sent:
                self.process.kill()
                self.kill_sent=True
            return
        try:
            if self.state in ("loading","busy") and now>=self.deadline:
                self.stop(final_state="timeout")
                return
            while self.connection.poll():
                response=self.connection.recv()
                if not isinstance(response,dict):
                    self.stop(final_state="failed")
                    return
                event=response.get("event")
                if event=="timeout":
                    self.stop(final_state="timeout")
                    return
                if event=="error":
                    self.stop(final_state="failed")
                    return
                if event not in ("ready","result","cleared"):
                    self.stop(final_state="failed")
                    return
                self._state("ready")
                self.result.emit(response)
            if not self.process.is_alive():
                self.stop(final_state="failed")
            elif self.state in ("loading","busy") and now>=self.deadline:
                self.stop(final_state="timeout")
        except (OSError,EOFError,ValueError):
            self.stop(final_state="failed")

    def shutdown_now(self):
        self.timer.stop()
        if not self.active:
            return
        if self.process.pid is not None and self.process.is_alive():
            self.process.terminate()
            self.process.join(.3)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(.5)
        self.final_state="stopped"
        self._release()

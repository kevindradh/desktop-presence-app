"""Nonmodal five-pose registration dialog; drafts stay private until explicit Save."""
import time
from dataclasses import replace
import base64
import json
from PyQt6.QtCore import QTimer,pyqtSignal
from PyQt6.QtWidgets import QDialog,QHBoxLayout,QLabel,QPushButton,QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage,QPixmap,QTransform
from ai.enrollment import GUIDES
from ai.enrollment_process import EnrollmentTarget
from app.ui.ai_lab import AiLab


class CaptureLab(AiLab):
    completed=pyqtSignal(object)
    discarded=pyqtSignal()

    def __init__(self,config,target,*,capture_target=None,verification=False):
        self.verification=verification
        self.capture_requested=False
        self.complete=False
        self.completed_photo=None
        self.preview_active=False
        self.guides=dict(GUIDES,LEFT='Putar perlahan hingga hidung ke kiri gambar',
                         RIGHT='Putar perlahan hingga hidung ke kanan gambar')
        effective=config if verification else replace(config,liveness_enabled=True,liveness_threshold=.85)
        super().__init__(effective,capture_target=capture_target,inference_target=target,consent_required=False)
        self.setWindowTitle('StarGate')
        self.reference_button.setText('Capture')
        if verification:self.reference_button.setText('Periksa wajah ini')
        self.reference_button.clicked.disconnect()
        self.reference_button.clicked.connect(self.request_capture)
        self.start_button.setText('Mulai')
        self.stop_button.setText('Hentikan && hapus')
        self.preview.setMinimumSize(640,360)
        self.preview.setMaximumHeight(16777215)
        self.preview.setStyleSheet('background: #142d25; border: 1px solid #d3ded4; border-radius: 6px;')
        self.preview.clear()
        for widget in (self.clear_button,self.record_button,self.condition,self.summary,
                       self.state_label,self.detail,self.threshold_label):
            widget.hide()
        for label in self.findChildren(QLabel):
            if label.text().startswith('Alat uji sementara.'):
                label.hide()
            if label.objectName()=='pageTitle':
                label.hide()
        self.guide=QLabel(self.guides['FRONT'] if verification else '1/5 • '+self.guides['FRONT'])
        self.guide.setWordWrap(True)
        self.centralWidget().layout().insertWidget(1,self.guide)
        self.controls()

    def controls(self):
        super().controls()
        if hasattr(self,'reference_button'):
            self.reference_button.setEnabled(not self.complete and not self.closing and self.cameras.busy
                and self.inference.state in ('ready','busy'))
            if self.complete:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(not self.closing)

    def request_capture(self):
        self.capture_requested=True
        self.pump()

    def pump(self):
        if self.complete or self.closing or not self.processing_allowed or self.inference.state!='ready':
            return
        if self.latest is not None and time.monotonic()-self.latest_at<1:
            if self.inference.submit(self.latest,capture=self.capture_requested):
                self.capture_requested=False

    def analyzed(self,response):
        if self.closing or (response.get('event')=='result' and not self.preview_active):
            return
        if response.get('event')=='result':
            response=dict(response)
            packet=response.pop('packet',None)
            expected=response.get('expected')
            count=response.get('captured',0)
            if hasattr(self,'guide'):
                self.guide.setText(self.guides['FRONT'] if self.verification else (f'{count+1}/5 • '+self.guides[expected] if expected else 'Lima sudut lengkap. Periksa data, lalu pilih Simpan.'))
            super().analyzed(response)
            if response.get('capture_message'):
                self.detail.setText(response['capture_message'])
            if packet is not None:
                self.complete=True
                try:
                    photo=base64.b64decode(json.loads(packet.body)['photo'],validate=True)
                    self.completed_photo=QImage.fromData(photo,'PNG')
                except (ValueError,KeyError,TypeError):
                    self.completed_photo=None
                self.cameras.stop_all()
                self.inference.stop()
                self.latest=None
                self.completed.emit(packet)
                self.controls()
        else:
            super().analyzed(response)

    def frame(self,device,image):
        if self.complete:
            if self.completed_photo is not None and not self.completed_photo.isNull():
                self.preview.setPixmap(QPixmap.fromImage(self.completed_photo).scaled(self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                self._mirror_preview()
            else:
                self.preview.setText('Probe diterima; kamera sudah dihentikan.' if self.verification else 'Lima sudut lengkap; kamera sudah dihentikan.')
            return
        if not self.preview_active:
            self.preview.clear()
            return
        super().frame(device,image)
        if image.isNull():
            self.preview.clear()
        else:
            self._mirror_preview()

    def _mirror_preview(self):
        # Only the displayed pixmap follows the user's motion; inference keeps the source frame.
        pixmap=self.preview.pixmap()
        if pixmap is not None and not pixmap.isNull():
            self.preview.setPixmap(pixmap.transformed(QTransform().scale(-1,1)))

    def start(self):
        super().start()
        self.preview_active=self.cameras.busy or self.inference.active

    def engine_state(self,state):
        super().engine_state(state)
        self.state_label.setVisible(state in ('failed','timeout'))

    def camera_state(self,device):
        super().camera_state(device)
        if self.cameras.nodes[device].state=='failed':
            self.state_label.show()

    def stop(self):
        self.preview_active=False
        self.capture_requested=False
        if hasattr(self,'complete'):
            self.complete=False
            self.completed_photo=None
        super().stop()
        self.preview.clear()
        self.state_label.hide()
        if hasattr(self,'guide'):
            self.guide.setText(self.guides['FRONT'] if self.verification else '1/5 • '+self.guides['FRONT'])
        self.discarded.emit()


class EnrollmentDialog(QDialog):
    saved=pyqtSignal(object)

    def __init__(self,controller,binding,fields,*,target=None,capture_target=None):
        super().__init__(controller)
        self.controller=controller
        self.binding=binding
        self.fields=dict(fields)
        self.packet=None
        self.saving=False
        self.closing=False
        self.result_code=QDialog.DialogCode.Rejected
        self.verification=binding.get('purpose')=='verification'
        self.setWindowTitle('StarGate')
        self.resize(1120,820)
        self.setMinimumSize(900,720)
        from app.services.settings import configured
        config=configured(controller.config,binding['settings'])
        self.lab=CaptureLab(config,target or EnrollmentTarget(controller.enrollment_service.key,binding),
            capture_target=capture_target,verification=self.verification)
        self.lab.setParent(self)
        panel=self.lab.takeCentralWidget()
        body=QVBoxLayout(self)
        body.addWidget(QLabel(f"{fields['code']} • {fields['name']}"))
        body.addWidget(panel)
        self.message=QLabel('Belum ada data yang disimpan.')
        self.message.setWordWrap(True)
        body.addWidget(self.message)
        self.save_button=QPushButton('Simpan')
        self.save_button.setProperty('variant','primary')
        if self.verification:self.save_button.setText('Bandingkan dengan database')
        self.cancel_button=QPushButton('Batal')
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)
        actions=QHBoxLayout()
        actions.addWidget(self.cancel_button,1)
        actions.addWidget(self.save_button,1)
        body.addLayout(actions)
        self.lab.completed.connect(self.complete)
        self.lab.discarded.connect(self.discard)
        self.lab.inference.changed.connect(self.state_changed)
        self.lab.cameras.changed.connect(lambda unused:self.state_changed('camera'))

    @property
    def busy(self):
        return self.saving or self.lab.cameras.busy or self.lab.inference.active

    def complete(self,packet):
        if not self.closing:
            self.packet=packet
            self.save_button.setEnabled(True)
            self.message.setText('Probe siap; bandingkan dengan data tersimpan. Probe ini tidak akan disimpan.' if self.verification else 'Lima sudut lengkap; foto profil diambil dari sampel depan. Simpan untuk menyelesaikan registrasi.')

    def discard(self):
        self.packet=None
        self.save_button.setEnabled(False)
        self.message.clear()

    def state_changed(self,state):
        if state in ('failed','timeout') or not self.lab.processing_allowed:
            self.packet=None
            self.save_button.setEnabled(False)

    def save(self):
        if self.saving or self.packet is None or self.closing or not self.controller.login:
            return
        if self.controller.jobs.tasks.busy:
            QTimer.singleShot(25,self.save)
            return
        self.saving=True
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.message.setText('Membandingkan wajah...' if self.verification else 'Menyimpan...')
        token=self.controller.login.token
        packet=self.packet
        options=dict(self.fields,member_id=self.binding['member_id'],revision=self.binding['revision'])
        def done(result):
            self.saving=False
            self.cancel_button.setEnabled(True)
            if result.error:
                self.message.setText(result.error)
                self.save_button.setEnabled(not self.closing)
                self.controller._handle_denial(result.error)
            else:
                self.packet=None
                if self.verification:
                    self.message.setText(('Cocok dengan anggota terpilih.' if result.value.matched else 'Tidak cocok dengan anggota terpilih.')+
                        ' Probe tidak disimpan.')
                    self.cancel_button.setText('Tutup')
                    return
                self.result_code=QDialog.DialogCode.Accepted
                self.saved.emit(result.value)
                self.closing=True
            if self.closing:
                self.close()
        operation=(lambda:self.controller.enrollment_service.verify(token,packet)) if self.verification else (lambda:self.controller.enrollment_service.save(token,packet,**options))
        self.controller.jobs.run(operation,done,blocks_ui=False)

    def reject(self):
        self.closing=True
        self.close()

    def closeEvent(self,event):
        self.closing=True
        self.save_button.setEnabled(False)
        self.lab.timer.stop()
        self.lab.closing=True
        self.lab.stop()
        self.packet=None
        if self.busy:
            QTimer.singleShot(50,self.close)
            event.ignore()
            return
        self.lab.cameras.shutdown_now()
        self.lab.inference.shutdown_now()
        self.controller.enrollment_service.cancel(self.binding)
        self.lab.deleteLater()
        QDialog.done(self,self.result_code.value)
        event.accept()

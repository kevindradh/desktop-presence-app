"""Explicit Stage 7 lab, isolated from login/enrollment/attendance and all databases."""
import numpy as np
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtGui import QColor,QPainter,QPen,QPixmap
from PyQt6.QtWidgets import (QCheckBox,QComboBox,QHBoxLayout,QLabel,QMainWindow,
    QPushButton,QSpinBox,QVBoxLayout,QWidget)
from app.services.camera_capture import CaptureSpec
from app.services.cameras import CameraManager,FINAL
from app.services.inference import InferenceController

STATUS={"no_face":"Tidak ada wajah", "multiple_faces":"Lebih dari satu wajah; gunakan satu orang",
    "too_small":"Wajah terlalu kecil; mendekat ke kamera", "partial_face":"Wajah terpotong; posisikan di tengah",
    "lighting":"Cahaya kurang sesuai", "blurred":"Wajah kurang tajam; tahan posisi dan periksa fokus",
    "alignment":"Posisi wajah belum sesuai", "spoof":"Ditolak oleh pemeriksaan keaslian",
    "ready":"Wajah lolos pemeriksaan awal"}


class AiLab(QMainWindow):
    def __init__(self,config,*,capture_target=None,inference_target=None,consent_required=True):
        super().__init__()
        self.setWindowTitle("StarGate — Uji AI Tahap 7")
        self.resize(1040,820)
        self.config=config
        self.closing=False
        self.latest=None
        self.latest_at=0.
        self.want_reference=False
        self.want_clear=False
        self.results=[]
        self.reference_active=False
        self.last_result=None
        self.result_at=0.
        self.cameras=CameraManager(config,parent=self,**({"capture_target":capture_target} if capture_target else {}))
        self.inference=InferenceController(config,self,**({"target":inference_target} if inference_target else {}))
        widget=QWidget()
        self.setCentralWidget(widget)
        body=QVBoxLayout(widget)
        title=QLabel("Pemeriksaan wajah — Tahap 7")
        title.setObjectName("pageTitle")
        body.addWidget(title)
        note=QLabel("Alat uji sementara. Tidak menyimpan foto atau embedding dan tidak mencatat absensi. Semua referensi hilang saat dihentikan. Ini belum bukti akurasi atau ketahanan anti-spoof produksi.")
        note.setWordWrap(True)
        body.addWidget(note)
        self.consent=QCheckBox("Saya setuju memproses wajah peserta yang mengizinkan, hanya di memori selama pengujian ini") if consent_required else None
        if self.consent is not None:
            body.addWidget(self.consent)
        row=QHBoxLayout()
        row.addWidget(QLabel("Nomor kamera lokal"))
        self.index=QSpinBox()
        self.index.setRange(0,15)
        row.addWidget(self.index)
        self.start_button=QPushButton("Mulai pemeriksaan")
        self.stop_button=QPushButton("Hentikan dan hapus referensi")
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        body.addLayout(row)
        self.preview=QLabel("Kamera belum dibuka")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(480,270)
        self.preview.setMaximumHeight(400)
        self.preview.setWordWrap(True)
        body.addWidget(self.preview,1)
        self.state_label=QLabel("Belum dimulai")
        self.detail=QLabel("")
        self.detail.setWordWrap(True)
        body.addWidget(self.state_label)
        body.addWidget(self.detail)
        row=QHBoxLayout()
        self.reference_button=QPushButton("Ambil referensi sementara")
        self.clear_button=QPushButton("Hapus referensi")
        row.addWidget(self.reference_button)
        row.addWidget(self.clear_button)
        body.addLayout(row)
        row=QHBoxLayout()
        self.condition=QComboBox()
        for title,code in (("Wajah asli","genuine"),("Foto cetak","print"),("Foto pada layar","screen_photo"),("Replay video","video")):
            self.condition.addItem(title,code)
        self.record_button=QPushButton("Catat hasil terakhir (angka saja)")
        row.addWidget(self.condition)
        row.addWidget(self.record_button)
        body.addLayout(row)
        self.summary=QLabel("Belum ada hasil yang dicatat. Catat satu hasil per percobaan, bukan per frame.")
        self.summary.setWordWrap(True)
        body.addWidget(self.summary)
        self.threshold_label=QLabel(f"Similarity {config.similarity_threshold:.2f} • anti-spoof "
            f"{'aktif' if config.liveness_enabled else 'NONAKTIF — hasil bukan bukti liveness'}, "
            f"ambang {config.liveness_threshold:.2f} • timeout {config.recognition_timeout:g} detik")
        body.addWidget(self.threshold_label)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.reference_button.clicked.connect(self.take_reference)
        self.clear_button.clicked.connect(self.clear_reference)
        self.record_button.clicked.connect(self.record)
        if self.consent is not None:
            self.consent.toggled.connect(self.consent_changed)
        self.cameras.frame_ready.connect(self.frame)
        self.cameras.changed.connect(self.camera_state)
        self.inference.changed.connect(self.engine_state)
        self.inference.result.connect(self.analyzed)
        self.timer=QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.pump)
        self.timer.start()
        self.controls()

    @property
    def processing_allowed(self):
        return self.consent is None or self.consent.isChecked()

    def controls(self):
        active=self.cameras.busy or self.inference.active
        self.start_button.setEnabled(self.processing_allowed and not active and not self.closing)
        self.stop_button.setEnabled(active and not self.closing)
        self.index.setEnabled(not active)
        ready=self.inference.state in ("ready","busy") and self.cameras.busy and not self.closing
        self.reference_button.setEnabled(ready)
        self.clear_button.setEnabled(self.reference_active and ready)
        self.record_button.setEnabled(self.last_result is not None and not self.closing)

    def consent_changed(self,checked):
        if not checked:
            self.stop()
        self.controls()

    def start(self):
        if not self.processing_allowed or self.closing or self.cameras.busy or self.inference.active:
            return
        self.last_result=None
        self.detail.clear()
        self.inference.start()
        if self.inference.state=="loading":
            self.cameras.start_many([CaptureSpec(1,"Kamera uji","USB",self.index.value(),1280,720,15)])
        self.controls()

    def stop(self):
        self.cameras.stop_all()
        self.inference.stop()
        if self.latest is not None:
            self.latest.fill(0)
        self.latest=None
        self.last_result=None
        self.reference_active=False
        self.want_reference=self.want_clear=False
        self.preview.setPixmap(QPixmap())
        self.preview.setText("Pemeriksaan dihentikan; referensi sementara dibuang")
        self.detail.clear()
        self.controls()

    def frame(self,device,image):
        if image.isNull() or self.closing or not self.processing_allowed:
            if self.latest is not None:
                self.latest.fill(0)
            self.latest=None
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Menunggu kamera")
            return
        import time
        pointer=image.constBits()
        pointer.setsize(image.sizeInBytes())
        rgb=np.frombuffer(pointer,dtype=np.uint8).reshape(image.height(),image.bytesPerLine())[:,:image.width()*3].reshape(image.height(),image.width(),3)
        self.latest=np.ascontiguousarray(rgb[:,:,::-1])
        self.latest_at=time.monotonic()
        overlay=image.copy()
        if self.last_result and self.latest_at-self.result_at<1 and self.last_result.get("box"):
            painter=QPainter(overlay)
            painter.setPen(QPen(QColor("#f5bd42"),2))
            x1,y1,x2,y2=self.last_result["box"]
            painter.drawRect(x1,y1,x2-x1,y2-y1)
            for x,y in self.last_result.get("points",()):
                painter.drawEllipse(int(x)-2,int(y)-2,4,4)
            painter.end()
        self.preview.setPixmap(QPixmap.fromImage(overlay).scaled(self.preview.size(),Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def camera_state(self,device):
        node=self.cameras.nodes[device]
        if node.state=="failed":
            self.stop()
            self.state_label.setText("Kamera tidak tersedia. Periksa nomor kamera dan mulai manual.")
        self.controls()

    def engine_state(self,state):
        text={"loading":"Menyiapkan model…", "ready":"Model siap", "busy":"Memeriksa wajah…",
            "stopping":"Menghentikan…", "stopped":"Pemeriksaan dihentikan", "timeout":"Waktu pemeriksaan habis; mulai ulang",
            "failed":"Model gagal dimuat/dijalankan; periksa berkas dan checksum"}
        self.state_label.setText(text[state])
        if state in ("failed","timeout"):
            self.cameras.stop_all()
            self.reference_active=False
            self.last_result=None
            self.latest=None
            self.preview.setPixmap(QPixmap())
            self.preview.setText(text[state])
        self.controls()

    def take_reference(self):
        self.want_reference=True
        self.pump()

    def clear_reference(self):
        self.want_clear=True
        self.pump()

    def pump(self):
        import time
        if self.closing or not self.processing_allowed or self.inference.state!="ready":
            return
        if self.want_clear:
            if self.inference.clear_reference():
                self.want_clear=False
            return
        if self.latest is not None and time.monotonic()-self.latest_at<1:
            if self.inference.submit(self.latest,reference=self.want_reference):
                self.want_reference=False

    def analyzed(self,response):
        if response["event"]=="cleared":
            self.reference_active=False
            self.last_result=None
            self.detail.setText("Referensi sementara dihapus")
        elif response["event"]=="result":
            import time
            self.result_at=time.monotonic()
            self.last_result=response
            self.reference_active=response["has_reference"]
            score=response["live_score"]
            similarity=response["similarity"]
            detail=STATUS.get(response["status"],"Pemeriksaan belum selesai")
            detail+=f" • {response['face_count']} wajah • {response['elapsed_ms']:.0f} ms"
            if score is not None:
                detail+=f" • skor live {score:.3f}"
            if similarity is not None:
                detail+=f" • similarity {similarity:.3f} • "+("Cocok dengan referensi" if response["matched"] else "Tidak cocok")
            elif self.reference_active:
                detail+=" • referensi sementara tersedia"
            self.detail.setText(detail)
        self.controls()

    def record(self):
        if self.last_result is None:
            return
        r=self.last_result
        # Copy scalar diagnostics only; omit box, landmarks, image, embedding and identity.
        self.results.append(dict(condition=self.condition.currentData(),status=r["status"],
            live_score=r["live_score"],similarity=r["similarity"],elapsed_ms=r["elapsed_ms"]))
        self.last_result=None
        self.summary.setText("; ".join(f"{code}: {sum(v['condition']==code for v in self.results)} percobaan, "
            f"{sum(v['condition']==code and v['status']=='spoof' for v in self.results)} ditolak anti-spoof"
            for code in ("genuine","print","screen_photo","video")))
        self.controls()

    def closeEvent(self,event):
        self.closing=True
        self.timer.stop()
        self.stop()
        if self.cameras.busy or self.inference.active:
            QTimer.singleShot(50,self.close)
            event.ignore()
            return
        self.cameras.shutdown_now()
        self.inference.shutdown_now()
        self.results.clear()
        event.accept()

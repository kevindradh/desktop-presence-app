"""SuperAdmin backup/restore with reviewed archive and explicit typed confirmation."""
from dataclasses import dataclass
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFileDialog,QFormLayout,QHBoxLayout,QLineEdit,QPushButton,QVBoxLayout,QWidget
from app.services.auth import AuthError
from app.services.database import DataValidationError, DatabaseUnavailable
from app.services.tasks import TaskController
from app.widgets.cards import text_label


@dataclass(frozen=True)
class Result:
    value: object=None
    error: str=''


class BackupsPage(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.reviewed=None;self.restoring=False;self.preparing=False
        self.tasks=TaskController(controller.reporter,self)
        self.tasks.succeeded.connect(self.completed); self.tasks.cancelled.connect(self.cancelled); self.tasks.settled.connect(self.settled)
        self.prepare_timer=QTimer(self);self.prepare_timer.setInterval(100);self.prepare_timer.timeout.connect(self.quiesced)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(text_label('Cadangan terenkripsi • Retensi 7 hari','sectionTitle'))
        layout.addWidget(text_label('Cadangan memuat data aplikasi, foto profil dan embedding. Simpan kata sandi cadangan secara terpisah; kata sandi tidak dapat dipulihkan. Hapus salinan berusia lebih dari 7 hari, termasuk salinan eksternal.','muted'))
        layout.addWidget(text_label('Pemulihan mengganti data, mengakhiri semua sesi, serta menghapus foto profil dan embedding. Anggota wajib registrasi wajah ulang. Kredensial kamera jaringan harus dimasukkan ulang. Cadangan pengaman dibuat sebelum perubahan.','muted'))
        self.password=QLineEdit();self.password.setEchoMode(QLineEdit.EchoMode.Password);self.password.setMaxLength(256)
        self.repeat=QLineEdit();self.repeat.setEchoMode(QLineEdit.EchoMode.Password);self.repeat.setMaxLength(256)
        self.path=QLineEdit();self.path.setReadOnly(True)
        self.confirmation=QLineEdit();self.confirmation.setPlaceholderText('Ketik PULIHKAN setelah memeriksa ringkasan')
        form=QFormLayout()
        for name,field in (('Kata sandi cadangan',self.password),('Ulangi untuk membuat cadangan',self.repeat),('Berkas pemulihan',self.path),('Konfirmasi pemulihan',self.confirmation)):form.addRow(name,field)
        layout.addLayout(form)
        row=QHBoxLayout();self.backup_button=QPushButton('Buat cadangan');self.choose_button=QPushButton('Pilih dan periksa cadangan');self.restore_button=QPushButton('Pulihkan data');self.cancel_button=QPushButton('Batalkan proses')
        for b in (self.backup_button,self.choose_button,self.restore_button,self.cancel_button):row.addWidget(b)
        layout.addLayout(row)
        self.summary=text_label('Belum ada cadangan yang diperiksa.');layout.addWidget(self.summary)
        self.message=text_label('Pilih lokasi baru saat membuat cadangan; berkas yang sudah ada tidak ditimpa.');layout.addWidget(self.message)
        self.progress=text_label('');layout.addWidget(self.progress);self.tasks.progress.connect(lambda n:self.progress.setText(f'Proses: {n}%'))
        self.backup_button.clicked.connect(self.backup);self.choose_button.clicked.connect(self.inspect);self.restore_button.clicked.connect(self.restore);self.cancel_button.clicked.connect(self.cancel)
        self.password.textChanged.connect(self.invalidate);self.confirmation.textChanged.connect(self.controls)
        layout.addStretch();self.controls()

    @property
    def busy(self):return self.tasks.busy or self.preparing
    @property
    def pending(self):return self.busy

    def invalidate(self):
        self.reviewed=None;self.summary.setText('Periksa cadangan kembali setelah mengubah kata sandi.');self.controls()

    def controls(self):
        for field in (self.password,self.repeat,self.confirmation):field.setEnabled(not self.busy)
        self.backup_button.setEnabled(not self.busy);self.choose_button.setEnabled(not self.busy)
        self.restore_button.setEnabled(not self.busy and self.reviewed is not None and self.confirmation.text()=='PULIHKAN')
        self.cancel_button.setEnabled(self.busy)

    def run(self,operation,callback):
        c=self.controller
        if self.tasks.busy or not c.login:return
        self.callback=callback;self.request_token=c.login.token
        def work(ctx):
            try:return Result(operation(self.request_token,ctx))
            except (AuthError,DataValidationError,DatabaseUnavailable) as e:return Result(error=str(e))
        self.tasks.start(work);self.controls()

    def completed(self,result):
        if result.error:self.message.setText(result.error)
        else:self.callback(result.value)

    def settled(self):
        c=self.controller
        if self.restoring:
            self.restoring=False;c._maintenance=False
            if c.shell:
                for field in (c.shell.navigation,c.shell.password_button,c.shell.logout_button):field.setEnabled(True)
        self.controls()

    def failed(self,*args):self.message.setText('Proses gagal. Periksa catatan aplikasi dan coba kembali.')
    def cancelled(self):self.message.setText('Proses dibatalkan; perubahan data tidak diterapkan.')

    def backup(self):
        if self.password.text()!=self.repeat.text():self.message.setText('Kedua kata sandi cadangan harus sama.');return
        path,_=QFileDialog.getSaveFileName(self,'Simpan cadangan baru','stargate.sgbackup','Cadangan StarGate (*.sgbackup)')
        if not path:return
        password=self.password.text()
        def done(result):
            self.message.setText(f'Cadangan berhasil dibuat. Berlaku sampai {result["expires_at"]}.');self.message.setToolTip(path)
            self.password.clear();self.repeat.clear()
        self.run(lambda token,ctx:self.controller.backup_service.backup(token,path,password,ctx),done)

    def inspect(self):
        path,_=QFileDialog.getOpenFileName(self,'Periksa cadangan','','Cadangan StarGate (*.sgbackup)')
        if not path:return
        password=self.password.text();self.path.setText(path);self.reviewed=None
        def done(info):
            self.reviewed=info
            self.summary.setText(f'Dibuat {info["created_at"]} • Berlaku sampai {info["expires_at"]}\n{info["records"]} record; {info["members"]} anggota; {info["photos"]} foto dan {info["embeddings"]} embedding akan dilewati.\nSeluruh sesi berakhir; login menggunakan akun dan password dalam cadangan. Ketik PULIHKAN untuk melanjutkan.')
        self.run(lambda token,ctx:self.controller.backup_service.inspect(token,path,password),done)

    def restore(self):
        if self.reviewed is None or self.confirmation.text()!='PULIHKAN':return
        c=self.controller
        if self.busy:return
        self.preparing=True;c._maintenance=True
        for field in (c.shell.navigation,c.shell.password_button,c.shell.logout_button):field.setEnabled(False)
        c.stop_enrollment();c.stop_attendance();c.cameras.stop_all()
        for route,page in c.shell.administrative_pages.items():
            if route!='backup' and hasattr(page,'on_leave'):page.on_leave()
        self.message.setText('Menghentikan kamera dan proses aktif sebelum pemulihan…')
        self.prepare_timer.start();self.controls()

    def quiesced(self):
        c=self.controller
        if c._closing or not c.login:self.cancel();return
        if c.cameras.busy or c.jobs.tasks.busy or (c.enrollment_dialog and c.enrollment_dialog.busy):return
        if any(getattr(p,'busy',False) for key,p in c.shell.administrative_pages.items() if key!='backup'):return
        self.prepare_timer.stop();self.preparing=False;self.restoring=True
        path=self.path.text();password=self.password.text();digest=self.reviewed['sha256']
        def done(result):
            message='Pemulihan selesai. Semua anggota perlu registrasi wajah ulang. Silakan masuk dengan akun dalam cadangan.'
            if result['cleanup_pending']:message+=' Pembersihan foto lama perlu dicoba ulang.'
            try:c.credentials.clear()
            except Exception:message+=' Hapus sesi tersimpan dari penyimpanan aman bila diperlukan.'
            c._return_login(message)
        self.run(lambda token,ctx:c.backup_service.restore(token,path,password,'PULIHKAN',ctx,expected_digest=digest),done)

    def cancel(self):
        if self.preparing:self.prepare_timer.stop();self.preparing=False;self.restoring=True;self.settled()
        else:self.tasks.cancel()

    def reload(self):pass
    def on_leave(self):
        self.cancel()

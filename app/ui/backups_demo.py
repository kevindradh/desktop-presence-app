"""Disposable recovery demo with explicit actions and public synthetic credentials."""
from contextlib import contextmanager
from PyQt6.QtWidgets import QLabel,QPushButton,QToolBar
from sqlalchemy import select
from app.models.entities import Member,Role
from app.repositories.core import AuditRepository
from app.ui.attendance_demo import NoCredentials
from app.ui.session_window import SessionWindow
from database.attendance_demo import synthetic_camera

DEMO_USER='demo_recovery'
DEMO_PASSWORD='Demo-recovery-2026!'


class BackupsDemo(SessionWindow):
    def __init__(self,config,logger,reporter,auth,login,migration):
        super().__init__(config,logger,reporter,auth,NoCredentials())
        @contextmanager
        def owner():yield migration
        self.backup_service.owner=owner
        self.cameras.capture_target=synthetic_camera
        self._accepted(login);self.checkout_timer.stop()
        self.setWindowTitle('StarGate - DEMO Audit dan Pemulihan Tahap 13')
        bar=QToolBar('Demo pemulihan',self);bar.setMovable(False)
        note=QLabel(' DEMO SINTETIS • Database test sementara • Data kerja tidak diubah ');note.setWordWrap(True);bar.addWidget(note)
        self.mutate_button=QPushButton('Ubah satu anggota sesudah backup');bar.addWidget(self.mutate_button)
        self.login_demo_button=QPushButton('Masuk ulang akun demo');bar.addWidget(self.login_demo_button)
        self.mutate_button.clicked.connect(self.mutate);self.login_demo_button.clicked.connect(self.login_demo)
        self.addToolBar(bar);self.navigate('backup')

    def mutate(self):
        if not self.login or self._maintenance:return
        token=self.login.token
        def operation(session,actor):
            row=session.scalar(select(Member).order_by(Member.id));row.full_name='DIUBAH SESUDAH BACKUP'
            AuditRepository(session).append('member.updated','member',row.id,actor_id=actor.id,details={'changed_fields':['full_name']})
        self.jobs.run(lambda:self.service._protected(token,'members',operation),lambda result:self._message(result.error or 'Nama anggota pertama diubah. Restore untuk mengembalikan nama semula.'))

    def login_demo(self):
        if self.login or self._maintenance:return
        self.jobs.run(lambda:self.service.login(DEMO_USER,DEMO_PASSWORD),lambda result:self._accepted(result.value) if not result.error else self._message(result.error))

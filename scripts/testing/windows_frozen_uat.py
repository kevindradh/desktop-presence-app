"""Build-only installed-runtime UAT; hard-gated to a fresh synthetic database."""
import multiprocessing
multiprocessing.freeze_support()
import json
import os
from pathlib import Path
import sys
import traceback

def run():
    from app.settings.paths import runtime_paths
    from app.settings.config import load_config
    from app.services.database import Database,create_database_engine
    from app.services.auth import AuthService
    from app.services.credential_store import CredentialStore
    paths=runtime_paths()
    config=load_config(paths.data,bundle_root=paths.resources)
    assert (config.database.name=='stargate_clean14' and config.database.host=='127.0.0.1'
            and config.database.port==55434), 'Only the newly owned clean-profile database is permitted'
    database=Database(create_database_engine(config.database))
    auth=AuthService(database)
    credentials=CredentialStore(config)
    try:
        if len(sys.argv)>1 and sys.argv[1]=='inspect':
            from sqlalchemy import select,func
            from app.models.entities import Member,Attendance,FaceEmbedding,User
            with database.transaction() as session:
                counts={cls.__tablename__:session.scalar(select(func.count()).select_from(cls))
                        for cls in (Member,Attendance,FaceEmbedding,User)}
            assert counts=={'members':71,'attendance':1,'face_embeddings':0,'users':1}
            assert (config.root/'keep-after-uninstall.txt').read_text().strip()=='synthetic-preserve-stage14'
            print(json.dumps({'phase':'inspect','preserved_counts':counts,'sentinel':True}),flush=True)
            return
        if len(sys.argv)>1 and sys.argv[1]=='resume':
            token=credentials.get();assert token
            login=auth.resume(token)
            assert auth.authorize(login.token,'backup')
            auth.logout(login.token);credentials.clear()
            assert credentials.get() is None
            print(json.dumps({'phase':'resume','native_credential_restart':True,'cleanup':True}),flush=True)
            return
        import secrets
        from datetime import datetime,time,timezone
        from zoneinfo import ZoneInfo
        from threading import Event
        import time as monotonic_time
        import numpy as np
        from sqlalchemy import select,func
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QImage,QColor
        from PyQt6.QtCore import QByteArray,QBuffer,QIODevice
        from app.models.entities import User,Member,Location,DeviceType,FaceAngle,FaceEmbedding,Attendance
        from app.repositories.core import GroupRepository,MemberRepository,ShiftRepository,DeviceRepository,EmbeddingRepository
        from app.services.bootstrap_admin import bootstrap_super_admin
        from app.services.member_photos import PhotoStore
        from app.services.attendance import AttendanceService
        from app.services.devices import DevicesService
        from ai.contracts import Analysis
        from ai.attendance_process import signed_packet
        from app.services.reports import ReportsService,ReportFilter
        from app.exports.attendance import export_report
        from app.services.tasks import TaskContext
        from app.services.backups import BackupService,REMOVED_PHOTO
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        app=QApplication.instance() or QApplication([])
        initial=secrets.token_urlsafe(24)+'aA1!';changed=secrets.token_urlsafe(24)+'aA1!'
        with database.transaction() as session:
            assert session.scalar(select(func.count()).select_from(User))==0, 'Refusing to reuse a populated test database'
            bootstrap_super_admin(session,'frozen_uat_admin','Penguji Sintetis Windows',initial)
        login=auth.login('frozen_uat_admin',initial)
        assert login.principal.must_change_password
        login=auth.change_password(login.token,initial,changed)
        assert not login.principal.must_change_password
        image=QImage(12,12,QImage.Format.Format_RGB32);image.fill(QColor('#17602f'))
        buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);assert image.save(buffer,'PNG')
        photo=PhotoStore(config.root).import_bytes(bytes(buffer.data()))
        today=datetime.now(ZoneInfo(config.timezone)).date()
        vector=np.zeros(512,dtype=np.float32);vector[0]=1
        version='synthetic-frozen-uat'
        with database.transaction() as session:
            group=GroupRepository(session).create('Grup sintetis Windows')
            member=MemberRepository(session).create('WIN-UAT-001','Peserta Sintetis Windows',group.id,photo)
            member_id=member.id
            shift=ShiftRepository(session).create('Shift sintetis Windows',time(8),time(17),10)
            ShiftRepository(session).assign(member.id,shift.id,today,today)
            location=session.scalar(select(Location))
            device=DeviceRepository(session).create('Perangkat sintetis',DeviceType.USB,location.id)
            device_id=device.id
            for angle in FaceAngle:EmbeddingRepository(session).create(member.id,vector,angle,version)
            for index in range(70):
                row=MemberRepository(session).create(f'EXPORT-{index:03}',
                    'José 東京 '+('Nama sintetis untuk uji Windows '*3)+str(index),group.id,REMOVED_PHOTO)
                ShiftRepository(session).assign(row.id,shift.id,today,today)
        clock=lambda:datetime.combine(today,time(8),ZoneInfo(config.timezone)).astimezone(timezone.utc)
        attendance=AttendanceService(auth,config,DevicesService(auth,config),clock=clock)
        binding=attendance.begin(login.token,[device_id])[0].binding
        result=attendance.submit(login.token,signed_packet(attendance.key,binding,1,monotonic_time.monotonic(),
            analysis=Analysis('ready',1,live_score=.99,live_class=1,embedding=vector,model_version=version)))
        assert result.saved and result.event=='IN'
        attendance.cancel_all()
        reports=ReportsService(auth,config)
        snapshot=reports.build(login.token,ReportFilter(today,today))
        assert len(snapshot.rows)==71
        output=Path(r'C:\StarGate-UAT14\frozen-exports');output.mkdir(exist_ok=True)
        context=lambda:TaskContext(Event(),lambda value:None)
        for kind in ('xlsx','pdf'):
            export_report(reports,login.token,snapshot.id,output/('synthetic.'+kind),kind,context())
        print(json.dumps({'phase':'data','bootstrap_login_change':True,'synthetic_attendance':True,
                          'exports_rows':71,'exports':['xlsx','pdf']}),flush=True)
        backup=BackupService(auth,config.root,config_file=config.config_file,resource_root=config.resource_root)
        password=secrets.token_urlsafe(24)+'aA1!'
        destination=config.root/'frozen-roundtrip.sgbackup'
        backup.backup(login.token,destination,password)
        info=backup.inspect(login.token,destination,password)
        assert info['photos']==1 and info['embeddings']==5
        with database.transaction() as session:
            session.get(Member,member_id).full_name='Changed before restore'
        result=backup.restore(login.token,destination,password,'PULIHKAN',expected_digest=info['sha256'])
        assert result['reenrollment_required'] and not result['cleanup_pending']
        with database.transaction() as session:
            assert session.get(Member,member_id).full_name=='Peserta Sintetis Windows'
            assert session.get(Member,member_id).photo_path==REMOVED_PHOTO
            assert session.scalar(select(func.count()).select_from(FaceEmbedding))==0
            assert session.scalar(select(func.count()).select_from(Attendance))==1
        assert not list((config.root/'.local/member_photos').glob('*.png'))
        fresh=auth.login('frozen_uat_admin',changed)
        grant=auth.remember(fresh.token);credentials.set(grant.token)
        assert credentials.get()==grant.token
        auth.close_session(fresh.token)
        print(json.dumps({'phase':'restore','database_roundtrip':True,'biometrics_removed':True,
            'history_preserved':True,'native_credential_saved':True,'real_faces_used':False}),flush=True)
    finally:database.close()

try:run()
except BaseException as error:
    if isinstance(error,SystemExit):raise
    print(json.dumps({'frozen_uat':'FAIL','error_type':type(error).__name__,
        'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno}
                  for f in traceback.extract_tb(error.__traceback__)]}),flush=True)
    raise SystemExit(2)

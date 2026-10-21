"""Reproducible report data, five statuses and 65 rows (two UI pages)."""
import secrets
from sqlalchemy import select
from app.models.entities import Role,Shift
from app.repositories.core import MemberRepository,ShiftRepository,UserRepository
from app.services.auth import password_hash
from database.dashboard_demo import seed_dashboard_demo


def seed_reports_demo(store,config):
    data=seed_dashboard_demo(store,config)
    day=data.clock.now().date()
    password=secrets.token_urlsafe(24)
    hashed=password_hash(password)
    with store.db.transaction() as session:
        from app.models.entities import MemberGroup
        group=session.scalar(select(MemberGroup).order_by(MemberGroup.id))
        shift=session.scalar(select(Shift).where(Shift.shift_name=='Demo 08:00–17:00'))
        for index in range(60):
            name=f'Peserta laporan {index+1:02}'
            if index==0:name='José Müller 東京 - contoh nama panjang pada laporan '+('kehadiran '*8)
            member=MemberRepository(session).create(f'DEMO-12-{index+1:03}',name,group.id,'synthetic/no-photo.png')
            ShiftRepository(session).assign(member.id,shift.id,day,day)
        viewer=UserRepository(session).create_with_hash('demo_report_viewer','Viewer Demo Laporan',hashed,Role.VIEWER)
        viewer.must_change_password=False
    data.auth.close_session(data.login.token)
    data.login=data.auth.login('demo_report_viewer',password)
    data.token=data.login.token
    return data

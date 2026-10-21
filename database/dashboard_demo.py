"""Five synthetic participants for a reproducible Stage 11 dashboard."""
from datetime import time, timedelta
from sqlalchemy import select
from app.models.entities import AttendanceStatus, AttendanceType, MemberLeave
from app.repositories.core import (AttendanceRepository, GroupRepository, MemberRepository, ShiftRepository)
from database.attendance_demo import seed_demo


def seed_dashboard_demo(store, config):
    data=seed_demo(store,config)
    data.clock.advance(11*60)
    day=data.clock.now().date()
    with store.db.transaction() as session:
        from app.models.entities import Shift
        morning=session.scalar(select(Shift))
        group=GroupRepository(session).create('Operasional demo')
        short=ShiftRepository(session).create('Demo awal 07:00–08:00',time(7),time(8))
        for code,name,state in (('P','Hadir tepat waktu','PRESENT'),('L','Hadir terlambat','LATE'),
                                ('I','Sedang izin','LEAVE'),('A','Belum hadir setelah shift','ABSENT')):
            member=MemberRepository(session).create('DEMO-11-'+code,name,group.id,'synthetic/no-photo.png')
            ShiftRepository(session).assign(member.id,short.id if state=='ABSENT' else morning.id,day,day)
            if state=='LEAVE':
                session.add(MemberLeave(member_id=member.id,starts_on=day,ends_on=day))
            elif state in ('PRESENT','LATE'):
                AttendanceRepository(session).record(member_id=member.id,device_id=data.devices[0],shift_id=morning.id,
                    event_type=AttendanceType.IN,timestamp=data.clock.now()-timedelta(minutes=6 if state=='PRESENT' else 0),
                    work_date=day,status=AttendanceStatus(state))
    return data

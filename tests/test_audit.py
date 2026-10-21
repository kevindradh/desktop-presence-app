from datetime import datetime,timedelta,timezone
import pytest
from sqlalchemy import select
from app.models.entities import AuditLog,Role
from app.repositories.core import AuditRepository,MemberRepository,SettingsRepository
from app.services.audit import AuditFilter,AuditService
from app.services.auth import AuthError
from app.services.database import DataValidationError
from tests.test_database import store,graph,record
from tests.test_auth import auth,add_role,NEW

pytestmark=pytest.mark.database


def filters(**kwargs):
    now=datetime.now(timezone.utc)
    return AuditFilter(now-timedelta(days=1),now+timedelta(days=1),**kwargs)


@pytest.mark.parametrize('role',list(Role))
def test_audit_permission_filter_and_no_sensitive_fields(auth,store,role):
    service,login,now=auth;_,other=add_role(service,login,role)
    audit=AuditService(service)
    if role not in (Role.SUPER_ADMIN,Role.ADMIN):
        with pytest.raises(AuthError):audit.read(other.token,filters())
        return
    rows,more=audit.read(other.token,filters(action='auth.login',actor=other.principal.username))
    assert len(rows)==1 and rows[0][2]==other.principal.username and rows[0][3]=='auth.login'
    assert NEW not in str(rows) and other.token not in str(rows)
    service.logout(other.token)
    with pytest.raises(AuthError):audit.read(other.token,filters())


def test_cross_feature_audit_and_pagination(auth,store):
    service,login,now=auth
    with store.db.transaction() as session:
        group,member,shift,device=graph(session)
        record(session,member,shift,device)
        MemberRepository(session).deactivate(member.id,actor_id=login.principal.id)
        SettingsRepository(session).set('duplicate_window',120,actor_id=login.principal.id)
        for _ in range(105):AuditRepository(session).append('system.test','system')
    audit=AuditService(service)
    rows,more=audit.read(login.token,filters(action='system.test'))
    assert len(rows)==100 and more
    next_rows,more=audit.read(login.token,filters(action='system.test',offset=100))
    assert len(next_rows)==5 and not more and not {r[0] for r in rows}&{r[0] for r in next_rows}
    with store.db.transaction() as session:actions=set(session.scalars(select(AuditLog.action)))
    assert {'auth.login','member.created','member.deactivated','attendance.recorded','user.created','setting.changed'}<=actions


def test_audit_invalid_filters(auth):
    service,login,now=auth;audit=AuditService(service)
    for options in ({'action':"auth.login' OR 1=1"},{'offset':-1},{'actor':'x'*81}):
        with pytest.raises(DataValidationError):audit.read(login.token,filters(**options))

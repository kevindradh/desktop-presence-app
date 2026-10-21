"""Read-only, authorized and bounded audit inspection."""
from dataclasses import dataclass
from datetime import datetime
import re
from sqlalchemy import select
from app.models.entities import AuditLog, User
from app.services.database import DataValidationError


@dataclass(frozen=True)
class AuditFilter:
    start: datetime
    end: datetime
    action: str = ''
    actor: str = ''
    offset: int = 0


class AuditService:
    def __init__(self, auth):
        self.auth = auth

    def read(self, token, filters):
        if (not isinstance(filters, AuditFilter) or not isinstance(filters.start, datetime)
                or not isinstance(filters.end, datetime) or filters.start.utcoffset() is None
                or filters.end.utcoffset() is None or filters.end <= filters.start
                or (filters.end - filters.start).days > 366
                or type(filters.offset) is not int or not 0 <= filters.offset <= 1_000_000
                or not isinstance(filters.action, str) or not re.fullmatch(r'[a-z0-9_.]{0,80}', filters.action)
                or not isinstance(filters.actor, str) or len(filters.actor) > 80):
            raise DataValidationError('Filter audit tidak valid; gunakan rentang maksimal 366 hari.')
        def operation(session, user):
            query = (select(AuditLog, User.username).outerjoin(User, User.id == AuditLog.actor_id)
                     .where(AuditLog.created_at >= filters.start, AuditLog.created_at < filters.end))
            if filters.action: query = query.where(AuditLog.action == filters.action)
            if filters.actor: query = query.where(User.username == filters.actor.strip())
            rows = session.execute(query.order_by(AuditLog.id.desc()).offset(filters.offset).limit(101)).all()
            # DTOs only: no session, password hash, token or face data leaves this boundary.
            return tuple((row.id, row.created_at, actor or 'Sistem', row.action,
                          row.entity_type, row.entity_id, dict(row.details)) for row, actor in rows[:100]), len(rows) > 100
        return self.auth._protected(token, 'audit', operation)

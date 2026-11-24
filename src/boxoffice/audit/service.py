import json
import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from boxoffice.audit.contract import AuditEntry, AuditService
from boxoffice.audit.storage import AuditRow


class SqlAuditService(AuditService):

    def __init__(self, session_factory: sessionmaker, delay_s: float = 0.0):
        self._sf, self._delay = session_factory, delay_s

    def record(self, entry: AuditEntry) -> bool:
        if self._delay:
            time.sleep(self._delay)
        with self._sf() as s:
            s.add(AuditRow(
                event_id=entry.event_id, action=entry.action, entity_type=entry.entity_type,
                entity_id=entry.entity_id, occurred_at=entry.occurred_at.replace(tzinfo=None),
                details_json=json.dumps(entry.details, default=str, ensure_ascii=False)))
            try:
                s.commit()
                return True
            except IntegrityError:
                s.rollback()
                return False

    def list_entries(self, limit=50, offset=0, entity_type=None) -> list[AuditEntry]:
        with self._sf() as s:
            q = select(AuditRow).order_by(AuditRow.id)
            if entity_type:
                q = q.where(AuditRow.entity_type == entity_type)
            rows = s.scalars(q.limit(limit).offset(offset)).all()
            return [AuditEntry(r.event_id, r.action, r.entity_type, r.entity_id, r.occurred_at,
                               json.loads(r.details_json)) for r in rows]

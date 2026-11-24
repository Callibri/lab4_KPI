from dataclasses import asdict

from boxoffice.application import events as ev
from boxoffice.application.ports import AuditPort
from boxoffice.audit.contract import AuditEntry, AuditService

_MAP = {
    ev.UserRegistered: ("user.registered", "user", "user_id"),
    ev.MovieCreated: ("movie.created", "movie", "movie_id"),
    ev.MovieUpdated: ("movie.updated", "movie", "movie_id"),
    ev.MovieDeleted: ("movie.deleted", "movie", "movie_id"),
    ev.ReportAdded: ("report.added", "report", "report_id"),
    ev.ReportCorrected: ("report.corrected", "report", "report_id"),
    ev.ReportDeleted: ("report.deleted", "report", "report_id"),
}


def to_audit_entry(event: ev.DomainEvent) -> AuditEntry:
    action, entity_type, id_field = _MAP[type(event)]
    data = asdict(event)
    details = {k: v for k, v in data.items() if k not in ("event_id", "occurred_at", id_field)}
    return AuditEntry(event.event_id, action, entity_type, data[id_field], event.occurred_at, details)


class SyncAuditAdapter(AuditPort):

    def __init__(self, audit: AuditService):
        self._audit = audit

    def record(self, event: ev.DomainEvent) -> None:
        self._audit.record(to_audit_entry(event))


class AuditEventSubscriber:

    def __init__(self, audit: AuditService):
        self._audit = audit

    def __call__(self, event: ev.DomainEvent) -> None:
        self._audit.record(to_audit_entry(event))

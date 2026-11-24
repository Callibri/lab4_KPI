import logging

from boxoffice.application.events import DomainEvent
from boxoffice.application.ports import AuditPort, EventPublisher

log = logging.getLogger(__name__)


class SideEffects:

    def __init__(self, audit: AuditPort | None = None, publisher: EventPublisher | None = None):
        self._audit, self._publisher = audit, publisher

    def emit(self, event: DomainEvent) -> None:
        if self._audit is not None:
            try:
                self._audit.record(event)
            except Exception:
                log.exception("Synchronous audit failed for %s", type(event).__name__)
        if self._publisher is not None:
            try:
                self._publisher.publish(event)
            except Exception:
                log.exception("Publishing failed for %s", type(event).__name__)

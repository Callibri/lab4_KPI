from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class AuditUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class AuditEntry:
    event_id: str
    action: str
    entity_type: str
    entity_id: int
    occurred_at: datetime
    details: dict = field(default_factory=dict)


class AuditService(ABC):
    @abstractmethod
    def record(self, entry: AuditEntry) -> bool:
        pass

    @abstractmethod
    def list_entries(
        self, limit: int = 50, offset: int = 0, entity_type: str | None = None
    ) -> list[AuditEntry]: ...

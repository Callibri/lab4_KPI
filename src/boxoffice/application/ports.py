from abc import ABC, abstractmethod


class TokenService(ABC):
    @abstractmethod
    def issue(self, user_id: int) -> str: ...

    @abstractmethod
    def verify(self, token: str) -> int:
        pass


from boxoffice.application.events import DomainEvent


class AuditPort(ABC):

    @abstractmethod
    def record(self, event: DomainEvent) -> None: ...


class EventPublisher(ABC):

    @abstractmethod
    def publish(self, event: DomainEvent) -> None: ...

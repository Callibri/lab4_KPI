from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: uuid4().hex)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True, kw_only=True)
class UserRegistered(DomainEvent):
    user_id: int
    email: str


@dataclass(frozen=True, kw_only=True)
class MovieCreated(DomainEvent):
    movie_id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int


@dataclass(frozen=True, kw_only=True)
class MovieUpdated(DomainEvent):
    movie_id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int


@dataclass(frozen=True, kw_only=True)
class MovieDeleted(DomainEvent):
    movie_id: int
    title: str


@dataclass(frozen=True, kw_only=True)
class ReportAdded(DomainEvent):
    report_id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int


@dataclass(frozen=True, kw_only=True)
class ReportCorrected(DomainEvent):
    report_id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int
    previous_revenue_usd: int
    previous_tickets_sold: int


@dataclass(frozen=True, kw_only=True)
class ReportDeleted(DomainEvent):
    report_id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int

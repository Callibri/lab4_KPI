import os
from typing import Iterator

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from boxoffice.application.commands.movies import CreateMovieHandler, DeleteMovieHandler, UpdateMovieHandler
from boxoffice.application.commands.reports import AddReportHandler, DeleteReportHandler, UpdateReportHandler
from boxoffice.application.commands.users import RegisterUserHandler
from boxoffice.application.queries.handlers import (
    GetMovieQueryHandler, GetMovieSummaryQueryHandler, GetRegionRevenueQueryHandler,
    GetTopMoviesQueryHandler, ListMoviesQueryHandler, ListReportsQueryHandler, LoginQueryHandler,
)
from boxoffice.application import events as ev
from boxoffice.application.registry import Handlers
from boxoffice.application.side_effects import SideEffects
from boxoffice.audit.contract import AuditService
from boxoffice.audit.service import SqlAuditService
from boxoffice.audit.storage import AuditBase
from boxoffice.infrastructure.audit_adapter import AuditEventSubscriber, SyncAuditAdapter
from boxoffice.infrastructure.event_bus import InProcessEventBus
from boxoffice.domain.factories import MovieFactory, ReportFactory, UserFactory
from boxoffice.infrastructure import orm_models
from boxoffice.infrastructure.db import Base, make_engine
from boxoffice.infrastructure.read_repositories import (
    SqlAnalyticsReadRepository, SqlCredentialsReadRepository, SqlMovieReadRepository,
    SqlReportReadRepository,
)
from boxoffice.infrastructure.repositories import (
    SqlAlchemyMovieRepository, SqlAlchemyReportRepository, SqlAlchemyUserRepository,
)
from boxoffice.infrastructure.security import JwtTokenService, Pbkdf2PasswordHasher
from boxoffice.presentation.api import create_app

DEFAULT_SECRET = "dev-secret-key-change-me-in-production-32b"


def build_handlers(session: Session, hasher, tokens, effects: SideEffects) -> Handlers:
    users = SqlAlchemyUserRepository(session)
    movies = SqlAlchemyMovieRepository(session)
    reports = SqlAlchemyReportRepository(session)
    movie_factory = MovieFactory(movies)
    movie_read = SqlMovieReadRepository(session)
    report_read = SqlReportReadRepository(session)
    analytics_read = SqlAnalyticsReadRepository(session)
    credentials_read = SqlCredentialsReadRepository(session)
    return Handlers(
        register_user=RegisterUserHandler(UserFactory(users, hasher), users, effects),
        create_movie=CreateMovieHandler(movie_factory, movies, effects),
        update_movie=UpdateMovieHandler(movie_factory, movies, effects),
        delete_movie=DeleteMovieHandler(movies, effects),
        add_report=AddReportHandler(movies, reports, ReportFactory(reports), effects),
        update_report=UpdateReportHandler(reports, effects),
        delete_report=DeleteReportHandler(reports, effects),
        login=LoginQueryHandler(credentials_read, hasher, tokens),
        list_movies=ListMoviesQueryHandler(movie_read),
        get_movie=GetMovieQueryHandler(movie_read),
        list_reports=ListReportsQueryHandler(report_read),
        movie_summary=GetMovieSummaryQueryHandler(analytics_read),
        top_movies=GetTopMoviesQueryHandler(analytics_read),
        region_revenue=GetRegionRevenueQueryHandler(analytics_read),
    )


def build_app(
    database_url: str | None = None,
    secret_key: str | None = None,
    mode: str | None = None,
    audit_service: AuditService | None = None,
    audit_delay_s: float | None = None,
) -> FastAPI:
    database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///./boxoffice.db")
    mode = mode or os.getenv("COMMUNICATION_MODE", "async")
    if mode not in ("sync", "async", "none"):
        raise ValueError("mode must be sync, async or none")
    if audit_delay_s is None:
        audit_delay_s = float(os.getenv("AUDIT_DELAY_MS", "0")) / 1000
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    AuditBase.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    hasher = Pbkdf2PasswordHasher()
    tokens = JwtTokenService(secret_key or os.getenv("SECRET_KEY", DEFAULT_SECRET))

    audit = audit_service or SqlAuditService(session_factory, delay_s=audit_delay_s)
    bus = InProcessEventBus()
    if mode == "sync":
        effects = SideEffects(audit=SyncAuditAdapter(audit))
    elif mode == "async":
        bus.subscribe(ev.DomainEvent, AuditEventSubscriber(audit))
        effects = SideEffects(publisher=bus)
    else:
        effects = SideEffects()

    def handlers_scope() -> Iterator[Handlers]:
        with session_factory() as session:
            yield build_handlers(session, hasher, tokens, effects)

    app = create_app(handlers_scope, tokens)
    app.state.session_factory = session_factory
    app.state.audit_service = audit
    app.state.bus = bus
    return app

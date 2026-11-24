from dataclasses import dataclass
from datetime import date

from boxoffice.application.ports import TokenService
from boxoffice.application.queries.ports import (
    AnalyticsReadRepository, CredentialsReadRepository, MovieReadRepository, ReportReadRepository,
)
from boxoffice.application.queries.read_models import (
    MovieDetails, MovieListItem, MovieSummary, RegionRevenueItem, ReportItem, TopMovieItem,
)
from boxoffice.domain.errors import AuthenticationError, NotFoundError
from boxoffice.domain.ports import PasswordHasher


@dataclass(frozen=True)
class LoginQuery:
    email: str
    password: str


@dataclass(frozen=True)
class ListMoviesQuery:
    genre: str | None = None
    year: int | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class GetMovieQuery:
    movie_id: int


@dataclass(frozen=True)
class ListReportsQuery:
    movie_id: int
    date_from: date | None = None
    date_to: date | None = None
    region: str | None = None


@dataclass(frozen=True)
class GetMovieSummaryQuery:
    movie_id: int


@dataclass(frozen=True)
class GetTopMoviesQuery:
    limit: int = 10


@dataclass(frozen=True)
class GetRegionRevenueQuery:
    pass


class LoginQueryHandler:

    def __init__(self, credentials: CredentialsReadRepository, hasher: PasswordHasher, tokens: TokenService):
        self._credentials, self._hasher, self._tokens = credentials, hasher, tokens

    def handle(self, query: LoginQuery) -> str:
        found = self._credentials.get_credentials(query.email.strip().lower())
        if found is None or not self._hasher.verify(query.password, found.password_hash):
            raise AuthenticationError("Invalid email or password")
        return self._tokens.issue(found.user_id)


class ListMoviesQueryHandler:
    def __init__(self, movies: MovieReadRepository):
        self._movies = movies

    def handle(self, q: ListMoviesQuery) -> list[MovieListItem]:
        return self._movies.list_movies(q.genre, q.year, q.limit, q.offset)


class GetMovieQueryHandler:
    def __init__(self, movies: MovieReadRepository):
        self._movies = movies

    def handle(self, q: GetMovieQuery) -> MovieDetails:
        details = self._movies.get_details(q.movie_id)
        if details is None:
            raise NotFoundError("Movie not found")
        return details


class ListReportsQueryHandler:
    def __init__(self, reports: ReportReadRepository):
        self._reports = reports

    def handle(self, q: ListReportsQuery) -> list[ReportItem]:
        items = self._reports.list_for_movie(q.movie_id, q.date_from, q.date_to, q.region)
        if items is None:
            raise NotFoundError("Movie not found")
        return items


class GetMovieSummaryQueryHandler:
    def __init__(self, analytics: AnalyticsReadRepository):
        self._analytics = analytics

    def handle(self, q: GetMovieSummaryQuery) -> MovieSummary:
        summary = self._analytics.movie_summary(q.movie_id)
        if summary is None:
            raise NotFoundError("Movie not found")
        return summary


class GetTopMoviesQueryHandler:
    def __init__(self, analytics: AnalyticsReadRepository):
        self._analytics = analytics

    def handle(self, q: GetTopMoviesQuery) -> list[TopMovieItem]:
        return self._analytics.top_movies(q.limit)


class GetRegionRevenueQueryHandler:
    def __init__(self, analytics: AnalyticsReadRepository):
        self._analytics = analytics

    def handle(self, q: GetRegionRevenueQuery) -> list[RegionRevenueItem]:
        return self._analytics.revenue_by_region()

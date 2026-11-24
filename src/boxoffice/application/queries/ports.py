from abc import ABC, abstractmethod
from datetime import date

from boxoffice.application.queries.read_models import (
    MovieDetails, MovieListItem, MovieSummary, RegionRevenueItem, ReportItem, TopMovieItem,
    UserCredentials,
)


class MovieReadRepository(ABC):
    @abstractmethod
    def list_movies(
        self, genre: str | None, year: int | None, limit: int, offset: int
    ) -> list[MovieListItem]: ...

    @abstractmethod
    def get_details(self, movie_id: int) -> MovieDetails | None: ...


class ReportReadRepository(ABC):
    @abstractmethod
    def list_for_movie(
        self, movie_id: int, date_from: date | None, date_to: date | None, region: str | None
    ) -> list[ReportItem] | None:
        pass


class AnalyticsReadRepository(ABC):
    @abstractmethod
    def movie_summary(self, movie_id: int) -> MovieSummary | None: ...

    @abstractmethod
    def top_movies(self, limit: int) -> list[TopMovieItem]: ...

    @abstractmethod
    def revenue_by_region(self) -> list[RegionRevenueItem]: ...


class CredentialsReadRepository(ABC):
    @abstractmethod
    def get_credentials(self, email: str) -> UserCredentials | None: ...

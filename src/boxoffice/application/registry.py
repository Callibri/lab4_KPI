from dataclasses import dataclass

from boxoffice.application.commands.movies import CreateMovieHandler, DeleteMovieHandler, UpdateMovieHandler
from boxoffice.application.commands.reports import AddReportHandler, DeleteReportHandler, UpdateReportHandler
from boxoffice.application.commands.users import RegisterUserHandler
from boxoffice.application.queries.handlers import (
    GetMovieQueryHandler, GetMovieSummaryQueryHandler, GetRegionRevenueQueryHandler,
    GetTopMoviesQueryHandler, ListMoviesQueryHandler, ListReportsQueryHandler, LoginQueryHandler,
)


@dataclass
class Handlers:
    register_user: RegisterUserHandler
    create_movie: CreateMovieHandler
    update_movie: UpdateMovieHandler
    delete_movie: DeleteMovieHandler
    add_report: AddReportHandler
    update_report: UpdateReportHandler
    delete_report: DeleteReportHandler
    login: LoginQueryHandler
    list_movies: ListMoviesQueryHandler
    get_movie: GetMovieQueryHandler
    list_reports: ListReportsQueryHandler
    movie_summary: GetMovieSummaryQueryHandler
    top_movies: GetTopMoviesQueryHandler
    region_revenue: GetRegionRevenueQueryHandler

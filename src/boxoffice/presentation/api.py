from typing import Callable, Iterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from boxoffice.application.ports import TokenService
from boxoffice.application.registry import Handlers
from boxoffice.domain.errors import (
    AuthenticationError, ConflictError, DomainError, DomainValidationError, NotFoundError,
)
from boxoffice.presentation.routers import (
    analytics_router, audit_router, auth_router, movies_router, reports_router,
)

ERROR_STATUS = {
    DomainValidationError: 400,
    AuthenticationError: 401,
    NotFoundError: 404,
    ConflictError: 409,
}


def create_app(handlers_scope: Callable[[], Iterator[Handlers]], tokens: TokenService) -> FastAPI:
    app = FastAPI(title="Box Office Analytics (Lab 4: Sync/Async communication)")
    app.state.handlers_scope = handlers_scope
    app.state.tokens = tokens
    for router in (auth_router, movies_router, reports_router, analytics_router, audit_router):
        app.include_router(router)

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError):
        status = next((code for cls, code in ERROR_STATUS.items() if isinstance(exc, cls)), 500)
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        return JSONResponse(status_code=status, content={"detail": str(exc)}, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError):
        errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=400, content={"detail": errors})

    return app

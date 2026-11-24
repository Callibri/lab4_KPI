from typing import Iterator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from boxoffice.application.registry import Handlers
from boxoffice.domain.errors import AuthenticationError

bearer_scheme = HTTPBearer(auto_error=False)


def get_handlers(request: Request) -> Iterator[Handlers]:
    yield from request.app.state.handlers_scope()


def require_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    return request.app.state.tokens.verify(credentials.credentials)

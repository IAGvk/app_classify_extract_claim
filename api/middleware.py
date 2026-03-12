"""Request ID middleware — injects a unique X-Request-ID into every request/response."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import Request, Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject ``X-Request-ID`` if the client did not supply one.

    The ID is propagated in the response so callers can correlate logs.
    """

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

"""GET /health — liveness and readiness probe."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])

_APP_VERSION = "1.2.0"


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return ``{"status": "ok"}`` if the API process is running.

    Used by Docker ``HEALTHCHECK``, load-balancer probes, and the
    Streamlit sidebar connectivity check.
    """
    return HealthResponse(status="ok", version=_APP_VERSION)

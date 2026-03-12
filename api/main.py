"""FastAPI application — entry point for the Claims Processor API.

Start with::

    uvicorn app_classify_extract_claim.api.main:app --reload --port 8000

Or via Docker Compose (see ``docker/docker-compose.yml``).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_classify_extract_claim.api.middleware import RequestIdMiddleware
from app_classify_extract_claim.api.routes import health, process_email
from app_classify_extract_claim.config.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

_APP_VERSION = "1.2.0"


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start the Kafka consumer on startup; stop it cleanly on shutdown."""
    settings = get_settings()
    consumer_thread = None

    if settings.kafka_consumer_enabled:
        from app_classify_extract_claim.services.kafka_consumer import (
            start_consumer,
            stop_consumer,
        )

        consumer_thread = start_consumer(settings)
        logger.info(
            "Kafka consumer started (daemon=%s thread=%s)",
            consumer_thread.daemon,
            consumer_thread.name,
        )
    else:
        logger.info("Kafka consumer disabled (KAFKA_CONSUMER_ENABLED=false)")

    yield  # ← application runs here

    if consumer_thread is not None:
        from app_classify_extract_claim.services.kafka_consumer import stop_consumer

        stop_consumer()
        consumer_thread.join(timeout=10)
        logger.info("Kafka consumer stopped")


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="Claims Processor API",
        description=(
            "Agentic AI pipeline for end-to-end insurance claims "
            "classification, extraction and lodgement."
        ),
        version=_APP_VERSION,
        lifespan=lifespan,
    )

    # CORS — allow all origins for local dev; tighten to specific origins in v2.0
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health.router)
    app.include_router(process_email.router)

    return app


# Module-level singleton used by uvicorn
app = create_app()

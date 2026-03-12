"""Shared fixtures for FastAPI endpoint tests."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

import app_classify_extract_claim.config.settings as _settings_mod


@pytest.fixture(autouse=True)
def _api_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable the Kafka consumer for every test in this package."""
    monkeypatch.setenv("KAFKA_CONSUMER_ENABLED", "false")
    monkeypatch.setenv("MOCK_LLM", "true")
    # Reset the settings singleton so the monkeypatched env is picked up
    monkeypatch.setattr(_settings_mod, "_settings", None)


@pytest.fixture
async def async_client(_api_test_env: None) -> AsyncClient:
    """Return an httpx AsyncClient wired to the FastAPI test app.

    Creates a fresh app instance (with KAFKA_CONSUMER_ENABLED=false) so the
    lifespan does not attempt to connect to Redpanda.
    """
    from app_classify_extract_claim.api.main import create_app

    test_app = create_app()
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client

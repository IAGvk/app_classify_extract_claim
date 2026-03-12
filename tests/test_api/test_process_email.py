"""Tests for POST /process-email."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

import app_classify_extract_claim.api.routes.process_email as _route_mod

# Minimal RFC-5322 email bytes used as an upload fixture
_MINIMAL_EML = (
    b"From: test@example.com\r\n"
    b"To: claims@gio.com.au\r\n"
    b"Subject: Test motor claim\r\n"
    b"MIME-Version: 1.0\r\n"
    b"Content-Type: text/plain\r\n"
    b"\r\n"
    b"My car was hit. Policy ABC123.\r\n"
)

_SUCCESS_RESULT: dict[str, Any] = {
    "lodge_status": "SUCCESS",
    "claim_reference": "GIO-TESTAPI1",
    "insurance_type": "motor",
    "vulnerability_flag": False,
    "error_reason": None,
}


@pytest.fixture
def mock_pipeline(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace parse_input and get_graph in the route module with fast mocks."""
    # Mock parse_input so no real file parsing happens
    monkeypatch.setattr(
        _route_mod,
        "parse_input",
        lambda _path: {"body": "My car was hit. Policy ABC123.", "attachments": []},
    )

    # Mock get_graph to return a graph whose ainvoke returns a canned result
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_SUCCESS_RESULT)
    monkeypatch.setattr(_route_mod, "get_graph", lambda: mock_graph)
    return mock_graph


async def test_process_email_success(
    async_client: AsyncClient,
    mock_pipeline: MagicMock,
) -> None:
    """Happy path — valid .eml upload should return 200 with lodge_status SUCCESS."""
    response = await async_client.post(
        "/process-email",
        files={"email_file": ("motor.eml", _MINIMAL_EML, "message/rfc822")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["lodge_status"] == "SUCCESS"
    assert body["claim_reference"] == "GIO-TESTAPI1"
    assert body["insurance_type"] == "motor"
    assert body["vulnerability_flag"] is False


async def test_process_email_returns_email_id(
    async_client: AsyncClient,
    mock_pipeline: MagicMock,
) -> None:
    """Response must contain a non-empty email_id UUID."""
    response = await async_client.post(
        "/process-email",
        files={"email_file": ("motor.eml", _MINIMAL_EML, "message/rfc822")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("email_id"), "Expected a non-empty email_id in response"


async def test_process_email_pipeline_called_once(
    async_client: AsyncClient,
    mock_pipeline: MagicMock,
) -> None:
    """get_graph().ainvoke must be called exactly once per request."""
    await async_client.post(
        "/process-email",
        files={"email_file": ("motor.eml", _MINIMAL_EML, "message/rfc822")},
    )
    mock_pipeline.ainvoke.assert_called_once()


async def test_process_email_missing_file_returns_422(
    async_client: AsyncClient,
) -> None:
    """Submitting with no file should return HTTP 422 Unprocessable Entity."""
    response = await async_client.post("/process-email")
    assert response.status_code == 422


async def test_process_email_oversized_file_returns_413(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Files exceeding max_email_size_mb must return HTTP 413."""
    import app_classify_extract_claim.config.settings as _settings_mod
    from app_classify_extract_claim.config.settings import Settings

    # Override the size limit to 0 so any file triggers the check
    tiny_settings = Settings(
        GCP_PROJECT_ID="test",
        KAFKA_CONSUMER_ENABLED=False,
        MAX_EMAIL_SIZE_MB=0,
    )  # type: ignore[call-arg]
    monkeypatch.setattr(_settings_mod, "_settings", tiny_settings)

    response = await async_client.post(
        "/process-email",
        files={"email_file": ("big.eml", _MINIMAL_EML, "message/rfc822")},
    )
    assert response.status_code == 413

"""Tests for classify_email node."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app_classify_extract_claim.graph.nodes.classify_email import classify_email
from app_classify_extract_claim.schemas.claim_data import EmailTypeResponse


@pytest.mark.asyncio
async def test_webform_detected_by_heuristics(webform_state, mock_settings):
    with patch("app_classify_extract_claim.graph.nodes.classify_email.get_settings", return_value=mock_settings):
        result = await classify_email(webform_state)

    assert result["email_type"] == "webform"


@pytest.mark.asyncio
async def test_freetext_email_classified_by_llm(motor_state, mock_settings):
    mock_client = AsyncMock()
    mock_client.ainvoke_structured = AsyncMock(return_value=EmailTypeResponse(email_type="freetext"))

    with (
        patch("app_classify_extract_claim.graph.nodes.classify_email.get_settings", return_value=mock_settings),
        patch("app_classify_extract_claim.graph.nodes.classify_email.llm_module.LLMClient.from_settings", return_value=mock_client),
    ):
        result = await classify_email(motor_state)

    assert result["email_type"] == "freetext"


@pytest.mark.asyncio
async def test_falls_back_to_freetext_on_error(motor_state, mock_settings):
    mock_client = AsyncMock()
    mock_client.ainvoke_structured = AsyncMock(side_effect=RuntimeError("LLM down"))

    with (
        patch("app_classify_extract_claim.graph.nodes.classify_email.get_settings", return_value=mock_settings),
        patch("app_classify_extract_claim.graph.nodes.classify_email.llm_module.LLMClient.from_settings", return_value=mock_client),
    ):
        result = await classify_email(motor_state)

    assert result["email_type"] == "freetext"


@pytest.mark.asyncio
async def test_another_webform_signal(mock_settings):
    from app_classify_extract_claim.graph.state import initial_state

    body = "A new claim submission has been received\nReference ID: SUB-001\nPolicy Number: GIO123\nDate of Loss: 2025-01-15"
    state = initial_state("wf-test", body, [])

    with patch("app_classify_extract_claim.graph.nodes.classify_email.get_settings", return_value=mock_settings):
        result = await classify_email(state)

    assert result["email_type"] == "webform"

"""Tests for classify node."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app_classify_extract_claim.graph.nodes.classify import classify
from app_classify_extract_claim.schemas.claim_data import (
    ClaimContext,
    ClaimsGroupingResponse,
    ClaimStatusResponse,
    InsuranceTypeResponse,
)


def _make_client(insurance="motor", status="new_claim", claims=None):
    if claims is None:
        claims = [
            ClaimContext(
                description="Motor vehicle accident",
                risk="ABC123",
                unique_email_info="Accident on Main St",
                attachments=[],
            )
        ]
    mock = AsyncMock()

    async def side_effect(schema, *args, **kwargs):
        if schema is InsuranceTypeResponse:
            return InsuranceTypeResponse(insurance_type=insurance)
        if schema is ClaimStatusResponse:
            return ClaimStatusResponse(claim_type=status)
        if schema is ClaimsGroupingResponse:
            return ClaimsGroupingResponse(claims=claims)
        return schema.model_validate({})

    mock.ainvoke_structured = AsyncMock(side_effect=side_effect)
    return mock


@pytest.mark.asyncio
async def test_motor_new_claim(motor_state, mock_settings):
    mock_client = _make_client(insurance="motor", status="new_claim")

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.classify.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.classify.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await classify(motor_state)

    assert result["insurance_type"] == "motor"
    assert result["claim_status"] == "new_claim"
    assert len(result["claims"]) >= 1


@pytest.mark.asyncio
async def test_non_motor_new_claim(non_motor_state, mock_settings):
    mock_client = _make_client(insurance="non-motor", status="new_claim", claims=[])

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.classify.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.classify.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await classify(non_motor_state)

    assert result["insurance_type"] == "non-motor"
    assert result["claim_status"] == "new_claim"


@pytest.mark.asyncio
async def test_existing_claim_detected(existing_claim_state, mock_settings):
    mock_client = _make_client(insurance="motor", status="existing_claim", claims=[])

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.classify.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.classify.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await classify(existing_claim_state)

    assert result["claim_status"] == "existing_claim"


@pytest.mark.asyncio
async def test_classify_survives_error(motor_state, mock_settings):
    mock_client = AsyncMock()
    mock_client.ainvoke_structured = AsyncMock(side_effect=RuntimeError("API error"))

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.classify.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.classify.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await classify(motor_state)

    assert "insurance_type" in result
    assert "error_node" in result

"""Tests for extract_data node."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app_classify_extract_claim.graph.nodes.extract_data import extract_data
from app_classify_extract_claim.schemas.claim_data import ExtractedClaim


def _make_extract_client(claim_dict: dict):
    mock = AsyncMock()
    mock.ainvoke_structured = AsyncMock(return_value=ExtractedClaim.model_validate(claim_dict))
    return mock


@pytest.mark.asyncio
async def test_freetext_extraction(motor_state, extracted_motor_claim, mock_settings):
    motor_state["email_type"] = "freetext"
    mock_client = _make_extract_client(extracted_motor_claim)

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await extract_data(motor_state)

    assert result["extracted_claim"] is not None
    assert result["extracted_claim"]["insured_details"]["policy_number"] == "GIO1234567"
    assert result["extracted_claim"]["vehicle_information"]["vehicle_registration"] == "ABC123"


@pytest.mark.asyncio
async def test_webform_extraction(webform_state, extracted_motor_claim, mock_settings):
    webform_state["email_type"] = "webform"
    mock_client = _make_extract_client(extracted_motor_claim)

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await extract_data(webform_state)

    assert result["extracted_claim"] is not None
    # Webform path calls ainvoke_structured once (single pass)
    assert mock_client.ainvoke_structured.call_count == 1


@pytest.mark.asyncio
async def test_two_stage_form_extraction(extracted_motor_claim, mock_settings):
    """When raw_files contains a PDF, 2-stage extraction should be used."""
    from app_classify_extract_claim.graph.state import initial_state

    pdf_file = {
        "filename": "claim_form.pdf",
        "mime_type": "application/pdf",
        "text_content": "MOTOR CLAIM FORM...",
        "base64_content": None,
        "raw_bytes": b"",
    }
    state = initial_state("test-form", "Please find attached claim form.", [pdf_file])
    state["email_type"] = "freetext"

    mock_client = _make_extract_client(extracted_motor_claim)
    # Stage 2 also returns same
    mock_client.ainvoke_structured = AsyncMock(
        return_value=ExtractedClaim.model_validate(extracted_motor_claim)
    )

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await extract_data(state)

    assert result["extracted_claim"] is not None
    # 2-stage: called twice (stage1 + stage2)
    assert mock_client.ainvoke_structured.call_count == 2


@pytest.mark.asyncio
async def test_extract_data_returns_none_on_error(motor_state, mock_settings):
    mock_client = AsyncMock()
    mock_client.ainvoke_structured = AsyncMock(side_effect=Exception("LLM error"))

    with (
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "app_classify_extract_claim.graph.nodes.extract_data.llm_module.LLMClient.from_settings",
            return_value=mock_client,
        ),
    ):
        result = await extract_data(motor_state)

    assert result["extracted_claim"] is None
    assert "error_node" in result

"""Tests for policy_retrieval node."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app_classify_extract_claim.graph.nodes.policy_retrieval import policy_retrieval


@pytest.mark.asyncio
async def test_policy_found_by_exact_number(motor_state, extracted_motor_claim, mock_settings):
    motor_state["extracted_claim"] = extracted_motor_claim  # policy_number = GIO1234567

    with patch("app_classify_extract_claim.graph.nodes.policy_retrieval.get_settings", return_value=mock_settings):
        result = await policy_retrieval(motor_state)

    assert result["policy_found"] is True
    assert result["policy"] is not None
    assert result["policy"]["policy_number"] == "GIO1234567"


@pytest.mark.asyncio
async def test_policy_found_by_name_fuzzy(motor_state, extracted_motor_claim, mock_settings):
    extracted_motor_claim["insured_details"]["policy_number"] = None
    extracted_motor_claim["insured_details"]["insured_name"] = "John Smith"
    motor_state["extracted_claim"] = extracted_motor_claim

    with patch("app_classify_extract_claim.graph.nodes.policy_retrieval.get_settings", return_value=mock_settings):
        result = await policy_retrieval(motor_state)

    assert result["policy_found"] is True
    assert result["policy"]["holder"]["name"] == "John Smith"


@pytest.mark.asyncio
async def test_policy_not_found(motor_state, extracted_motor_claim, mock_settings):
    extracted_motor_claim["insured_details"]["policy_number"] = "UNKNOWN99999"
    extracted_motor_claim["insured_details"]["insured_name"] = "Nobody Nowhere"
    motor_state["extracted_claim"] = extracted_motor_claim

    with patch("app_classify_extract_claim.graph.nodes.policy_retrieval.get_settings", return_value=mock_settings):
        result = await policy_retrieval(motor_state)

    assert result["policy_found"] is False
    assert result["policy"] is None


@pytest.mark.asyncio
async def test_policy_retrieval_no_extracted_claim(motor_state, mock_settings):
    motor_state["extracted_claim"] = None

    with patch("app_classify_extract_claim.graph.nodes.policy_retrieval.get_settings", return_value=mock_settings):
        result = await policy_retrieval(motor_state)

    assert result["policy_found"] is False


@pytest.mark.asyncio
async def test_policy_number_normalised(motor_state, extracted_motor_claim, mock_settings):
    """Policy number with dashes should still match."""
    extracted_motor_claim["insured_details"]["policy_number"] = "GIO-1234567"
    motor_state["extracted_claim"] = extracted_motor_claim

    with patch("app_classify_extract_claim.graph.nodes.policy_retrieval.get_settings", return_value=mock_settings):
        result = await policy_retrieval(motor_state)

    # normalise() strips dashes — should still match GIO1234567
    assert result["policy_found"] is True

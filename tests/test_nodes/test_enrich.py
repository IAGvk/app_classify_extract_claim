"""Tests for enrich node."""

from __future__ import annotations

import pytest

from app_classify_extract_claim.graph.nodes.enrich import enrich

MOCK_POLICY = {
    "policy_number": "GIO1234567",
    "policy_type": "motor",
    "status": "active",
    "holder": {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "0412345678",
        "address": "12 Elm St",
    },
    "vehicle": {
        "registration": "ABC123",
        "make": "Toyota",
        "model": "Camry",
        "year": 2021,
        "colour": "White",
    },
}


@pytest.mark.asyncio
async def test_enrich_fills_missing_policy_number(motor_state, extracted_motor_claim):
    """Policy number from policy store fills null in extracted claim."""
    extracted_motor_claim["insured_details"]["policy_number"] = None
    motor_state["extracted_claim"] = extracted_motor_claim
    motor_state["policy"] = MOCK_POLICY

    result = await enrich(motor_state)

    assert result["enriched_claim"]["insured_details"]["policy_number"] == "GIO1234567"


@pytest.mark.asyncio
async def test_enrich_fills_vehicle_details(motor_state, extracted_motor_claim):
    """Vehicle details from policy fill null extraction fields."""
    extracted_motor_claim["vehicle_information"]["vehicle_make"] = None
    extracted_motor_claim["vehicle_information"]["vehicle_model"] = None
    motor_state["extracted_claim"] = extracted_motor_claim
    motor_state["policy"] = MOCK_POLICY

    result = await enrich(motor_state)

    assert result["enriched_claim"]["vehicle_information"]["vehicle_make"] == "Toyota"
    assert result["enriched_claim"]["vehicle_information"]["vehicle_model"] == "Camry"


@pytest.mark.asyncio
async def test_enrich_does_not_overwrite_existing_values(motor_state, extracted_motor_claim):
    """Existing non-null values in extracted claim should not be overwritten."""
    extracted_motor_claim["insured_details"]["policy_number"] = "GIO9999999"
    motor_state["extracted_claim"] = extracted_motor_claim
    motor_state["policy"] = MOCK_POLICY  # has GIO1234567

    result = await enrich(motor_state)

    # extracted value should be preserved
    assert result["enriched_claim"]["insured_details"]["policy_number"] == "GIO9999999"


@pytest.mark.asyncio
async def test_enrich_no_policy(motor_state, extracted_motor_claim):
    """With no policy, enriched_claim equals extracted_claim."""
    motor_state["extracted_claim"] = extracted_motor_claim
    motor_state["policy"] = None

    result = await enrich(motor_state)

    assert result["enriched_claim"]["insured_details"]["policy_number"] == "GIO1234567"


@pytest.mark.asyncio
async def test_enrich_no_extracted_claim(motor_state):
    motor_state["extracted_claim"] = None
    motor_state["policy"] = MOCK_POLICY

    result = await enrich(motor_state)

    # Should not crash
    assert "enriched_claim" in result

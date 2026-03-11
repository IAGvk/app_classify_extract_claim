"""Tests for check_fields node."""

from __future__ import annotations

import pytest

from app_classify_extract_claim.graph.nodes.check_fields import check_fields


def _make_state_with_enriched(extracted_motor_claim, insurance_type="motor"):
    from app_classify_extract_claim.graph.state import initial_state

    state = initial_state("test", "body", [])
    state["enriched_claim"] = extracted_motor_claim
    state["insurance_type"] = insurance_type
    return state


@pytest.mark.asyncio
async def test_motor_claim_complete(extracted_motor_claim):
    state = _make_state_with_enriched(extracted_motor_claim, "motor")

    result = await check_fields(state)

    assert result["fields_complete"] is True
    assert result["missing_fields"] == []


@pytest.mark.asyncio
async def test_motor_claim_missing_registration(extracted_motor_claim):
    extracted_motor_claim["vehicle_information"]["vehicle_registration"] = None
    state = _make_state_with_enriched(extracted_motor_claim, "motor")

    result = await check_fields(state)

    assert result["fields_complete"] is False
    assert "vehicle_information.vehicle_registration" in result["missing_fields"]


@pytest.mark.asyncio
async def test_motor_claim_missing_driver_name(extracted_motor_claim):
    extracted_motor_claim["drivers_details"]["driver_name"] = None
    state = _make_state_with_enriched(extracted_motor_claim, "motor")

    result = await check_fields(state)

    assert result["fields_complete"] is False
    assert "drivers_details.driver_name" in result["missing_fields"]


@pytest.mark.asyncio
async def test_motor_claim_missing_date_of_loss(extracted_motor_claim):
    extracted_motor_claim["incident_details"]["date_of_loss"] = None
    state = _make_state_with_enriched(extracted_motor_claim, "motor")

    result = await check_fields(state)

    assert result["fields_complete"] is False
    assert "incident_details.date_of_loss" in result["missing_fields"]


@pytest.mark.asyncio
async def test_non_motor_claim_complete():
    from app_classify_extract_claim.graph.state import initial_state

    state = initial_state("test-nm", "body", [])
    state["insurance_type"] = "non-motor"
    state["enriched_claim"] = {
        "insured_details": {"insured_name": "Acme Pty Ltd", "policy_number": "AMI5550001"},
        "incident_details": {
            "date_of_loss": "2025-02-20",
            "incident_description": "Storm damage to property roof",
        },
    }

    result = await check_fields(state)

    assert result["fields_complete"] is True


@pytest.mark.asyncio
async def test_non_motor_missing_insured_name():
    from app_classify_extract_claim.graph.state import initial_state

    state = initial_state("test-nm-missing", "body", [])
    state["insurance_type"] = "non-motor"
    state["enriched_claim"] = {
        "insured_details": {"insured_name": None, "policy_number": "AMI5550001"},
        "incident_details": {
            "date_of_loss": "2025-02-20",
            "incident_description": "Storm damage",
        },
    }

    result = await check_fields(state)

    assert result["fields_complete"] is False
    assert "insured_details.insured_name" in result["missing_fields"]

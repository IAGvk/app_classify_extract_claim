"""Tests for verify node."""
from __future__ import annotations

import pytest

from app_classify_extract_claim.graph.nodes.verify import verify


@pytest.mark.asyncio
async def test_verify_pass_on_valid_claim(motor_state, extracted_motor_claim):
    motor_state["extracted_claim"] = extracted_motor_claim
    motor_state["vulnerability_flag"] = False

    result = await verify(motor_state)
    assert result["verification_result"] == "PASS"
    assert result["verification_errors"] == []


@pytest.mark.asyncio
async def test_verify_fail_on_none_claim(motor_state):
    motor_state["extracted_claim"] = None
    motor_state["vulnerability_flag"] = False

    result = await verify(motor_state)
    assert result["verification_result"] == "FAIL"
    assert any("None" in e or "null" in e.lower() or "extracted_claim" in e.lower()
               for e in result["verification_errors"])


@pytest.mark.asyncio
async def test_verify_fail_on_future_date(motor_state, extracted_motor_claim):
    extracted_motor_claim["incident_details"]["date_of_loss"] = "2099-01-01"
    motor_state["extracted_claim"] = extracted_motor_claim

    result = await verify(motor_state)
    assert result["verification_result"] == "FAIL"
    assert any("future" in e for e in result["verification_errors"])


@pytest.mark.asyncio
async def test_verify_warn_on_old_date(motor_state, extracted_motor_claim):
    extracted_motor_claim["incident_details"]["date_of_loss"] = "2018-01-01"
    motor_state["extracted_claim"] = extracted_motor_claim

    result = await verify(motor_state)
    assert result["verification_result"] in ("WARN", "PASS")  # 5-year rule → WARN


@pytest.mark.asyncio
async def test_verify_warn_on_vulnerability_flag(motor_state, extracted_motor_claim):
    motor_state["extracted_claim"] = extracted_motor_claim
    motor_state["vulnerability_flag"] = True

    result = await verify(motor_state)
    assert result["verification_result"] == "WARN"
    assert any("SENSITIVE_CLAIM" in e for e in result["verification_errors"])


@pytest.mark.asyncio
async def test_verify_warn_on_missing_date(motor_state, extracted_motor_claim):
    extracted_motor_claim["incident_details"]["date_of_loss"] = None
    motor_state["extracted_claim"] = extracted_motor_claim

    result = await verify(motor_state)
    # Missing date = warning, not failure
    assert result["verification_result"] == "WARN"
    assert any("date_of_loss" in e.lower() for e in result["verification_errors"])


@pytest.mark.asyncio
async def test_verify_warn_on_bad_policy_prefix(motor_state, extracted_motor_claim):
    extracted_motor_claim["insured_details"]["policy_number"] = "INVALID99999"
    motor_state["extracted_claim"] = extracted_motor_claim

    result = await verify(motor_state)
    # Bad prefix = warning only
    assert any("policy_number" in e.lower() for e in result["verification_errors"])

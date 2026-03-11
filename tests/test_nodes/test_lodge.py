"""Tests for lodge node."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app_classify_extract_claim.graph.nodes.lodge import lodge


@pytest.mark.asyncio
async def test_lodge_success_creates_reference(
    motor_state, extracted_motor_claim, mock_settings, tmp_path
):
    mock_settings.lodged_claims_path = tmp_path / "lodged.jsonl"
    motor_state["enriched_claim"] = extracted_motor_claim
    motor_state["insurance_type"] = "motor"
    motor_state["vulnerability_flag"] = False

    with patch(
        "app_classify_extract_claim.graph.nodes.lodge.get_settings", return_value=mock_settings
    ):
        result = await lodge(motor_state)

    assert result["lodge_status"] == "SUCCESS"
    assert result["claim_reference"] is not None
    assert result["claim_reference"].startswith("GIO-")


@pytest.mark.asyncio
async def test_lodge_writes_to_jsonl(motor_state, extracted_motor_claim, mock_settings, tmp_path):
    lodged_path = tmp_path / "lodged.jsonl"
    mock_settings.lodged_claims_path = lodged_path
    motor_state["enriched_claim"] = extracted_motor_claim
    motor_state["insurance_type"] = "motor"
    motor_state["vulnerability_flag"] = False

    with patch(
        "app_classify_extract_claim.graph.nodes.lodge.get_settings", return_value=mock_settings
    ):
        result = await lodge(motor_state)

    assert lodged_path.exists()
    records = [json.loads(line) for line in lodged_path.read_text().splitlines()]
    assert len(records) == 1
    assert records[0]["claim_reference"] == result["claim_reference"]


@pytest.mark.asyncio
async def test_lodge_sets_high_priority_for_vulnerable(
    motor_state, extracted_motor_claim, mock_settings, tmp_path
):
    mock_settings.lodged_claims_path = tmp_path / "lodged.jsonl"
    motor_state["enriched_claim"] = extracted_motor_claim
    motor_state["insurance_type"] = "motor"
    motor_state["vulnerability_flag"] = True

    with patch(
        "app_classify_extract_claim.graph.nodes.lodge.get_settings", return_value=mock_settings
    ):
        await lodge(motor_state)

    records = [json.loads(line) for line in (tmp_path / "lodged.jsonl").read_text().splitlines()]
    assert records[0]["priority"] == "HIGH"
    assert records[0]["handler"] == "sensitive_claims_team"


@pytest.mark.asyncio
async def test_lodge_normal_priority_for_non_vulnerable(
    motor_state, extracted_motor_claim, mock_settings, tmp_path
):
    mock_settings.lodged_claims_path = tmp_path / "lodged.jsonl"
    motor_state["enriched_claim"] = extracted_motor_claim
    motor_state["vulnerability_flag"] = False

    with patch(
        "app_classify_extract_claim.graph.nodes.lodge.get_settings", return_value=mock_settings
    ):
        await lodge(motor_state)

    records = [json.loads(line) for line in (tmp_path / "lodged.jsonl").read_text().splitlines()]
    assert records[0]["priority"] == "NORMAL"
    assert records[0]["handler"] == "standard_queue"


@pytest.mark.asyncio
async def test_lodge_multiple_calls_append_jsonl(
    motor_state, extracted_motor_claim, mock_settings, tmp_path
):
    lodged_path = tmp_path / "lodged.jsonl"
    mock_settings.lodged_claims_path = lodged_path
    motor_state["enriched_claim"] = extracted_motor_claim

    with patch(
        "app_classify_extract_claim.graph.nodes.lodge.get_settings", return_value=mock_settings
    ):
        await lodge(motor_state)
        await lodge(motor_state)

    lines = lodged_path.read_text().splitlines()
    assert len(lines) == 2

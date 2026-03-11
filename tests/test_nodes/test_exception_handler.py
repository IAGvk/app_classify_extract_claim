"""Tests for exception_handler node."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app_classify_extract_claim.graph.nodes.exception_handler import exception_handler


@pytest.mark.asyncio
async def test_exception_handler_writes_to_jsonl(motor_state, mock_settings, tmp_path):
    exc_path = tmp_path / "exceptions.jsonl"
    mock_settings.exceptions_path = exc_path
    motor_state["error_reason"] = "test error"
    motor_state["error_node"] = "classify"

    with patch(
        "app_classify_extract_claim.graph.nodes.exception_handler.get_settings",
        return_value=mock_settings,
    ):
        await exception_handler(motor_state)

    assert exc_path.exists()
    records = [json.loads(line) for line in exc_path.read_text().splitlines()]
    assert len(records) == 1


@pytest.mark.asyncio
async def test_exception_handler_captures_error_reason(motor_state, mock_settings, tmp_path):
    exc_path = tmp_path / "exceptions.jsonl"
    mock_settings.exceptions_path = exc_path
    motor_state["error_reason"] = "field validation failed"
    motor_state["error_node"] = "verify"

    with patch(
        "app_classify_extract_claim.graph.nodes.exception_handler.get_settings",
        return_value=mock_settings,
    ):
        await exception_handler(motor_state)

    records = [json.loads(line) for line in exc_path.read_text().splitlines()]
    assert records[0]["error_reason"] == "field validation failed"
    assert records[0]["error_node"] == "verify"


@pytest.mark.asyncio
async def test_exception_handler_existing_claim_reason(motor_state, mock_settings, tmp_path):
    exc_path = tmp_path / "exceptions.jsonl"
    mock_settings.exceptions_path = exc_path
    motor_state["error_reason"] = "existing claim"
    motor_state["error_node"] = "classify"

    with patch(
        "app_classify_extract_claim.graph.nodes.exception_handler.get_settings",
        return_value=mock_settings,
    ):
        await exception_handler(motor_state)

    records = [json.loads(line) for line in exc_path.read_text().splitlines()]
    assert records[0]["error_reason"] == "existing claim"


@pytest.mark.asyncio
async def test_exception_handler_exception_id_format(motor_state, mock_settings, tmp_path):
    exc_path = tmp_path / "exceptions.jsonl"
    mock_settings.exceptions_path = exc_path
    motor_state["error_reason"] = "missing fields"
    motor_state["error_node"] = "check_fields"

    with patch(
        "app_classify_extract_claim.graph.nodes.exception_handler.get_settings",
        return_value=mock_settings,
    ):
        await exception_handler(motor_state)

    records = [json.loads(line) for line in exc_path.read_text().splitlines()]
    assert "exception_id" in records[0]
    assert records[0]["exception_id"].startswith("EXC-")


@pytest.mark.asyncio
async def test_exception_handler_multiple_exceptions_append(motor_state, mock_settings, tmp_path):
    exc_path = tmp_path / "exceptions.jsonl"
    mock_settings.exceptions_path = exc_path
    motor_state["error_reason"] = "error1"

    with patch(
        "app_classify_extract_claim.graph.nodes.exception_handler.get_settings",
        return_value=mock_settings,
    ):
        await exception_handler(motor_state)
        motor_state["error_reason"] = "error2"
        await exception_handler(motor_state)

    lines = exc_path.read_text().splitlines()
    assert len(lines) == 2

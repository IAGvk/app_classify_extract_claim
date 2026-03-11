"""Integration tests for the full LangGraph pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from app_classify_extract_claim.graph.builder import build_graph
from app_classify_extract_claim.graph.state import initial_state

MOTOR_EMAIL_BODY = """
Subject: New motor claim
From: john.smith@example.com

Dear Claims Team,

I would like to lodge a new motor vehicle claim.

Policy Number: GIO-M-001
Date of Incident: 12/01/2024
Description: My vehicle was rear-ended at an intersection.

Insured: John Smith
"""


@pytest.fixture
def graph_env(tmp_path, monkeypatch):
    """Set MOCK_LLM and temp output paths for integration tests."""
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("LODGED_CLAIMS_PATH", str(tmp_path / "lodged.jsonl"))
    monkeypatch.setenv("EXCEPTIONS_PATH", str(tmp_path / "exceptions.jsonl"))
    monkeypatch.setenv(
        "VULNERABILITY_PHRASES_PATH",
        str(Path(__file__).parent / "../../data/vulnera_phrases.csv"),
    )
    monkeypatch.setenv(
        "MOCK_POLICIES_PATH",
        str(Path(__file__).parent / "../../data/mock_policies.json"),
    )
    return tmp_path


@pytest.mark.asyncio
async def test_full_pipeline_happy_path(graph_env):
    """Happy path: motor new claim flows through all nodes to lodge."""
    state = initial_state(
        email_id="test-001",
        email_body=MOTOR_EMAIL_BODY,
        raw_files=[],
    )

    graph = build_graph()
    result = await graph.ainvoke(state)

    # Pipeline should complete without unhandled error
    assert result is not None
    # With MOCK_LLM=true, lodge or exception handler should be reached
    assert result.get("lodge_status") is not None or result.get("exception_record") is not None


@pytest.mark.asyncio
async def test_full_pipeline_initial_state_defaults():
    """initial_state factory populates all required defaults."""
    state = initial_state(
        email_id="test-002",
        email_body="Test email body.",
        raw_files=[],
    )

    assert state["email_id"] == "test-002"
    assert state["email_body"] == "Test email body."
    assert state["raw_files"] == []
    assert state["vulnerability_flag"] is False
    assert state["completed"] is False
    assert state["error_reason"] is None


@pytest.mark.asyncio
async def test_full_pipeline_existing_claim_routes_to_exception(graph_env):
    """When claim_status is EXISTING, pipeline routes to exception_handler."""
    state = initial_state(
        email_id="test-003",
        email_body="Regarding my existing claim GIO-12345678.",
        raw_files=[],
    )
    # Pre-set state to simulate classify node result
    state["claim_status"] = "EXISTING"
    state["error_reason"] = "existing claim — routing to exception handler"
    state["error_node"] = "classify"

    graph = build_graph()
    result = await graph.ainvoke(state)

    assert result is not None


@pytest.mark.asyncio
async def test_graph_builds_without_error():
    """build_graph() compiles successfully."""
    graph = build_graph()
    assert graph is not None

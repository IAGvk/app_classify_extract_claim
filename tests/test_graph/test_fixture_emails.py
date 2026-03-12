"""Integration tests: full LangGraph pipeline on real .eml fixture files.

Covers three happy-path email scenarios:
  * Motor new claim         (freetext .eml)
  * Non-motor new claim     (freetext .eml)
  * Webform submission      (webform .eml)

Each test uses a matching mock-LLM responses JSON fixture so the pipeline
runs without GCP credentials and produces a deterministic lodgement result.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app_classify_extract_claim.graph.builder import build_graph
from app_classify_extract_claim.graph.state import initial_state
from app_classify_extract_claim.services.file_parser import parse_input

# ── Paths ─────────────────────────────────────────────────────────────────────────────

_SAMPLE = Path(__file__).parent.parent / "sample_data"
_DATA = Path(__file__).parent.parent.parent / "data"


# ── Shared fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def fixture_env(tmp_path, monkeypatch):
    """Configure MOCK_LLM + tmp output paths for fixture-based integration tests.

    * Resets the module-level ``_settings`` cache so every test builds a fresh
      ``Settings`` from the monkeypatched environment.
    * Each individual test additionally sets ``MOCK_LLM_FIXTURE`` to its own
      responses file before invoking the graph.
    """
    import app_classify_extract_claim.config.settings as _settings_mod

    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("LODGED_CLAIMS_PATH", str(tmp_path / "lodged.jsonl"))
    monkeypatch.setenv("EXCEPTIONS_PATH", str(tmp_path / "exceptions.jsonl"))
    monkeypatch.setenv("VULNERABILITY_PHRASES_PATH", str(_DATA / "vulnera_phrases.csv"))
    monkeypatch.setenv("MOCK_POLICIES_PATH", str(_DATA / "mock_policies.json"))
    # Force Settings to rebuild from the patched environment on first call
    monkeypatch.setattr(_settings_mod, "_settings", None)
    return tmp_path


# ── Motor new claim ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_motor_fixture_email_lodges(fixture_env, monkeypatch):
    """Full pipeline: motor_new_claim.eml → lodge SUCCESS with GIO-* reference."""
    monkeypatch.setenv("MOCK_LLM_FIXTURE", str(_SAMPLE / "mock_llm_responses_motor.json"))
    lodged_path = fixture_env / "lodged.jsonl"

    parsed = parse_input(_SAMPLE / "motor_new_claim.eml")
    state = initial_state(
        email_id="fixture-motor-001",
        email_body=parsed["body"],
        raw_files=[],
    )
    result = await build_graph().ainvoke(state)

    assert result is not None, "Pipeline returned None"
    assert result.get("lodge_status") == "SUCCESS", (
        f"Expected lodge_status=SUCCESS, got: {result.get('lodge_status')}  "
        f"exception={result.get('exception_record')}"
    )
    ref = result.get("claim_reference", "")
    assert ref.startswith("GIO-"), f"Unexpected claim_reference: {ref!r}"
    assert lodged_path.exists(), "lodged_claims.jsonl was not created"
    records = [json.loads(line) for line in lodged_path.read_text().splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["insurance_type"] == "motor"
    assert records[0]["claim_reference"] == ref


# ── Non-motor new claim ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_non_motor_fixture_email_lodges(fixture_env, monkeypatch):
    """Full pipeline: non_motor_new_claim.eml → lodge SUCCESS with GIO-* reference."""
    monkeypatch.setenv("MOCK_LLM_FIXTURE", str(_SAMPLE / "mock_llm_responses_non_motor.json"))
    lodged_path = fixture_env / "lodged.jsonl"

    parsed = parse_input(_SAMPLE / "non_motor_new_claim.eml")
    state = initial_state(
        email_id="fixture-nonmotor-001",
        email_body=parsed["body"],
        raw_files=[],
    )
    result = await build_graph().ainvoke(state)

    assert result is not None, "Pipeline returned None"
    assert result.get("lodge_status") == "SUCCESS", (
        f"Expected lodge_status=SUCCESS, got: {result.get('lodge_status')}  "
        f"exception={result.get('exception_record')}"
    )
    ref = result.get("claim_reference", "")
    assert ref.startswith("GIO-"), f"Unexpected claim_reference: {ref!r}"
    assert lodged_path.exists(), "lodged_claims.jsonl was not created"
    records = [json.loads(line) for line in lodged_path.read_text().splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["insurance_type"] == "non-motor"
    assert records[0]["claim_reference"] == ref


# ── Webform submission ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webform_fixture_email_lodges(fixture_env, monkeypatch):
    """Full pipeline: webform_submission.eml → lodge SUCCESS with GIO-* reference."""
    monkeypatch.setenv("MOCK_LLM_FIXTURE", str(_SAMPLE / "mock_llm_responses_webform_eml.json"))
    lodged_path = fixture_env / "lodged.jsonl"

    parsed = parse_input(_SAMPLE / "webform_submission.eml")
    state = initial_state(
        email_id="fixture-webform-001",
        email_body=parsed["body"],
        raw_files=[],
    )
    result = await build_graph().ainvoke(state)

    assert result is not None, "Pipeline returned None"
    assert result.get("lodge_status") == "SUCCESS", (
        f"Expected lodge_status=SUCCESS, got: {result.get('lodge_status')}  "
        f"exception={result.get('exception_record')}"
    )
    ref = result.get("claim_reference", "")
    assert ref.startswith("GIO-"), f"Unexpected claim_reference: {ref!r}"
    assert lodged_path.exists(), "lodged_claims.jsonl was not created"
    records = [json.loads(line) for line in lodged_path.read_text().splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["insurance_type"] == "motor"
    assert records[0]["claim_reference"] == ref

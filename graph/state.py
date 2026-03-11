"""LangGraph state definition for the claims pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    # ── Input ─────────────────────────────────────────────────────────────────
    email_id: str
    email_body: str
    # list of ParsedFile dicts: {filename, mime_type, text_content, base64_content}
    raw_files: list[dict[str, Any]]

    # ── vulnerability_check output ────────────────────────────────────────────
    vulnerability_flag: bool
    vulnerability_tags: list[str]
    vulnerability_score: float

    # ── classify_email output ─────────────────────────────────────────────────
    email_type: str  # "freetext" | "webform"

    # ── classify output ───────────────────────────────────────────────────────
    insurance_type: str  # "motor" | "non-motor" | "undetermined"
    claim_status: str  # "new_claim" | "existing_claim"
    claims: list[dict[str, Any]]  # list of ClaimContext dicts

    # ── extract_data output ───────────────────────────────────────────────────
    extracted_claim: dict[str, Any] | None  # ExtractedClaim.model_dump()

    # ── verify output ─────────────────────────────────────────────────────────
    verification_result: str  # "PASS" | "WARN" | "FAIL"
    verification_errors: list[str]

    # ── policy_retrieval output ───────────────────────────────────────────────
    policy: dict[str, Any] | None
    policy_found: bool

    # ── enrich output ─────────────────────────────────────────────────────────
    enriched_claim: dict[str, Any] | None

    # ── check_fields output ───────────────────────────────────────────────────
    fields_complete: bool
    missing_fields: list[str]

    # ── lodge output ──────────────────────────────────────────────────────────
    claim_reference: str | None
    lodge_status: str  # "SUCCESS" | "FAILED" | "PENDING"

    # ── exception_handler / error tracking ───────────────────────────────────
    error_reason: str | None
    error_node: str | None
    exception_record: dict[str, Any] | None
    completed: bool


def initial_state(email_id: str, email_body: str, raw_files: list[dict]) -> GraphState:
    """Return a fully populated initial state with safe defaults."""
    return GraphState(
        email_id=email_id,
        email_body=email_body,
        raw_files=raw_files,
        # defaults
        vulnerability_flag=False,
        vulnerability_tags=[],
        vulnerability_score=0.0,
        email_type="freetext",
        insurance_type="undetermined",
        claim_status="new_claim",
        claims=[],
        extracted_claim=None,
        verification_result="PASS",
        verification_errors=[],
        policy=None,
        policy_found=False,
        enriched_claim=None,
        fields_complete=False,
        missing_fields=[],
        claim_reference=None,
        lodge_status="PENDING",
        error_reason=None,
        error_node=None,
        exception_record=None,
        completed=False,
    )

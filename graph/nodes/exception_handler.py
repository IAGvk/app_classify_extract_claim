"""Node: exception_handler

Terminal node for all failure/incomplete paths.

Captures full pipeline state into an exception record and writes to
``data/exceptions_queue.jsonl`` for manual review.

Triggered by:
  - claim_status == 'existing_claim'  (routed manually for v1.x)
  - verify    → FAIL
  - check_fields → incomplete
  - lodge     → FAILED
  - any unhandled node error (error_node set)
"""
from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import TYPE_CHECKING

from app_classify_extract_claim.config.settings import get_settings

if TYPE_CHECKING:
    from pathlib import Path

    from app_classify_extract_claim.graph.state import GraphState

logger = logging.getLogger(__name__)


def _write_jsonl(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


async def exception_handler(state: GraphState) -> dict:
    """Capture full state and write to human review queue.

    Updates:
        exception_record, completed
    """
    settings = get_settings()
    now = datetime.now(UTC).isoformat()

    # Determine reason
    error_reason: str = state.get("error_reason") or "UNKNOWN"
    error_node: str = state.get("error_node") or "UNKNOWN"
    claim_status: str = state.get("claim_status", "") or ""
    fields_complete: bool = state.get("fields_complete", True)
    verification_result: str = state.get("verification_result", "") or ""
    lodge_status: str = state.get("lodge_status", "") or ""

    if (claim_status == "existing_claim" and not error_reason) or error_reason == "UNKNOWN":
        error_reason = "Existing claim — routed to manual review queue"
        error_node = "classify"
    elif verification_result == "FAIL":
        error_reason = error_reason or "Verification failed"
        error_node = error_node or "verify"
    elif not fields_complete:
        missing = state.get("missing_fields", [])
        error_reason = error_reason or f"Missing mandatory fields: {missing}"
        error_node = error_node or "check_fields"
    elif lodge_status == "FAILED":
        error_reason = error_reason or "Lodge submission failed"
        error_node = error_node or "lodge"

    exception_record = {
        "exception_id": f"EXC-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        "timestamped_at": now,
        "email_id": state.get("email_id"),
        "error_reason": error_reason,
        "error_node": error_node,
        "vulnerability_flag": state.get("vulnerability_flag", False),
        "vulnerability_tags": state.get("vulnerability_tags", []),
        "insurance_type": state.get("insurance_type"),
        "claim_status": claim_status,
        "verification_result": verification_result,
        "verification_errors": state.get("verification_errors", []),
        "missing_fields": state.get("missing_fields", []),
        "lodge_status": lodge_status,
        "policy_found": state.get("policy_found", False),
        "extracted_claim": state.get("extracted_claim"),
        "enriched_claim": state.get("enriched_claim"),
        "email_body_snippet": (state.get("email_body") or "")[:500],
    }

    try:
        _write_jsonl(exception_record, settings.exceptions_path)
        logger.warning(
            "exception_handler: recorded  id=%s  reason=%r  node=%s",
            exception_record["exception_id"], error_reason, error_node,
        )
    except Exception as exc:
        logger.error("exception_handler: failed to write JSONL: %s", exc)

    return {
        "exception_record": exception_record,
        "completed": True,
    }

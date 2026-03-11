"""Node: lodge  (v1.x — mock lodge via local JSONL)

Generates a fake claim reference (GIO-XXXXXXXX) and writes the full
lodgement record to ``data/lodged_claims.jsonl``.

v2.x: replace _mock_lodge with real Claims Management System API call.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app_classify_extract_claim.config.settings import get_settings
from app_classify_extract_claim.graph.state import GraphState

logger = logging.getLogger(__name__)


def _generate_reference() -> str:
    return f"GIO-{uuid.uuid4().hex[:8].upper()}"


def _write_jsonl(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


async def lodge(state: GraphState) -> dict:
    """Mock lodge — write to JSONL, return claim reference.

    Updates:
        claim_reference, lodge_status
    """
    settings = get_settings()
    enriched: dict | None = state.get("enriched_claim") or {}
    vuln_flag: bool = state.get("vulnerability_flag", False)
    insurance_type: str = state.get("insurance_type", "undetermined") or "undetermined"
    email_id: str = state.get("email_id", "unknown") or "unknown"

    try:
        reference = _generate_reference()
        now = datetime.now(timezone.utc).isoformat()

        lodge_record = {
            "claim_reference": reference,
            "email_id": email_id,
            "lodged_at": now,
            "insurance_type": insurance_type,
            "vulnerability_flag": vuln_flag,
            "priority": "HIGH" if vuln_flag else "NORMAL",
            "handler": "sensitive_claims_team" if vuln_flag else "standard_queue",
            "claim_data": enriched,
            "verification_errors": state.get("verification_errors", []),
            "policy_found": state.get("policy_found", False),
        }

        _write_jsonl(lodge_record, settings.lodged_claims_path)

        logger.info(
            "lodge: SUCCESS  reference=%s  type=%s  vulnerable=%s",
            reference, insurance_type, vuln_flag,
        )
        return {
            "claim_reference": reference,
            "lodge_status": "SUCCESS",
            "completed": True,
        }

    except Exception as exc:
        logger.error("lodge failed: %s", exc, exc_info=True)
        return {
            "claim_reference": None,
            "lodge_status": "FAILED",
            "error_reason": f"lodge error: {exc}",
            "error_node": "lodge",
        }

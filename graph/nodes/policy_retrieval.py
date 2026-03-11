"""Node: policy_retrieval  (v1.x — mock JSON store)

Looks up policy by:
1. Exact policy_number match
2. Fuzzy insured name match (fallback)

v2.x: replace _lookup_* functions with HTTP calls to the Policy API.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from app_classify_extract_claim.config.settings import get_settings

if TYPE_CHECKING:
    from pathlib import Path

    from app_classify_extract_claim.graph.state import GraphState

logger = logging.getLogger(__name__)


def _load_policies(path: Path) -> list[dict]:
    if not path.exists():
        logger.warning("Mock policies file not found: %s", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("policies", [])
    except Exception as exc:
        logger.error("Failed to load mock policies: %s", exc)
        return []


def _normalise(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _find_by_policy_number(policies: list[dict], number: str) -> dict | None:
    norm = _normalise(number)
    for p in policies:
        if _normalise(p.get("policy_number")) == norm:
            return p
    return None


def _find_by_name(policies: list[dict], name: str) -> dict | None:
    """Simple substring name match."""
    norm = _normalise(name)
    if len(norm) < 3:
        return None
    for p in policies:
        holder = p.get("holder", {})
        holder_name = _normalise(holder.get("name", ""))
        if norm in holder_name or holder_name in norm:
            return p
    return None


async def policy_retrieval(state: GraphState) -> dict:
    """Fetch policy from mock store.

    Updates:
        policy, policy_found
    """
    settings = get_settings()
    extracted: dict | None = state.get("extracted_claim") or {}
    insured = extracted.get("insured_details", {}) if extracted else {}
    policy_number: str | None = insured.get("policy_number")
    insured_name: str | None = insured.get("insured_name")

    policies = _load_policies(settings.mock_policies_path)

    try:
        found: dict | None = None

        if policy_number:
            found = _find_by_policy_number(policies, policy_number)
            if found:
                logger.info("policy_retrieval: exact match on policy_number=%s", policy_number)

        if not found and insured_name:
            found = _find_by_name(policies, insured_name)
            if found:
                logger.info("policy_retrieval: fuzzy name match for '%s'", insured_name)

        if not found:
            logger.info(
                "policy_retrieval: no policy found  policy_number=%s  name=%s",
                policy_number,
                insured_name,
            )
            return {"policy": None, "policy_found": False}

        return {"policy": found, "policy_found": True}

    except Exception as exc:
        logger.error("policy_retrieval failed: %s", exc, exc_info=True)
        return {
            "policy": None,
            "policy_found": False,
            "error_reason": f"policy_retrieval error: {exc}",
            "error_node": "policy_retrieval",
        }

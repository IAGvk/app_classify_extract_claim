"""Node: classify_email

Determines whether the email is a freetext narrative or a structured webform
submission, routing downstream extraction to the correct prompt/schema.
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from app_classify_extract_claim.config.settings import get_settings

if TYPE_CHECKING:
    from app_classify_extract_claim.graph.state import GraphState
from app_classify_extract_claim.prompts.classify_prompts import get_email_type_prompt
from app_classify_extract_claim.schemas.claim_data import EmailTypeResponse
from app_classify_extract_claim.services import llm_client as llm_module

logger = logging.getLogger(__name__)

# Regex heuristics — strong webform signals
_WEBFORM_PATTERNS = [
    re.compile(r"submission\s*(id|reference|number)\s*[:#]", re.I),
    re.compile(r"a new claim submission has been received", re.I),
    re.compile(r"(policy\s*number|date\s*of\s*loss|claim\s*type)\s*:", re.I),
    re.compile(r"(reference\s*id|reference\s*number)\s*:", re.I),
    re.compile(r"what\s*happened\?", re.I),
]
_WEBFORM_MIN_HITS = 2  # need ≥2 pattern matches to auto-classify as webform


async def classify_email(state: GraphState) -> dict:
    """Classify email as 'freetext' or 'webform'.

    Updates:
        email_type
    """
    settings = get_settings()
    body: str = state.get("email_body", "") or ""

    try:
        # ── Heuristic fast-path ───────────────────────────────────────────────
        hits = sum(1 for p in _WEBFORM_PATTERNS if p.search(body))
        if hits >= _WEBFORM_MIN_HITS:
            logger.info("classify_email: webform detected via heuristics (%d hits)", hits)
            return {"email_type": "webform"}

        # ── LLM fallback ──────────────────────────────────────────────────────
        client = llm_module.LLMClient.from_settings(settings)
        response: EmailTypeResponse = await client.ainvoke_structured(
            EmailTypeResponse,
            get_email_type_prompt(),
            f"Email body:\n\n{body[:4000]}",
        )
        email_type = response.email_type or "freetext"
        logger.info("classify_email: LLM → %s", email_type)
        return {"email_type": email_type}

    except Exception as exc:
        logger.error("classify_email failed: %s", exc, exc_info=True)
        return {
            "email_type": "freetext",  # safe default
            "error_reason": f"classify_email error: {exc}",
            "error_node": "classify_email",
        }

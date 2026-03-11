"""Node: classify

Three parallel LLM sub-tasks:
1. Insurance type:  motor | non-motor | undetermined
2. Claim status:    new_claim | existing_claim
3. Multi-claim:     groups the email into 1-N claim contexts

All three calls are awaited concurrently via asyncio.gather.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app_classify_extract_claim.config.settings import get_settings

if TYPE_CHECKING:
    from app_classify_extract_claim.graph.state import GraphState
from app_classify_extract_claim.prompts.classify_prompts import (
    get_claim_status_system_prompt,
    get_insurance_type_form_system_prompt,
    get_insurance_type_keyword_system_prompt,
    get_multi_claim_system_prompt,
)
from app_classify_extract_claim.schemas.claim_data import (
    ClaimsGroupingResponse,
    ClaimStatusResponse,
    InsuranceTypeResponse,
)
from app_classify_extract_claim.services import llm_client as llm_module
from app_classify_extract_claim.services.file_parser import files_to_langchain_parts

logger = logging.getLogger(__name__)


async def classify(state: GraphState) -> dict:
    """Classify insurance type, claim status, and group into individual claims.

    Updates:
        insurance_type, claim_status, claims
    Branching:
        If claim_status == 'existing_claim' → exception_handler (handled in builder)
    """
    settings = get_settings()
    body: str = state.get("email_body", "") or ""
    raw_files: list[dict] = state.get("raw_files", []) or []
    client = llm_module.LLMClient.from_settings(settings)

    attachment_parts, attachment_names = files_to_langchain_parts(raw_files)

    # Build human content blocks
    def _body_block(extra: str = "") -> list[dict]:
        text = f"Email Message:\n{body}"
        if attachment_names:
            text += "\n\nAttachments (provided):\n" + "\n".join(f"- {n}" for n in attachment_names)
        if extra:
            text += f"\n\n{extra}"
        return [{"type": "text", "text": text}, *attachment_parts]

    try:
        # ── 1. Insurance type: form-based detection ───────────────────────────
        async def _insurance_type() -> InsuranceTypeResponse:
            if raw_files:
                form_resp: InsuranceTypeResponse = await client.ainvoke_structured(
                    InsuranceTypeResponse,
                    get_insurance_type_form_system_prompt(),
                    _body_block(),
                )
                if form_resp.insurance_type != "undetermined":
                    return form_resp
            # Keyword fallback
            kw_resp: InsuranceTypeResponse = await client.ainvoke_structured(
                InsuranceTypeResponse,
                get_insurance_type_keyword_system_prompt(),
                _body_block(),
            )
            # Keyword node must return motor or non-motor
            if kw_resp.insurance_type == "undetermined":
                return InsuranceTypeResponse(insurance_type="non-motor")
            return kw_resp

        # ── 2. Claim status ───────────────────────────────────────────────────
        async def _claim_status() -> ClaimStatusResponse:
            return await client.ainvoke_structured(
                ClaimStatusResponse,
                get_claim_status_system_prompt(),
                _body_block(),
            )

        # ── 3. Multi-claim grouping ───────────────────────────────────────────
        async def _multi_claim() -> ClaimsGroupingResponse:
            return await client.ainvoke_structured(
                ClaimsGroupingResponse,
                get_multi_claim_system_prompt(),
                _body_block(),
            )

        ins_resp, status_resp, multi_resp = await asyncio.gather(
            _insurance_type(),
            _claim_status(),
            _multi_claim(),
        )

        insurance_type = ins_resp.insurance_type
        claim_status = status_resp.claim_type
        claims = [c.model_dump() for c in (multi_resp.claims or [])]

        logger.info(
            "classify: type=%s  status=%s  claims=%d",
            insurance_type, claim_status, len(claims),
        )
        return {
            "insurance_type": insurance_type,
            "claim_status": claim_status,
            "claims": claims,
        }

    except Exception as exc:
        logger.error("classify failed: %s", exc, exc_info=True)
        return {
            "insurance_type": "undetermined",
            "claim_status": "new_claim",
            "claims": [],
            "error_reason": f"classify error: {exc}",
            "error_node": "classify",
        }

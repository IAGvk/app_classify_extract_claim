"""Node: extract_data

Multimodal claim data extraction using Gemini.

Strategy:
- webform  → single-pass with webform prompt
- freetext + no form attachments → single-pass freetext prompt
- freetext + form attachments → 2-stage:
    Stage 1: extract from form attachments only
    Stage 2: enrich with email body (fills nulls, finds cross-source conflicts)

Images are passed inline as base64 data URLs.
"""
from __future__ import annotations

import json
import logging

from app_classify_extract_claim.config.settings import get_settings
from app_classify_extract_claim.graph.state import GraphState
from app_classify_extract_claim.prompts.extraction_prompts import (
    get_form_enrichment_prompt,
    get_form_stage1_prompt,
    get_freetext_prompt,
    get_webform_prompt,
)
from app_classify_extract_claim.schemas.claim_data import ExtractedClaim
from app_classify_extract_claim.services import llm_client as llm_module
from app_classify_extract_claim.services.file_parser import files_to_langchain_parts

logger = logging.getLogger(__name__)

# MIME types that indicate structured form attachments (PDF/DOCX)
_FORM_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _has_form_attachments(raw_files: list[dict]) -> bool:
    return any(f.get("mime_type", "") in _FORM_MIMES for f in raw_files)


async def extract_data(state: GraphState) -> dict:
    """Extract structured claim data from email body + attachments.

    Updates:
        extracted_claim  (ExtractedClaim.model_dump())
    """
    settings = get_settings()
    body: str = state.get("email_body", "") or ""
    raw_files: list[dict] = state.get("raw_files", []) or []
    email_type: str = state.get("email_type", "freetext") or "freetext"
    client = llm_module.LLMClient.from_settings(settings)

    attachment_parts, attachment_names = files_to_langchain_parts(raw_files)

    def _email_text_block(prefix: str = "Email Message:") -> dict:
        text = f"{prefix}\n{body}"
        if attachment_names:
            text += "\n\nAttachments (provided):\n" + "\n".join(f"- {n}" for n in attachment_names)
        return {"type": "text", "text": text}

    try:
        if email_type == "webform":
            # ── Single pass: webform ──────────────────────────────────────────
            logger.info("extract_data: webform single-pass extraction")
            content = [_email_text_block(), *attachment_parts]
            result: ExtractedClaim = await client.ainvoke_structured(
                ExtractedClaim, get_webform_prompt(), content
            )

        elif _has_form_attachments(raw_files):
            # ── 2-stage form extraction ───────────────────────────────────────
            logger.info("extract_data: 2-stage form extraction")

            # Stage 1: form attachments only
            stage1_content = [
                {"type": "text", "text": "Extract claim data from the attached claim form(s)."},
                *attachment_parts,
            ]
            stage1: ExtractedClaim = await client.ainvoke_structured(
                ExtractedClaim, get_form_stage1_prompt(), stage1_content
            )
            stage1_json = json.dumps(stage1.model_dump(), default=str, indent=2)
            logger.debug("extract_data: stage1 complete — %d chars", len(stage1_json))

            # Stage 2: enrich with email body
            enrich_prompt = get_form_enrichment_prompt(stage1_json)
            stage2_content = [_email_text_block("Email Body (for enrichment):"), *attachment_parts]
            result = await client.ainvoke_structured(
                ExtractedClaim, enrich_prompt, stage2_content
            )

        else:
            # ── Single pass: freetext ─────────────────────────────────────────
            logger.info("extract_data: freetext single-pass extraction")
            content = [_email_text_block(), *attachment_parts]
            result = await client.ainvoke_structured(
                ExtractedClaim, get_freetext_prompt(), content
            )

        extracted = result.model_dump()
        logger.info(
            "extract_data: extracted policy=%s  date_of_loss=%s  vehicle_reg=%s",
            extracted.get("insured_details", {}).get("policy_number"),
            extracted.get("incident_details", {}).get("date_of_loss"),
            extracted.get("vehicle_information", {}).get("vehicle_registration"),
        )
        return {"extracted_claim": extracted}

    except Exception as exc:
        logger.error("extract_data failed: %s", exc, exc_info=True)
        return {
            "extracted_claim": None,
            "error_reason": f"extract_data error: {exc}",
            "error_node": "extract_data",
        }

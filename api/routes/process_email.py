"""POST /process-email — upload a .eml file and run the LangGraph pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
import tempfile
from typing import Any, cast
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app_classify_extract_claim.config.settings import get_settings
from app_classify_extract_claim.graph.builder import get_graph
from app_classify_extract_claim.graph.state import initial_state
from app_classify_extract_claim.services.file_parser import parse_input

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Pipeline"])


class ProcessEmailResponse(BaseModel):
    """Structured response returned after the pipeline completes."""

    email_id: str
    lodge_status: str
    claim_reference: str | None = None
    insurance_type: str | None = None
    vulnerability_flag: bool = False
    error_reason: str | None = None


@router.post(
    "/process-email",
    response_model=ProcessEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Process an email through the claims pipeline",
)
async def process_email(
    email_file: UploadFile = File(..., description=".eml or .txt email file"),
) -> ProcessEmailResponse:
    """Upload a ``.eml`` or ``.txt`` email and run the full 10-node pipeline.

    Returns the claim reference, lodge status, detected insurance type,
    vulnerability flag, and any error reason if the claim could not be lodged.

    Raises:
        413: Email exceeds the configured size limit.
        500: Unhandled pipeline error.
    """
    settings = get_settings()
    email_id = str(uuid.uuid4())

    # ── Read and size-check ───────────────────────────────────────────────────
    content = await email_file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_email_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Email exceeds {settings.max_email_size_mb} MB limit ({size_mb:.1f} MB).",
        )

    # ── Write to a temp file so parse_input can read it ───────────────────────
    original_name = email_file.filename or "upload.eml"
    suffix = Path(original_name).suffix.lower() or ".eml"
    tmp_dir = Path(tempfile.mkdtemp(prefix="claims_api_"))
    tmp_email_path = tmp_dir / f"{email_id}{suffix}"

    try:
        tmp_email_path.write_bytes(content)
        logger.info(
            "[api] processing email_id=%s file=%s size_mb=%.2f",
            email_id,
            original_name,
            size_mb,
        )

        # ── Parse + build initial state ───────────────────────────────────────
        parsed = parse_input(str(tmp_email_path))
        email_body: str = parsed.get("body", "")
        raw_files: list[dict[str, Any]] = cast(
            "list[dict[str, Any]]", parsed.get("attachments", [])
        )

        state = initial_state(
            email_id=email_id,
            email_body=email_body,
            raw_files=raw_files,
        )

        # ── Run the pipeline ──────────────────────────────────────────────────
        graph = get_graph()
        result: dict[str, Any] = await graph.ainvoke(state)

        lodge_status: str = result.get("lodge_status", "UNKNOWN")
        logger.info(
            "[api] completed email_id=%s status=%s ref=%s",
            email_id,
            lodge_status,
            result.get("claim_reference"),
        )

        return ProcessEmailResponse(
            email_id=email_id,
            lodge_status=lodge_status,
            claim_reference=result.get("claim_reference"),
            insurance_type=result.get("insurance_type"),
            vulnerability_flag=bool(result.get("vulnerability_flag", False)),
            error_reason=result.get("error_reason"),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[api] pipeline error for email_id=%s: %s", email_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline error: {exc}",
        ) from exc
    finally:
        # ── Clean up temp files ───────────────────────────────────────────────
        try:
            tmp_email_path.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except OSError:
            pass

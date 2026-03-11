"""Node: verify

Rule-based + Pydantic validation of extracted claim data.

Checks:
- Pydantic model re-validation (catches type errors in raw dict)
- date_of_loss: not in the future, not more than 5 years old
- policy_number: must match known GIO/AMI prefix patterns if present
- phone format: digits only after stripping spaces/dashes
- email format: basic @ check
- If vulnerability_flag → inject SENSITIVE_CLAIM marker into errors (as warning, not fail)

Result:
- PASS  — all checks passed
- WARN  — non-critical issues (continue with warnings)
- FAIL  — critical issues (route to exception_handler)
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime

from app_classify_extract_claim.graph.state import GraphState
from app_classify_extract_claim.schemas.claim_data import ExtractedClaim

logger = logging.getLogger(__name__)

# Policy prefix patterns (GIO / AMI)
_POLICY_PREFIX_RE = re.compile(
    r"^(GIO|AMI|HO|BA|PA|CP|FA|MA|PL|WC|BI|CA|GL|PR|FI|ML|EN|EL|LL|BG|OM|HH|HA|FP|HO)",
    re.I,
)
_AMI_MID_RE = re.compile(r"^[A-Z]{2}(HO|BA|FA|CP|PA|GL|PL|MA|CA|WC|BI|PR|FI|ML)", re.I)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_DIGITS_RE = re.compile(r"\d{8,}")


async def verify(state: GraphState) -> dict:
    """Validate the extracted claim and return verification result.

    Updates:
        verification_result, verification_errors
    """
    errors: list[str] = []
    warnings: list[str] = []
    extracted: dict | None = state.get("extracted_claim")
    vuln_flag: bool = state.get("vulnerability_flag", False)

    try:
        # ── 1. Pydantic re-validation ─────────────────────────────────────────
        if extracted is None:
            errors.append("CRITICAL: extracted_claim is None — extraction failed")
        else:
            try:
                claim = ExtractedClaim.model_validate(extracted)
            except Exception as exc:
                errors.append(f"Schema validation error: {exc}")
                claim = None

            if claim:
                _check_date(claim, errors, warnings)
                _check_policy_number(claim, warnings)
                _check_phone(claim, warnings)
                _check_email_field(claim, warnings)

        # ── 2. Vulnerability escalation note ─────────────────────────────────
        if vuln_flag:
            warnings.append("SENSITIVE_CLAIM: vulnerability flag set — escalate to sensitive claims handler")

        # ── Result ────────────────────────────────────────────────────────────
        if errors:
            result = "FAIL"
        elif warnings:
            result = "WARN"
        else:
            result = "PASS"

        all_msgs = errors + warnings
        logger.info(
            "verify: result=%s  errors=%d  warnings=%d",
            result, len(errors), len(warnings),
        )
        return {
            "verification_result": result,
            "verification_errors": all_msgs,
        }

    except Exception as exc:
        logger.error("verify node error: %s", exc, exc_info=True)
        return {
            "verification_result": "FAIL",
            "verification_errors": [f"verify node exception: {exc}"],
            "error_reason": f"verify error: {exc}",
            "error_node": "verify",
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_date(claim: ExtractedClaim, errors: list, warnings: list) -> None:
    dol = claim.incident_details.date_of_loss
    if not dol:
        warnings.append("Missing date_of_loss — will need to be provided")
        return
    try:
        d = datetime.strptime(dol, "%Y-%m-%d").date()
        today = date.today()
        if d > today:
            errors.append(f"date_of_loss {dol} is in the future")
        elif (today - d).days > 5 * 365:
            warnings.append(f"date_of_loss {dol} is more than 5 years ago — verify claim age")
    except ValueError:
        warnings.append(f"date_of_loss '{dol}' is not in YYYY-MM-DD format")


def _check_policy_number(claim: ExtractedClaim, warnings: list) -> None:
    pn = claim.insured_details.policy_number
    if pn and not (_POLICY_PREFIX_RE.match(pn) or _AMI_MID_RE.match(pn)):
        warnings.append(f"policy_number '{pn}' does not match known GIO/AMI prefix patterns")


def _check_phone(claim: ExtractedClaim, warnings: list) -> None:
    for num in claim.insured_details.insured_numbers:
        digits = re.sub(r"[\s\-+()]", "", num.number)
        if not _PHONE_DIGITS_RE.search(digits):
            warnings.append(f"Phone number '{num.number}' has fewer than 8 digits")


def _check_email_field(claim: ExtractedClaim, warnings: list) -> None:
    email_addr = claim.insured_details.insured_email
    if email_addr and not _EMAIL_RE.match(email_addr):
        warnings.append(f"insured_email '{email_addr}' does not look like a valid email")

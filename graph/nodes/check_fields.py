"""Node: check_fields

Mandatory field completeness gate before lodgement.

Motor mandatory fields:
    date_of_loss, vehicle_registration, driver_name (first or last),
    incident_description, policy_number

Non-motor mandatory fields:
    date_of_loss, incident_description, policy_number, insured_name

All claims:
    insured_details must not be entirely empty
"""
from __future__ import annotations

import logging

from app_classify_extract_claim.graph.state import GraphState

logger = logging.getLogger(__name__)

_MOTOR_REQUIRED = [
    ("incident_details", "date_of_loss"),
    ("vehicle_information", "vehicle_registration"),
    ("incident_details", "incident_description"),
    ("insured_details", "policy_number"),
]
_NON_MOTOR_REQUIRED = [
    ("incident_details", "date_of_loss"),
    ("incident_details", "incident_description"),
    ("insured_details", "policy_number"),
    ("insured_details", "insured_name"),
]


def _has_driver_name(claim: dict) -> bool:
    driver = claim.get("drivers_details", {}) or {}
    name = driver.get("driver_name") or {}
    return bool(name.get("first_name") or name.get("last_name"))


async def check_fields(state: GraphState) -> dict:
    """Check mandatory fields are populated for the claim type.

    Updates:
        fields_complete, missing_fields
    """
    enriched: dict | None = state.get("enriched_claim") or {}
    insurance_type: str = state.get("insurance_type", "undetermined") or "undetermined"
    missing: list[str] = []

    try:
        required = _MOTOR_REQUIRED if insurance_type == "motor" else _NON_MOTOR_REQUIRED

        for section, field in required:
            section_data = enriched.get(section, {}) or {}
            if not section_data.get(field):
                missing.append(f"{section}.{field}")

        # Motor additional check: driver name
        if insurance_type == "motor" and not _has_driver_name(enriched):
            missing.append("drivers_details.driver_name")

        complete = len(missing) == 0
        if missing:
            logger.warning("check_fields: missing mandatory fields: %s", missing)
        else:
            logger.info("check_fields: all mandatory fields present for %s claim", insurance_type)

        return {
            "fields_complete": complete,
            "missing_fields": missing,
        }

    except Exception as exc:
        logger.error("check_fields failed: %s", exc, exc_info=True)
        return {
            "fields_complete": False,
            "missing_fields": [f"check_fields exception: {exc}"],
            "error_reason": f"check_fields error: {exc}",
            "error_node": "check_fields",
        }

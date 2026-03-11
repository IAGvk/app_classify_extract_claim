"""Node: enrich

Merges policy record data into the extracted claim, filling null fields
with policy-known values and tagging enriched fields with source=policy_system.
"""
from __future__ import annotations

import copy
import logging

from app_classify_extract_claim.graph.state import GraphState

logger = logging.getLogger(__name__)


def _deep_merge(extracted: dict, policy: dict) -> dict:
    """Fill null/missing extracted fields from policy where possible."""
    result = copy.deepcopy(extracted)
    enrichment_log: list[str] = []

    # ── Insured details ───────────────────────────────────────────────────────
    ins_ext = result.setdefault("insured_details", {})
    holder = policy.get("holder", {})

    _fill(ins_ext, "policy_number", policy.get("policy_number"), enrichment_log)
    _fill(ins_ext, "insured_name", holder.get("name"), enrichment_log)
    _fill(ins_ext, "insured_email", holder.get("email"), enrichment_log)
    if not ins_ext.get("insured_numbers") and holder.get("phone"):
        ins_ext["insured_numbers"] = [{"number": holder["phone"], "type": "other"}]
        enrichment_log.append("insured_details.insured_numbers")

    # ── Vehicle information ───────────────────────────────────────────────────
    vehicle = policy.get("vehicle")
    if vehicle:
        veh_ext = result.setdefault("vehicle_information", {})
        _fill(veh_ext, "vehicle_registration", vehicle.get("registration"), enrichment_log)
        _fill(veh_ext, "vehicle_make", vehicle.get("make"), enrichment_log)
        _fill(veh_ext, "vehicle_model", vehicle.get("model"), enrichment_log)
        _fill(veh_ext, "vehicle_year", vehicle.get("year"), enrichment_log)
        _fill(veh_ext, "vehicle_colour", vehicle.get("colour"), enrichment_log)

    if enrichment_log:
        logger.info("enrich: filled %d field(s) from policy: %s", len(enrichment_log), enrichment_log)
    else:
        logger.info("enrich: no null fields to fill from policy")

    # Attach enrichment metadata
    result["_enrichment_sources"] = enrichment_log
    result["_policy_number_used"] = policy.get("policy_number")

    return result


def _fill(target: dict, key: str, value, log: list) -> None:
    """Fill target[key] with value only if target[key] is null/empty."""
    if value is not None and value != "" and not target.get(key):
        target[key] = value
        log.append(key)


async def enrich(state: GraphState) -> dict:
    """Merge policy data into extracted claim.

    Updates:
        enriched_claim
    """
    extracted: dict | None = state.get("extracted_claim")
    policy: dict | None = state.get("policy")

    try:
        if not extracted:
            logger.warning("enrich: no extracted_claim — passing through")
            return {"enriched_claim": extracted or {}}

        if not policy:
            logger.info("enrich: no policy found — passing extracted claim through unchanged")
            return {"enriched_claim": copy.deepcopy(extracted)}

        enriched = _deep_merge(extracted, policy)
        return {"enriched_claim": enriched}

    except Exception as exc:
        logger.error("enrich failed: %s", exc, exc_info=True)
        return {
            "enriched_claim": extracted or {},
            "error_reason": f"enrich error: {exc}",
            "error_node": "enrich",
        }

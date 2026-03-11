"""Extraction prompts for freetext, webform, and form-based emails.

Ported and adapted from sample_guide_prompts.py with shared components.
"""
from __future__ import annotations

import json

# ── Shared guidelines (same as sample_guide_prompts.py) ──────────────────────

CONFLICT_TRACKING_GUIDELINES = """## CONFLICT TRACKING:
**Mandatory process for each field:**
1. Scan email_body for this field → record value if found
2. Scan each attachment for this field → record value if found
3. Compare all non-null recorded values → if they differ, populate conflict_metadata

**IMPORTANT — Only track GENUINE conflicts:**
- IGNORE null, None, empty string (""), or empty list ([]) when comparing values
- Only create conflict if 2+ sources have DIFFERENT non-empty values
- If one source has null and another has a value → NOT a conflict (missing data)

**Format when conflicts exist:**
```json
"conflict_metadata": {
    "vehicle_information.vehicle_registration": {
        "ABC123": ["claim_form.pdf"],
        "ABC-123": ["email_body"]
    }
}
```
**When sources agree OR one is null:** Leave conflict_metadata empty for that field."""

MAIN_CONTACT_GUIDELINES = """## MAIN CONTACT DETECTION (from EMAIL BODY):
1. Explicitly designated contact → use that person
2. Follow-up contact mentioned → use that person
3. Original sender of a forwarded email → use them
4. Direct email sender (default)

Fill main_contact.contact_name, phone_numbers, and email."""

CLAIM_REPORTER_GUIDELINES = """## CLAIM REPORTER:
1. Email sender (default)
2. Form field "Reported by / Lodged by / Submitted by" if present
Set party_type to "Claim_Reporter"."""

NA_HANDLING = """## NA HANDLING:
If a field contains ONLY 'NA', 'N/A', 'N.A.', 'n/a' treat as null/missing."""

CHECKBOX_GUIDELINES = """## CHECKBOX / YES/NO INTERPRETATION:
- Ticked/shaded/dashed/circled checkbox next to "Yes" → return "Yes"
- Same for "No" → return "No"
- Ambiguous or no marking → return null"""

IMAGE_ANALYSIS_NOTE = """## IMAGE ATTACHMENTS:
For image attachments, analyse the image content and extract any visible
insurance claim-relevant information: vehicle damage, registration plates,
incident location, document content, form fields."""


def get_freetext_prompt() -> str:
    return f"""You are an AI assistant specialised in extracting motor and non-motor
insurance claim information from unstructured emails and documents.

## EXTRACTION GUIDELINES:
- Extract as much relevant information as possible from all sources
- Cross-reference information between email and attachments
- If information is unclear or missing, leave field as null — DO NOT INFER

{NA_HANDLING}

{CONFLICT_TRACKING_GUIDELINES}

{MAIN_CONTACT_GUIDELINES}

{CLAIM_REPORTER_GUIDELINES}

{IMAGE_ANALYSIS_NOTE}

Extract all available claim data according to the ExtractedClaim schema."""


def get_webform_prompt() -> str:
    return f"""You are an AI assistant specialised in extracting insurance claim
information from webform submissions.

Extract all available information into the complete schema structure.

{NA_HANDLING}

- If "Other Parties involved" is "No" or blank → third_party_driver = null

{IMAGE_ANALYSIS_NOTE}

Return only valid JSON that matches the ExtractedClaim schema."""


def get_form_stage1_prompt() -> str:
    return f"""You are an AI assistant specialised in extracting motor claim
information from insurance claim forms.

## EXTRACTION GUIDELINES:
- Extract as much relevant information as possible from the claim form
- If information is unclear or missing, leave field as null — DO NOT INFER

{CHECKBOX_GUIDELINES}

{NA_HANDLING}

{CLAIM_REPORTER_GUIDELINES}

## INTERNAL CONFLICT DETECTION:
Even within the same form, different sections can contradict each other.
When this happens, record both values in conflict_metadata with the same source filename.

{IMAGE_ANALYSIS_NOTE}

Extract all available claim data according to the ExtractedClaim schema."""


def get_form_enrichment_prompt(stage1_json: str) -> str:
    return f"""You are an AI assistant enriching motor claim data by combining
form extraction with email context.

## CONTEXT:
You have already extracted data from the claim form (Stage 1 extraction below).
Now review the email body and any additional attachments to:
1. Fill fields that were null in Stage 1
2. Detect conflicts where email/attachments contradict the form
3. Extract main contact information from email sender/body

## STAGE 1 EXTRACTION (from claim form):
```json
{stage1_json}
```

## GUIDELINES:
- Form data from Stage 1 is primary — only update where email provides missing info
- If information is unclear or missing, leave as null — DO NOT INFER

{MAIN_CONTACT_GUIDELINES}

{CLAIM_REPORTER_GUIDELINES}

{NA_HANDLING}

{CONFLICT_TRACKING_GUIDELINES}

{IMAGE_ANALYSIS_NOTE}

Return the enriched ExtractedClaim."""


def get_conflict_check_prompt(conflicts_list: list[dict]) -> str:
    return f"""You are analysing ALL conflicting values from different sources
in an insurance claim.

Below are all the conflicts detected. For EACH field, determine if the
conflicting values are semantically equivalent.

Conflicts to analyse:
{json.dumps(conflicts_list, indent=2)}

EQUIVALENT examples (same info, different format):
- "ABC123" vs "ABC-123" vs "ABC 123" → same registration
- "John Smith" vs "JOHN SMITH" → same name
- "2024-11-20" vs "20/11/2024" → same date
- "0412345678" vs "0412 345 678" → same phone
- "Car hit tree" vs "Vehicle collided with a tree" → same event

NON-EQUIVALENT (genuinely contradictory):
- "ABC123" vs "XYZ789" → different registrations
- "Red sedan" vs "Blue SUV" → different vehicles
- "John Smith" vs "Jane Doe" → different people
- Different incident dates

Return a ConflictResolutionResponse with resolutions for ALL fields listed."""

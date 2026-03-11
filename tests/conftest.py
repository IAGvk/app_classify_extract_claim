"""Shared pytest fixtures for the claims pipeline test suite."""
from __future__ import annotations

from pathlib import Path

import pytest

from app_classify_extract_claim.graph.state import GraphState, initial_state

# ── Sample data ───────────────────────────────────────────────────────────────

MOTOR_EMAIL = """
Hi,

I'd like to lodge a motor vehicle insurance claim.

On 15 January 2025 I was driving my Toyota Camry (registration ABC123)
on Main Street, Sydney when another vehicle ran a red light and hit
my front bumper. The other driver was John Doe (registration XYZ999).

My policy number is GIO1234567.

Please let me know what's next.

Kind regards,
Sarah Smith
sarah.smith@example.com
0412 345 678
""".strip()

NON_MOTOR_EMAIL = """
Dear Claims Team,

I am writing to lodge a property insurance claim.

A storm on 20 February 2025 damaged the roof and gutters of my investment
property at 45 Oak Ave, Melbourne VIC 3000.

Policy: AMI5550001

Please advise on the next steps.

Regards,
Acme Property Pty Ltd
""".strip()

WEBFORM_EMAIL = """
Reference ID: WF-20250315-001
Submission ID: 67891234
Policy Number: GIO9876543
Date of Loss: 2025-03-10
What happened? I reversed into a pole in a car park causing damage to my rear bumper.
Registration: XYZ789
Driver Name: Sarah Johnson
Date of Birth: 1985-04-22
""".strip()

EXISTING_CLAIM_EMAIL = """
Hi,

Can I please follow up on my claim GIO-AB123456?
I lodged it last week and haven't heard back yet.

Thanks,
Michael
""".strip()

VULNERABLE_EMAIL = """
Hi,

I need to lodge a claim. I can't afford to fix my car out of pocket —
I'm really struggling financially since losing my job last month.
I'm going through a really hard time and this accident has made
everything so much worse.

My policy is GIO2468101, the accident was on 1 March 2025.

Please help me.

Regards,
Michael Brown
""".strip()


@pytest.fixture
def motor_state() -> GraphState:
    return initial_state("test-motor-001", MOTOR_EMAIL, [])


@pytest.fixture
def non_motor_state() -> GraphState:
    s = initial_state("test-nonmotor-001", NON_MOTOR_EMAIL, [])
    return s


@pytest.fixture
def webform_state() -> GraphState:
    return initial_state("test-webform-001", WEBFORM_EMAIL, [])


@pytest.fixture
def existing_claim_state() -> GraphState:
    return initial_state("test-existing-001", EXISTING_CLAIM_EMAIL, [])


@pytest.fixture
def vulnerable_state() -> GraphState:
    return initial_state("test-vulnerable-001", VULNERABLE_EMAIL, [])


@pytest.fixture
def extracted_motor_claim() -> dict:
    return {
        "insured_details": {
            "policy_number": "GIO1234567",
            "insured_name": "Sarah Smith",
            "insured_contact_name": {"title": None, "first_name": "Sarah", "middle_name": None, "last_name": "Smith"},
            "insured_numbers": [{"number": "0412345678", "type": "mobile"}],
            "insured_email": "sarah.smith@example.com",
            "claim_tax_status": None,
            "intend_to_claim_itc": None,
            "abn": None,
        },
        "vehicle_information": {
            "vehicle_registration": "ABC123",
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_year": None,
            "vehicle_colour": None,
            "vehicle_type": None,
        },
        "drivers_details": {
            "driver_name": {"title": None, "first_name": "Sarah", "middle_name": None, "last_name": "Smith"},
            "driver_date_of_birth": None,
            "driver_age": None,
            "driver_licence_number": None,
            "driver_licence_state": None,
            "same_as_insured": True,
        },
        "incident_details": {
            "date_of_loss": "2025-01-15",
            "incident_description": "Driving on Main Street Sydney when another vehicle ran a red light and hit my front bumper.",
            "incident_suburb": "Sydney",
            "incident_state": "AU_NSW",
            "incident_postcode": None,
            "incident_address_lines": ["Main Street"],
            "vehicle_towed": None,
            "vehicle_damage_description": "Front bumper damage",
            "police_report_number": None,
        },
        "third_party_driver": {
            "tp_driver_name": {"title": None, "first_name": "John", "middle_name": None, "last_name": "Doe"},
            "tp_contact_number": None,
            "tp_address_lines": None,
            "tp_suburb": None,
            "tp_postcode": None,
            "tp_state": None,
            "tp_car_registration": "XYZ999",
            "tp_vehicle_make": None,
            "tp_vehicle_model": None,
        },
        "main_contact": {
            "contact_name": {"title": None, "first_name": "Sarah", "middle_name": None, "last_name": "Smith"},
            "phone_numbers": [{"number": "0412345678", "type": "mobile"}],
            "email": "sarah.smith@example.com",
        },
        "claim_reporter": {
            "reporter_name": {"title": None, "first_name": "Sarah", "middle_name": None, "last_name": "Smith"},
            "party_type": "Claim_Reporter",
        },
        "conflict_metadata": {},
    }


@pytest.fixture
def mock_settings(tmp_path):
    """Settings pointing to tmp directories for JSONL outputs."""
    from app_classify_extract_claim.config.settings import Settings

    phrases_path = Path(__file__).parent.parent / "data" / "vulnera_phrases.csv"
    policies_path = Path(__file__).parent.parent / "data" / "mock_policies.json"

    settings = Settings(
        GCP_PROJECT_ID="test-project",
        GCP_LOCATION_ID="us-central1",
        GCP_GEMINI_MODEL="gemini-1.5-pro-002",
        MOCK_LLM=True,
        LODGED_CLAIMS_PATH=str(tmp_path / "lodged_claims.jsonl"),
        EXCEPTIONS_PATH=str(tmp_path / "exceptions_queue.jsonl"),
        VULNERABILITY_PHRASES_PATH=str(phrases_path),
        MOCK_POLICIES_PATH=str(policies_path),
    )
    return settings

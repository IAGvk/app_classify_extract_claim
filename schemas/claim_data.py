"""Pydantic models for structured LLM extraction output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ── Name / contact primitives ─────────────────────────────────────────────────


class Name(BaseModel):
    title: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None

    def full(self) -> str:
        parts = [p for p in [self.title, self.first_name, self.middle_name, self.last_name] if p]
        return " ".join(parts)


class ContactNumber(BaseModel):
    number: str
    type: Literal["mobile", "home", "work", "other"] = "other"


# ── Sub-sections ──────────────────────────────────────────────────────────────


class InsuredDetails(BaseModel):
    policy_number: str | None = None
    insured_name: str | None = None
    insured_contact_name: Name | None = None
    insured_numbers: list[ContactNumber] = Field(default_factory=list)
    insured_email: str | None = None
    claim_tax_status: Literal["Yes", "No"] | None = None
    intend_to_claim_itc: Literal["Yes", "No", "Not Sure"] | None = None
    abn: str | None = None


class VehicleInformation(BaseModel):
    vehicle_registration: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_year: int | None = None
    vehicle_colour: str | None = None
    vehicle_type: str | None = None  # sedan, SUV, ute, etc.


class DriverDetails(BaseModel):
    driver_name: Name | None = None
    driver_date_of_birth: str | None = None  # YYYY-MM-DD
    driver_age: int | None = None
    driver_licence_number: str | None = None
    driver_licence_state: str | None = None
    same_as_insured: bool | None = None


class ThirdPartyDetails(BaseModel):
    tp_driver_name: Name | None = None
    tp_contact_number: str | None = None
    tp_address_lines: list[str] | None = None
    tp_suburb: str | None = None
    tp_postcode: str | None = None
    tp_state: str | None = None
    tp_car_registration: str | None = None
    tp_vehicle_make: str | None = None
    tp_vehicle_model: str | None = None


class IncidentDetails(BaseModel):
    date_of_loss: str | None = None  # YYYY-MM-DD
    incident_description: str | None = None
    incident_address_lines: list[str] | None = None
    incident_suburb: str | None = None
    incident_postcode: str | None = None
    incident_state: str | None = None
    vehicle_towed: Literal["Yes", "No"] | None = None
    vehicle_damage_description: str | None = None
    police_report_number: str | None = None


class MainContact(BaseModel):
    contact_name: Name | None = None
    phone_numbers: list[ContactNumber] = Field(default_factory=list)
    email: str | None = None


class ClaimReporter(BaseModel):
    reporter_name: Name | None = None
    party_type: str = "Claim_Reporter"


# ── Top-level extraction result ───────────────────────────────────────────────


class ExtractedClaim(BaseModel):
    """Unified extraction schema usable for freetext, webform, and form-based emails."""

    insured_details: InsuredDetails = Field(default_factory=InsuredDetails)
    vehicle_information: VehicleInformation = Field(default_factory=VehicleInformation)
    drivers_details: DriverDetails = Field(default_factory=DriverDetails)
    incident_details: IncidentDetails = Field(default_factory=IncidentDetails)
    third_party_driver: ThirdPartyDetails | None = None
    main_contact: MainContact | None = None
    claim_reporter: ClaimReporter | None = None
    conflict_metadata: dict[str, dict[str, list[str]]] = Field(default_factory=dict)


# ── LLM response helpers ──────────────────────────────────────────────────────


class ClaimContext(BaseModel):
    """One claim identified within a multi-claim email."""

    description: str
    risk: str
    unique_email_info: str
    attachments: list[str] = Field(default_factory=list)


class ClaimsGroupingResponse(BaseModel):
    claims: list[ClaimContext]


class InsuranceTypeResponse(BaseModel):
    insurance_type: Literal["motor", "non-motor", "undetermined"]


class ClaimStatusResponse(BaseModel):
    claim_type: Literal["new_claim", "existing_claim"]


class EmailTypeResponse(BaseModel):
    email_type: Literal["freetext", "webform"]


class VulnerabilityConfirmResponse(BaseModel):
    confirmed: bool
    matched_phrases: list[str] = Field(default_factory=list)
    severity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    notes: str | None = None


class ConflictResolution(BaseModel):
    field_name: str
    is_equivalent: bool
    canonical_value: str | None = None
    reason: str


class ConflictResolutionResponse(BaseModel):
    resolutions: list[ConflictResolution]

# Data Schemas

**File:** `schemas/claim_data.py`

All structured LLM inputs and outputs are defined as **Pydantic v2 `BaseModel`** classes.
Every node that calls the LLM passes a schema class to `LLMClient.ainvoke_structured()`,
which uses LangChain's `.with_structured_output()` to coerce the LLM response.

---

## Schema hierarchy

```
ExtractedClaim
├── insured_details:       InsuredDetails
│   └── insured_contact_name:  Name
│   └── insured_numbers:       list[ContactNumber]
├── vehicle_information:  VehicleInformation
├── drivers_details:       DriverDetails
│   └── driver_name:           Name
├── incident_details:      IncidentDetails
├── third_party_driver:    ThirdPartyDetails | None
│   └── tp_driver_name:        Name
├── main_contact:          MainContact | None
│   └── contact_name:          Name
│   └── phone_numbers:         list[ContactNumber]
└── claim_reporter:        ClaimReporter | None
    └── reporter_name:         Name
```

---

## Primitive types

### `Name`

```python
class Name(BaseModel):
    title: str | None           # Mr, Mrs, Dr, etc.
    first_name: str | None
    middle_name: str | None
    last_name: str | None

    def full(self) -> str: ...  # Concatenates non-None parts
```

### `ContactNumber`

```python
class ContactNumber(BaseModel):
    number: str
    type: Literal["mobile", "home", "work", "other"]
```

---

## Core sub-schemas

### `InsuredDetails`

| Field                  | Type                                     | Description                           |
| ---------------------- | ---------------------------------------- | ------------------------------------- |
| `policy_number`        | `str \| None`                            | Policy identifier, e.g. `"GIO-M-001"` |
| `insured_name`         | `str \| None`                            | Full name of the policy holder        |
| `insured_contact_name` | `Name \| None`                           | Structured name                       |
| `insured_numbers`      | `list[ContactNumber]`                    | Phone numbers                         |
| `insured_email`        | `str \| None`                            | Email address                         |
| `claim_tax_status`     | `Literal["Yes","No"] \| None`            | Registered for GST?                   |
| `intend_to_claim_itc`  | `Literal["Yes","No","Not Sure"] \| None` | Claiming ITC?                         |
| `abn`                  | `str \| None`                            | Australian Business Number            |

### `VehicleInformation`

| Field                  | Type          | Description           |
| ---------------------- | ------------- | --------------------- |
| `vehicle_registration` | `str \| None` | Rego plate            |
| `vehicle_make`         | `str \| None` | e.g. `"Toyota"`       |
| `vehicle_model`        | `str \| None` | e.g. `"Camry"`        |
| `vehicle_year`         | `int \| None` | 4-digit year          |
| `vehicle_colour`       | `str \| None` | e.g. `"Silver"`       |
| `vehicle_type`         | `str \| None` | sedan, SUV, ute, etc. |

### `DriverDetails`

| Field                   | Type           | Description                  |
| ----------------------- | -------------- | ---------------------------- |
| `driver_name`           | `Name \| None` | Driver's full name           |
| `driver_date_of_birth`  | `str \| None`  | YYYY-MM-DD                   |
| `driver_age`            | `int \| None`  | Calculated or stated age     |
| `driver_licence_number` | `str \| None`  | Licence number               |
| `driver_licence_state`  | `str \| None`  | Issuing state                |
| `same_as_insured`       | `bool \| None` | Is driver the policy holder? |

### `IncidentDetails`

| Field                        | Type                          | Description                |
| ---------------------------- | ----------------------------- | -------------------------- |
| `date_of_loss`               | `str \| None`                 | YYYY-MM-DD format          |
| `incident_description`       | `str \| None`                 | What happened              |
| `incident_address_lines`     | `list[str] \| None`           | Street address of incident |
| `incident_suburb`            | `str \| None`                 |                            |
| `incident_postcode`          | `str \| None`                 |                            |
| `incident_state`             | `str \| None`                 |                            |
| `vehicle_towed`              | `Literal["Yes","No"] \| None` | Was vehicle towed?         |
| `vehicle_damage_description` | `str \| None`                 | Damage description         |
| `police_report_number`       | `str \| None`                 | If reported to police      |

---

## LLM response helper schemas

| Schema                         | Used by node          | Returns                                                       |
| ------------------------------ | --------------------- | ------------------------------------------------------------- |
| `EmailTypeResponse`            | `classify_email`      | `email_type: Literal["freetext","webform"]`                   |
| `InsuranceTypeResponse`        | `classify`            | `insurance_type: Literal["motor","non-motor","undetermined"]` |
| `ClaimStatusResponse`          | `classify`            | `claim_type: Literal["new_claim","existing_claim"]`           |
| `ClaimsGroupingResponse`       | `classify`            | `claims: list[ClaimContext]`                                  |
| `VulnerabilityConfirmResponse` | `vulnerability_check` | `confirmed`, `matched_phrases`, `severity_score`, `notes`     |
| `ConflictResolutionResponse`   | `verify` (optional)   | `resolutions: list[ConflictResolution]`                       |

---

## API reference

::: app_classify_extract_claim.schemas.claim_data
    options:
      show_source: false
      members:
        - Name
        - ContactNumber
        - InsuredDetails
        - VehicleInformation
        - DriverDetails
        - IncidentDetails
        - ThirdPartyDetails
        - MainContact
        - ClaimReporter
        - ExtractedClaim
        - EmailTypeResponse
        - InsuranceTypeResponse
        - ClaimStatusResponse
        - ClaimsGroupingResponse
        - VulnerabilityConfirmResponse
        - ConflictResolutionResponse

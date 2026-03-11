# extract_data

**File:** `graph/nodes/extract_data.py`  
**Position:** Node 4  
**LLM calls:** 1

---

## Purpose

Extract all structured claim fields from the unstructured email body and any attachment
text, populating an `ExtractedClaim` Pydantic model. This is the most complex LLM call
in the pipeline — it covers over 40 distinct fields across six sub-schemas.

---

## Extraction strategy by `email_type`

| `email_type` | LLM approach                                                           |
| ------------ | ---------------------------------------------------------------------- |
| `freetext`   | Named-entity recognition style: find values embedded in narrative text |
| `webform`    | Field-value parsing: locate labelled fields and extract their values   |

The system prompt adapts to `email_type`. Both paths produce the same `ExtractedClaim` output schema.

---

## State contract

|            | Field             | Type           | Description                    |
| ---------- | ----------------- | -------------- | ------------------------------ |
| **Reads**  | `email_body`      | `str`          | Full email body                |
| **Reads**  | `raw_files`       | `list[dict]`   | Attachment text content        |
| **Reads**  | `email_type`      | `str`          | From `classify_email`          |
| **Reads**  | `insurance_type`  | `str`          | From `classify`                |
| **Reads**  | `claims`          | `list[dict]`   | Claim contexts from `classify` |
| **Writes** | `extracted_claim` | `dict \| None` | `ExtractedClaim.model_dump()`  |

---

## Output schema (abbreviated)

```python
class ExtractedClaim(BaseModel):
    insured_details: InsuredDetails      # policy_number, name, contact, ABN, tax status
    vehicle_information: VehicleInformation  # rego, make, model, year, colour
    drivers_details: DriverDetails       # driver name, DOB, licence
    incident_details: IncidentDetails    # date_of_loss, description, location, police report
    third_party_driver: ThirdPartyDetails | None
    main_contact: MainContact | None
    claim_reporter: ClaimReporter | None
    conflict_metadata: dict              # populated by verify node
```

The full schema is documented in [Data Schemas](../schemas.md).

---

## API reference

::: app_classify_extract_claim.graph.nodes.extract_data
    options:
      show_source: true
      members:
        - extract_data

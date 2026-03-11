# check_fields

**File:** `graph/nodes/check_fields.py`  
**Position:** Node 8  
**LLM calls:** 0  
**Branches:** → `exception_handler` if `fields_complete == False`

---

## Purpose

Validate that all **mandatory fields** required to lodge a claim are present
in the enriched claim record. Fields can be missing because the LLM failed to
extract them, the customer omitted them, or no matching policy was found.

---

## Mandatory fields by insurance type

### Motor claims

| Field path                                 | Description                |
| ------------------------------------------ | -------------------------- |
| `insured_details.policy_number`            | Policy identifier          |
| `incident_details.date_of_loss`            | When the incident occurred |
| `incident_details.incident_description`    | What happened              |
| `vehicle_information.vehicle_registration` | Vehicle registration       |
| `insured_details.insured_name`             | Policy holder name         |

### Non-motor claims

| Field path                              | Description                |
| --------------------------------------- | -------------------------- |
| `insured_details.policy_number`         | Policy identifier          |
| `incident_details.date_of_loss`         | When the incident occurred |
| `incident_details.incident_description` | What happened              |
| `insured_details.insured_name`          | Policy holder name         |

Fields are looked up with dotted-path notation against the `enriched_claim` dict.
A field is considered **missing** if its value is `None`, an empty string, or absent.

---

## State contract

|            | Field             | Type           | Description                                   |
| ---------- | ----------------- | -------------- | --------------------------------------------- |
| **Reads**  | `enriched_claim`  | `dict \| None` | From `enrich`                                 |
| **Reads**  | `insurance_type`  | `str`          | Determines which mandatory field list applies |
| **Writes** | `fields_complete` | `bool`         | True if all mandatory fields present          |
| **Writes** | `missing_fields`  | `list[str]`    | Names of any missing mandatory fields         |

---

## API reference

::: app_classify_extract_claim.graph.nodes.check_fields
    options:
      show_source: true
      members:
        - check_fields

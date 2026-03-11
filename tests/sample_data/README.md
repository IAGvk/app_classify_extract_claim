# Sample Data

Test input files for the claims pipeline. Use these with the CLI runner or in test fixtures.

## Quick start

```bash
# Run any sample through the pipeline (mock mode — no GCP calls)
MOCK_LLM=true python app_classify_extract_claim/run.py \
    --input app_classify_extract_claim/tests/sample_data/motor_new_claim.eml \
    --pretty
```

---

## Files

### `.eml` samples (RFC-2822 email format)

| File                        | Scenario                                                               | Expected path                                             |
| --------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------- |
| `motor_new_claim.eml`       | New motor claim, rear-end collision, full details, third-party present | Happy path → lodge                                        |
| `non_motor_new_claim.eml`   | New home contents claim, burst pipe water damage                       | Happy path → lodge                                        |
| `existing_claim_update.eml` | Follow-up on existing reference `GIO-20260289`                         | classify → exception_handler                              |
| `vulnerable_customer.eml`   | Elderly pensioner, distressed, hospital admission, carer involved      | vulnerability flag HIGH, lodge with sensitive_claims_team |
| `webform_submission.eml`    | Structured GIO online webform output wrapped in an email               | classify_email=webform → extract_data webform path        |

### `.txt` samples (plain text, no MIME headers required)

| File                      | Scenario                                            | Expected path                                      |
| ------------------------- | --------------------------------------------------- | -------------------------------------------------- |
| `motor_new_claim.txt`     | New motor claim, hail damage, no third party        | Happy path → lodge                                 |
| `non_motor_new_claim.txt` | New contents claim, burglary, police report present | Happy path → lodge                                 |
| `webform_submission.txt`  | Structured webform submission saved as plain text   | classify_email=webform → extract_data webform path |

---

## Policies referenced

The mock policy store (`data/mock_policies.json`) contains matching records for most samples:

| Policy Number | Type                 | Holder          |
| ------------- | -------------------- | --------------- |
| `GIO-M-001`   | Motor                | John Smith      |
| `GIO-M-002`   | Motor                | Helen Bradshaw  |
| `GIO-M-003`   | Motor                | David O'Keefe   |
| `GIO-M-004`   | Motor                | Robert Chen     |
| `GIO-M-005`   | Motor                | Priya Patel     |
| `GIO-M-006`   | Motor                | Aisha Malik     |
| `AMI-NM-001`  | Non-motor (Home)     | Margaret Nguyen |
| `AMI-NM-002`  | Non-motor (Contents) | Liam O'Hara     |

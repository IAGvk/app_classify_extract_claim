# Testing Guide

---

## Running tests

All tests run offline — no GCP credentials required.

```bash
# Full test suite (recommended)
make test

# With coverage report
make test-cov

# Quick smoke test (fail fast on first failure)
make test-fast

# Direct pytest
cd app_classify_extract_claim
MOCK_LLM=true PYTHONPATH=.. python -m pytest tests/ -v
```

Coverage target: **≥ 60%** (enforced by `pyproject.toml` `fail_under=60`).

---

## Test structure

```
tests/
├── conftest.py              ← Shared fixtures: states, mock_settings
├── test_integration.py      ← End-to-end pipeline tests (all 8 sample inputs)
├── test_nodes/
│   ├── test_vulnerability_check.py
│   ├── test_classify_email.py
│   ├── test_classify.py
│   ├── test_extract_data.py
│   ├── test_verify.py
│   ├── test_policy_retrieval.py
│   ├── test_enrich.py
│   ├── test_check_fields.py
│   ├── test_lodge.py
│   └── test_exception_handler.py
└── sample_data/
    ├── motor_new_claim.eml
    ├── non_motor_new_claim.eml
    ├── vulnerable_customer.eml
    ├── existing_claim_update.eml
    ├── webform_submission.eml
    ├── motor_new_claim.txt
    ├── non_motor_new_claim.txt
    ├── webform_submission.txt
    ├── mock_llm_responses_motor.json
    ├── mock_llm_responses_non_motor.json
    ├── mock_llm_responses_vulnerable.json
    ├── mock_llm_responses_existing_claim.json
    ├── mock_llm_responses_webform_eml.json
    ├── mock_llm_responses_motor_txt.json
    ├── mock_llm_responses_non_motor_txt.json
    └── mock_llm_responses_webform_txt.json
```

---

## Shared fixtures (`conftest.py`)

| Fixture                 | Type         | Description                                          |
| ----------------------- | ------------ | ---------------------------------------------------- |
| `mock_settings`         | `Settings`   | Settings with `mock_llm=True` and local paths        |
| `motor_state`           | `GraphState` | State pre-loaded with `motor_new_claim.eml` body     |
| `vulnerable_state`      | `GraphState` | State pre-loaded with `vulnerable_customer.eml` body |
| `extracted_motor_claim` | `dict`       | `ExtractedClaim.model_dump()` for a motor claim      |

Use `mock_settings` in all unit tests to prevent real GCP calls even if `MOCK_LLM` is accidentally unset.

---

## Writing a unit test

```python
import pytest
from unittest.mock import AsyncMock, patch
from app_classify_extract_claim.graph.nodes.classify_email import classify_email
from app_classify_extract_claim.schemas.claim_data import EmailTypeResponse

@pytest.mark.asyncio
async def test_classify_email_freetext(motor_state, mock_settings):
    mock_response = EmailTypeResponse(email_type="freetext")
    mock_client = AsyncMock()
    mock_client.ainvoke_structured = AsyncMock(return_value=mock_response)

    with (
        patch("...classify_email.get_settings", return_value=mock_settings),
        patch("...classify_email.llm_module.LLMClient.from_settings",
              return_value=mock_client),
    ):
        result = await classify_email(motor_state)

    assert result["email_type"] == "freetext"
```

---

## Integration tests (end-to-end)

Integration tests run the **full compiled graph** with a fixture file:

```python
@pytest.mark.asyncio
async def test_motor_new_claim_lodges():
    state = initial_state("test-motor", MOTOR_EMAIL_BODY, [])
    os.environ["MOCK_LLM_FIXTURE"] = "tests/sample_data/mock_llm_responses_motor.json"
    result = await graph.ainvoke(state)
    assert result["lodge_status"] == "SUCCESS"
    assert result["claim_reference"].startswith("GIO-")
```

---

## Fixture sample table

All 8 combinations have been verified to produce the expected outcome:

| Input file                  | Fixture file                             | Expected outcome             |
| --------------------------- | ---------------------------------------- | ---------------------------- |
| `motor_new_claim.eml`       | `mock_llm_responses_motor.json`          | `lodge=SUCCESS`              |
| `non_motor_new_claim.eml`   | `mock_llm_responses_non_motor.json`      | `lodge=SUCCESS`              |
| `vulnerable_customer.eml`   | `mock_llm_responses_vulnerable.json`     | `lodge=SUCCESS`, `vuln=True` |
| `existing_claim_update.eml` | `mock_llm_responses_existing_claim.json` | `exception_handler`          |
| `webform_submission.eml`    | `mock_llm_responses_webform_eml.json`    | `lodge=SUCCESS`              |
| `motor_new_claim.txt`       | `mock_llm_responses_motor_txt.json`      | `lodge=SUCCESS`              |
| `non_motor_new_claim.txt`   | `mock_llm_responses_non_motor_txt.json`  | `lodge=SUCCESS`              |
| `webform_submission.txt`    | `mock_llm_responses_webform_txt.json`    | `lodge=SUCCESS`              |

---

## Adding a fixture for a new test scenario

1. Create the input file under `tests/sample_data/`
2. Run with `MOCK_LLM=true` (blank) to verify the pipeline reaches the expected node
3. Create a fixture JSON following the [fixture format](services/llm_client.md#fixture-file-locations)
4. Run again with `MOCK_LLM_FIXTURE=path/to/fixture.json` to verify realistic flow
5. Add the combination to the integration test matrix in `test_integration.py`

# LLM Client

**File:** `services/llm_client.py`

---

## Overview

`LLMClient` is the single abstraction layer between pipeline nodes and the LLM.
All nodes call `client.ainvoke_structured()` — they never instantiate
`ChatVertexAI` or construct LangChain chains directly.

This design means:
- Swapping the underlying model (Gemini → GPT-4o, for example) requires a single file change
- Mock mode is enabled transparently — nodes do not know or care whether they speak to a real LLM
- Structured output validation (Pydantic) is centralised here

---

## Class interface

```python
class LLMClient:

    @classmethod
    def from_settings(cls, settings: Settings) -> "LLMClient":
        """Factory method. Reads MOCK_LLM and MOCK_LLM_FIXTURE env vars."""

    async def ainvoke_structured(
        self,
        schema: type[T],
        system_prompt: str,
        user_text: str,
        images: list[str] | None = None,
    ) -> T:
        """
        Call the LLM and return a validated Pydantic instance of `schema`.

        In real mode: calls ChatVertexAI with .with_structured_output(schema).
        In mock mode:  calls _mock_structured(schema, fixture).
        """
```

---

## Mock mode

### Tier 1 — blank mock (`MOCK_LLM=true`)

Returns a minimal valid instance built by inspecting the schema fields:

| Field type          | Mock value                  |
| ------------------- | --------------------------- |
| `Literal["a", "b"]` | First literal value (`"a"`) |
| `list[...]`         | `[]` (empty list)           |
| `dict`              | `{}` (empty dict)           |
| `str \| None`       | `None`                      |
| `bool`              | `False`                     |
| `float`             | `0.0`                       |

Use blank mode for **unit tests** that verify node routing logic,
not for tests that depend on realistic LLM output.

### Tier 2 — fixture mock (`MOCK_LLM_FIXTURE=path/to/fixture.json`)

The fixture JSON is keyed by Pydantic schema class name:

```json
{
  "EmailTypeResponse":    { "email_type": "freetext" },
  "InsuranceTypeResponse": { "insurance_type": "motor" },
  "ClaimStatusResponse":  { "claim_type": "new_claim" },
  "ClaimsGroupingResponse": { "claims": [...] },
  "ExtractedClaim":        { ... },
  "VulnerabilityConfirmResponse": { ... },
  "ConflictResolutionResponse": { ... }
}
```

Use fixture mode for **integration tests** and local end-to-end pipeline runs.

---

## Fixture file locations

| Sample input                | Fixture file                                               |
| --------------------------- | ---------------------------------------------------------- |
| `motor_new_claim.eml`       | `tests/sample_data/mock_llm_responses_motor.json`          |
| `non_motor_new_claim.eml`   | `tests/sample_data/mock_llm_responses_non_motor.json`      |
| `vulnerable_customer.eml`   | `tests/sample_data/mock_llm_responses_vulnerable.json`     |
| `existing_claim_update.eml` | `tests/sample_data/mock_llm_responses_existing_claim.json` |
| `webform_submission.eml`    | `tests/sample_data/mock_llm_responses_webform_eml.json`    |
| `motor_new_claim.txt`       | `tests/sample_data/mock_llm_responses_motor_txt.json`      |
| `non_motor_new_claim.txt`   | `tests/sample_data/mock_llm_responses_non_motor_txt.json`  |
| `webform_submission.txt`    | `tests/sample_data/mock_llm_responses_webform_txt.json`    |

---

## Running with fixture

```bash
# Using make
make run INPUT=tests/sample_data/motor_new_claim.eml \
         FIXTURE=tests/sample_data/mock_llm_responses_motor.json

# Using Python directly
MOCK_LLM=true \
MOCK_LLM_FIXTURE=tests/sample_data/mock_llm_responses_motor.json \
PYTHONPATH=/Users/yourname/end \
python run.py --input tests/sample_data/motor_new_claim.eml --pretty
```

---

## Real (production) mode

Set the following env vars (no `MOCK_LLM`):

```bash
GCP_PROJECT_ID=your-project-id
GCP_LOCATION_ID=us-central1
GCP_GEMINI_MODEL=gemini-1.5-pro-002
# Authenticate: gcloud auth application-default login
```

---

## API reference

::: app_classify_extract_claim.services.llm_client
    options:
      show_source: true
      members:
        - LLMClient

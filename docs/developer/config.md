# Configuration & Environment Variables

**File:** `config/settings.py`

All configuration is supplied via environment variables or a `.env` file.
The `.env.example` file in the repo root shows every variable with its default.

---

## Environment variable reference

### GCP / Gemini

| Variable           | Type  | Default                | Description                  |
| ------------------ | ----- | ---------------------- | ---------------------------- |
| `GCP_PROJECT_ID`   | `str` | `"my-gcp-project"`     | GCP project ID for Vertex AI |
| `GCP_LOCATION_ID`  | `str` | `"us-central1"`        | Vertex AI region             |
| `GCP_GEMINI_MODEL` | `str` | `"gemini-1.5-pro-002"` | Model identifier             |

### Development / testing

| Variable           | Type   | Default   | Description                                             |
| ------------------ | ------ | --------- | ------------------------------------------------------- |
| `MOCK_LLM`         | `bool` | `false`   | If `true`, all LLM calls are mocked                     |
| `MOCK_LLM_FIXTURE` | `str`  | _(unset)_ | Path to a fixture JSON for deterministic mock responses |
| `LOG_LEVEL`        | `str`  | `"INFO"`  | Python logging level (DEBUG, INFO, WARNING, ERROR)      |

### Pipeline behaviour

| Variable                              | Type  | Default   | Description                                           |
| ------------------------------------- | ----- | --------- | ----------------------------------------------------- |
| `MAX_ATTACHMENT_SIZE_MB`              | `int` | `20`      | Maximum size of a single attachment                   |
| `MAX_EMAIL_SIZE_MB`                   | `int` | `50`      | Maximum total email size                              |
| `VULNERABILITY_LLM_CONFIRM_THRESHOLD` | `int` | `1`       | Min keyword hits before LLM confirmation is triggered |
| `HTTPS_PROXY`                         | `str` | _(unset)_ | Corporate proxy URL if GCP traffic must be proxied    |

### File paths

| Variable                     | Type   | Default                       | Description            |
| ---------------------------- | ------ | ----------------------------- | ---------------------- |
| `MOCK_POLICIES_PATH`         | `Path` | `data/mock_policies.json`     | Policy store location  |
| `LODGED_CLAIMS_PATH`         | `Path` | `data/lodged_claims.jsonl`    | Lodged claims output   |
| `EXCEPTIONS_PATH`            | `Path` | `data/exceptions_queue.jsonl` | Exception queue output |
| `VULNERABILITY_PHRASES_PATH` | `Path` | `data/vulnera_phrases.csv`    | Keyword phrase CSV     |

---

## `.env` file setup

```bash
# Copy the example and fill in real values
cp .env.example .env
```

```ini
# .env.example (safe to commit — no real values)
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION_ID=us-central1
GCP_GEMINI_MODEL=gemini-1.5-pro-002
MOCK_LLM=false
LOG_LEVEL=INFO
MAX_ATTACHMENT_SIZE_MB=20
MAX_EMAIL_SIZE_MB=50
VULNERABILITY_LLM_CONFIRM_THRESHOLD=1
```

!!! warning
    Never commit `.env` — it is gitignored. Only `.env.example` belongs in version control.

---

## Settings singleton

`get_settings()` returns a cached `Settings` instance. In tests, override with:

```python
from unittest.mock import patch
from app_classify_extract_claim.config.settings import Settings

mock_settings = Settings(
    gcp_project_id="test",
    mock_llm=True,
    vulnerability_phrases_path=Path("data/vulnera_phrases.csv"),
    ...
)

with patch("app_classify_extract_claim.graph.nodes.my_node.get_settings",
           return_value=mock_settings):
    result = await my_node(state)
```

---

## API reference

::: app_classify_extract_claim.config.settings
    options:
      show_source: false
      members:
        - Settings
        - get_settings

# Insurance Claims Pipeline (v1.2)

End-to-end agentic AI pipeline that processes insurance claim emails through a LangGraph state machine, classifies them, extracts structured data, validates against policy records, and lodges the claim.

---

## Pipeline Architecture

```
START
  └─► vulnerability_check
        └─► classify_email
              └─► classify
                    ├─► exception_handler  (existing claim / error)
                    └─► extract_data
                          └─► verify
                                ├─► exception_handler  (validation FAIL)
                                └─► policy_retrieval
                                      └─► enrich
                                            └─► check_fields
                                                  ├─► exception_handler  (missing fields)
                                                  └─► lodge
                                                        ├─► exception_handler  (lodge FAILED)
                                                        └─► END
```

### Node Responsibilities

| Node                  | Responsibility                                                                              |
| --------------------- | ------------------------------------------------------------------------------------------- |
| `vulnerability_check` | Two-stage keyword scan + LLM confirmation; flags vulnerable customers                       |
| `classify_email`      | Determines email type: `freetext`, `webform`, or `form`                                     |
| `classify`            | Parallel LLM calls: insurance type, claim status, multi-claim grouping                      |
| `extract_data`        | Structured extraction; two-stage for forms, single-pass otherwise; conflict resolution pass |
| `verify`              | Pydantic re-validation + date/policy/phone/email rules                                      |
| `policy_retrieval`    | Matches claim to mock policy store (exact or fuzzy name)                                    |
| `enrich`              | Fills null extracted fields from matched policy record                                      |
| `check_fields`        | Gates on mandatory fields (motor vs non-motor rules)                                        |
| `lodge`               | Writes to `lodged_claims.jsonl`; assigns `GIO-XXXXXXXX` reference                           |
| `exception_handler`   | Captures full state to `exceptions_queue.jsonl`                                             |

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
# For development / testing:
pip install -r requirements-dev.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set GCP_PROJECT_ID (and optionally HTTPS_PROXY)
```

---

## Running the API (FastAPI)

### Docker Compose — full local stack (API + UI + Redpanda)

```bash
# From inside app_classify_extract_claim/ (your normal working directory)
make docker-up

# Or directly:
docker compose -f docker/docker-compose.yml up --build
```

| Service                   | URL                        |
| ------------------------- | -------------------------- |
| Streamlit Inbox Simulator | http://localhost:8501      |
| FastAPI (Swagger docs)    | http://localhost:8000/docs |
| Redpanda Console          | http://localhost:8080      |

### API only (without Docker Compose)

```bash
# Install deps first
pip install -r requirements.txt

# Start API (Kafka consumer disabled — no Redpanda needed)
KAFKA_CONSUMER_ENABLED=false uvicorn app_classify_extract_claim.api.main:app --reload --port 8000
```

### Send a test email via the API

```bash
curl -X POST http://localhost:8000/process-email \
     -F "email_file=@path/to/email.eml"
```

---

### Locally (mock mode — no GCP calls)

```bash
MOCK_LLM=true python app_classify_extract_claim/run.py --input path/to/email.eml --pretty
```

### Locally (real Gemini)

```bash
# Ensure Application Default Credentials are set:
gcloud auth application-default login

python app_classify_extract_claim/run.py --input path/to/email.eml --pretty
```

### Supported input formats

| Format | Notes                                                        |
| ------ | ------------------------------------------------------------ |
| `.eml` | Full RFC 2822 email; attachments are extracted automatically |
| `.txt` | Plain-text email body; no attachment parsing                 |

Attachments supported: PDF, DOCX, PNG/JPG/GIF/WEBP images (Gemini multimodal).

---

## Running Tests

```bash
# Unit + integration tests (mock LLM — no GCP required)
MOCK_LLM=true pytest tests/ -v

# Fixture-based end-to-end tests (motor / non-motor / webform .eml files)
MOCK_LLM=true pytest tests/test_graph/test_fixture_emails.py -v

# With coverage
MOCK_LLM=true pytest tests/ --cov=. --cov-report=term-missing
```

---

## Output files

| File                          | Contents                                              |
| ----------------------------- | ----------------------------------------------------- |
| `data/lodged_claims.jsonl`    | One JSON record per successfully lodged claim         |
| `data/exceptions_queue.jsonl` | One JSON record per claim routed to exception handler |

---

## Project Structure

```
app_classify_extract_claim/
├── config/
│   └── settings.py          # Pydantic Settings (loaded from .env)
├── data/
│   ├── mock_policies.json   # Local policy store (v1.x)
│   └── vulnera_phrases.csv  # Vulnerability keyword list
├── graph/
│   ├── builder.py           # StateGraph construction + compilation
│   ├── state.py             # GraphState TypedDict + initial_state()
│   └── nodes/
│       ├── vulnerability_check.py
│       ├── classify_email.py
│       ├── classify.py
│       ├── extract_data.py
│       ├── verify.py
│       ├── policy_retrieval.py
│       ├── enrich.py
│       ├── check_fields.py
│       ├── lodge.py
│       └── exception_handler.py
├── prompts/                 # LLM prompt builders
├── schemas/                 # Pydantic models
├── services/
│   ├── file_parser.py       # .eml / .txt / PDF / DOCX / image parsing
│   ├── llm_client.py        # ChatVertexAI wrapper
│   └── vulnerability_scanner.py
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── test_nodes/          # Unit tests per node
│   └── test_graph/          # Integration tests
├── run.py                   # CLI entry point
├── requirements.txt
└── requirements-dev.txt
```

---

## Roadmap

| Version  | Scope                                                                                      |
| -------- | ------------------------------------------------------------------------------------------ |
| v1.0     | Core LangGraph pipeline, Gemini LLM, local JSONL outputs                                   |
| v1.1     | Mock policy store, full lodge/enrich, conflict resolution, fixture-based integration tests |
| **v1.2** | **FastAPI REST API + Redpanda (Kafka) event triggers + Streamlit UI** ✓                    |
| v1.3     | SQLite job persistence, `GET /status/{job_id}` polling, multi-claim fan-out stub           |
| v2.0     | Real policy API, cloud Pub/Sub, Cloud Run, Secret Manager                                  |
| v2.1     | OpenCV image pre-processing, full observability, active learning                           |

# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

> Pending changes that have not yet been released.

---

## [1.2.0] — 2026-03-13

### Added

- **`config/settings.py`** — new fields: `api_port`, `kafka_bootstrap_servers`,
  `kafka_topic_inbox`, `kafka_consumer_group_id`, `kafka_consumer_enabled`,
  `broker_type` (`kafka` | `pubsub`)
- **`services/kafka_producer.py`** — `KafkaEmailProducer` class; publishes
  file-drop events (`email_id`, `inbox_path`, `filename`) to the Kafka inbox
  topic using `confluent-kafka`; `build_email_id()` UUID helper
- **`services/kafka_consumer.py`** — background daemon thread that polls
  `claims.email.inbox`, runs the LangGraph pipeline via `asyncio.run()` for
  each message, commits offset on success, cleans up temp files
- **`api/`** — FastAPI application package:
  - `api/main.py` — `create_app()` factory; `@asynccontextmanager` lifespan
    starts/stops Kafka consumer thread; CORS + `RequestIdMiddleware`
  - `api/middleware.py` — `RequestIdMiddleware` injects `X-Request-ID` header
  - `api/routes/health.py` — `GET /health` liveness probe
  - `api/routes/process_email.py` — `POST /process-email` multipart upload;
    saves to temp dir, calls `parse_input` + `get_graph().ainvoke`, returns
    `ProcessEmailResponse` (claim_reference, lodge_status, insurance_type,
    vulnerability_flag, error_reason)
- **`ui/streamlit_app.py`** — 3-column Inbox Simulator UI:
  - Left: `st.file_uploader` drop zone, Submit button → `POST /process-email`
  - Centre: pipeline step progress indicator
  - Right: structured result JSON, vulnerability badge, exception record view
  - Sidebar: API connectivity badge, links to Redpanda Console and API docs
  - Bottom: recent lodged claims expander
- **`docker/Dockerfile.api`** — `python:3.11-slim` image for the FastAPI service;
  `HEALTHCHECK` via `urllib.request`
- **`docker/Dockerfile.ui`** — `python:3.11-slim` image for the Streamlit UI;
  `HEALTHCHECK` via `_stcore/health`
- **`docker/docker-compose.yml`** — four-service stack: `redpanda`,
  `redpanda-console`, `api`, `ui`; shared `data/` volume mount; `redpanda-setup`
  init container creates `claims.email.inbox` topic
- **`tests/test_api/`** — 8 new FastAPI endpoint tests:
  - `test_health.py` (3 tests) — `GET /health` returns 200, `status: ok`, version
  - `test_process_email.py` (5 tests) — success path, email_id present, pipeline
    called once, missing file → 422, oversized file → 413
  - `tests/test_api/conftest.py` — `async_client` fixture with
    `KAFKA_CONSUMER_ENABLED=false` to skip broker connection in tests
- **`requirements.txt`** — added: `fastapi`, `uvicorn[standard]`,
  `python-multipart`, `confluent-kafka`, `streamlit`, `watchdog`
- **`requirements-dev.txt`** — added: `httpx`

### Changed

- `pyproject.toml` — `[project.dependencies]` updated to include all v1.2
  packages; `[project.optional-dependencies.dev]` adds `httpx`
- `.env.example` — added `API_PORT`, `KAFKA_BOOTSTRAP_SERVERS`,
  `KAFKA_TOPIC_INBOX`, `KAFKA_CONSUMER_GROUP_ID`, `KAFKA_CONSUMER_ENABLED`,
  `BROKER_TYPE`
- `README.md` — v1.2 marked complete in roadmap table

---

## [1.1.0] — 2026-03-12

### Added

- **Conflict resolution pass** in `extract_data` node — after primary extraction, when
  `conflict_metadata` is non-empty the LLM is re-invoked with `ConflictResolutionResponse`
  to determine whether conflicting values (e.g. `ABC123` vs `ABC-123`) are semantically
  equivalent and consolidate to a canonical form
- **`_apply_canonical()` helper** — writes resolved canonical values into the extracted dict
  via dot-path (e.g. `vehicle_information.vehicle_registration`)
- **Fixture-based integration tests** (`tests/test_graph/test_fixture_emails.py`) — three
  full end-to-end pipeline runs over real `.eml` files with mock-LLM fixture responses:
  - `motor_new_claim.eml` → assert `lodge_status == SUCCESS`, `insurance_type == motor`
  - `non_motor_new_claim.eml` → assert `lodge_status == SUCCESS`, `insurance_type == non-motor`
  - `webform_submission.eml` → assert `lodge_status == SUCCESS`, `insurance_type == motor`
- Settings cache reset (`_settings = None`) in fixture-env pytest fixture ensures each
  integration test receives a freshly-built `Settings` from the monkeypatched environment

### Changed

- `README.md` heading updated to v1.1; roadmap corrected to reflect actual version scope
- `tests/test_graph/test_fixture_emails.py` fixture isolation improved with
  `monkeypatch.setattr(_settings_mod, "_settings", None)`

---

## [1.0.0] — 2025-01-01

### Added

- **10-node LangGraph pipeline** for end-to-end insurance claims processing:
  - `vulnerability_check` — flags vulnerable customers via keyword and LLM confirmation
  - `classify_email` — determines email type (new claim, update, enquiry, other)
  - `classify` — determines insurance type (motor, non-motor) and claim status (new/existing)
  - `extract_data` — extracts structured claim fields from free-form email/webform text
  - `verify` — resolves conflicts between extracted fields and LLM-provided values
  - `policy_retrieval` — looks up matched policy from `data/mock_policies.json`
  - `enrich` — merges extracted claim with policy details
  - `check_fields` — validates all mandatory fields are populated
  - `lodge` — persists claim to `data/lodged_claims.jsonl`, generates `GIO-XXXXXXXX` reference
  - `exception_handler` — routes unresolvable claims to `data/exceptions_queue.jsonl`
- **LangGraph `StateGraph`** with conditional routing between nodes
- **LangChain `ChatVertexAI`** integration for Gemini multimodal LLM via GCP Vertex AI
- **Pydantic v2 schemas** for all structured LLM outputs (`schemas/`)
- **Mock LLM mode** (`MOCK_LLM=true`) with optional fixture injection (`MOCK_LLM_FIXTURE=path`)
- **8 sample input files** (`.eml` and `.txt`) under `tests/sample_data/`
- **8 LLM fixture files** for fully deterministic offline pipeline runs
- **`run.py` CLI** — `--input`, `--pretty`, `--fixture` flags for local execution
- **`Makefile`** with `install`, `lint`, `format`, `typecheck`, `test`, `run`, `all` targets
- **`pyproject.toml`** — unified tool configuration (ruff, mypy, pytest, coverage, setuptools)
- **`.pre-commit-config.yaml`** — ruff, ruff-format, hygiene hooks, detect-secrets
- **`CONTRIBUTING.md`** — env setup, fixture table, branching conventions, PR checklist
- **`.github/workflows/ci.yml`** — lint → type-check → test pipeline on push/PR
- **GIO / AMI branding** throughout (no CGU or WFI references)

### Changed

- N/A — initial release

### Deprecated

- N/A

### Removed

- N/A

### Fixed

- N/A

### Security

- `.gitignore` excludes `.env`, `service_account*.json`, `*.pem`, and lodged-claim data files

---

[Unreleased]: https://github.com/IAGvk/app_classify_extract_claim/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/IAGvk/app_classify_extract_claim/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/IAGvk/app_classify_extract_claim/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/IAGvk/app_classify_extract_claim/releases/tag/v1.0.0

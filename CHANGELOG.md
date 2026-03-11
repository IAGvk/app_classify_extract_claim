# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

> Pending changes that have not yet been released.

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

[Unreleased]: https://github.com/IAGvk/app_classify_extract_claim/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/IAGvk/app_classify_extract_claim/releases/tag/v1.0.0

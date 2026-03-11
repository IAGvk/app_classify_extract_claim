# Developer Documentation

Welcome to the technical documentation for the **Claims Processing Pipeline** (v1.0.0).

This section is intended for engineers working on, extending, or operating the pipeline.
It covers every layer of the system from high-level architecture down to individual file responsibilities.

---

## Quick-start

```bash
# 1. Clone and enter the workspace
git clone https://github.com/IAGvk/lg_practice.git
cd lg_practice

# 2. Create and activate a virtual env from the parent directory
python -m venv .venv && source .venv/bin/activate

# 3. Install the project in editable mode + dev extras
cd app_classify_extract_claim
pip install -r requirements.txt -r requirements-dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Run the full test suite (mock LLM, no GCP credentials needed)
make test

# 6. Run the pipeline end-to-end (mock, no GCP needed)
make run

# 7. Serve the docs locally
pip install -r requirements-docs.txt
mkdocs serve
```

---

## Repository layout

```
app_classify_extract_claim/          ← git root & Python package root
├── config/
│   └── settings.py                  ← pydantic-settings, all env vars
├── data/
│   ├── mock_policies.json           ← 15 sample policies (dev/test only)
│   ├── lodged_claims.jsonl          ← runtime output (gitignored)
│   ├── exceptions_queue.jsonl       ← runtime output (gitignored)
│   └── vulnera_phrases.csv          ← keyword phrase list for Stage 1 scan
├── docs/                            ← MkDocs source (this site)
├── graph/
│   ├── builder.py                   ← StateGraph factory + conditional edges
│   ├── state.py                     ← GraphState TypedDict definition
│   └── nodes/                       ← one file per pipeline node (10 total)
├── prompts/                         ← prompt-builder functions (per LLM call)
├── schemas/
│   └── claim_data.py                ← all Pydantic v2 models
├── services/
│   ├── llm_client.py                ← LLM abstraction (real + mock)
│   ├── file_parser.py               ← email/attachment ingestion
│   └── vulnerability_scanner.py    ← keyword scan + score
├── tests/
│   ├── conftest.py                  ← shared fixtures (states, mock settings)
│   ├── test_integration.py         ← end-to-end pipeline tests
│   ├── test_nodes/                  ← unit test per node (10 files)
│   └── sample_data/                 ← 8 input files + 8 LLM fixture JSONs
├── run.py                           ← CLI entry point
├── pyproject.toml                   ← unified tool config
├── Makefile                         ← dev workflow shortcuts
└── mkdocs.yml                       ← documentation site config
```

---

## Navigation guide

| Section                                               | Best for                                            |
| ----------------------------------------------------- | --------------------------------------------------- |
| [Architecture → HLD](architecture/hld.md)             | System context, component overview, deployment      |
| [Architecture → LLD](architecture/lld.md)             | Class diagrams, module responsibilities, interfaces |
| [Architecture → Data Flow](architecture/data_flow.md) | State machine, field-by-field transformation trace  |
| [Architecture → ADRs](architecture/decisions.md)      | *Why* key technical choices were made               |
| [Pipeline Nodes](nodes/index.md)                      | Per-node inputs, outputs, edge routing, prompts     |
| [Services](services/llm_client.md)                    | LLM client internals, mock mode, fixture loading    |
| [Schemas](schemas.md)                                 | All Pydantic models, field contracts                |
| [Config](config.md)                                   | Every environment variable, defaults, validation    |
| [Testing](testing.md)                                 | Running tests, fixtures, coverage targets           |

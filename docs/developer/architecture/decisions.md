# Architecture Decision Records

Each ADR answers: *what was decided, why, and what alternatives were considered.*

---

## ADR-001 — LangGraph as pipeline orchestrator

**Status:** Accepted | **Date:** 2025-01

### Context

The pipeline requires stateful sequential execution with conditional branching
(e.g. skip to exception handling if an existing claim is detected mid-pipeline).
Alternatives included plain `asyncio` coroutine chaining, Prefect/Airflow, and
a simple hand-written state machine.

### Decision

Use **LangGraph `StateGraph`** as the orchestrator.

### Rationale

| Criterion            | LangGraph       | Plain asyncio         | Prefect/Airflow    |
| -------------------- | --------------- | --------------------- | ------------------ |
| Conditional edges    | Native support  | Manual `if/else`      | Possible but heavy |
| State passing        | Automatic merge | Manual dict threading | Task context       |
| Visual graph         | Built-in        | None                  | Dashboard          |
| LLM-native           | Yes             | No                    | No                 |
| Operational overhead | None (library)  | None                  | Significant        |

LangGraph's `add_conditional_edges` cleanly models the four branching points
without boilerplate, and its `StateGraph` pattern enforces the immutable-update
contract that makes nodes testable in isolation.

---

## ADR-002 — Google Gemini via LangChain `ChatVertexAI`

**Status:** Accepted | **Date:** 2025-01

### Context

The pipeline needs a multimodal LLM capable of reading email text, PDF attachments,
and images (photographs of damage). Enterprise GCP auth (Workload Identity / ADC)
is a hard requirement.

### Decision

Use `langchain-google-vertexai` with `ChatVertexAI(model="gemini-1.5-pro-002")`.

### Rationale

- **Multimodal natively** — Gemini 1.5 Pro handles text, PDF, and image inputs in one call
- **Structured output** — LangChain's `.with_structured_output(schema)` wraps Gemini's
  function-calling mode, returning validated Pydantic objects directly
- **GCP-native auth** — no API key management; ADC works in Cloud Run, GKE, and local dev
- **`api_transport="rest"`** — avoids gRPC dependency conflicts in containerised environments

### Alternatives considered

- OpenAI GPT-4o: Strong, but requires API key management and data residency review
- Anthropic Claude: No native Vertex AI deployment in target region at decision time

---

## ADR-003 — Pydantic v2 for all schemas

**Status:** Accepted | **Date:** 2025-01

### Context

LLM outputs are inherently unreliable. Every structured response must be validated
before it flows into downstream nodes.

### Decision

All LLM input/output schemas use **Pydantic v2 `BaseModel`**.

### Rationale

- `model_validate()` raises `ValidationError` on bad LLM output, never silently passing `None`
- `model_dump()` provides a stable dict serialisation for state storage
- LangChain's `.with_structured_output()` natively accepts Pydantic classes
- v2 is 5–50× faster than v1 for validation-heavy workloads
- `Field(default_factory=...)` ensures empty sub-objects never cause `AttributeError`

---

## ADR-004 — `MOCK_LLM` + fixture system for testing

**Status:** Accepted | **Date:** 2025-01

### Context

Running pytest against the real Gemini API would require:
1. Live GCP credentials in CI
2. Network access
3. Non-deterministic responses
4. Non-zero API cost per test run

### Decision

Implement a two-tier mock system:

1. `MOCK_LLM=true` → `_mock_structured()` returns a minimal valid instance built from schema defaults
2. `MOCK_LLM_FIXTURE=path/to/fixture.json` → responses loaded from JSON keyed by `schema.__name__`

### Rationale

- Tier 1 (blank mock) requires zero setup — all tests can run offline with no fixture
- Tier 2 (fixture) allows testing realistic end-to-end flows without touching GCP
- Fixtures are committed to the repo (`tests/sample_data/mock_llm_responses_*.json`),
  making the tested scenarios reproducible and reviewable in PRs
- The `schema.__name__` key lookup is simple and avoids complex registration patterns

### Trade-offs

- Fixture files must be kept in sync with schema changes — a schema rename or field addition
  requires updating the relevant fixture file
- `_mock_structured()` blank-mode returns empty lists (`[]`) for list fields, which may
  not represent realistic outputs; fixture mode should be preferred for integration tests

---

## ADR-005 — Single `GraphState` TypedDict with `total=False`

**Status:** Accepted | **Date:** 2025-01

### Context

LangGraph requires a state type. Options: `TypedDict`, `dataclass`, Pydantic model.

### Decision

Use `TypedDict` with `total=False`.

### Rationale

- `total=False` means every field is optional — early nodes (e.g. `vulnerability_check`)
  can safely return without setting fields that later nodes own
- LangGraph performs dict-merge updates natively, which works directly with `TypedDict`
- Pydantic model state would require `.model_copy(update=...)` on every node return,
  adding verbosity with no meaningful benefit at this stage
- `initial_state()` provides full defaults, so `state.get("field", default)` is still safe

---

## ADR-006 — Ruff as primary linter/formatter

**Status:** Accepted | **Date:** 2025-01

### Context

The project previously used flake8, isort, and black as separate tools.

### Decision

Replace all three with **ruff**, configured in `pyproject.toml`.

### Rationale

- Single tool to install and configure
- 10–100× faster than the equivalent flake8 + isort + black chain
- Compatible rule set — imports E, W, F (flake8), I (isort), B (bugbear), UP (pyupgrade)
- Native VS Code extension (`charliermarsh.ruff`) with auto-fix on save

---

## ADR-007 — Append-only JSONL for persistent storage

**Status:** Accepted | **Date:** 2025-01

### Context

The pipeline needs to persist lodged claims and exception records. Options:
SQLite, PostgreSQL, flat JSON file, JSONL.

### Decision

Use **append-only JSONL** files (`lodged_claims.jsonl`, `exceptions_queue.jsonl`).

### Rationale

- **Zero dependencies** — no database driver, migration tooling, or connection pooling
- **Audit-friendly** — append-only means records are never overwritten; full history is preserved
- **CMS-ready** — a future consumer can tail the JSONL file or Kafka topic and import records
- **Gitignored** — runtime data never enters source control

### Trade-offs

- Not queryable without loading into memory or a tool like DuckDB
- No transaction isolation — concurrent writers would need file locking (acceptable for v1.0 single-process model)
- Production replacement: swap `lodge.py` I/O for a database write or Kafka produce; node interface is unchanged

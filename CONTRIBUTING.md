# Contributing

## Environment setup

```bash
# 1. Create a virtual environment from the *parent* directory
cd /path/to/parent           # one level above this repo
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
cd app_classify_extract_claim
pip install -r requirements.txt -r requirements-dev.txt
pip install ruff mypy pre-commit

# 3. Install pre-commit hooks
pre-commit install
```

> **PYTHONPATH note:** The package root lives one directory above this repo.
> All `make` targets set `PYTHONPATH` automatically.
> For direct `python` invocations use: `PYTHONPATH=.. python run.py ...`

---

## Running locally (no GCP)

```bash
# Blank mock — pipeline runs with all-empty LLM responses
make run-plain INPUT=tests/sample_data/motor_new_claim.eml

# Realistic fixture — happy path all the way to lodge
make run INPUT=tests/sample_data/motor_new_claim.eml \
         FIXTURE=tests/sample_data/mock_llm_responses_motor.json
```

Available fixture files in `tests/sample_data/`:

| Fixture                                  | Input                       | Expected outcome          |
| ---------------------------------------- | --------------------------- | ------------------------- |
| `mock_llm_responses_motor.json`          | `motor_new_claim.eml`       | `lodge=SUCCESS`           |
| `mock_llm_responses_non_motor.json`      | `non_motor_new_claim.eml`   | `lodge=SUCCESS`           |
| `mock_llm_responses_vulnerable.json`     | `vulnerable_customer.eml`   | `lodge=SUCCESS vuln=True` |
| `mock_llm_responses_existing_claim.json` | `existing_claim_update.eml` | `exception_handler`       |
| `mock_llm_responses_webform_eml.json`    | `webform_submission.eml`    | `lodge=SUCCESS`           |
| `mock_llm_responses_motor_txt.json`      | `motor_new_claim.txt`       | `lodge=SUCCESS`           |
| `mock_llm_responses_non_motor_txt.json`  | `non_motor_new_claim.txt`   | `lodge=SUCCESS`           |
| `mock_llm_responses_webform_txt.json`    | `webform_submission.txt`    | `lodge=SUCCESS`           |

---

## Tests

```bash
make test          # full suite, mock LLM
make test-cov      # with coverage (opens htmlcov/index.html)
make test-fast     # stop on first failure (-x)
```

All tests must pass before raising a PR. Coverage target: **≥ 60 %** (configured in `pyproject.toml`).

---

## Code quality

```bash
make lint          # ruff lint check (no side-effects)
make format        # ruff auto-format + fix
make typecheck     # mypy strict check over source (excludes tests/)
make pylint        # pylint check
make all           # format-check + lint + typecheck + test
```

Pre-commit runs `ruff` automatically on every `git commit`. Fix issues with `make format`.

---

## Pipeline architecture

```
vulnerability_check → classify_email → classify → extract_data
  → verify → policy_retrieval → enrich → check_fields → lodge
  (any node exception) → exception_handler → END
```

See `graph/builder.py` for routing logic and conditional edges.

---

## Adding a new node

1. Create `graph/nodes/your_node.py` — async function `your_node(state: GraphState) -> dict`
2. Register in `graph/builder.py` (`build_graph()`)
3. Add conditional edge or linear edge as appropriate
4. Add tests in `tests/test_nodes/test_your_node.py` — mock `LLMClient.from_settings`
5. Update `graph/state.py` if new state fields are required

---

## Branching and PR conventions

| Branch prefix | Purpose                          |
| ------------- | -------------------------------- |
| `feat/`       | New feature                      |
| `fix/`        | Bug fix                          |
| `refactor/`   | Non-functional code change       |
| `test/`       | Test additions / fixes           |
| `chore/`      | Dependency bumps, config changes |

PR checklist:
- [ ] `make all` passes locally
- [ ] New tests cover the change (happy path + at least one edge case)
- [ ] Docstring on every new public function / class
- [ ] No hardcoded credentials or policy numbers in source code
- [ ] `CHANGELOG.md` entry (if user-facing change)

# ── Claims Pipeline — Developer Makefile ──────────────────────────────────────
#
# Usage:
#   make install        Install runtime + dev dependencies
#   make lint           Run ruff (lint + format check)
#   make format         Auto-format with ruff
#   make typecheck      Run mypy
#   make test           Run test suite (MOCK_LLM=true, no GCP calls)
#   make test-cov       Run tests with coverage report
#   make run INPUT=...  Run the pipeline on a file
#   make run-api        Start the FastAPI server (no Docker)
#   make docker-up      Build and start the full Docker Compose stack
#   make docker-down    Stop and remove the Docker Compose stack
#   make docker-logs    Tail logs from the Docker Compose stack
#   make docs           Serve docs locally (http://127.0.0.1:8000)
#   make docs-build     Build static docs site to ./site/
#   make docs-deploy    Deploy docs to GitHub Pages
#   make clean          Remove build artefacts and caches
#   make all            lint + typecheck + test
#
# Prerequisites:  Python ≥ 3.11, source ../.venv/bin/activate
#                 or set PYTHON to your preferred interpreter.

PYTHON     ?= python
PIP        ?= pip
REPO_ROOT  := $(shell git rev-parse --show-toplevel)
PARENT_DIR := $(shell dirname $(REPO_ROOT))
SRC        := .
TESTS      := tests

# Pipeline defaults
INPUT      ?= tests/sample_data/motor_new_claim.eml
FIXTURE    ?= tests/sample_data/mock_llm_responses_motor.json

.DEFAULT_GOAL := help

# ── Help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  Claims Pipeline — available targets"
	@echo ""
	@echo "  make install          Install all dependencies (runtime + dev)"
	@echo "  make lint             Ruff lint check (no auto-fix)"
	@echo "  make format           Ruff auto-format + fix"
	@echo "  make typecheck        Mypy type check"
	@echo "  make pylint           Pylint check"
	@echo "  make test             Unit tests (mock LLM, no GCP)"
	@echo "  make test-cov         Unit tests with HTML coverage report"
	@echo "  make run              Run pipeline on INPUT with FIXTURE"
	@echo "  make run-plain        Run pipeline on INPUT (blank mock LLM)"  @echo "  make run-api          Start FastAPI server (no Docker, consumer disabled)"
  @echo "  make docker-up        Build + start full Docker Compose stack"
  @echo "  make docker-down      Stop + remove Docker Compose stack"
  @echo "  make docker-logs      Tail logs from Docker Compose stack"	@echo "  make docs             Serve docs locally (http://127.0.0.1:8000)"
	@echo "  make docs-build       Build static docs site to ./site/"
	@echo "  make docs-deploy      Deploy docs to GitHub Pages"
	@echo "  make clean            Remove caches and build artefacts"
	@echo "  make all              lint + typecheck + test"
	@echo ""
	@echo "  Variables:"
	@echo "    INPUT=$(INPUT)"
	@echo "    FIXTURE=$(FIXTURE)"
	@echo ""

# ── Install ───────────────────────────────────────────────────────────────────
.PHONY: install
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

.PHONY: install-dev
install-dev: install
	$(PIP) install ruff mypy types-Pillow pre-commit
	pre-commit install

.PHONY: install-docs
install-docs:
	$(PIP) install -r requirements-docs.txt

# ── Lint & format ─────────────────────────────────────────────────────────────
.PHONY: lint
lint:
	ruff check $(SRC)

.PHONY: format
format:
	ruff format $(SRC)
	ruff check --fix $(SRC)

.PHONY: format-check
format-check:
	ruff format --check $(SRC)

# ── Type checking ─────────────────────────────────────────────────────────────
.PHONY: typecheck
typecheck:
	PYTHONPATH=$(PARENT_DIR) mypy $(SRC) \
	    --exclude 'tests/' \
	    --exclude 'data/'

# ── Pylint ────────────────────────────────────────────────────────────────────
.PHONY: pylint
pylint:
	PYTHONPATH=$(PARENT_DIR) pylint $(SRC) \
	    --ignore=tests,data,__pycache__

# ── Tests ─────────────────────────────────────────────────────────────────────
.PHONY: test
test:
	MOCK_LLM=true PYTHONPATH=$(PARENT_DIR) \
	    $(PYTHON) -m pytest $(TESTS) -v

.PHONY: test-cov
test-cov:
	MOCK_LLM=true PYTHONPATH=$(PARENT_DIR) \
	    $(PYTHON) -m pytest $(TESTS) \
	    --cov=$(SRC) \
	    --cov-report=term-missing \
	    --cov-report=html:htmlcov \
	    -v
	@echo "\nCoverage report: htmlcov/index.html"

.PHONY: test-fast
test-fast:
	MOCK_LLM=true PYTHONPATH=$(PARENT_DIR) \
	    $(PYTHON) -m pytest $(TESTS) -x -q

# ── Pipeline run ──────────────────────────────────────────────────────────────
.PHONY: run
run:
	MOCK_LLM=true \
	MOCK_LLM_FIXTURE=$(FIXTURE) \
	PYTHONPATH=$(PARENT_DIR) \
	    $(PYTHON) run.py --input $(INPUT) --pretty

.PHONY: run-plain
run-plain:
	MOCK_LLM=true \
	PYTHONPATH=$(PARENT_DIR) \
	    $(PYTHON) run.py --input $(INPUT) --pretty

# ── API server ────────────────────────────────────────────────────────────────
.PHONY: run-api
run-api:
	KAFKA_CONSUMER_ENABLED=false \
	PYTHONPATH=$(PARENT_DIR) \
	    uvicorn app_classify_extract_claim.api.main:app \
	        --reload --port 8000

# ── Docker Compose ────────────────────────────────────────────────────────────
DOCKER_COMPOSE := docker compose -f docker/docker-compose.yml

.PHONY: docker-up
docker-up:
	$(DOCKER_COMPOSE) up --build

.PHONY: docker-up-detach
docker-up-detach:
	$(DOCKER_COMPOSE) up --build -d

.PHONY: docker-down
docker-down:
	$(DOCKER_COMPOSE) down

.PHONY: docker-logs
docker-logs:
	$(DOCKER_COMPOSE) logs -f

# ── Documentation ────────────────────────────────────────────────────────────
.PHONY: docs
docs:
	mkdocs serve

.PHONY: docs-build
docs-build:
	mkdocs build --strict

.PHONY: docs-deploy
docs-deploy:
	mkdocs gh-deploy --force

# ── Clean ─────────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc'       -delete 2>/dev/null || true
	find . -type f -name '*.pyo'       -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	rm -rf build dist *.egg-info site

# ── All ───────────────────────────────────────────────────────────────────────
.PHONY: all
all: format-check lint typecheck test

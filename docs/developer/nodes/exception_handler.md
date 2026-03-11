# exception_handler

**File:** `graph/nodes/exception_handler.py`  
**Position:** Node 10 (terminal)  
**LLM calls:** 0  
**Branches:** Always → `END`

---

## Purpose

Act as the catch-all terminal node for any claim that cannot be automatically
processed. It records the full context of the failure to the exception queue
so that human reviewers have all necessary information.

---

## When is exception_handler reached?

| Trigger                       | Reason                                  |
| ----------------------------- | --------------------------------------- |
| `classify` → `existing_claim` | Updates require manual merge            |
| `verify` → `FAIL`             | Logical inconsistency in extracted data |
| `check_fields` → incomplete   | One or more mandatory fields missing    |
| `lodge` → `FAILED`            | Persistence error                       |
| Any node sets `error_node`    | Unexpected exception in pipeline        |

---

## Exception record structure

```json
{
  "email_id": "motor_new_claim.eml",
  "error_reason": "Existing claim — routed to manual review",
  "error_node": "classify",
  "exception_at": "2025-01-15T10:23:45.123456Z",
  "pipeline_version": "1.0.0",
  "state_snapshot": {
    "insurance_type": "motor",
    "claim_status": "existing_claim",
    "vulnerability_flag": false,
    ...
  }
}
```

The full state snapshot is included so reviewers have complete context
without needing to re-run the pipeline.

---

## State contract

|            | Field              | Type           | Description                 |
| ---------- | ------------------ | -------------- | --------------------------- |
| **Reads**  | `error_reason`     | `str \| None`  | Why routing reached here    |
| **Reads**  | `error_node`       | `str \| None`  | Which node triggered it     |
| **Reads**  | `email_id`         | `str`          | Source message identifier   |
| **Reads**  | _(entire state)_   | `GraphState`   | Included in the snapshot    |
| **Writes** | `exception_record` | `dict \| None` | Full exception record dict  |
| **Writes** | `error_reason`     | `str`          | Normalised and standardised |
| **Writes** | `completed`        | `bool`         | Always set to `True`        |

---

## Human review workflow

The exception queue at `data/exceptions_queue.jsonl` is an append-only JSONL file.
The intended consumer is a human review dashboard or a Kafka consumer
that routes records to a case management tool.

Each record is self-contained — a human reviewer needs:
1. `error_reason` — quick triage label
2. `email_id` — to retrieve the original message
3. `state_snapshot` — all extracted data at the point of failure

---

## API reference

::: app_classify_extract_claim.graph.nodes.exception_handler
    options:
      show_source: true
      members:
        - exception_handler

# verify

**File:** `graph/nodes/verify.py`  
**Position:** Node 5  
**LLM calls:** 0 (rule-based)  
**Branches:** → `exception_handler` if `verification_result == "FAIL"`

---

## Purpose

Apply a set of deterministic rules to the extracted claim to catch logical
inconsistencies **before** any policy lookup or lodgement. This prevents
bad data from propagating further into the pipeline.

---

## Verification rules

| Rule                                        | Severity | Detail                      |
| ------------------------------------------- | -------- | --------------------------- |
| `extracted_claim` is `None`                 | **FAIL** | Extraction produced nothing |
| `date_of_loss` is in the future             | **FAIL** | Impossible incident date    |
| `date_of_loss` > 365 days in the past       | **WARN** | Potentially stale claim     |
| `date_of_loss` is missing                   | **WARN** | Missing but not blocking    |
| `policy_number` prefix ≠ `"GIO"` or `"AMI"` | **WARN** | Unexpected brand            |
| `vulnerability_flag is True`                | **WARN** | Flag for human attention    |

### Result escalation

- Any **FAIL** rule → `verification_result = "FAIL"` → routes to `exception_handler`
- Any **WARN** rule (no FAIL) → `verification_result = "WARN"` → continues pipeline
- All rules pass → `verification_result = "PASS"`

---

## State contract

|            | Field                 | Type           | Description                     |
| ---------- | --------------------- | -------------- | ------------------------------- |
| **Reads**  | `extracted_claim`     | `dict \| None` | From `extract_data`             |
| **Reads**  | `vulnerability_flag`  | `bool`         | From `vulnerability_check`      |
| **Writes** | `verification_result` | `str`          | `"PASS"`, `"WARN"`, or `"FAIL"` |
| **Writes** | `verification_errors` | `list[str]`    | Human-readable messages         |

---

## Design note: no LLM in verify

This node is deliberately LLM-free. Verification rules are **deterministic and auditable** —
a business stakeholder or compliance team can enumerate exactly what will trigger a FAIL.
Using an LLM here would make outcomes non-deterministic and harder to explain.

---

## API reference

::: app_classify_extract_claim.graph.nodes.verify
    options:
      show_source: true
      members:
        - verify

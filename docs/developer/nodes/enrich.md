# enrich

**File:** `graph/nodes/enrich.py`  
**Position:** Node 7  
**LLM calls:** 0

---

## Purpose

Merge the extracted claim data with the retrieved policy details into a single
`enriched_claim` dict. This is the canonical record that flows into `check_fields`
and ultimately into the lodged claims store.

---

## Merge logic

The `extracted_claim` dict (from `extract_data`) forms the base.
Policy fields are overlaid on top, with extracted fields taking precedence for
any field present in both (e.g. insured name — the customer-provided value wins).

Additional computed fields added during enrichment:

| Field                | Source        | Description                                     |
| -------------------- | ------------- | ----------------------------------------------- |
| `brand`              | Policy record | `"GIO"` or `"AMI"`                              |
| `product`            | Policy record | e.g. `"Motor Comprehensive"`                    |
| `excess`             | Policy record | Excess amount in AUD                            |
| `sum_insured`        | Policy record | Sum insured in AUD                              |
| `policy_active`      | Policy record | Whether policy is currently active              |
| `vulnerability_flag` | State         | Carries the flag forward into the lodged record |
| `pipeline_version`   | Hardcoded     | `"1.0.0"` — for auditability                    |

---

## State contract

|            | Field                | Type           | Description                |
| ---------- | -------------------- | -------------- | -------------------------- |
| **Reads**  | `extracted_claim`    | `dict \| None` | From `extract_data`        |
| **Reads**  | `policy`             | `dict \| None` | From `policy_retrieval`    |
| **Reads**  | `vulnerability_flag` | `bool`         | From `vulnerability_check` |
| **Writes** | `enriched_claim`     | `dict \| None` | Merged claim record        |

---

## API reference

::: app_classify_extract_claim.graph.nodes.enrich
    options:
      show_source: true
      members:
        - enrich

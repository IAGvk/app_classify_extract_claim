# policy_retrieval

**File:** `graph/nodes/policy_retrieval.py`  
**Position:** Node 6  
**LLM calls:** 0 (lookup-based)

---

## Purpose

Find the matching policy record for the extracted claim by looking up the
`policy_number` (or falling back to insured name) against the policy store.

In the current v1.0 implementation, the policy store is `data/mock_policies.json`.
The node's interface is designed so that the JSON file can be replaced with a
CMS API call or database query without changing any other part of the pipeline.

---

## Matching strategy

1. **Exact match** — look up `insured_details.policy_number` directly
2. **Normalised match** — strip whitespace and case-fold the policy number
3. **Name fuzzy match** (fallback) — if no policy number, search by `insured_name`

If no match is found, `policy_found=False` is set but the pipeline continues.
`check_fields` will subsequently fail if `policy_number` is a mandatory field.

---

## State contract

|            | Field             | Type           | Description                            |
| ---------- | ----------------- | -------------- | -------------------------------------- |
| **Reads**  | `extracted_claim` | `dict \| None` | For `policy_number` and `insured_name` |
| **Writes** | `policy`          | `dict \| None` | Raw policy record                      |
| **Writes** | `policy_found`    | `bool`         | Whether a policy was matched           |

---

## Policy record shape (mock)

```json
{
  "policy_number": "GIO-M-001",
  "holder": "Jane Smith",
  "product": "Motor Comprehensive",
  "brand": "GIO",
  "excess": 500,
  "sum_insured": 25000,
  "state": "NSW",
  "active": true
}
```

---

## API reference

::: app_classify_extract_claim.graph.nodes.policy_retrieval
    options:
      show_source: true
      members:
        - policy_retrieval

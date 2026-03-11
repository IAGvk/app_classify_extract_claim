# lodge

**File:** `graph/nodes/lodge.py`  
**Position:** Node 9  
**LLM calls:** 0  
**Branches:** → `exception_handler` if `lodge_status == "FAILED"`

---

## Purpose

Persist the validated, enriched claim record to the lodged claims store
and issue a unique claim reference number.

---

## Reference number format

```
GIO-XXXXXXXX
```

Where `XXXXXXXX` is 8 uppercase hexadecimal characters derived from a
`uuid4()` call, providing 4.3 billion possible values per prefix and
making collisions negligibly unlikely.

```python
# Generation logic
import uuid
claim_reference = "GIO-" + uuid.uuid4().hex[:8].upper()
# e.g. "GIO-A3F72B1D"
```

---

## Persistence

The enriched claim dict, augmented with:

- `claim_reference` — the generated reference number
- `lodged_at` — ISO-8601 UTC timestamp
- `email_id` — links back to the source message

is appended as a single JSON line to `data/lodged_claims.jsonl`.

The file is created if it does not exist. Each write uses a fresh `open(..., "a")`
call (reopened per record) to minimise the window for partial-write corruption.

---

## State contract

|            | Field                | Type           | Description                      |
| ---------- | -------------------- | -------------- | -------------------------------- |
| **Reads**  | `enriched_claim`     | `dict \| None` | Full merged claim record         |
| **Reads**  | `vulnerability_flag` | `bool`         | Included in the persisted record |
| **Reads**  | `email_id`           | `str`          | Source message identifier        |
| **Writes** | `claim_reference`    | `str \| None`  | `GIO-XXXXXXXX` reference         |
| **Writes** | `lodge_status`       | `str`          | `"SUCCESS"` or `"FAILED"`        |

---

## Failure handling

If any exception occurs during persistence (e.g. disk full, permission error),
the node sets `lodge_status = "FAILED"` and `error_reason`, which the
conditional edge detects, routing to `exception_handler`.

---

## API reference

::: app_classify_extract_claim.graph.nodes.lodge
    options:
      show_source: true
      members:
        - lodge

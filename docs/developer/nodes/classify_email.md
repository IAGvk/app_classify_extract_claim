# classify_email

**File:** `graph/nodes/classify_email.py`  
**Position:** Node 2  
**LLM calls:** 1

---

## Purpose

Determine whether the incoming message was composed as **free-text** (a regular email
written by the customer) or as a **webform submission** (structured key-value output
from an online form). This distinction affects how `extract_data` interprets the body.

---

## State contract

|            | Field        | Type         | Description                 |
| ---------- | ------------ | ------------ | --------------------------- |
| **Reads**  | `email_body` | `str`        | Full email body             |
| **Reads**  | `raw_files`  | `list[dict]` | Parsed attachments          |
| **Writes** | `email_type` | `str`        | `"freetext"` or `"webform"` |

---

## LLM schema

```python
class EmailTypeResponse(BaseModel):
    email_type: Literal["freetext", "webform"]
```

---

## Classification heuristics

The LLM is prompted to consider:

- Presence of structured `Field: Value` patterns → `webform`
- Conversational tone and free narrative → `freetext`
- HTML webform markers in the body → `webform`

The `email_type` feeds into `extract_data` where the prompt strategy differs
slightly between webform (field-by-field extraction) and freetext (NER-style extraction).

---

## API reference

::: app_classify_extract_claim.graph.nodes.classify_email
    options:
      show_source: true
      members:
        - classify_email

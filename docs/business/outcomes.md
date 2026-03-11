# Outcomes Explained

Every claim submission ends in one of two outcomes: **lodged** or **exception**.

---

## Outcome 1 — Lodged (automated success) ✅

**What it means:** The claim has been fully processed, validated, and saved.
A unique claim reference number has been issued.

**When it happens:** When all of the following are true:

- [ ] The message contains a new claim (not an update to an existing one)
- [ ] The extracted data passes all validation rules
- [ ] All mandatory fields are present
- [ ] The record was saved successfully

**Example reference:** `GIO-A3F72B1D`

**What happens next:** The claim record is available for the claims team to action.
The customer reference number can be used in any follow-up communication.

---

## Outcome 2 — Exception (human review required) 🔴

**What it means:** The system could not fully process the claim automatically.
The submission is placed in the **exception queue** for a human reviewer.

**When it happens:** Any one of the following conditions is met:

| Trigger                      | Reason                                                             |
| ---------------------------- | ------------------------------------------------------------------ |
| **Existing claim**           | The email is an update to an open claim — requires manual merge    |
| **Validation failure**       | Data is internally inconsistent (e.g. incident date in the future) |
| **Missing mandatory fields** | The email did not contain enough information to lodge              |
| **System error**             | An unexpected error occurred during processing                     |

**What the reviewer receives:**

Every exception record includes:

- The original email identifier
- A plain-English explanation of **why** the claim was routed for review
- The **full state of the claim** at the point it was routed — including everything
  the AI successfully extracted — so the reviewer doesn't start from scratch

---

## Outcome comparison

|                         | Lodged                    | Exception                                      |
| ----------------------- | ------------------------- | ---------------------------------------------- |
| **Speed**               | Seconds                   | Depends on queue length and staff availability |
| **Human involvement**   | None required             | Required                                       |
| **Reference issued?**   | Yes — immediately         | No — issued by reviewer after manual lodgement |
| **Record persisted?**   | Yes — lodged claims store | Yes — exception queue                          |
| **Vulnerability flag?** | Carried into the record   | Carried into the exception record              |

---

## Notes on WARNings

Between a clean PASS and a hard FAIL, the system also has a **WARN** state.
A WARN means:

- The claim will still proceed to lodgement automatically
- The reviewer will see an informational note in the claim record

Examples of warnings (not failures):

- Incident date is over a year ago (possible but unusual — flagged for awareness)
- Vulnerability indicators detected (claim continues, reviewer alerted)
- Policy number prefix is unexpected (logged but not blocking)

!!! note
    Warnings do **not** route to the exception queue. They are informational flags
    visible in the lodged claim record.

---

## Monitoring the exception queue

The exception queue is an append-only log file. A dashboard or integration can
read it to surface new records for the review team in near real-time.

Each record contains enough information for a reviewer to:

1. Identify the original email
2. Understand exactly why it was routed for review
3. Use the already-extracted data to complete lodgement manually — saving significant time

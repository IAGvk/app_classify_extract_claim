# Policy Matching

When a claim is submitted, the system needs to find the customer's insurance policy
so that the claim record can include the correct product, excess, and coverage details.
This page explains how that matching works.

---

## How policy matching works

The system uses the **policy number** that the customer provides in their email as
the primary lookup key.

```
Customer email contains: "My policy number is GIO-M-001"
                                         ↓
System looks up "GIO-M-001" in the policy store
                                         ↓
Match found: Jane Smith — Motor Comprehensive — GIO — $500 excess
```

### Matching steps (in order)

1. **Exact match** — look for the policy number exactly as the customer wrote it
2. **Normalised match** — strip spaces and case differences  
   (e.g. `" gio-m-001 "` → `"GIO-M-001"`)
3. **Name-based fallback** — if no policy number is provided, search by the
   customer's full name

---

## What information is added from the policy record

When a policy is successfully matched, the following are added to the claim:

| Detail               | Example             |
| -------------------- | ------------------- |
| Insurance brand      | GIO                 |
| Product name         | Motor Comprehensive |
| Excess amount        | $500                |
| Sum insured          | $25,000             |
| Policy state         | NSW                 |
| Policy active status | Yes                 |

These details enrich the claim record so the claims handler has everything
they need without having to look up the policy separately.

---

## What happens when no match is found

If the system cannot find a matching policy:

- The claim **continues processing** — the missing policy does not stop the pipeline
- The **field check** at the end of the pipeline will identify `policy_number` as missing
- The claim is routed to the **exception queue** for human review

The exception record will clearly state that no matching policy was found,
allowing the reviewer to look it up manually and complete the lodgement.

---

## Policy number formats

| Brand           | Format       | Example      |
| --------------- | ------------ | ------------ |
| GIO (motor)     | `GIO-M-XXX`  | `GIO-M-001`  |
| GIO (general)   | `GIOXXXXXXX` | `GIO1234567` |
| AMI (non-motor) | `AMI-NM-XXX` | `AMI-NM-001` |

The system validates that the policy number prefix matches the expected brand.
A mismatch generates a warning (the claim still processes) but is noted
in the claim record for the handler's awareness.

---

## FAQ

**Can a claim be lodged without a matching policy?**  
No. If the mandatory `policy_number` field is missing or unmatched, the claim
is routed to the exception queue for manual handling.

**What if the customer provides the wrong policy number?**  
The system will not find a match and will route the claim to human review.
The reviewer can correct the policy number and complete lodgement.

**Will this always use `mock_policies.json`?**  
No — the current implementation uses a sample policy file for development and testing.
The production version will connect to the live policy management system,
and the matching logic will remain identical.

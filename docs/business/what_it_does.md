# What the System Does

## The problem it solves

Every day, GIO and AMI receive hundreds of insurance claim submissions by email
and online webform. Traditionally, a team member would:

1. Read each email
2. Identify whether it was a new claim or an update to an existing one
3. Manually type the customer's details into the claims management system
4. Attach supporting documents
5. Assign a claim reference number

This process is **slow, error-prone, and resource-intensive** — particularly
for straightforward claims where the email contains all the required information.

---

## What the pipeline does instead

The Claims Processing Pipeline replaces the manual data-entry step for
**new claims** by automatically:

=== "Reading"
    The system reads the incoming email or webform submission, including
    any attached documents or photographs.

=== "Understanding"
    Using AI, it understands the content — identifying the type of insurance,
    the nature of the incident, and all relevant details such as the customer's
    name, policy number, vehicle registration, and incident date.

=== "Checking"
    It validates the information — confirming the incident date is not in the
    future, that a matching policy exists, and that all required fields are present.

=== "Lodging"
    For claims that pass all checks, it automatically creates a claim record
    and issues a unique reference number (e.g. `GIO-A3F72B1D`) within seconds.

=== "Routing"
    For claims that need human attention (updates to existing claims, incomplete
    information, or anything unusual), it immediately routes them to the
    exception queue so a team member can review them.

---

## What it does **not** do

!!! info "Scope of automation"
    The pipeline handles **ingestion and lodgement** only.

    It does **not**:

    - Assess liability or fault
    - Approve or deny claims
    - Contact the customer
    - Make payment decisions
    - Handle claims that are already open (these go straight to human review)

---

## Business value

| Metric                        | Manual process       | Automated pipeline                      |
| ----------------------------- | -------------------- | --------------------------------------- |
| Time to lodge a new claim     | Minutes to hours     | Seconds                                 |
| Data entry errors             | Possible             | Eliminated (AI extraction + validation) |
| Consistency                   | Varies by person     | Always follows the same rules           |
| Vulnerable customer detection | Depends on reader    | Automatic, every submission             |
| Scalability                   | Limited by team size | Handles any volume                      |

---

## Who uses the output?

| Output                     | Used by                                  |
| -------------------------- | ---------------------------------------- |
| **Lodged claim record**    | Claims management system (downstream)    |
| **Claim reference number** | Customer acknowledgement, claims team    |
| **Exception queue record** | Claims handler for manual review         |
| **Vulnerability flag**     | Claims handler, customer experience team |

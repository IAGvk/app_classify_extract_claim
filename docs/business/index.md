# Business Documentation

Welcome to the business-facing documentation for the **Claims Processing Pipeline**.

This section explains, in plain language, what the system does, how a claim moves
through it from start to finish, and what outcomes are possible.

No technical or programming knowledge is required to read this section.

---

<div class="grid cards" markdown>

-   :material-email-fast:{ .lg .middle } __What the System Does__

    ---

    A plain-language overview of the system's purpose and the problem it solves.

    [:octicons-arrow-right-24: Read more](what_it_does.md)

-   :material-map-marker-path:{ .lg .middle } __The Claim Journey__

    ---

    Step-by-step walkthrough of how a claim travels through the pipeline
    from the moment an email arrives to the moment it is lodged.

    [:octicons-arrow-right-24: Read more](claim_journey.md)

-   :material-check-circle-outline:{ .lg .middle } __Outcomes Explained__

    ---

    What does "lodged" mean? When does a claim go to human review?
    What triggers an exception?

    [:octicons-arrow-right-24: Read more](outcomes.md)

-   :material-shield-heart:{ .lg .middle } __Protecting Vulnerable Customers__

    ---

    How the system identifies and flags customers who may need extra care or support.

    [:octicons-arrow-right-24: Read more](vulnerability.md)

-   :material-file-search:{ .lg .middle } __Policy Matching__

    ---

    How the system finds the right policy for each claim — and what happens when
    it cannot.

    [:octicons-arrow-right-24: Read more](policies.md)

</div>

---

## Key facts at a glance

|                               |                                                             |
| ----------------------------- | ----------------------------------------------------------- |
| **Brands supported**          | GIO (motor insurance), AMI (non-motor insurance)            |
| **Accepted inputs**           | Email, webform submission                                   |
| **Processing time**           | Seconds (end-to-end, fully automated)                       |
| **Human review required?**    | Only for exceptions — the vast majority lodge automatically |
| **How a claim is identified** | Unique reference number, e.g. `GIO-A3F72B1D`                |
| **Customer vulnerability**    | Automatically detected and flagged in the claim record      |

# Claims Processing Pipeline

<div class="grid cards" markdown>

-   :material-code-braces:{ .lg .middle } __I'm a Developer__

    ---

    Deep-dive into architecture, code flow, individual nodes, schemas,
    environment config, and the testing guide.

    [:octicons-arrow-right-24: Developer Documentation](developer/index.md)

-   :material-chart-timeline-variant:{ .lg .middle } __I'm a Business Stakeholder__

    ---

    Understand how claims move through the system, what triggers a lodge vs
    an exception, and how vulnerable customers are protected — no code required.

    [:octicons-arrow-right-24: Business Documentation](business/index.md)

</div>

---

## At a glance

|                   |                                                           |
| ----------------- | --------------------------------------------------------- |
| **System**        | End-to-end agentic AI claims ingestion pipeline           |
| **Brands**        | GIO (motor), AMI (non-motor)                              |
| **Languages**     | Python 3.11+                                              |
| **Orchestration** | LangGraph `StateGraph`                                    |
| **LLM**           | Google Gemini via Vertex AI (LangChain `ChatVertexAI`)    |
| **Version**       | 1.0.0                                                     |
| **Repository**    | [IAGvk/lg_practice](https://github.com/IAGvk/lg_practice) |

---

## What does the pipeline do?

An **email or webform submission** arrives containing an insurance claim.  
The pipeline automatically:

1. **Scans** for signs of customer vulnerability
2. **Classifies** the message type and insurance product
3. **Extracts** structured claim data from unstructured text
4. **Verifies** the extracted data for consistency
5. **Retrieves** the matching policy record
6. **Enriches** the claim with policy details
7. **Validates** all mandatory fields are present
8. **Lodges** the claim and issues a reference number (e.g. `GIO-A3F72B1D`)
9. **Routes** any anomalies to the exception queue for human review

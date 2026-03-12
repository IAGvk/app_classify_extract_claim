"""Streamlit Inbox Simulator UI.

Run locally::

    streamlit run app_classify_extract_claim/ui/streamlit_app.py

Or via Docker Compose (port 8501).

Layout
------
Left column  — Inbox Drop Zone: upload a .eml / .txt and submit to the API
Centre column — Pipeline Status: live health check + step indicator
Right column  — Result: structured claim JSON or exception detail
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

import requests
import streamlit as st

# ── Configuration ─────────────────────────────────────────────────────────────

API_URL: str = os.environ.get("API_URL", "http://localhost:8000")
MOCK_LLM: bool = os.environ.get("MOCK_LLM", "false").lower() == "true"

_PIPELINE_STEPS = [
    "vulnerability_check",
    "classify_email",
    "classify",
    "extract_data",
    "verify",
    "policy_retrieval",
    "enrich",
    "check_fields",
    "lodge",
]

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Claims Inbox Simulator",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _check_api_health() -> tuple[bool, str]:
    """Return ``(is_up, version_or_error)``."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return True, data.get("version", "?")
        return False, f"HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except requests.exceptions.Timeout:
        return False, "Timeout"


def _submit_email(file_bytes: bytes, filename: str) -> dict:  # type: ignore[type-arg]
    """POST the email to /process-email and return the parsed JSON response."""
    resp = requests.post(
        f"{API_URL}/process-email",
        files={"email_file": (filename, file_bytes, "message/rfc822")},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


def _status_badge(lodge_status: str) -> str:
    mapping = {
        "SUCCESS": "🟢 SUCCESS",
        "FAILED": "🔴 FAILED",
        "PENDING": "🟡 PENDING",
    }
    return mapping.get(lodge_status, f"⚪ {lodge_status}")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Settings")
    st.text_input("API URL", value=API_URL, key="_api_url", disabled=True)

    is_up, api_version = _check_api_health()
    if is_up:
        st.success(f"API v{api_version} — online")
    else:
        st.error(f"API offline — {api_version}")
        st.info("Start the API with:\n```\nmake run-api\n```")

    st.divider()
    st.caption("Redpanda Console: http://localhost:8080")
    st.caption("API docs: http://localhost:8000/docs")

    if st.button("🔄 Refresh connectivity"):
        st.rerun()


# ── Main layout ───────────────────────────────────────────────────────────────

st.title("📨 Insurance Claims — Inbox Simulator")
st.caption("Drop a .eml or .txt email to run it through the 10-node LangGraph pipeline.")

col_inbox, col_status, col_result = st.columns([1, 1, 1], gap="medium")

# ── Column 1: Inbox Drop Zone ─────────────────────────────────────────────────

with col_inbox:
    st.subheader("📥 Inbox Drop Zone")

    uploaded_file = st.file_uploader(
        "Drop a `.eml` or `.txt` email file",
        type=["eml", "txt"],
        accept_multiple_files=False,
        help="The file will be sent to POST /process-email on the FastAPI service.",
    )

    submit_disabled = uploaded_file is None or not is_up
    submitted = st.button(
        "▶ Submit to Pipeline",
        disabled=submit_disabled,
        use_container_width=True,
        type="primary",
    )

    if not is_up:
        st.warning("API is offline. Start the API server before submitting.")
    elif uploaded_file is not None:
        st.info(
            f"**File:** {uploaded_file.name}  \n"
            f"**Size:** {len(uploaded_file.getvalue()) / 1024:.1f} KB"
        )

# ── Column 2: Pipeline Status ─────────────────────────────────────────────────

with col_status:
    st.subheader("⚙️ Pipeline Status")

    status_placeholder = st.empty()

    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "pipeline_result" not in st.session_state:
        st.session_state.pipeline_result = None
    if "pipeline_error" not in st.session_state:
        st.session_state.pipeline_error = None

    if not st.session_state.pipeline_running and st.session_state.pipeline_result is None:
        with status_placeholder.container():
            st.info("Waiting for email submission…")
            for step in _PIPELINE_STEPS:
                st.write(f"⬜ {step}")

# ── Column 3: Result ──────────────────────────────────────────────────────────

with col_result:
    st.subheader("📋 Result")
    result_placeholder = st.empty()

    if st.session_state.pipeline_result is None and not st.session_state.pipeline_running:
        result_placeholder.info("Result will appear here after the pipeline completes.")

# ── Submission logic ──────────────────────────────────────────────────────────

if submitted and uploaded_file is not None and is_up:
    st.session_state.pipeline_running = True
    st.session_state.pipeline_result = None
    st.session_state.pipeline_error = None

    # Show animated progress in col_status
    with col_status:
        with status_placeholder.container():
            st.info("Pipeline running…")
            step_placeholders = []
            for step in _PIPELINE_STEPS:
                step_placeholders.append(st.empty())
                step_placeholders[-1].write(f"⬜ {step}")

        # Animate steps while waiting (UI-only — we don't have server-sent events in v1.2)
        for i, step in enumerate(_PIPELINE_STEPS):
            time.sleep(0.15)
            step_placeholders[i].write(f"🔵 {step}")

    # Fire the actual request
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name

    try:
        with st.spinner("Waiting for pipeline result…"):
            result = _submit_email(file_bytes, filename)

        st.session_state.pipeline_result = result
        st.session_state.pipeline_running = False
        st.toast("Pipeline complete!", icon="✅")

    except requests.exceptions.HTTPError as exc:
        st.session_state.pipeline_error = str(exc)
        st.session_state.pipeline_running = False
    except Exception as exc:
        st.session_state.pipeline_error = str(exc)
        st.session_state.pipeline_running = False

    st.rerun()

# ── Render result ─────────────────────────────────────────────────────────────

if st.session_state.pipeline_result is not None:
    result = st.session_state.pipeline_result

    with col_status, status_placeholder.container():
        lodge_status = result.get("lodge_status", "UNKNOWN")
        if lodge_status == "SUCCESS":
            st.success("Pipeline complete")
        else:
            st.warning(f"Pipeline finished with status: {lodge_status}")

        for step in _PIPELINE_STEPS:
            st.write(f"✅ {step}")

    with col_result:
        lodge_status = result.get("lodge_status", "UNKNOWN")
        st.metric("Lodge Status", _status_badge(lodge_status))

        if result.get("claim_reference"):
            st.metric("Claim Reference", result["claim_reference"])

        if result.get("insurance_type"):
            st.metric("Insurance Type", result["insurance_type"].title())

        vuln = result.get("vulnerability_flag", False)
        st.metric("Vulnerability Flag", "⚠️ YES" if vuln else "No")

        if result.get("error_reason"):
            st.warning(f"**Error reason:** {result['error_reason']}")

        st.divider()
        st.caption("Full response JSON")
        st.json(result)

        # Link to exception record if failed
        if lodge_status != "SUCCESS":
            exceptions_path = Path("data/exceptions_queue.jsonl")
            if exceptions_path.exists():
                st.caption("Last exception record:")
                lines = exceptions_path.read_text().strip().splitlines()
                if lines:
                    try:
                        st.json(json.loads(lines[-1]))
                    except json.JSONDecodeError:
                        st.text(lines[-1])

elif st.session_state.pipeline_error is not None:
    with col_status:
        status_placeholder.error(f"Request failed: {st.session_state.pipeline_error}")

    with col_result:
        result_placeholder.error(
            f"Could not get a result from the API:\n\n{st.session_state.pipeline_error}"
        )

# ── Recent activity ───────────────────────────────────────────────────────────

st.divider()

with st.expander("📜 Recent lodged claims", expanded=False):
    lodged_path = Path("data/lodged_claims.jsonl")
    if lodged_path.exists():
        lines = lodged_path.read_text().strip().splitlines()
        if lines:
            recent = lines[-10:]  # last 10
            for line in reversed(recent):
                try:
                    record = json.loads(line)
                    ref = record.get("claim_reference", "—")
                    status_val = record.get("lodge_status", "?")
                    ins_type = record.get("insurance_type", "?")
                    ts = record.get("timestamp", "")
                    st.write(f"**{ref}** — {status_val} | {ins_type} | {ts}")
                except json.JSONDecodeError:
                    st.text(line)
        else:
            st.info("No lodged claims yet.")
    else:
        st.info("data/lodged_claims.jsonl not found.")

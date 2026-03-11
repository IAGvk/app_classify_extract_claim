"""LangGraph pipeline builder for the insurance claims processing workflow.

Node execution order (happy path):
    vulnerability_check
    → classify_email
    → classify              [BRANCH: existing_claim → exception_handler]
    → extract_data
    → verify                [BRANCH: FAIL → exception_handler]
    → policy_retrieval
    → enrich
    → check_fields          [BRANCH: incomplete → exception_handler]
    → lodge                 [BRANCH: FAILED → exception_handler]
    → END

    exception_handler → END  (always terminal)
"""
from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app_classify_extract_claim.graph.nodes.check_fields import check_fields
from app_classify_extract_claim.graph.nodes.classify import classify
from app_classify_extract_claim.graph.nodes.classify_email import classify_email
from app_classify_extract_claim.graph.nodes.enrich import enrich
from app_classify_extract_claim.graph.nodes.exception_handler import exception_handler
from app_classify_extract_claim.graph.nodes.extract_data import extract_data
from app_classify_extract_claim.graph.nodes.lodge import lodge
from app_classify_extract_claim.graph.nodes.policy_retrieval import policy_retrieval
from app_classify_extract_claim.graph.nodes.verify import verify
from app_classify_extract_claim.graph.nodes.vulnerability_check import vulnerability_check
from app_classify_extract_claim.graph.state import GraphState

logger = logging.getLogger(__name__)


# ── Conditional edge functions ────────────────────────────────────────────────

def _after_classify(state: GraphState) -> str:
    """Route to exception_handler for existing claims; otherwise extract_data."""
    if state.get("claim_status") == "existing_claim":
        logger.info("Graph: existing_claim detected — routing to exception_handler")
        return "exception_handler"
    # Also catch any hard error set by classify node itself
    if state.get("error_node") == "classify" and state.get("error_reason"):
        return "exception_handler"
    return "extract_data"


def _after_verify(state: GraphState) -> str:
    """Route to exception_handler on FAIL; otherwise policy_retrieval."""
    if state.get("verification_result") == "FAIL":
        logger.info("Graph: verification FAIL — routing to exception_handler")
        return "exception_handler"
    return "policy_retrieval"


def _after_check_fields(state: GraphState) -> str:
    """Route to exception_handler if mandatory fields are missing."""
    if not state.get("fields_complete", False):
        logger.info("Graph: missing mandatory fields — routing to exception_handler")
        return "exception_handler"
    return "lodge"


def _after_lodge(state: GraphState) -> str:
    """Route to exception_handler if lodge failed."""
    if state.get("lodge_status") == "FAILED":
        logger.info("Graph: lodge FAILED — routing to exception_handler")
        return "exception_handler"
    return END


# ── Graph factory ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and compile the LangGraph pipeline.

    Returns:
        Compiled StateGraph ready for ``await graph.ainvoke(state)``.
    """
    builder = StateGraph(GraphState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("vulnerability_check", vulnerability_check)
    builder.add_node("classify_email", classify_email)
    builder.add_node("classify", classify)
    builder.add_node("extract_data", extract_data)
    builder.add_node("verify", verify)
    builder.add_node("policy_retrieval", policy_retrieval)
    builder.add_node("enrich", enrich)
    builder.add_node("check_fields", check_fields)
    builder.add_node("lodge", lodge)
    builder.add_node("exception_handler", exception_handler)

    # ── Entry point ───────────────────────────────────────────────────────────
    builder.add_edge(START, "vulnerability_check")

    # ── Linear edges ─────────────────────────────────────────────────────────
    builder.add_edge("vulnerability_check", "classify_email")
    builder.add_edge("classify_email", "classify")

    # ── Conditional edges ─────────────────────────────────────────────────────
    builder.add_conditional_edges(
        "classify",
        _after_classify,
        {"extract_data": "extract_data", "exception_handler": "exception_handler"},
    )
    builder.add_edge("extract_data", "verify")
    builder.add_conditional_edges(
        "verify",
        _after_verify,
        {"policy_retrieval": "policy_retrieval", "exception_handler": "exception_handler"},
    )
    builder.add_edge("policy_retrieval", "enrich")
    builder.add_edge("enrich", "check_fields")
    builder.add_conditional_edges(
        "check_fields",
        _after_check_fields,
        {"lodge": "lodge", "exception_handler": "exception_handler"},
    )
    builder.add_conditional_edges(
        "lodge",
        _after_lodge,
        {END: END, "exception_handler": "exception_handler"},
    )
    builder.add_edge("exception_handler", END)

    graph = builder.compile()
    logger.info("LangGraph pipeline compiled successfully")
    return graph


# ── Singleton (module-level, built once) ──────────────────────────────────────
_graph = None


def get_graph() -> StateGraph:
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

"""LLM client — thin wrapper around ChatVertexAI (Gemini via LangChain).

In ``MOCK_LLM=true`` mode every call returns a configurable stub response,
so the full pipeline can be exercised without GCP credentials.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Literal, TypeVar, get_args, get_origin

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _load_fixture(path: str) -> dict[str, Any]:
    """Load a JSON fixture file mapping schema class names to response dicts."""
    fixture_path = Path(path)
    if not fixture_path.exists():
        raise FileNotFoundError(f"MOCK_LLM_FIXTURE file not found: {fixture_path}")
    with fixture_path.open() as fh:
        data = json.load(fh)
    logger.info("MOCK: loaded fixture with %d schema(s) from %s", len(data), fixture_path)
    return data


class LLMClient:
    """Async-capable LLM client backed by ChatVertexAI.

    Usage::

        client = LLMClient.from_settings(get_settings())
        result = await client.ainvoke_structured(MySchema, system, user, attachments)
    """

    def __init__(self, llm: Any, mock: bool = False, fixture: dict[str, Any] | None = None) -> None:
        self._llm = llm
        self._mock = mock
        self._fixture: dict[str, Any] = fixture or {}

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_settings(cls, settings: Any) -> "LLMClient":
        if settings.mock_llm:
            logger.info("LLMClient: MOCK mode enabled — no GCP calls will be made")
            fixture: dict[str, Any] = {}
            fixture_path = os.environ.get("MOCK_LLM_FIXTURE", "")
            if fixture_path:
                fixture = _load_fixture(fixture_path)
            return cls(llm=None, mock=True, fixture=fixture)

        try:
            from langchain_google_vertexai import ChatVertexAI  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "langchain-google-vertexai is not installed. "
                "Run: pip install langchain-google-vertexai"
            ) from exc

        if settings.https_proxy:
            proxy_url = f"http://{settings.https_proxy}"
            os.environ.setdefault("HTTPS_PROXY", proxy_url)
            os.environ.setdefault("https_proxy", proxy_url)

        llm = ChatVertexAI(
            model_name=settings.gcp_gemini_model,
            project=settings.gcp_project_id,
            location=settings.gcp_location_id,
            temperature=0.1,
            max_retries=0,
            api_transport="rest",
            model_kwargs={
                "generation_config": {"response_mime_type": "application/json"}
            },
        )
        logger.info(
            "LLMClient ready  model=%s  project=%s  location=%s",
            settings.gcp_gemini_model,
            settings.gcp_project_id,
            settings.gcp_location_id,
        )
        return cls(llm=llm, mock=False)

    # ── Primary interface ─────────────────────────────────────────────────────

    async def ainvoke_structured(
        self,
        schema: type[T],
        system_prompt: str,
        human_content: list[dict] | str,
        *,
        retries: int = 3,
    ) -> T:
        """Invoke LLM and parse into ``schema``.  Retries on transient errors."""
        from langchain_core.messages import HumanMessage, SystemMessage

        if self._mock:
            return self._mock_structured(schema, self._fixture)

        if isinstance(human_content, str):
            human_content = [{"type": "text", "text": human_content}]

        structured = (
            self._llm.with_structured_output(schema).with_retry(
                stop_after_attempt=retries,
                wait_exponential_jitter=True,
            )
        )
        response = await structured.ainvoke([
            SystemMessage(system_prompt),
            HumanMessage(content=human_content),
        ])
        return response

    async def ainvoke_text(
        self,
        system_prompt: str,
        human_text: str,
        *,
        retries: int = 3,
    ) -> str:
        """Invoke LLM and return raw text."""
        from langchain_core.messages import HumanMessage, SystemMessage

        if self._mock:
            return "{}"

        llm_with_retry = self._llm.with_retry(
            stop_after_attempt=retries,
            wait_exponential_jitter=True,
        )
        response = await llm_with_retry.ainvoke([
            SystemMessage(system_prompt),
            HumanMessage(content=human_text),
        ])
        return response.content or ""

    # ── Mock helpers ──────────────────────────────────────────────────────────

    def _mock_structured(self, schema: type[T], fixture: dict[str, Any] | None = None) -> T:
        """Return a mock instance of *schema*.

        If *fixture* contains a key matching ``schema.__name__``, that dict is
        used to construct the response (realistic fixture mode).  Otherwise
        falls back to building a minimal-valid instance so the pipeline can
        proceed without errors.
        """
        # ── Fixture path ──────────────────────────────────────────────────────
        if fixture and schema.__name__ in fixture:
            logger.debug("MOCK: fixture hit for %s", schema.__name__)
            return schema.model_validate(fixture[schema.__name__])
        logger.debug("MOCK: returning minimal %s", schema.__name__)
        logger.debug("MOCK: returning minimal %s", schema.__name__)

        def _first_value(ann: Any) -> Any:  # noqa: ANN401
            """Return the first valid value for an annotation type."""
            origin = get_origin(ann)
            # Literal[...] — pick first choice
            if origin is Literal:
                return get_args(ann)[0]
            # List[X] / list — return empty list
            if origin is list or ann is list:
                return []
            # Dict[K, V] / dict — return empty dict
            if origin is dict or ann is dict:
                return {}
            # Optional[X] / Union[X, None] — recurse on first non-None arg
            if origin is not None:  # other generic alias (Union, …)
                args = [a for a in get_args(ann) if a is not type(None)]
                if args:
                    return _first_value(args[0])
            if ann is str:
                return ""
            if ann is bool:
                return False
            if ann is int:
                return 0
            if ann is float:
                return 0.0
            return None

        # Fast path: schema validates without any values supplied
        try:
            return schema.model_validate({})
        except Exception:
            pass

        # Build a minimal dict that satisfies required fields
        minimal: dict[str, Any] = {}
        for name, finfo in schema.model_fields.items():
            if finfo.is_required():
                ann = finfo.annotation
                minimal[name] = _first_value(ann)
        return schema.model_validate(minimal)

"""Kafka / Redpanda background consumer.

Runs on a dedicated daemon thread inside the FastAPI process.
Polls ``claims.email.inbox``, loads the email from the shared inbox
directory, runs the LangGraph pipeline, and commits the offset on success.

Start/stop is managed by the FastAPI lifespan (``api/main.py``).
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import threading
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from app_classify_extract_claim.config.settings import Settings

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_consumer_thread: threading.Thread | None = None


# ── Public API ────────────────────────────────────────────────────────────────


def start_consumer(settings: Settings) -> threading.Thread:
    """Start the Kafka consumer in a daemon background thread.

    Returns the thread so callers can ``join()`` it during shutdown.
    """
    global _consumer_thread

    _stop_event.clear()
    _consumer_thread = threading.Thread(
        target=_consume_loop,
        args=(settings,),
        daemon=True,
        name="kafka-consumer",
    )
    _consumer_thread.start()
    logger.info(
        "[consumer] started — topic=%s bootstrap=%s group=%s",
        settings.kafka_topic_inbox,
        settings.kafka_bootstrap_servers,
        settings.kafka_consumer_group_id,
    )
    return _consumer_thread


def stop_consumer() -> None:
    """Signal the consumer thread to exit after its current ``poll()`` timeout."""
    _stop_event.set()
    logger.info("[consumer] stop signal sent")


# ── Internal loop ─────────────────────────────────────────────────────────────


def _consume_loop(settings: Settings) -> None:
    """Main polling loop — runs on the consumer thread."""
    from confluent_kafka import Consumer, KafkaError, KafkaException

    consumer: Any = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": settings.kafka_consumer_group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": "false",
        }
    )
    consumer.subscribe([settings.kafka_topic_inbox])
    logger.info("[consumer] subscribed to topic=%s", settings.kafka_topic_inbox)

    try:
        while not _stop_event.is_set():
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                code = msg.error().code()
                if code == KafkaError._PARTITION_EOF:
                    continue
                logger.error("[consumer] kafka error: %s", msg.error())
                continue
            try:
                raw = msg.value()
                payload: dict[str, Any] = json.loads(
                    raw.decode("utf-8") if isinstance(raw, bytes) else raw
                )
                asyncio.run(_handle_message(payload))
                consumer.commit(message=msg)
            except KafkaException as exc:
                logger.error("[consumer] kafka exception: %s", exc)
            except Exception as exc:
                logger.error("[consumer] unexpected error: %s", exc, exc_info=True)
    finally:
        consumer.close()
        logger.info("[consumer] closed")


async def _handle_message(payload: dict[str, Any]) -> None:
    """Run the LangGraph pipeline for a single inbox event payload."""
    from app_classify_extract_claim.graph.builder import get_graph
    from app_classify_extract_claim.graph.state import initial_state
    from app_classify_extract_claim.services.file_parser import parse_input

    email_id: str = payload.get("email_id", "unknown")
    inbox_path: str = payload.get("inbox_path", "")

    logger.info("[consumer] processing email_id=%s path=%s", email_id, inbox_path)

    parsed = parse_input(inbox_path)
    email_body: str = parsed.get("body", "")
    raw_files: list[dict[str, Any]] = cast("list[dict[str, Any]]", parsed.get("attachments", []))

    state = initial_state(
        email_id=email_id,
        email_body=email_body,
        raw_files=raw_files,
    )

    graph = get_graph()
    result: dict[str, Any] = await graph.ainvoke(state)

    lodge_status: str = result.get("lodge_status", "UNKNOWN")
    claim_ref: str | None = result.get("claim_reference")
    logger.info(
        "[consumer] completed email_id=%s status=%s ref=%s",
        email_id,
        lodge_status,
        claim_ref,
    )

    # Remove temporary inbox file after successful processing
    if inbox_path:
        try:
            Path(inbox_path).unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("[consumer] could not delete inbox file %s: %s", inbox_path, exc)

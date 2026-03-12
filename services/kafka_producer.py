"""Kafka / Redpanda email event producer — used by the Streamlit UI.

Usage::

    from app_classify_extract_claim.config.settings import get_settings
    from app_classify_extract_claim.services.kafka_producer import KafkaEmailProducer, build_email_id

    producer = KafkaEmailProducer(get_settings())
    email_id = build_email_id()
    producer.dispatch(email_id, inbox_path=Path("/tmp/inbox/abc.eml"), filename="abc.eml")
    producer.close()
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from pathlib import Path

    from app_classify_extract_claim.config.settings import Settings

logger = logging.getLogger(__name__)


class KafkaEmailProducer:
    """Publishes email file-drop events to the Kafka inbox topic.

    The event payload is::

        {
            "email_id": "<uuid>",
            "inbox_path": "/path/to/file.eml",
            "filename": "original_filename.eml"
        }
    """

    def __init__(self, settings: Settings) -> None:
        from confluent_kafka import Producer

        self._topic = settings.kafka_topic_inbox
        self._producer: Any = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})

    def dispatch(self, email_id: str, inbox_path: Path, filename: str) -> None:
        """Serialize and produce a file-drop event.

        Calls ``flush()`` before returning to guarantee delivery confirmation.
        """
        payload = json.dumps(
            {
                "email_id": email_id,
                "inbox_path": str(inbox_path),
                "filename": filename,
            }
        ).encode("utf-8")

        self._producer.produce(
            self._topic,
            key=email_id.encode("utf-8"),
            value=payload,
            on_delivery=_delivery_report,
        )
        self._producer.flush()
        logger.info(
            "[producer] dispatched email_id=%s topic=%s filename=%s",
            email_id,
            self._topic,
            filename,
        )

    def close(self) -> None:
        """Flush any remaining messages and release the producer."""
        self._producer.flush()


def build_email_id() -> str:
    """Generate a unique email ID for a new inbox event."""
    return str(uuid.uuid4())


def _delivery_report(err: object | None, msg: object) -> None:
    """Confluent-Kafka delivery callback — logs success or failure."""
    if err:
        logger.error("[producer] delivery failed: %s", err)
    else:
        logger.debug("[producer] delivered key=%s", getattr(msg, "key", lambda: b"?")())

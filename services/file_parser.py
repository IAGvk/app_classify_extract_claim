"""Parse email input files (.eml, .txt) and their attachments (PDF, DOCX, images).

Produces a list of ``ParsedFile`` dicts consumed by the LangGraph pipeline.

Supported input formats
-----------------------
* ``.eml``  — RFC-2822 email; body extracted, each MIME attachment handled separately
* ``.txt``  — plain-text treated as the email body (no attachments)
* ``.pdf``  — text extracted via pypdf
* ``.docx`` — text extracted via python-docx
* Images (jpg, png, gif, webp, bmp) — base64-encoded for Gemini multimodal
"""
from __future__ import annotations

import base64
import email
import email.policy
import io
import logging
import mimetypes
from pathlib import Path
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

# MIME → friendly label (also used for routing in extract_data)
IMAGE_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
}
TEXT_MIMES = {
    "text/plain", "text/html",
}

_SUPPORTED_ATTACHMENT_EXTS = {
    ".pdf", ".docx", ".doc",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    ".txt",
}


class ParsedFile(TypedDict):
    """Single attachment / inline file extracted from an email."""
    filename: str
    mime_type: str
    text_content: str | None     # extracted text (PDF, DOCX, plain-text attachments)
    base64_content: str | None   # base64 string for images
    raw_bytes: bytes             # always present; used for further processing


class ParsedEmail(TypedDict):
    """Full parsed representation of an incoming email."""
    subject: str
    sender: str
    recipients: list[str]
    body: str          # plain-text body (HTML stripped to plain fallback)
    attachments: list[ParsedFile]


# ── Public entry point ────────────────────────────────────────────────────────

def parse_input(file_path: str | Path) -> ParsedEmail:
    """Parse an email input file (.eml or .txt) and all its attachments.

    Args:
        file_path: Path to a ``.eml`` or ``.txt`` file.

    Returns:
        ParsedEmail dict with ``body`` and ``attachments``.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    ext = path.suffix.lower()
    if ext == ".eml":
        return _parse_eml(path)
    elif ext == ".txt":
        return _parse_txt(path)
    else:
        raise ValueError(
            f"Unsupported input format '{ext}'. Accepted: .eml, .txt"
        )


def parse_attachment_bytes(
    raw_bytes: bytes,
    filename: str,
    mime_type: str | None = None,
) -> ParsedFile:
    """Parse raw bytes of an attachment file into a ParsedFile dict.

    Used when attachments are supplied separately (e.g. via Streamlit upload).
    """
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"

    return _process_attachment(raw_bytes, filename, mime_type)


# ── EML parsing ───────────────────────────────────────────────────────────────

def _parse_eml(path: Path) -> ParsedEmail:
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw, policy=email.policy.default)

    subject = str(msg.get("Subject", ""))
    sender = str(msg.get("From", ""))
    to_header = msg.get("To", "")
    recipients = [a.strip() for a in to_header.split(",")] if to_header else []

    body_parts: list[str] = []
    attachments: list[ParsedFile] = []

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition = str(part.get_content_disposition() or "")
        filename = part.get_filename()

        if "attachment" in disposition or filename:
            _handle_attachment_part(part, filename, content_type, attachments)
        elif content_type == "text/plain" and "attachment" not in disposition:
            try:
                text = part.get_content()
                if text:
                    body_parts.append(text.strip())
            except Exception:
                payload = part.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode("utf-8", errors="replace").strip())
        elif content_type == "text/html" and not body_parts:
            # Fallback: strip tags from HTML body if no plain-text part
            try:
                html = part.get_content()
                body_parts.append(_strip_html(html))
            except Exception:
                pass

    body = "\n\n".join(filter(None, body_parts))
    logger.info(
        "Parsed .eml: subject=%r  attachments=%d  body_chars=%d",
        subject, len(attachments), len(body),
    )
    return ParsedEmail(
        subject=subject,
        sender=sender,
        recipients=recipients,
        body=body,
        attachments=attachments,
    )


def _handle_attachment_part(
    part: Any,
    filename: str | None,
    content_type: str,
    out: list[ParsedFile],
) -> None:
    filename = filename or f"attachment.{content_type.split('/')[-1]}"
    try:
        raw_bytes: bytes = part.get_payload(decode=True) or b""
    except Exception:
        raw_bytes = b""

    if not raw_bytes:
        return

    ext = Path(filename).suffix.lower()
    if ext not in _SUPPORTED_ATTACHMENT_EXTS and content_type not in IMAGE_MIMES:
        logger.debug("Skipping unsupported attachment: %s (%s)", filename, content_type)
        return

    out.append(_process_attachment(raw_bytes, filename, content_type))


# ── TXT parsing ───────────────────────────────────────────────────────────────

def _parse_txt(path: Path) -> ParsedEmail:
    body = path.read_text(encoding="utf-8", errors="replace")
    logger.info("Parsed .txt: body_chars=%d", len(body))
    return ParsedEmail(
        subject="",
        sender="",
        recipients=[],
        body=body.strip(),
        attachments=[],
    )


# ── Attachment processor ──────────────────────────────────────────────────────

def _process_attachment(raw_bytes: bytes, filename: str, mime_type: str) -> ParsedFile:
    """Convert raw bytes to a ParsedFile with extracted text or base64."""
    ext = Path(filename).suffix.lower()
    text_content: str | None = None
    base64_content: str | None = None

    # ── Images ─────────────────────────────────────────────────────────────
    if mime_type in IMAGE_MIMES or ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
        base64_content = base64.b64encode(raw_bytes).decode("ascii")
        if not mime_type or mime_type == "application/octet-stream":
            mime_type = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".gif": "image/gif",
                ".webp": "image/webp", ".bmp": "image/bmp",
            }.get(ext, "image/jpeg")

    # ── PDF ────────────────────────────────────────────────────────────────
    elif ext == ".pdf" or mime_type == "application/pdf":
        text_content = _extract_pdf_text(raw_bytes, filename)
        mime_type = "application/pdf"

    # ── DOCX ───────────────────────────────────────────────────────────────
    elif ext in {".docx", ".doc"} or "wordprocessingml" in mime_type:
        text_content = _extract_docx_text(raw_bytes, filename)
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # ── Plain text attachment ──────────────────────────────────────────────
    elif ext == ".txt" or mime_type == "text/plain":
        text_content = raw_bytes.decode("utf-8", errors="replace")
        mime_type = "text/plain"

    else:
        logger.debug("No text extractor for %s (%s) — stored as raw bytes only", filename, mime_type)

    return ParsedFile(
        filename=filename,
        mime_type=mime_type,
        text_content=text_content,
        base64_content=base64_content,
        raw_bytes=raw_bytes,
    )


# ── Text extractors ───────────────────────────────────────────────────────────

def _extract_pdf_text(raw_bytes: bytes, filename: str) -> str | None:
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        result = "\n\n".join(pages)
        logger.debug("PDF %s: extracted %d chars from %d pages", filename, len(result), len(reader.pages))
        return result or None
    except ImportError:
        logger.warning("pypdf not installed — cannot extract text from PDF %s", filename)
        return None
    except Exception as exc:
        logger.warning("PDF extraction failed for %s: %s", filename, exc)
        return None


def _extract_docx_text(raw_bytes: bytes, filename: str) -> str | None:
    try:
        import docx  # type: ignore

        doc = docx.Document(io.BytesIO(raw_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        result = "\n".join(paragraphs)
        logger.debug("DOCX %s: extracted %d chars", filename, len(result))
        return result or None
    except ImportError:
        logger.warning("python-docx not installed — cannot extract text from %s", filename)
        return None
    except Exception as exc:
        logger.warning("DOCX extraction failed for %s: %s", filename, exc)
        return None


def _strip_html(html: str) -> str:
    """Very basic HTML tag stripper (no dependency on bs4)."""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ── LangChain multimodal content builder ──────────────────────────────────────

def files_to_langchain_parts(
    parsed_files: list[ParsedFile],
) -> tuple[list[dict], list[str]]:
    """Convert ParsedFile list into LangChain multimodal content blocks.

    Returns:
        (content_parts, filenames)
        content_parts: list of dicts suitable for LangChain HumanMessage content
    """
    parts: list[dict] = []
    filenames: list[str] = []

    for f in parsed_files:
        filenames.append(f["filename"])

        if f["base64_content"]:
            # Image → inline data URL for Gemini multimodal
            parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{f['mime_type']};base64,{f['base64_content']}"
                },
            })
        elif f["text_content"]:
            parts.append({
                "type": "text",
                "text": f"[Attachment: {f['filename']}]\n{f['text_content']}",
            })
        else:
            # No text extracted — note existence only
            parts.append({
                "type": "text",
                "text": f"[Attachment: {f['filename']} — content could not be extracted]",
            })

    return parts, filenames

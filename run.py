#!/usr/bin/env python3
"""CLI runner — process a single email file (.eml or .txt) through the pipeline.

Usage:
    python run.py --input path/to/email.eml
    python run.py --input path/to/email.txt
    MOCK_LLM=true python run.py --input path/to/email.eml
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an email file through the insurance claims pipeline."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input .eml or .txt file.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


async def _run(input_path: Path) -> dict:
    from app_classify_extract_claim.graph.builder import get_graph
    from app_classify_extract_claim.graph.state import initial_state
    from app_classify_extract_claim.services.file_parser import parse_input

    parsed = parse_input(str(input_path))
    email_body = parsed.get("body", "")
    raw_files = parsed.get("attachments", [])
    email_id = input_path.stem

    state = initial_state(
        email_id=email_id,
        email_body=email_body,
        raw_files=raw_files,
    )

    graph = get_graph()
    result = await graph.ainvoke(state)
    return result


def main() -> None:
    args = _parse_args()

    if not args.input.exists():
        print(f"ERROR: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    suffix = args.input.suffix.lower()
    if suffix not in {".eml", ".txt"}:
        print(f"ERROR: Unsupported file type '{suffix}'. Use .eml or .txt.", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(_run(args.input))

    # Serialise — replace non-serialisable objects with their string repr
    def _default(obj: object) -> dict | str:
        try:
            return obj.model_dump()
        except AttributeError:
            return str(obj)

    indent = 2 if args.pretty else None
    print(json.dumps(result, default=_default, indent=indent))


if __name__ == "__main__":
    main()

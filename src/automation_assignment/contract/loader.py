"""Fetch and archive the exact Swagger document used by a test run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx


def load_swagger_document(
    spec_url: str,
    *,
    timeout_seconds: float,
    evidence_path: Path,
) -> dict[str, Any]:
    response = httpx.get(spec_url, timeout=timeout_seconds)
    response.raise_for_status()
    document: dict[str, Any] = response.json()
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(document, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return document

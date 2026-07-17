"""Recursive redaction for request diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REDACTED = "***REDACTED***"
SENSITIVE_KEYS = frozenset({"authorization", "password", "proxy-authorization"})


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: REDACTED if str(key).lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value

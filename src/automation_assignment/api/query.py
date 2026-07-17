"""Reusable query serialization without leaking None values."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def defined_query(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}

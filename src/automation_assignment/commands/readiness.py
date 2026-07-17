"""Service readiness probe with injectable time and HTTP dependencies."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

import httpx

from automation_assignment.config import Settings


class HttpGet(Protocol):
    def __call__(self, url: str, *, timeout: float) -> httpx.Response: ...


def wait_for_api(
    settings: Settings,
    *,
    get: HttpGet = httpx.get,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    output: Callable[[str], None] = print,
) -> int:
    deadline = monotonic() + settings.api_readiness_timeout_seconds
    last_error = "not attempted"
    while monotonic() < deadline:
        try:
            response = get(
                settings.spec_url,
                timeout=min(settings.api_timeout_seconds, 5),
            )
            if response.status_code == httpx.codes.OK and response.json().get("swagger") == "2.0":
                output(f"API ready: {settings.spec_url}")
                return 0
            last_error = f"status={response.status_code} body={response.text[:200]}"
        except (httpx.HTTPError, ValueError) as exc:
            last_error = str(exc)
        sleep(1)
    output(f"API readiness timed out after {settings.api_readiness_timeout_seconds}s: {last_error}")
    return 1

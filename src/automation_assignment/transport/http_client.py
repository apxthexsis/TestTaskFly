"""Shared HTTP transport with explicit URL invariants and safe diagnostics."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx

from automation_assignment.config import Credentials
from automation_assignment.transport.http_method import HttpMethod
from automation_assignment.transport.redaction import redact

LOGGER = logging.getLogger(__name__)
MAX_LOGGED_BODY_CHARACTERS = 2_000


def normalize_base_url(value: str) -> httpx.URL:
    """Return an absolute base URL whose path ends in exactly one slash."""

    url = httpx.URL(value)
    if not url.is_absolute_url:
        raise ValueError("API base URL must be absolute")
    if url.query or url.fragment:
        raise ValueError("API base URL must not contain query parameters or a fragment")
    path = url.path if url.path.endswith("/") else f"{url.path}/"
    return url.copy_with(path=path)


class HttpClient:
    """Transport only; API paths and payload semantics belong to API clients."""

    def __init__(
        self,
        base_url: str,
        *,
        credentials: Credentials | None = None,
        timeout_seconds: float = 10.0,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        auth = httpx.BasicAuth(*credentials.as_auth_tuple()) if credentials else None
        self._client = httpx.Client(
            base_url=normalize_base_url(base_url),
            auth=auth,
            timeout=timeout_seconds,
            headers=headers,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: HttpMethod,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        content: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        if not path or path.startswith("/") or httpx.URL(path).is_absolute_url:
            raise ValueError("API path must be a non-empty relative path")

        LOGGER.info(
            "API request method=%s path=%s params=%s headers=%s body=%s",
            method,
            path,
            redact(dict(params or {})),
            redact(dict(headers or {})),
            redact(json) if json is not None else "<raw-content>" if content else None,
        )
        response = self._client.request(
            method.value,
            path,
            params=params,
            json=json,
            content=content,
            headers=headers,
        )
        LOGGER.info(
            "API response method=%s path=%s status=%s body=%s",
            method,
            path,
            response.status_code,
            response.text[:MAX_LOGGED_BODY_CHARACTERS],
        )
        return response

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

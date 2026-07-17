"""HTTP gateway for integration endpoints."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from automation_assignment.api.query import defined_query
from automation_assignment.api.routes import INTEGRATIONS, JSON_CONTENT_TYPE
from automation_assignment.domain import CreateIntegrationRequest, UpdateIntegrationRequest
from automation_assignment.transport import HttpClient, HttpMethod


class IntegrationsClient:
    def __init__(self, transport: HttpClient) -> None:
        self._transport = transport

    def list(self, *, page: int | None = None, limit: int | None = None) -> httpx.Response:
        return self._transport.request(
            HttpMethod.GET,
            INTEGRATIONS.collection,
            params=defined_query({"page": page, "limit": limit}),
        )

    def create(self, request: CreateIntegrationRequest) -> httpx.Response:
        return self._transport.request(
            HttpMethod.POST,
            INTEGRATIONS.collection,
            json=request.model_dump(mode="json"),
        )

    def create_unvalidated(self, payload: Mapping[str, Any]) -> httpx.Response:
        return self._transport.request(
            HttpMethod.POST,
            INTEGRATIONS.collection,
            json=dict(payload),
        )

    def create_raw(self, content: str, content_type: str = JSON_CONTENT_TYPE) -> httpx.Response:
        return self._transport.request(
            HttpMethod.POST,
            INTEGRATIONS.collection,
            content=content,
            headers={"Content-Type": content_type},
        )

    def get(self, integration_id: str) -> httpx.Response:
        return self._transport.request(HttpMethod.GET, INTEGRATIONS.item(integration_id))

    def update(self, request: UpdateIntegrationRequest) -> httpx.Response:
        return self._transport.request(
            HttpMethod.PUT,
            INTEGRATIONS.collection,
            json=request.model_dump(mode="json"),
        )

    def update_unvalidated(self, payload: Mapping[str, Any]) -> httpx.Response:
        return self._transport.request(
            HttpMethod.PUT,
            INTEGRATIONS.collection,
            json=dict(payload),
        )

    def delete(self, integration_id: str) -> httpx.Response:
        return self._transport.request(HttpMethod.DELETE, INTEGRATIONS.item(integration_id))

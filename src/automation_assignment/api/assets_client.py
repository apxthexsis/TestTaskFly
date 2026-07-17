"""HTTP gateway for asset endpoints."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from automation_assignment.api.query import defined_query
from automation_assignment.api.routes import ASSETS, INTEGRATION_ID_QUERY, JSON_CONTENT_TYPE
from automation_assignment.domain import CreateAssetRequest, UpdateAssetRequest
from automation_assignment.transport import HttpClient, HttpMethod


class AssetsClient:
    def __init__(self, transport: HttpClient) -> None:
        self._transport = transport

    def list(
        self,
        integration_id: str,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> httpx.Response:
        return self._transport.request(
            HttpMethod.GET,
            ASSETS.collection,
            params=defined_query(
                {INTEGRATION_ID_QUERY: integration_id, "page": page, "limit": limit}
            ),
        )

    def create(self, request: CreateAssetRequest) -> httpx.Response:
        return self._transport.request(
            HttpMethod.POST,
            ASSETS.collection,
            json=request.model_dump(mode="json"),
        )

    def create_unvalidated(self, payload: Mapping[str, Any]) -> httpx.Response:
        return self._transport.request(
            HttpMethod.POST,
            ASSETS.collection,
            json=dict(payload),
        )

    def create_raw(self, content: str, content_type: str = JSON_CONTENT_TYPE) -> httpx.Response:
        return self._transport.request(
            HttpMethod.POST,
            ASSETS.collection,
            content=content,
            headers={"Content-Type": content_type},
        )

    def get(self, asset_id: str) -> httpx.Response:
        return self._transport.request(HttpMethod.GET, ASSETS.item(asset_id))

    def update(self, request: UpdateAssetRequest) -> httpx.Response:
        return self._transport.request(
            HttpMethod.PATCH,
            ASSETS.collection,
            json=request.model_dump(mode="json"),
        )

    def update_unvalidated(self, payload: Mapping[str, Any]) -> httpx.Response:
        return self._transport.request(
            HttpMethod.PATCH,
            ASSETS.collection,
            json=dict(payload),
        )

    def delete(self, asset_id: str) -> httpx.Response:
        return self._transport.request(HttpMethod.DELETE, ASSETS.item(asset_id))

"""Collision-resistant builders for valid domain requests."""

from __future__ import annotations

from itertools import count
from uuid import uuid4

from automation_assignment.domain import CreateAssetRequest, CreateIntegrationRequest


class DataFactory:
    def __init__(self, run_id: str | None = None) -> None:
        self.run_id = run_id or uuid4().hex[:10]
        self._counter = count(1)

    def _unique(self, prefix: str) -> str:
        return f"qa-{self.run_id}-{prefix}-{next(self._counter)}"

    def integration(
        self,
        *,
        name: str | None = None,
        kind: str = "webhook",
    ) -> CreateIntegrationRequest:
        return CreateIntegrationRequest(name=name or self._unique("integration"), type=kind)

    def asset(
        self,
        integration_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> CreateAssetRequest:
        return CreateAssetRequest(
            name=name or self._unique("asset"),
            description=description or self._unique("description"),
            integration_id=integration_id,
        )

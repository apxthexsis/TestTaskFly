"""Typed setup workflow for independent tenant resource graphs."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from automation_assignment.api import AssetsClient, IntegrationsClient
from automation_assignment.domain import Asset, CreateAssetRequest, Integration
from automation_assignment.support import DataFactory
from automation_assignment.workflows.entity_registry import CreatedEntityRegistry


class SetupRequestError(RuntimeError):
    pass


def _parse_successful[ModelT: BaseModel](
    response: httpx.Response,
    model: type[ModelT],
) -> ModelT:
    if not response.is_success:
        raise SetupRequestError(
            f"Setup request failed with {response.status_code}: {response.text}"
        )
    return model.model_validate(response.json())


@dataclass(frozen=True)
class TenantGraph:
    integration: Integration
    asset: Asset


class TenantWorkflow:
    def __init__(
        self,
        integrations: IntegrationsClient,
        assets: AssetsClient,
        registry: CreatedEntityRegistry,
        data: DataFactory,
    ) -> None:
        self._integrations = integrations
        self._assets = assets
        self._registry = registry
        self._data = data

    def create_integration(self) -> Integration:
        response = self._integrations.create(self._data.integration())
        integration = _parse_successful(response, Integration)
        self._registry.register_integration(integration)
        return integration

    def create_asset(self, integration_id: str) -> Asset:
        return self.create_asset_from(self._data.asset(integration_id))

    def create_asset_from(self, request: CreateAssetRequest) -> Asset:
        response = self._assets.create(request)
        asset = _parse_successful(response, Asset)
        self._registry.register_asset(asset)
        return asset

    def create_graph(self) -> TenantGraph:
        integration = self.create_integration()
        asset = self.create_asset(integration.id)
        return TenantGraph(integration=integration, asset=asset)

"""Registry of entities created by one test."""

from __future__ import annotations

from dataclasses import dataclass, field

from automation_assignment.domain import Asset, Integration


@dataclass
class CreatedEntityRegistry:
    integration_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)

    def register_integration(self, integration: Integration) -> None:
        self.integration_ids.append(integration.id)

    def register_asset(self, asset: Asset) -> None:
        self.asset_ids.append(asset.id)

    def unregister_integration(self, integration_id: str) -> None:
        if integration_id in self.integration_ids:
            self.integration_ids.remove(integration_id)

    def unregister_asset(self, asset_id: str) -> None:
        if asset_id in self.asset_ids:
            self.asset_ids.remove(asset_id)

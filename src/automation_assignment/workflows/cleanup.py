"""Best-effort, dependency-aware cleanup with structured diagnostics."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from automation_assignment.api import AssetsClient, IntegrationsClient
from automation_assignment.workflows.entity_registry import CreatedEntityRegistry

LOGGER = logging.getLogger(__name__)


class EntityType(StrEnum):
    ASSET = "asset"
    INTEGRATION = "integration"


@dataclass(frozen=True)
class CleanupFailure:
    entity_type: EntityType
    entity_id: str
    error: str


@dataclass
class CleanupReport:
    failures: list[CleanupFailure] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.failures


class CleanupManager:
    def __init__(
        self,
        integrations: IntegrationsClient,
        assets: AssetsClient,
    ) -> None:
        self._integrations = integrations
        self._assets = assets

    def cleanup(self, registry: CreatedEntityRegistry) -> CleanupReport:
        report = CleanupReport()
        for asset_id in reversed(registry.asset_ids):
            self._delete(report, EntityType.ASSET, asset_id, self._assets.delete)
        for integration_id in reversed(registry.integration_ids):
            self._delete(
                report,
                EntityType.INTEGRATION,
                integration_id,
                self._integrations.delete,
            )
        return report

    @staticmethod
    def _delete(
        report: CleanupReport,
        entity_type: EntityType,
        entity_id: str,
        delete: Callable[[str], object],
    ) -> None:
        try:
            delete(entity_id)
        except Exception as exc:  # cleanup must never mask the original test failure
            LOGGER.exception("Cleanup failed for %s %s", entity_type, entity_id)
            report.failures.append(CleanupFailure(entity_type, entity_id, str(exc)))

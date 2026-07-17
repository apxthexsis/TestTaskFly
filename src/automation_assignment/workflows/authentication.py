"""Typed operation probes used by the authentication matrix spec."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import httpx

from automation_assignment.api import AssetsClient, IntegrationsClient
from automation_assignment.api.routes import ASSETS, INTEGRATIONS
from automation_assignment.domain import UpdateAssetRequest, UpdateIntegrationRequest
from automation_assignment.transport import HttpMethod

MISSING_RESOURCE_ID = "00000000-0000-4000-8000-000000000000"
PROBE_NAME = "unauthorized-probe"


@dataclass(frozen=True)
class OperationProbe:
    name: str
    call: Callable[[], httpx.Response]


def _operation_name(method: HttpMethod, path: str) -> str:
    return f"{method.value} /{path}"


class AuthenticationProbe:
    def __init__(self, integrations: IntegrationsClient, assets: AssetsClient) -> None:
        self._integrations = integrations
        self._assets = assets

    def operations(self) -> tuple[OperationProbe, ...]:
        missing_id = MISSING_RESOURCE_ID
        return (
            OperationProbe(
                _operation_name(HttpMethod.GET, INTEGRATIONS.collection),
                self._integrations.list,
            ),
            OperationProbe(
                _operation_name(HttpMethod.POST, INTEGRATIONS.collection),
                lambda: self._integrations.create_unvalidated(
                    {"name": PROBE_NAME, "type": "webhook"}
                ),
            ),
            OperationProbe(
                _operation_name(HttpMethod.PUT, INTEGRATIONS.collection),
                lambda: self._integrations.update(
                    UpdateIntegrationRequest(id=missing_id, name=PROBE_NAME)
                ),
            ),
            OperationProbe(
                _operation_name(HttpMethod.GET, INTEGRATIONS.item("{id}")),
                lambda: self._integrations.get(missing_id),
            ),
            OperationProbe(
                _operation_name(HttpMethod.DELETE, INTEGRATIONS.item("{id}")),
                lambda: self._integrations.delete(missing_id),
            ),
            OperationProbe(
                _operation_name(HttpMethod.GET, ASSETS.collection),
                lambda: self._assets.list(missing_id),
            ),
            OperationProbe(
                _operation_name(HttpMethod.POST, ASSETS.collection),
                lambda: self._assets.create_unvalidated(
                    {
                        "name": PROBE_NAME,
                        "description": "probe",
                        "integration_id": missing_id,
                    }
                ),
            ),
            OperationProbe(
                _operation_name(HttpMethod.PATCH, ASSETS.collection),
                lambda: self._assets.update(
                    UpdateAssetRequest(
                        id=missing_id,
                        name=PROBE_NAME,
                        description="probe",
                    )
                ),
            ),
            OperationProbe(
                _operation_name(HttpMethod.GET, ASSETS.item("{id}")),
                lambda: self._assets.get(missing_id),
            ),
            OperationProbe(
                _operation_name(HttpMethod.DELETE, ASSETS.item("{id}")),
                lambda: self._assets.delete(missing_id),
            ),
        )

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
from locust import HttpUser, constant_throughput, events, task

from automation_assignment.api import AssetsClient, IntegrationsClient
from automation_assignment.api.routes import ASSETS, INTEGRATION_ID_QUERY, INTEGRATIONS
from automation_assignment.config import Credentials
from automation_assignment.domain import (
    Asset,
    CreateAssetRequest,
    CreateIntegrationRequest,
    Integration,
)
from automation_assignment.transport import HttpClient, normalize_base_url

_credentials = itertools.cycle(
    [
        (os.environ["TEST_USER_1_USERNAME"], os.environ["TEST_USER_1_PASSWORD"]),
        (os.environ["TEST_USER_2_USERNAME"], os.environ["TEST_USER_2_PASSWORD"]),
    ]
)


@dataclass(frozen=True)
class LoadGraph:
    integration: Integration
    asset: Asset


class TenantApiUser(HttpUser):
    """Read-heavy traffic over both resource types and both supplied tenants."""

    host = str(normalize_base_url(os.environ["API_BASE_URL"]))
    wait_time = constant_throughput(1)

    _setup_transport: HttpClient
    _graph: LoadGraph

    def on_start(self) -> None:
        username, password = next(_credentials)
        credentials = Credentials(username=username, password=password)
        self.client.auth = credentials.as_auth_tuple()
        self._setup_transport = HttpClient(self.host, credentials=credentials)
        integrations = IntegrationsClient(self._setup_transport)
        assets = AssetsClient(self._setup_transport)
        suffix = uuid4().hex[:10]

        integration_response = integrations.create(
            CreateIntegrationRequest(name=f"load-integration-{suffix}", type="webhook")
        )
        integration_response.raise_for_status()
        integration = Integration.model_validate(integration_response.json())

        asset_response = assets.create(
            CreateAssetRequest(
                name=f"load-asset-{suffix}",
                description="Locust read target",
                integration_id=integration.id,
            )
        )
        asset_response.raise_for_status()
        self._graph = LoadGraph(
            integration=integration,
            asset=Asset.model_validate(asset_response.json()),
        )

    def on_stop(self) -> None:
        if not hasattr(self, "_setup_transport"):
            return
        if hasattr(self, "_graph"):
            AssetsClient(self._setup_transport).delete(self._graph.asset.id)
            IntegrationsClient(self._setup_transport).delete(self._graph.integration.id)
        self._setup_transport.close()

    @staticmethod
    def _expect_ok(response: Any) -> None:
        if response.status_code != httpx.codes.OK:
            response.failure(f"expected 200, received {response.status_code}")

    @task(5)
    def list_integrations(self) -> None:
        with self.client.get(
            INTEGRATIONS.collection,
            name=f"GET {INTEGRATIONS.contract_collection}",
            catch_response=True,
        ) as response:
            self._expect_ok(response)

    @task(2)
    def get_integration(self) -> None:
        with self.client.get(
            INTEGRATIONS.item(self._graph.integration.id),
            name=f"GET {INTEGRATIONS.contract_item}",
            catch_response=True,
        ) as response:
            self._expect_ok(response)

    @task(2)
    def list_assets(self) -> None:
        with self.client.get(
            ASSETS.collection,
            params={INTEGRATION_ID_QUERY: self._graph.integration.id, "page": 1, "limit": 10},
            name=f"GET {ASSETS.contract_collection}",
            catch_response=True,
        ) as response:
            self._expect_ok(response)

    @task(1)
    def get_asset(self) -> None:
        with self.client.get(
            ASSETS.item(self._graph.asset.id),
            name=f"GET {ASSETS.contract_item}",
            catch_response=True,
        ) as response:
            self._expect_ok(response)


@events.test_stop.add_listener
def enforce_throughput(environment: Any, **_: Any) -> None:
    stats = environment.runner.stats.total
    minimum = int(os.environ.get("LOAD_MIN_SUCCESSFUL_REQUESTS", "1000"))
    successful = stats.num_requests - stats.num_failures
    if successful < minimum or stats.num_failures:
        environment.process_exit_code = 1
        print(
            "LOAD GATE FAILED: "
            f"successful={successful}, required={minimum}, failures={stats.num_failures}"
        )
    else:
        print(
            "LOAD GATE PASSED: "
            f"successful={successful}, required={minimum}, failures={stats.num_failures}"
        )

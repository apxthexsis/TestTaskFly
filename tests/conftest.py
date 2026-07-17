from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import schemathesis
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from pydantic import SecretStr

from automation_assignment.api import AssetsClient, IntegrationsClient
from automation_assignment.config import Credentials, Settings, get_settings
from automation_assignment.contract import (
    SwaggerContract,
    load_swagger_document,
)
from automation_assignment.support import DataFactory
from automation_assignment.transport import HttpClient
from automation_assignment.workflows import (
    AuthenticationProbe,
    CleanupManager,
    CreatedEntityRegistry,
    TenantWorkflow,
)

hypothesis_settings.register_profile(
    "contract",
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
hypothesis_settings.load_profile("contract")


def pytest_html_report_title(report: Any) -> None:
    report.title = "Integration API Release Gate"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


def _transport(
    settings: Settings,
    credentials: Credentials | None = None,
    **kwargs: Any,
) -> HttpClient:
    return HttpClient(
        settings.base_url,
        credentials=credentials,
        timeout_seconds=settings.api_timeout_seconds,
        **kwargs,
    )


@pytest.fixture(scope="session")
def user1_transport(settings: Settings) -> Iterator[HttpClient]:
    with _transport(settings, settings.user1) as transport:
        yield transport


@pytest.fixture(scope="session")
def user2_transport(settings: Settings) -> Iterator[HttpClient]:
    with _transport(settings, settings.user2) as transport:
        yield transport


@pytest.fixture(scope="session")
def anonymous_transport(settings: Settings) -> Iterator[HttpClient]:
    with _transport(settings) as transport:
        yield transport


@pytest.fixture(scope="session")
def invalid_password_transport(settings: Settings) -> Iterator[HttpClient]:
    credentials = Credentials(
        username=settings.user1.username,
        password=SecretStr("not-the-password"),
    )
    with _transport(settings, credentials) as transport:
        yield transport


@pytest.fixture(scope="session")
def unknown_user_transport(settings: Settings) -> Iterator[HttpClient]:
    credentials = Credentials(username="unknown-test-user", password=SecretStr("not-the-password"))
    with _transport(settings, credentials) as transport:
        yield transport


@pytest.fixture(scope="session")
def malformed_auth_transport(settings: Settings) -> Iterator[HttpClient]:
    with _transport(settings, headers={"Authorization": "Basic !!!not-base64!!!"}) as transport:
        yield transport


@pytest.fixture(scope="session")
def user1_integrations_client(user1_transport: HttpClient) -> IntegrationsClient:
    return IntegrationsClient(user1_transport)


@pytest.fixture(scope="session")
def user2_integrations_client(user2_transport: HttpClient) -> IntegrationsClient:
    return IntegrationsClient(user2_transport)


@pytest.fixture(scope="session")
def user1_assets_client(user1_transport: HttpClient) -> AssetsClient:
    return AssetsClient(user1_transport)


@pytest.fixture(scope="session")
def user2_assets_client(user2_transport: HttpClient) -> AssetsClient:
    return AssetsClient(user2_transport)


@pytest.fixture(scope="session")
def swagger_document(settings: Settings) -> dict[str, Any]:
    return load_swagger_document(
        settings.spec_url,
        timeout_seconds=settings.api_timeout_seconds,
        evidence_path=Path("reports/openapi.json"),
    )


@pytest.fixture(scope="session")
def contract(swagger_document: dict[str, Any]) -> SwaggerContract:
    return SwaggerContract(swagger_document)


@pytest.fixture(scope="session")
def api_schema(swagger_document: dict[str, Any], settings: Settings) -> Any:
    del swagger_document
    return schemathesis.openapi.from_url(settings.spec_url)


@pytest.fixture
def data() -> DataFactory:
    return DataFactory()


@pytest.fixture
def user1_registry(
    user1_integrations_client: IntegrationsClient,
    user1_assets_client: AssetsClient,
) -> Iterator[CreatedEntityRegistry]:
    registry = CreatedEntityRegistry()
    yield registry
    CleanupManager(user1_integrations_client, user1_assets_client).cleanup(registry)


@pytest.fixture
def user2_registry(
    user2_integrations_client: IntegrationsClient,
    user2_assets_client: AssetsClient,
) -> Iterator[CreatedEntityRegistry]:
    registry = CreatedEntityRegistry()
    yield registry
    CleanupManager(user2_integrations_client, user2_assets_client).cleanup(registry)


@pytest.fixture
def user1_workflow(
    user1_integrations_client: IntegrationsClient,
    user1_assets_client: AssetsClient,
    user1_registry: CreatedEntityRegistry,
    data: DataFactory,
) -> TenantWorkflow:
    return TenantWorkflow(
        user1_integrations_client,
        user1_assets_client,
        user1_registry,
        data,
    )


@pytest.fixture
def user2_workflow(
    user2_integrations_client: IntegrationsClient,
    user2_assets_client: AssetsClient,
    user2_registry: CreatedEntityRegistry,
    data: DataFactory,
) -> TenantWorkflow:
    return TenantWorkflow(
        user2_integrations_client,
        user2_assets_client,
        user2_registry,
        data,
    )


def _authentication_probe(transport: HttpClient) -> AuthenticationProbe:
    return AuthenticationProbe(IntegrationsClient(transport), AssetsClient(transport))


@pytest.fixture(scope="session")
def anonymous_authentication_probe(anonymous_transport: HttpClient) -> AuthenticationProbe:
    return _authentication_probe(anonymous_transport)


@pytest.fixture(scope="session")
def invalid_password_authentication_probe(
    invalid_password_transport: HttpClient,
) -> AuthenticationProbe:
    return _authentication_probe(invalid_password_transport)


@pytest.fixture(scope="session")
def unknown_user_authentication_probe(unknown_user_transport: HttpClient) -> AuthenticationProbe:
    return _authentication_probe(unknown_user_transport)


@pytest.fixture(scope="session")
def malformed_authentication_probe(malformed_auth_transport: HttpClient) -> AuthenticationProbe:
    return _authentication_probe(malformed_auth_transport)

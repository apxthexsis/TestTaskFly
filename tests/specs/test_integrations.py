from __future__ import annotations

import httpx
import pytest

from automation_assignment.api import IntegrationsClient
from automation_assignment.api.routes import INTEGRATIONS
from automation_assignment.contract import SwaggerContract
from automation_assignment.domain import Integration, UpdateIntegrationRequest
from automation_assignment.support import DataFactory
from automation_assignment.transport import HttpMethod
from automation_assignment.workflows import CreatedEntityRegistry, TenantWorkflow
from automation_assignment.workflows.authentication import MISSING_RESOURCE_ID

pytestmark = pytest.mark.api


@pytest.mark.bug("BUG-003")
def test_create_integration_matches_published_contract(
    user1_integrations_client: IntegrationsClient,
    user1_registry: CreatedEntityRegistry,
    data: DataFactory,
    contract: SwaggerContract,
) -> None:
    response = user1_integrations_client.create(data.integration())
    if response.is_success:
        user1_registry.register_integration(Integration.model_validate(response.json()))

    assert response.status_code == httpx.codes.OK, response.text
    contract.validate_response(INTEGRATIONS.contract_collection, HttpMethod.POST, response)


def test_integration_crud_behavior(
    user1_integrations_client: IntegrationsClient,
    user1_registry: CreatedEntityRegistry,
    user1_workflow: TenantWorkflow,
    data: DataFactory,
    contract: SwaggerContract,
) -> None:
    created = user1_workflow.create_integration()

    fetched_response = user1_integrations_client.get(created.id)
    assert fetched_response.status_code == httpx.codes.OK, fetched_response.text
    contract.validate_response(
        INTEGRATIONS.contract_item,
        HttpMethod.GET,
        fetched_response,
    )
    assert Integration.model_validate(fetched_response.json()) == created

    updated_name = data.integration().name
    updated_response = user1_integrations_client.update(
        UpdateIntegrationRequest(id=created.id, name=updated_name)
    )
    assert updated_response.status_code == httpx.codes.OK, updated_response.text
    contract.validate_response(
        INTEGRATIONS.contract_collection,
        HttpMethod.PUT,
        updated_response,
    )
    assert Integration.model_validate(updated_response.json()).name == updated_name

    listed_response = user1_integrations_client.list(page=1, limit=100)
    assert listed_response.status_code == httpx.codes.OK, listed_response.text
    contract.validate_response(
        INTEGRATIONS.contract_collection,
        HttpMethod.GET,
        listed_response,
    )
    assert created.id in {item["id"] for item in listed_response.json()}

    deleted_response = user1_integrations_client.delete(created.id)
    assert deleted_response.status_code == httpx.codes.OK, deleted_response.text
    contract.validate_response(
        INTEGRATIONS.contract_item,
        HttpMethod.DELETE,
        deleted_response,
    )
    user1_registry.unregister_integration(created.id)
    assert user1_integrations_client.get(created.id).status_code == httpx.codes.NOT_FOUND


def test_integration_pagination_limit_is_honored(
    user1_integrations_client: IntegrationsClient,
    user1_workflow: TenantWorkflow,
) -> None:
    for _ in range(3):
        user1_workflow.create_integration()

    response = user1_integrations_client.list(page=1, limit=1)
    assert response.status_code == httpx.codes.OK, response.text
    assert len(response.json()) <= 1


@pytest.mark.bug("BUG-006")
@pytest.mark.parametrize("page,limit", [(0, 10), (-1, 10), (1, 0), (1, -1)])
def test_integration_pagination_rejects_invalid_boundaries(
    user1_integrations_client: IntegrationsClient,
    page: int,
    limit: int,
) -> None:
    response = user1_integrations_client.list(page=page, limit=limit)
    assert response.status_code == httpx.codes.BAD_REQUEST, response.text


@pytest.mark.bug("BUG-004")
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "missing-type"},
        {"type": "missing-name"},
        {"name": "", "type": "webhook"},
        {"name": 42, "type": "webhook"},
        {"name": "unknown-field", "type": "webhook", "unexpected": True},
    ],
)
def test_create_integration_rejects_invalid_payloads(
    user1_integrations_client: IntegrationsClient,
    payload: dict[str, object],
) -> None:
    response = user1_integrations_client.create_unvalidated(payload)
    assert response.status_code == httpx.codes.BAD_REQUEST, response.text


def test_create_integration_rejects_malformed_json(
    user1_integrations_client: IntegrationsClient,
) -> None:
    response = user1_integrations_client.create_raw('{"name":')
    assert response.status_code == httpx.codes.BAD_REQUEST, response.text


def test_unknown_integration_returns_not_found(
    user1_integrations_client: IntegrationsClient,
) -> None:
    response = user1_integrations_client.get(MISSING_RESOURCE_ID)
    assert response.status_code == httpx.codes.NOT_FOUND, response.text

from __future__ import annotations

import httpx
import pytest

from automation_assignment.api import AssetsClient
from automation_assignment.api.routes import ASSETS
from automation_assignment.contract import SwaggerContract
from automation_assignment.domain import Asset, UpdateAssetRequest
from automation_assignment.support import DataFactory
from automation_assignment.transport import HttpMethod
from automation_assignment.workflows import CreatedEntityRegistry, TenantWorkflow
from automation_assignment.workflows.authentication import MISSING_RESOURCE_ID

pytestmark = pytest.mark.api


@pytest.mark.bug("BUG-003")
def test_create_asset_matches_published_contract(
    user1_assets_client: AssetsClient,
    user1_registry: CreatedEntityRegistry,
    user1_workflow: TenantWorkflow,
    data: DataFactory,
    contract: SwaggerContract,
) -> None:
    integration = user1_workflow.create_integration()
    response = user1_assets_client.create(data.asset(integration.id))
    if response.is_success:
        user1_registry.register_asset(Asset.model_validate(response.json()))

    assert response.status_code == httpx.codes.OK, response.text
    contract.validate_response(ASSETS.contract_collection, HttpMethod.POST, response)


def test_asset_crud_behavior(
    user1_assets_client: AssetsClient,
    user1_registry: CreatedEntityRegistry,
    user1_workflow: TenantWorkflow,
    data: DataFactory,
    contract: SwaggerContract,
) -> None:
    graph = user1_workflow.create_graph()
    created = graph.asset

    fetched_response = user1_assets_client.get(created.id)
    assert fetched_response.status_code == httpx.codes.OK, fetched_response.text
    contract.validate_response(ASSETS.contract_item, HttpMethod.GET, fetched_response)
    assert Asset.model_validate(fetched_response.json()) == created

    new_name = data.asset(graph.integration.id).name
    updated_response = user1_assets_client.update(
        UpdateAssetRequest(
            id=created.id,
            name=new_name,
            description="updated by automation",
        )
    )
    assert updated_response.status_code == httpx.codes.OK, updated_response.text
    contract.validate_response(
        ASSETS.contract_collection,
        HttpMethod.PATCH,
        updated_response,
    )
    assert Asset.model_validate(updated_response.json()).name == new_name

    listed_response = user1_assets_client.list(graph.integration.id, page=1, limit=100)
    assert listed_response.status_code == httpx.codes.OK, listed_response.text
    contract.validate_response(
        ASSETS.contract_collection,
        HttpMethod.GET,
        listed_response,
    )
    assert created.id in {item["id"] for item in listed_response.json()}

    deleted_response = user1_assets_client.delete(created.id)
    assert deleted_response.status_code == httpx.codes.NO_CONTENT, deleted_response.text
    contract.validate_response(ASSETS.contract_item, HttpMethod.DELETE, deleted_response)
    user1_registry.unregister_asset(created.id)
    assert user1_assets_client.get(created.id).status_code == httpx.codes.NOT_FOUND


@pytest.mark.bug("BUG-005")
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "missing-relation", "description": "invalid"},
        {"name": "", "description": "invalid", "integration_id": "missing"},
        {"name": 42, "description": "invalid", "integration_id": "missing"},
        {
            "name": "unknown-field",
            "description": "invalid",
            "integration_id": "missing",
            "unexpected": True,
        },
    ],
)
def test_create_asset_rejects_invalid_payloads(
    user1_assets_client: AssetsClient,
    payload: dict[str, object],
) -> None:
    response = user1_assets_client.create_unvalidated(payload)
    assert response.status_code in {httpx.codes.BAD_REQUEST, httpx.codes.NOT_FOUND}, response.text


@pytest.mark.bug("BUG-005")
def test_create_asset_rejects_unknown_integration(
    user1_assets_client: AssetsClient,
    data: DataFactory,
) -> None:
    response = user1_assets_client.create(data.asset(MISSING_RESOURCE_ID))
    assert response.status_code == httpx.codes.NOT_FOUND, response.text


def test_create_asset_rejects_malformed_json(user1_assets_client: AssetsClient) -> None:
    response = user1_assets_client.create_raw('{"name":')
    assert response.status_code == httpx.codes.BAD_REQUEST, response.text


@pytest.mark.bug("BUG-006")
@pytest.mark.parametrize("page,limit", [(0, 10), (-1, 10), (1, 0), (1, -1)])
def test_asset_pagination_rejects_invalid_boundaries(
    user1_assets_client: AssetsClient,
    page: int,
    limit: int,
) -> None:
    response = user1_assets_client.list(MISSING_RESOURCE_ID, page=page, limit=limit)
    assert response.status_code == httpx.codes.BAD_REQUEST, response.text

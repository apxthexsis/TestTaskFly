from __future__ import annotations

import httpx
import pytest

from automation_assignment.api import AssetsClient, IntegrationsClient
from automation_assignment.domain import UpdateAssetRequest, UpdateIntegrationRequest
from automation_assignment.workflows import TenantWorkflow

pytestmark = [pytest.mark.api, pytest.mark.security]

CROSS_TENANT_REJECTION_STATUSES = {httpx.codes.FORBIDDEN, httpx.codes.NOT_FOUND}


def test_tenants_cannot_list_each_others_integrations(
    user1_workflow: TenantWorkflow,
    user2_workflow: TenantWorkflow,
    user1_integrations_client: IntegrationsClient,
    user2_integrations_client: IntegrationsClient,
) -> None:
    graph1 = user1_workflow.create_graph()
    graph2 = user2_workflow.create_graph()
    user1_ids = {item["id"] for item in user1_integrations_client.list(page=1, limit=100).json()}
    user2_ids = {item["id"] for item in user2_integrations_client.list(page=1, limit=100).json()}
    assert graph1.integration.id in user1_ids
    assert graph2.integration.id not in user1_ids
    assert graph2.integration.id in user2_ids
    assert graph1.integration.id not in user2_ids


def test_cross_tenant_integration_operations_are_rejected(
    user1_workflow: TenantWorkflow,
    user2_integrations_client: IntegrationsClient,
    user1_integrations_client: IntegrationsClient,
) -> None:
    graph = user1_workflow.create_graph()
    responses = {
        "get": user2_integrations_client.get(graph.integration.id),
        "update": user2_integrations_client.update(
            UpdateIntegrationRequest(id=graph.integration.id, name="cross-tenant-update")
        ),
        "delete": user2_integrations_client.delete(graph.integration.id),
    }
    assert all(
        response.status_code in CROSS_TENANT_REJECTION_STATUSES for response in responses.values()
    ), {key: (value.status_code, value.text) for key, value in responses.items()}
    assert user1_integrations_client.get(graph.integration.id).status_code == httpx.codes.OK


def test_cross_tenant_asset_operations_and_relationships_are_rejected(
    user1_workflow: TenantWorkflow,
    user2_assets_client: AssetsClient,
    user1_assets_client: AssetsClient,
) -> None:
    graph = user1_workflow.create_graph()
    responses = {
        "get": user2_assets_client.get(graph.asset.id),
        "update": user2_assets_client.update(
            UpdateAssetRequest(
                id=graph.asset.id,
                name="cross-tenant-update",
                description="must not be accepted",
            )
        ),
        "delete": user2_assets_client.delete(graph.asset.id),
        "create-under-foreign-integration": user2_assets_client.create_unvalidated(
            {
                "name": "cross-tenant-create",
                "description": "must not be accepted",
                "integration_id": graph.integration.id,
            }
        ),
    }
    assert all(
        response.status_code in CROSS_TENANT_REJECTION_STATUSES for response in responses.values()
    ), {key: (value.status_code, value.text) for key, value in responses.items()}

    foreign_list = user2_assets_client.list(graph.integration.id)
    if foreign_list.status_code == httpx.codes.OK:
        assert graph.asset.id not in {item["id"] for item in foreign_list.json()}
    else:
        assert foreign_list.status_code in CROSS_TENANT_REJECTION_STATUSES, foreign_list.text
    assert user1_assets_client.get(graph.asset.id).status_code == httpx.codes.OK


def test_tenant_identifiers_are_stable_and_distinct(
    user1_workflow: TenantWorkflow,
    user2_workflow: TenantWorkflow,
) -> None:
    graph1 = user1_workflow.create_graph()
    graph2 = user2_workflow.create_graph()
    assert graph1.integration.tenant_id == graph1.asset.tenant_id
    assert graph2.integration.tenant_id == graph2.asset.tenant_id
    assert graph1.integration.tenant_id != graph2.integration.tenant_id

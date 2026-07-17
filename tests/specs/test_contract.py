from __future__ import annotations

from base64 import b64encode
from typing import Any

import pytest
import schemathesis

from automation_assignment.api.routes import ASSETS, INTEGRATIONS
from automation_assignment.config import Settings
from automation_assignment.contract import SwaggerContract
from automation_assignment.transport import HttpMethod

pytestmark = [pytest.mark.api, pytest.mark.contract]


def test_swagger_root_and_all_documented_operations(contract: SwaggerContract) -> None:
    contract.assert_valid_root()
    expected = {
        (ASSETS.contract_collection, HttpMethod.GET.value.lower()),
        (ASSETS.contract_collection, HttpMethod.POST.value.lower()),
        (ASSETS.contract_collection, HttpMethod.PATCH.value.lower()),
        (ASSETS.contract_item, HttpMethod.GET.value.lower()),
        (ASSETS.contract_item, HttpMethod.DELETE.value.lower()),
        (INTEGRATIONS.contract_collection, HttpMethod.GET.value.lower()),
        (INTEGRATIONS.contract_collection, HttpMethod.POST.value.lower()),
        (INTEGRATIONS.contract_collection, HttpMethod.PUT.value.lower()),
        (INTEGRATIONS.contract_item, HttpMethod.GET.value.lower()),
        (INTEGRATIONS.contract_item, HttpMethod.DELETE.value.lower()),
    }
    actual = {
        (path, method)
        for path, path_item in contract.document["paths"].items()
        for method in path_item
        if method in {"get", "post", "put", "patch", "delete"}
    }
    assert actual == expected


@pytest.mark.bug("BUG-001")
def test_swagger_declares_basic_authentication(contract: SwaggerContract) -> None:
    contract.assert_basic_auth_declared()


@pytest.mark.bug("BUG-001")
def test_all_protected_operations_document_unauthorized_response(contract: SwaggerContract) -> None:
    missing = []
    for path, path_item in contract.document["paths"].items():
        for method, operation in path_item.items():
            if method in {"get", "post", "put", "patch", "delete"} and "401" not in operation.get(
                "responses", {}
            ):
                missing.append(f"{method.upper()} {path}")
    assert not missing, f"Protected operations missing a documented 401 response: {missing}"


@pytest.mark.bug("BUG-002")
def test_asset_identifier_type_is_consistent(contract: SwaggerContract) -> None:
    model_type = contract.document["definitions"]["model.Asset"]["properties"]["id"]["type"]
    path_parameters = contract.operation(ASSETS.contract_item, HttpMethod.GET)["parameters"]
    path_type = next(item["type"] for item in path_parameters if item["name"] == "id")
    assert path_type == model_type, f"model.Asset.id is {model_type}, path id is {path_type}"


lazy_schema = schemathesis.pytest.from_fixture("api_schema")


@lazy_schema.include(method="GET").parametrize()
def test_generated_read_only_contract_cases(case: Any, settings: Settings) -> None:
    token = b64encode(
        f"{settings.user1.username}:{settings.user1.password.get_secret_value()}".encode()
    ).decode()
    case.headers = dict(case.headers or {})
    case.headers["Authorization"] = f"Basic {token}"
    case.call_and_validate()

from __future__ import annotations

import httpx
import pytest

from automation_assignment.contract import ContractError, SwaggerContract
from automation_assignment.transport import HttpMethod


def _document() -> dict[str, object]:
    return {
        "swagger": "2.0",
        "basePath": "/api/v1",
        "securityDefinitions": {"basicAuth": {"type": "basic"}},
        "security": [{"basicAuth": []}],
        "paths": {
            "/things": {
                "get": {
                    "responses": {
                        "200": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/Thing"},
                            }
                        }
                    }
                }
            }
        },
        "definitions": {
            "Thing": {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            }
        },
    }


def _response(status: int, body: object) -> httpx.Response:
    return httpx.Response(status, json=body, request=httpx.Request("GET", "http://test/things"))


def test_contract_validates_local_references() -> None:
    contract = SwaggerContract(_document())  # type: ignore[arg-type]
    contract.assert_valid_root()
    contract.assert_basic_auth_declared()
    contract.validate_response("/things", HttpMethod.GET, _response(200, [{"id": "one"}]))


def test_contract_rejects_invalid_response_shape() -> None:
    contract = SwaggerContract(_document())  # type: ignore[arg-type]
    with pytest.raises(ContractError, match="does not match"):
        contract.validate_response("/things", HttpMethod.GET, _response(200, [{"id": 42}]))


def test_contract_rejects_undocumented_status() -> None:
    contract = SwaggerContract(_document())  # type: ignore[arg-type]
    with pytest.raises(ContractError, match="Undocumented status"):
        contract.validate_response("/things", HttpMethod.GET, _response(500, {}))

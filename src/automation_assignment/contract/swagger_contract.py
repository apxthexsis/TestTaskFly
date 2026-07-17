"""Swagger 2.0 inspection and runtime response validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import httpx
from jsonschema import Draft4Validator

from automation_assignment.transport import HttpMethod


class ContractError(AssertionError):
    pass


class SwaggerContract:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document

    def operation(self, path: str, method: HttpMethod) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], self.document["paths"][path][method.value.lower()])
        except KeyError as exc:
            message = f"Operation missing from contract: {method.value} {path}"
            raise ContractError(message) from exc

    def assert_valid_root(self) -> None:
        if self.document.get("swagger") != "2.0":
            raise ContractError("Expected a Swagger 2.0 document")
        if self.document.get("basePath") != "/api/v1":
            raise ContractError("Expected basePath /api/v1")
        if not isinstance(self.document.get("paths"), dict):
            raise ContractError("Contract paths must be an object")

    def assert_basic_auth_declared(self) -> None:
        definitions = self.document.get("securityDefinitions", {})
        basic_schemes = [
            name for name, definition in definitions.items() if definition.get("type") == "basic"
        ]
        if not basic_schemes:
            raise ContractError("Swagger contract does not declare HTTP Basic Authentication")
        if not self.document.get("security"):
            protected = any(
                operation.get("security")
                for path_item in self.document.get("paths", {}).values()
                for operation in path_item.values()
                if isinstance(operation, dict)
            )
            if not protected:
                raise ContractError("Basic Authentication is declared but applied to no operations")

    def response_schema(
        self,
        path: str,
        method: HttpMethod,
        status_code: int,
    ) -> dict[str, Any] | None:
        operation = self.operation(path, method)
        response = operation.get("responses", {}).get(str(status_code))
        if response is None:
            raise ContractError(
                f"Undocumented status {status_code} for {method.value} {path}; "
                f"documented={sorted(operation.get('responses', {}))}"
            )
        schema = response.get("schema")
        return self._dereference(schema) if schema else None

    def validate_response(
        self,
        path: str,
        method: HttpMethod,
        response: httpx.Response,
    ) -> None:
        schema = self.response_schema(path, method, response.status_code)
        if schema is None or response.status_code == httpx.codes.NO_CONTENT:
            return
        try:
            instance = response.json()
        except ValueError as exc:
            raise ContractError(
                f"Expected JSON for {method.value} {path} status {response.status_code}"
            ) from exc
        errors = sorted(
            Draft4Validator(schema).iter_errors(instance),
            key=lambda item: list(item.path),
        )
        if errors:
            details = "; ".join(error.message for error in errors)
            raise ContractError(f"Response does not match Swagger schema: {details}")

    def _dereference(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self._dereference(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            target = self._resolve_pointer(value["$ref"])
            merged = {**target, **{key: item for key, item in value.items() if key != "$ref"}}
            return self._dereference(merged)
        return {key: self._dereference(item) for key, item in deepcopy(value).items()}

    def _resolve_pointer(self, pointer: str) -> dict[str, Any]:
        if not pointer.startswith("#/"):
            raise ContractError(f"Only local Swagger references are supported: {pointer}")
        current: Any = self.document
        for token in pointer[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            current = current[token]
        if not isinstance(current, dict):
            raise ContractError(f"Swagger reference is not an object: {pointer}")
        return current

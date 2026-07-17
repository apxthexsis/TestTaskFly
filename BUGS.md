# Defect Report

The following defects were reproduced on Apple Silicon Docker on 2026-07-17. They remain failing release-gate tests; the load gate passed independently. See the verified execution section in `TEST_PLAN.md` for the final run totals.

## BUG-001 - Basic Authentication is absent from the OpenAPI contract

- **Severity:** High
- **Area:** API contract / authentication
- **Prerequisite:** Start the published service and fetch `/swagger/doc.json`.
- **Steps:** Inspect the root `securityDefinitions` and operation/root `security` declarations.
- **Expected:** The Swagger 2.0 document declares HTTP Basic Authentication and marks protected operations accordingly.
- **Actual:** The contract contains no Basic Authentication security definition even though every API operation is protected by Basic Authentication.
- **Impact:** Generated clients and contract tools cannot discover or apply the required authentication scheme, and unauthorized responses are missing from parts of the declared contract.
- **Automated evidence:** `tests/specs/test_contract.py::test_swagger_declares_basic_authentication`

## BUG-002 - Asset identifier has contradictory contract types

- **Severity:** Medium
- **Area:** API contract / assets
- **Prerequisite:** Fetch `/swagger/doc.json`.
- **Steps:** Compare `model.Asset.id` with the `id` path parameter on `/assets/{id}`.
- **Expected:** The identifier uses one consistent type across the resource schema and all operations.
- **Actual:** `model.Asset.id` is declared as a string while `/assets/{id}` declares the path parameter as an integer.
- **Impact:** Valid resource IDs may be rejected by generated clients and generated contract cases exercise the wrong identifier domain.
- **Automated evidence:** `tests/specs/test_contract.py::test_asset_identifier_type_is_consistent`

## BUG-003 - Create endpoints return an undocumented success status

- **Severity:** High
- **Area:** API contract / integrations / assets
- **Prerequisite:** Authenticate as either supplied user.
- **Steps:** POST a valid integration or asset body to the corresponding collection endpoint.
- **Expected:** The service returns the Swagger-documented `200` response and matching response schema.
- **Actual:** Creation returns `201`, which is absent from the documented responses.
- **Impact:** Contract validation and generated clients reject successful creation; dependent CRUD and tenant scenarios cannot safely continue under the published contract.
- **Automated evidence:** `tests/specs/test_integrations.py::test_create_integration_matches_published_contract` and `tests/specs/test_assets.py::test_create_asset_matches_published_contract`. Behavioral CRUD and tenant tests continue independently.

## BUG-004 - Integration payload validation is inconsistent

- **Severity:** High
- **Area:** `POST /api/v1/integrations`
- **Prerequisite:** Authenticate as either supplied user.
- **Steps:** Submit bodies with a missing `type`, an unknown property, missing required values, empty values, or wrong field types.
- **Expected:** Every invalid request is rejected with `400` and a stable error response.
- **Actual:** Missing `type` and unknown fields are accepted; other invalid variants can return `500` instead of `400`.
- **Impact:** Invalid records may be persisted and client mistakes can trigger server errors.
- **Automated evidence:** `tests/specs/test_integrations.py::test_create_integration_rejects_invalid_payloads`.

## BUG-005 - Asset validation does not enforce required data or relationship integrity

- **Severity:** High
- **Area:** `POST /api/v1/assets`
- **Prerequisite:** Authenticate as either supplied user.
- **Steps:** Submit an asset with missing fields, an empty name, an unknown field, or a nonexistent `integration_id`.
- **Expected:** Invalid bodies return `400`; nonexistent integration references return `404` or another documented client error.
- **Actual:** The service accepts these requests and returns `201`.
- **Impact:** Orphaned and structurally invalid assets can be created.
- **Automated evidence:** `tests/specs/test_assets.py::test_create_asset_rejects_invalid_payloads` and `tests/specs/test_assets.py::test_create_asset_rejects_unknown_integration`.

## BUG-006 - Pagination boundaries are not validated safely

- **Severity:** Medium
- **Area:** `GET /api/v1/integrations`, `GET /api/v1/assets`
- **Prerequisite:** Authenticate as either supplied user.
- **Steps:** Send `page=0`, `page=-1`, `limit=0`, or `limit=-1`.
- **Expected:** Every invalid boundary returns `400` with a documented error representation.
- **Actual:** Requests return a mixture of `200` and `500`; one `GET /integrations?page=0` response is an empty `500` without JSON or `Content-Type`.
- **Impact:** Invalid inputs can cause internal errors and clients receive inconsistent behavior.
- **Automated evidence:** `tests/specs/test_integrations.py::test_integration_pagination_rejects_invalid_boundaries`, `tests/specs/test_assets.py::test_asset_pagination_rejects_invalid_boundaries`, and `tests/specs/test_contract.py::test_generated_read_only_contract_cases`.

## BUG-007 - Integration update checks routing before authentication

- **Severity:** High
- **Area:** `PUT /api/v1/integrations` / authentication
- **Prerequisite:** Prepare requests with no credentials, malformed Basic Auth, a wrong password, and an unknown user.
- **Steps:** Call the integration update operation with each invalid authentication variant.
- **Expected:** Every protected operation consistently returns `401` before revealing resource or routing behavior.
- **Actual:** `PUT /integrations` returns `404` for these callers.
- **Impact:** Authentication behavior is inconsistent and exposes endpoint-processing differences to unauthenticated clients.
- **Automated evidence:** `tests/specs/test_authentication.py::test_every_operation_rejects_invalid_authentication`.

## BUG-008 - A schema-valid generated asset query is rejected

- **Severity:** Medium
- **Area:** Swagger contract / `GET /api/v1/assets`
- **Prerequisite:** Authenticate as either supplied user and load the live Swagger document.
- **Steps:** Send the schema-generated query `integrationId=&amp;page=0`.
- **Expected:** The implementation accepts values allowed by the contract, or the contract defines the missing constraints and documents the rejection response.
- **Actual:** The request is contract-valid but the service returns `400`.
- **Impact:** Generated clients and contract-driven tests cannot predict valid query input.
- **Automated evidence:** `tests/specs/test_contract.py::test_generated_read_only_contract_cases`.

## BUG-009 - Unsupported methods return not found instead of method not allowed

- **Severity:** Low
- **Area:** HTTP semantics / integration and asset resource paths
- **Prerequisite:** Service is running.
- **Steps:** Send `TRACE` to an integration or asset resource path.
- **Expected:** Existing resources reject unsupported methods with `405 Method Not Allowed` and an `Allow` header.
- **Actual:** The service returns `404`.
- **Impact:** Clients cannot distinguish an unknown resource from an unsupported method.
- **Automated evidence:** Schemathesis method-not-allowed check recorded under `tests/specs/test_contract.py::test_generated_read_only_contract_cases`.

## BUG-010 - Tenant isolation is not enforced

- **Severity:** Critical
- **Area:** Multi-tenancy / integrations / assets
- **Prerequisite:** Create independent integration-and-asset graphs as `test1` and `test2`.
- **Steps:** List the other tenant's integrations; GET and DELETE a foreign integration; access or mutate a foreign asset; create an asset under the other tenant's integration.
- **Expected:** Foreign resources are absent from lists and every direct cross-tenant operation returns `403` or `404` without changing the owner's data.
- **Actual:** Tenant 1 can list Tenant 2 integrations; cross-tenant integration GET and DELETE succeed; foreign asset operations and creation under a foreign integration also succeed.
- **Impact:** One customer can discover, access, modify, delete, or attach data to another customer's resources.
- **Automated evidence:** `tests/specs/test_tenant_segregation.py::test_tenants_cannot_list_each_others_integrations`, `test_cross_tenant_integration_operations_are_rejected`, and `test_cross_tenant_asset_operations_and_relationships_are_rejected`.

## BUG-011 - Owner cannot update an existing integration

- **Severity:** High
- **Area:** `PUT /api/v1/integrations`
- **Prerequisite:** Authenticate as the owner and create a valid integration.
- **Steps:** Send the documented update body containing that integration ID and a new name.
- **Expected:** The owner receives `200` and the persisted integration contains the new name.
- **Actual:** The update returns `404` for the existing owned integration.
- **Impact:** The documented integration update operation is unusable for normal owner CRUD.
- **Automated evidence:** `tests/specs/test_integrations.py::test_integration_crud_behavior`.

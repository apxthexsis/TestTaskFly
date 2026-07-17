# Test Plan

## Objective and release criteria

Assess whether the REST API is ready for release by verifying Basic Authentication, integration and asset behavior, tenant segregation, conformance with its exposed Swagger 2.0 document, and at least 1,000 successful requests per minute. Any reproducible security, contract, functional, or throughput defect fails the release gate and is documented in `BUGS.md`.

## Scope and approach

The suite covers the ten documented operations across `/integrations`, `/integrations/{id}`, `/assets`, and `/assets/{id}`. Positive flows use typed models and both supplied tenants. Negative coverage includes absent and invalid authentication, malformed JSON, invalid identifiers and relationships, missing/empty/wrong-type data, unknown fields, pagination boundaries, deleted resources, and cross-tenant access.

The live Swagger document is archived for each run. Targeted tests validate operation status codes and response bodies against it. A bounded Schemathesis read-only pass generates additional query and path cases while avoiding uncontrolled destructive state.

The load profile distributes authenticated read requests evenly across both tenants and covers integration lists/items plus asset lists/items. It runs for 60 seconds at a configured capacity above 20 RPS and passes only when at least 1,000 requests succeed with no unexpected responses.

## Test data and isolation

All created names contain a per-run UUID. Function-scoped entity registries are cleaned by a dependency-aware cleanup manager that deletes assets before integrations, even after assertion failures. Tenant-isolation tests create independent graphs for both users and verify cross-tenant read, update, delete, relationship, and list behavior without relying on test order.

Contract-status checks are intentionally separate from behavioral setup. A successful but undocumented status still fails its dedicated release-gate test, while dependent CRUD and tenant scenarios continue against the returned entity. This prevents one root cause from hiding unrelated behavior.

## Risks and limitations

- The service is in-memory and has no documented reset endpoint, so cleanup is best effort and unique data prevents collisions.
- Swagger schemas declare few validation constraints; explicit negative tests are required in addition to generated cases.
- A single-host load test demonstrates the stated throughput on that host, not horizontal scalability or production latency objectives.
- The assignment provides no formal latency SLO. Latency percentiles are reported diagnostically but do not fail the gate.

## Evidence

The one-command runner preserves self-contained HTML, JUnit, the live contract, Locust HTML/CSV, service logs, host/container statistics, and an aggregate quality/functional/load summary. Secrets and Authorization headers must not appear in any artifact.

## Verified execution

The refactored framework was run on 2026-07-17 on an Apple Silicon Mac using Docker Engine 29.6.1 and Compose 5.3.0. Formatting, lint, strict typing, architecture rules, unit tests, collection, and setup completed without framework errors. JUnit recorded 29 passed and 37 failed cases out of 66 generated cases; the failures are confirmed product, security, and contract defects. All CRUD and tenant scenarios continued beyond create-status validation, revealing critical cross-tenant access and mutation failures. The independent load gate passed with 1,500 successful requests in the measured minute at 25.42 RPS, zero failures, p50 9 ms, p95 20 ms, and p99 24 ms across all four intended read endpoint families. The overall release decision is **FAIL** because product defects remain release blockers.

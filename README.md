# Automation Engineer Home Assignment

This project tests the Infralight multi-tenant REST API with Python 3.12 and Pytest. Endpoint-specific API clients are the REST equivalent of page objects: specs describe intent while HTTP transport, typed domain models, endpoint calls, lifecycle workflows, contract validation, and diagnostics live in explicit layers.

## One-command execution (macOS/Linux)

Requirements: Docker with Compose v2. The assignment image supports both Apple Silicon and AMD64 hosts.

```bash
make assignment
```

This invokes `run-assignment.sh`; `bash ./run-assignment.sh` is the equivalent command when Make is unavailable. The script uses `.env` when present and otherwise the assignment-safe defaults in `.env.example`. It runs the formatting/lint/type gate, starts the service, waits for Swagger, runs the complete Pytest release gate, runs Locust even if functional tests fail, saves evidence under `reports/`, stops the containers, and returns a non-zero status if any gate fails.

Generated evidence:

- `reports/pytest-report.html` and `reports/junit.xml`
- `reports/openapi.json` and `reports/service.log`
- `reports/locust-report.html` and `reports/locust_stats*.csv`
- `reports/docker-stats-before-load.txt` and `reports/docker-stats-after-load.txt`
- `reports/run-summary.md`

Product defects intentionally remain failed tests. This is a release-readiness suite, so a non-zero exit can be the correct result; consult the HTML report and `BUGS.md`.

The refactored verified run was executed on Apple Silicon Docker Engine 29.6.1 / Compose 5.3.0. All framework quality checks passed. JUnit recorded 29 passes, 37 product/security/contract failures, and no errors across 66 generated cases. Unlike the baseline run, CRUD and all tenant scenarios continued beyond the create-status defect and exposed critical tenant-isolation failures. Load passed with 1,500 successful requests at 25.42 RPS and zero failures across integration and asset list/item endpoints (p50 9 ms, p95 20 ms, p99 24 ms).

## Architecture

The detailed dependency rules and design decisions are documented in `ARCHITECTURE.md` and enforced by `tests/unit/test_architecture.py`.

```text
tests/specs                 thin scenario intent and release decisions
        |
workflows/                  tenant setup, authentication probes, cleanup
        |
api/                        IntegrationsClient / AssetsClient gateways
        |
transport/                  URL invariants, HTTP methods, auth, redaction
        |
service container           /api/v1 and /swagger/doc.json

domain/                     transport-independent request/response models
contract/                   live Swagger loader and response validator
config/                     environment and secret boundary
commands/ + __main__.py     one CLI entry point with explicit subcommands
```

`Settings` is the only configuration boundary. Credentials use `SecretStr`, Authorization headers are redacted, and every test-data name has a unique run prefix. `CreatedEntityRegistry` records ownership while `CleanupManager` deletes assets before integrations and returns structured cleanup failures without masking the original assertion.

Transport accepts only relative API paths and fails fast instead of silently applying `lstrip`/`rstrip` fixes. Routes and HTTP methods have one source of truth. Typed create/update calls are separate from deliberately unvalidated negative-test calls, so malformed payload coverage does not weaken the positive API surface.

Published status-code compliance is tested separately from behavioral setup. Therefore an undocumented but successful `201` remains a release-gate failure while CRUD, pagination, and tenant-isolation scenarios continue and provide independent evidence instead of cascading from one setup assertion.

## Useful developer commands

With Python 3.12 and [uv](https://docs.astral.sh/uv/) installed:

```bash
uv sync --all-groups
uv run ruff check .
uv run mypy src
uv run pytest tests/unit
uv run automation-assignment --help
```

Against an already running service, export the variables from `.env.example`, change `API_BASE_URL` and `API_SPEC_URL` to reachable addresses, then run:

```bash
uv run pytest tests/specs --html=reports/pytest-report.html --self-contained-html
```

## Configuration

Copy `.env.example` to `.env` only when overrides are needed. `.env`, generated reports, caches, and virtual environments are excluded from source control. Never place credentials in test modules or command-line logs.

The main configuration knobs are the two API URLs, both test-user credential pairs, request/readiness timeouts, the pinned SUT image, and the load profile. After a five-second warm-up, load defaults to 25 users with one request per user per second, providing headroom above the required 20 RPS and enforcing at least 1,000 successful requests in 60 seconds.

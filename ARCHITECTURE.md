# Architecture

## Dependency direction

```text
tests/specs
    |
    v
workflows  ----->  support
    |
    v
api  ------------> domain
    |
    v
transport  ------> config
```

`contract`, `reporting`, and `commands` are focused side boundaries. The architecture unit test parses imports and rejects upward dependencies from `domain`, `transport`, or `api`.

## Layer responsibilities

- `domain`: transport-independent request and response models.
- `config`: environment parsing and secret-safe credentials.
- `transport`: URL invariants, HTTP execution, authentication, methods, and redacted diagnostics. It accepts relative paths only.
- `api`: endpoint-specific gateways. Typed positive methods and explicitly named `*_unvalidated` negative-test methods are separate interfaces.
- `workflows`: cross-endpoint setup, tenant graphs, authentication probes, entity ownership, and cleanup coordination.
- `contract`: live Swagger acquisition and runtime response-schema validation.
- `support`: deterministic test-data builders.
- `commands`: implementation of CLI commands; `__main__.py` is the single package entry point.
- `tests/specs`: thin scenario intent, assertions, and release decisions.

## Important decisions

### API clients, not generic resources

`IntegrationsClient` and `AssetsClient` clearly communicate that these classes make service calls. The earlier generic `resources.py` container was removed.

### Strict paths instead of silent normalization

The transport normalizes the configured base URL once. Every API path must then be relative; absolute paths or leading slashes fail fast. This prevents hidden `lstrip` behavior and accidental loss of `/api/v1`.

### Contract compliance and behavior are independent signals

Dedicated tests require the Swagger-documented create status. Behavioral setup accepts any successful 2xx response so an undocumented `201` remains a release blocker without preventing CRUD and tenant-isolation coverage.

### Cleanup records ownership

`CreatedEntityRegistry` stores only entities owned by the current test. `CleanupManager` deletes children before parents and returns a structured `CleanupReport`; cleanup failures cannot hide the original assertion.

### One executable boundary

All container commands use `python -m automation_assignment <subcommand>`. The package exposes `wait-for-api` and `write-summary` subcommands.

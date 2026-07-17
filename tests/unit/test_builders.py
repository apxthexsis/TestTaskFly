from automation_assignment.support import DataFactory


def test_factory_generates_unique_traceable_data() -> None:
    factory = DataFactory(run_id="known-run")
    first = factory.integration()
    second = factory.integration()
    asset = factory.asset("integration-id")
    assert first.name != second.name
    assert first.name.startswith("qa-known-run-")
    assert asset.integration_id == "integration-id"
    assert asset.name.startswith("qa-known-run-")

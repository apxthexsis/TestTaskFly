from unittest.mock import Mock, call

from automation_assignment.workflows import CleanupManager, CreatedEntityRegistry


def test_cleanup_deletes_children_first_and_reports_failures() -> None:
    calls = Mock()
    integrations = Mock()
    assets = Mock()

    def delete_asset(entity_id: str) -> None:
        calls("asset", entity_id)
        if entity_id == "asset-2":
            raise RuntimeError("simulated cleanup failure")

    assets.delete.side_effect = delete_asset
    integrations.delete.side_effect = lambda entity_id: calls("integration", entity_id)
    registry = CreatedEntityRegistry(
        integration_ids=["integration-1", "integration-2"],
        asset_ids=["asset-1", "asset-2"],
    )

    report = CleanupManager(integrations, assets).cleanup(registry)

    assert calls.call_args_list == [
        call("asset", "asset-2"),
        call("asset", "asset-1"),
        call("integration", "integration-2"),
        call("integration", "integration-1"),
    ]
    assert not report.succeeded
    assert [(failure.entity_type, failure.entity_id) for failure in report.failures] == [
        ("asset", "asset-2")
    ]

from __future__ import annotations

from typing import Any

import httpx
import pytest

from automation_assignment.api import IntegrationsClient
from automation_assignment.workflows import AuthenticationProbe

pytestmark = [pytest.mark.api, pytest.mark.security]


@pytest.mark.bug("BUG-007")
@pytest.mark.parametrize(
    "probe_fixture",
    [
        "anonymous_authentication_probe",
        "invalid_password_authentication_probe",
        "unknown_user_authentication_probe",
        "malformed_authentication_probe",
    ],
)
def test_every_operation_rejects_invalid_authentication(
    probe_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    probe: AuthenticationProbe = request.getfixturevalue(probe_fixture)
    failures: list[str] = []
    for operation in probe.operations():
        response = operation.call()
        if response.status_code != httpx.codes.UNAUTHORIZED:
            failures.append(
                f"{operation.name}: expected 401, got {response.status_code} {response.text}"
            )
        assert "password" not in response.text.lower()
        assert "authorization" not in response.text.lower()
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize(
    "fixture_name",
    ["user1_integrations_client", "user2_integrations_client"],
)
def test_both_supplied_users_can_authenticate(
    fixture_name: str,
    request: pytest.FixtureRequest,
) -> None:
    client: IntegrationsClient = request.getfixturevalue(fixture_name)
    response = client.list()
    assert response.status_code == httpx.codes.OK, response.text
    assert isinstance(response.json(), list)


def test_response_never_echoes_basic_auth_credentials(
    anonymous_authentication_probe: AuthenticationProbe,
    settings: Any,
) -> None:
    response = anonymous_authentication_probe.operations()[0].call()
    forbidden = {
        settings.test_user_1_username,
        settings.test_user_1_password.get_secret_value(),
        settings.test_user_2_username,
        settings.test_user_2_password.get_secret_value(),
    }
    assert all(secret not in response.text for secret in forbidden)

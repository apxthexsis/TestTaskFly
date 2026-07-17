import pytest
from pydantic import SecretStr, ValidationError

from automation_assignment.config import Credentials, Settings


def _environment() -> dict[str, str]:
    return {
        "TEST_USER_1_USERNAME": "alpha",
        "TEST_USER_1_PASSWORD": "alpha-secret",
        "TEST_USER_2_USERNAME": "beta",
        "TEST_USER_2_PASSWORD": "beta-secret",
    }


def test_settings_load_credentials_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _environment().items():
        monkeypatch.setenv(key, value)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.user1.as_auth_tuple() == ("alpha", "alpha-secret")
    assert settings.user2.as_auth_tuple() == ("beta", "beta-secret")
    assert "alpha-secret" not in repr(settings)


def test_blank_username_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _environment().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("TEST_USER_1_USERNAME", " ")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_credentials_do_not_print_password() -> None:
    credentials = Credentials(username="user", password=SecretStr("top-secret"))
    assert "top-secret" not in repr(credentials)

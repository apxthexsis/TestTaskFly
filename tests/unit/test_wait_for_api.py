import httpx

from automation_assignment.commands.readiness import wait_for_api
from automation_assignment.config import Settings


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        api_spec_url="http://unavailable/swagger/doc.json",
        api_readiness_timeout_seconds=1,
        api_timeout_seconds=1,
        test_user_1_username="alpha",
        test_user_1_password="alpha-secret",
        test_user_2_username="beta",
        test_user_2_password="beta-secret",
    )  # type: ignore[call-arg]


def test_readiness_timeout_returns_failure() -> None:
    settings = _settings()
    clock = iter([0.0, 0.0, 2.0])
    output: list[str] = []

    def unavailable(url: str, *, timeout: float) -> httpx.Response:
        del timeout
        request = httpx.Request("GET", url)
        raise httpx.ConnectError("unavailable", request=request)

    result = wait_for_api(
        settings,
        get=unavailable,
        monotonic=lambda: next(clock),
        sleep=lambda _: None,
        output=output.append,
    )

    assert result == 1
    assert "readiness timed out" in output[0]

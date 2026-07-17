import pytest

from automation_assignment.transport import HttpClient, HttpMethod, normalize_base_url

TEST_API_BASE_URL = "http://service.test/api/v1"


def test_base_url_is_normalized_once_without_dropping_api_path() -> None:
    assert str(normalize_base_url(TEST_API_BASE_URL)) == f"{TEST_API_BASE_URL}/"
    assert str(normalize_base_url(f"{TEST_API_BASE_URL}/")) == f"{TEST_API_BASE_URL}/"


def test_base_url_requires_an_absolute_service_url() -> None:
    with pytest.raises(ValueError, match="absolute"):
        normalize_base_url("/api/v1")


@pytest.mark.parametrize("path", ["", "/integrations", "https://other.test/integrations"])
def test_transport_rejects_paths_outside_its_relative_path_contract(path: str) -> None:
    with (
        HttpClient(TEST_API_BASE_URL) as client,
        pytest.raises(ValueError, match="relative path"),
    ):
        client.request(HttpMethod.GET, path)

from automation_assignment.transport.redaction import REDACTED, redact


def test_redaction_is_recursive_and_case_insensitive() -> None:
    value = {
        "Authorization": "Basic secret",
        "nested": {"password": "secret", "safe": "visible"},
        "items": [{"proxy-authorization": "secret"}],
    }
    result = redact(value)
    assert result["Authorization"] == REDACTED
    assert result["nested"]["password"] == REDACTED
    assert result["nested"]["safe"] == "visible"
    assert result["items"][0]["proxy-authorization"] == REDACTED

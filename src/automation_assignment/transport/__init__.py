"""HTTP transport primitives independent of API resources."""

from automation_assignment.transport.http_client import HttpClient, normalize_base_url
from automation_assignment.transport.http_method import HttpMethod

__all__ = ["HttpClient", "HttpMethod", "normalize_base_url"]

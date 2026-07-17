"""Endpoint-specific service clients."""

from automation_assignment.api.assets_client import AssetsClient
from automation_assignment.api.integrations_client import IntegrationsClient

__all__ = ["AssetsClient", "IntegrationsClient"]

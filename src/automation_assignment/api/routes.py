"""Single source of API and Swagger resource paths."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceRoutes:
    collection: str

    def item(self, resource_id: str) -> str:
        return f"{self.collection}/{resource_id}"

    @property
    def contract_collection(self) -> str:
        return f"/{self.collection}"

    @property
    def contract_item(self) -> str:
        return f"/{self.collection}/{{id}}"


INTEGRATIONS = ResourceRoutes("integrations")
ASSETS = ResourceRoutes("assets")

INTEGRATION_ID_QUERY = "integrationId"
JSON_CONTENT_TYPE = "application/json"

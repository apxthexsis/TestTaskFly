"""Typed domain requests and API responses."""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateIntegrationRequest(ApiModel):
    name: str
    type: str


class UpdateIntegrationRequest(ApiModel):
    id: str
    name: str


class Integration(ApiModel):
    id: str
    name: str
    tenant_id: str
    type: str


class CreateAssetRequest(ApiModel):
    name: str
    description: str
    integration_id: str


class UpdateAssetRequest(ApiModel):
    id: str
    name: str
    description: str


class Asset(ApiModel):
    id: str
    name: str
    description: str
    integration_id: str
    tenant_id: str


class HttpError(ApiModel):
    code: int
    message: str

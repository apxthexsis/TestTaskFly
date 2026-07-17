"""Validated configuration and secret-safe credentials."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Credentials(BaseModel):
    """A Basic Authentication identity without a printable password."""

    username: str
    password: SecretStr

    def as_auth_tuple(self) -> tuple[str, str]:
        return self.username, self.password.get_secret_value()


class Settings(BaseSettings):
    """Single source of configuration for tests, orchestration, and load."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_base_url: AnyHttpUrl = AnyHttpUrl("http://sut:8080/api/v1")
    api_spec_url: AnyHttpUrl = AnyHttpUrl("http://sut:8080/swagger/doc.json")
    api_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    api_readiness_timeout_seconds: float = Field(default=60.0, gt=0, le=600)

    test_user_1_username: str
    test_user_1_password: SecretStr
    test_user_2_username: str
    test_user_2_password: SecretStr

    load_users: int = Field(default=25, ge=1, le=10_000)
    load_spawn_rate: float = Field(default=25.0, gt=0)
    load_duration_seconds: int = Field(default=60, ge=1)
    load_min_successful_requests: int = Field(default=1_000, ge=1)
    load_target_rps: float = Field(default=20.0, gt=0)

    @field_validator("test_user_1_username", "test_user_2_username")
    @classmethod
    def username_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("username must not be blank")
        return value

    @property
    def base_url(self) -> str:
        return str(self.api_base_url)

    @property
    def spec_url(self) -> str:
        return str(self.api_spec_url)

    @property
    def user1(self) -> Credentials:
        return Credentials(
            username=self.test_user_1_username,
            password=self.test_user_1_password,
        )

    @property
    def user2(self) -> Credentials:
        return Credentials(
            username=self.test_user_2_username,
            password=self.test_user_2_password,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
